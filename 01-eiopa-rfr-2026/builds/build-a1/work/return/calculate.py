"""Offline implementation of EIOPA-BoS-26/198 (May 2026)."""

import argparse
import json
import math
import re
import tempfile
from pathlib import Path

from scipy.optimize import brentq

from portfolios import calculate_portfolio_examples


def decode(value):
    if value in ("TRUE", "FALSE"):
        return value == "TRUE"
    try:
        return float(value)
    except ValueError:
        return re.sub(r"\\([\\tn])", lambda m: {"\\": "\\", "t": "\t", "n": "\n"}[m[1]], value)


class Workbook:
    def __init__(self, directory):
        self.sheets = {}
        for path in sorted(Path(directory).glob("*.tsv")):
            for line in path.read_text(encoding="utf-8").splitlines():
                address, value = line.split("\t", 1)
                sheet, cell = address.rsplit("!", 1)
                if re.fullmatch(r"[A-Z]+[0-9]+", cell):
                    self.sheets.setdefault(sheet, {})[cell] = decode(value)

    def __getitem__(self, name):
        return self.sheets[name]


def e1_controls(book):
    sheet = book["Input Data & Extrapolation"]
    rows = sorted(int(k[1:]) for k in sheet if re.fullmatch(r"G\d+", k) and isinstance(sheet[k], float))
    maturities = {r: int(sheet[f"G{r}"]) for r in rows}
    dlt = [maturities[r] for r in rows if sheet.get(f"H{r}") == 1]
    weights = {maturities[r]: sheet[f"I{r}"] for r in rows if sheet.get(f"I{r}", 0) > 0}
    return sheet, maturities, dlt, weights, min(weights)


def bootstrap(book):
    """D.3.5, D.4.8 and D.5: par repricing with constant interval forwards."""
    s, rows, dlt, weights, fsp = e1_controls(book)
    if s["H11"] != "SWP":
        raise ValueError("This example implementation requires par swap inputs")
    frequency = int(s["H12"])
    cra = s["H16"] / 10000.0
    rates = {t: s[f"J{r}"] - cra for r, t in rows.items() if t in dlt}
    discounts = [1.0]
    previous = 0
    for maturity in dlt:
        coupon = rates[maturity] / frequency
        n = (maturity - previous) * frequency
        base = discounts[-1]
        known = math.fsum(discounts[1:])
        if previous == 0:
            forward_cc_per_period = math.log1p(coupon)
        else:
            def residual(x):
                tail = [base * math.exp(-j * x) for j in range(1, n + 1)]
                return coupon * (known + math.fsum(tail)) + tail[-1] - 1.0
            forward_cc_per_period = brentq(residual, -0.5, 0.5, xtol=5e-16, rtol=9e-16)
            if abs(residual(forward_cc_per_period)) > 2e-13:
                raise ArithmeticError("Bootstrap root does not reprice the swap")
        discounts.extend(base * math.exp(-j * forward_cc_per_period) for j in range(1, n + 1))
        previous = maturity
    zero_cc = {t: -math.log(discounts[t * frequency]) / t for t in range(1, max(dlt) + 1)}
    previous_dlt = max((t for t in dlt if t < fsp), default=0)
    first_forward = (fsp * zero_cc[fsp] - previous_dlt * zero_cc.get(previous_dlt, 0.0)) / (fsp - previous_dlt)
    llfr = weights[fsp] * first_forward + math.fsum(
        w * (t * zero_cc[t] - fsp * zero_cc[fsp]) / (t - fsp)
        for t, w in weights.items() if t > fsp
    )
    curve = extrapolate(zero_cc, llfr, fsp, s["H14"], s["H15"], rows.values())
    return {"zero_rates_cc": stringify(zero_cc), "llfr": llfr, "basic_rfr": stringify(curve)}


def stringify(curve):
    return {str(t): float(x) for t, x in curve.items()}


def extrapolate(zero_cc, llfr, fsp, ufr, alpha, maturities):
    """8.5.5--8.5.8; also 10.2.2--10.2.4 for adjusted inputs."""
    result = {}
    ufr_cc = math.log1p(ufr)
    for t in maturities:
        if t <= fsp:
            rate = zero_cc[t]
        else:
            h = t - fsp
            b = -math.expm1(-alpha * h) / (alpha * h)
            forward = ufr_cc + (llfr - ufr_cc) * b
            rate = (fsp * zero_cc[fsp] + h * forward) / t
        result[t] = math.expm1(rate)
    return result


def unit_clip(x):
    return max(0.0, min(x, 1.0))


def with_va(a1, book, va, maturity_sheet):
    """10.1.6 and 10.2.1: shift log forwards and the first LLFR term."""
    s, rows, dlt, weights, fsp = e1_controls(book)
    shift = math.log1p(va)
    zero_cc = {t: math.log1p(a1["basic_rfr"][str(t)]) + shift for t in range(1, fsp + 1)}
    llfr = a1["llfr"] + weights[fsp] * shift
    grid = sorted(int(v) for k, v in book[maturity_sheet].items()
                  if re.fullmatch(r"G\d+", k) and isinstance(v, float))
    curve = extrapolate(zero_cc, llfr, fsp, s["H14"], s["H15"], grid)
    return llfr, stringify(curve)


def downstream_from_a1_file(book, path):
    """The sole A1 interface for A2/A3, used in normal and --a1 runs."""
    a1 = json.loads(Path(path).read_text(encoding="utf-8"))
    s = book["Input Data & Extrapolation"]
    css = book["CSSR Calculation"]
    controls = book["VA Term Structures"]
    notional_va = 0.85 * s["L10"]
    cssr = unit_clip((css["L11"] - css["L10"]) / (css["L14"] - css["L13"]))
    llfr2, curve2 = with_va(a1, book, notional_va, "CSSR Calculation")
    usa = min(controls["H12"], 1.05) if controls["H11"] else 1.0
    currency_va = 0.85 * cssr * s["L10"] * usa
    omega = unit_clip((s["L11"] * s["L12"] - 0.006) / 0.003)
    macro_va = 0.0
    if controls["H10"] and not controls["H11"]:
        macro_va = 0.85 * cssr * max(s["L11"] - 1.3 * s["L10"], 0.0) * omega
    total_va = currency_va + macro_va
    llfr3, curve3 = with_va(a1, book, total_va, "VA Term Structures")
    return ({"notional_va": notional_va, "cssr": cssr, "llfr": llfr2, "curve": curve2},
            {"currency_va": currency_va, "omega_co": omega, "total_va": total_va,
             "llfr": llfr3, "curve": curve3})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--a1", type=Path)
    args = parser.parse_args()
    book = Workbook(args.bundle / "E1")
    if args.a1:
        a1 = json.loads(args.a1.read_text(encoding="utf-8"))
        a2, a3 = downstream_from_a1_file(book, args.a1)
    else:
        a1 = bootstrap(book)
        with tempfile.TemporaryDirectory(prefix="eiopa-a1-") as temporary:
            path = Path(temporary) / "a1.json"
            path.write_text(json.dumps(a1, allow_nan=False), encoding="utf-8")
            a2, a3 = downstream_from_a1_file(book, path)
    b1, b2, c1 = calculate_portfolio_examples(Workbook(args.bundle / "E2"), Workbook(args.bundle / "E3"))
    result = {"A1": a1, "A2": a2, "A3": a3, "B1": b1, "B2": b2, "C1": c1}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
