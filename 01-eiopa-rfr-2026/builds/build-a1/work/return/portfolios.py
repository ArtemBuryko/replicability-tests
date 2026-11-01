"""Reference-portfolio calculations: Sections 9.2 and Annexes E, F, G."""

import bisect
import math
import re
from decimal import Decimal, ROUND_HALF_UP

from scipy.optimize import brentq


# Methodological country/currency and peer mappings: Table 1 and Annex A.
EURO_AREA = set("AT BE BG CY DE EE EL ES FI FR GR HR IE IT LT LU LV MT NL PT SI SK".split())
EEA = EURO_AREA | set("CZ DK HU IS LI NO PL RO SE".split())
LOCAL_CURRENCY = {
    **{country: "EUR" for country in EURO_AREA},
    "AU": "AUD", "CA": "CAD", "CH": "CHF", "CN": "CNY", "CO": "COP",
    "CZ": "CZK", "DK": "DKK", "HK": "HKD", "HU": "HUF", "IS": "ISK",
    "JP": "JPY", "LI": "CHF", "NO": "NOK", "PL": "PLN", "RO": "RON",
    "SE": "SEK", "TW": "TWD", "UK": "GBP", "US": "USD",
}
PEER = {"EE": "BE", "LV": "SK", "LI": "CH", "LU": "NL"}


def numeric(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def col_number(col):
    result = 0
    for c in col:
        result = 26 * result + ord(c) - ord("A") + 1
    return result


def col_name(n):
    result = ""
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(ord("A") + r) + result
    return result


def cells_by_row(sheet):
    rows = {}
    for address, value in sheet.items():
        col, row = re.fullmatch(r"([A-Z]+)(\d+)", address).groups()
        rows.setdefault(int(row), {})[col] = value
    return dict(sorted(rows.items()))


def linear(points, t):
    """G.1.2: linear interpolation of yields, flat outside observed knots."""
    points = sorted(points)
    if not points:
        raise ValueError("No yield observations available")
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]
    j = bisect.bisect_left([p[0] for p in points], t)
    x0, y0 = points[j - 1]
    x1, y1 = points[j]
    return y0 + (y1 - y0) * (t - x0) / (x1 - x0)


def table_curves(sheet, header_row, xcol="F"):
    """Read a horizontal table until the next nonnumeric maturity row."""
    rows = cells_by_row(sheet)
    labels = {c: label for c, label in rows[header_row].items() if c != xcol}
    result = {label: [] for label in labels.values()}
    row = header_row + 1
    while numeric(rows.get(row, {}).get(xcol)):
        data = rows[row]
        for col, label in labels.items():
            if numeric(data.get(col)):
                result[label].append((data[xcol], data[col]))
        row += 1
    return result


def corporate_curves(sheet):
    rows = cells_by_row(sheet)
    result = {}
    for row, cells in rows.items():
        for col, label in cells.items():
            if not isinstance(label, str) or not re.fullmatch(r"(?:Non-)?Financials CQS [0-6]", label):
                continue
            duration_col = col_name(col_number(col) + 1)
            yield_col = col_name(col_number(col) + 2)
            points = []
            r = row + 3
            while isinstance(rows.get(r, {}).get(col), str):
                entry = rows[r]
                if numeric(entry.get(duration_col)) and numeric(entry.get(yield_col)):
                    points.append((entry[duration_col], entry[yield_col]))
                r += 1
            if points:
                if int(label[-1]) >= 4:
                    # Table 12: one index for the whole rating, regardless of tenor.
                    points = points[:1]
                result[label] = points
    for sector in ("Financials", "Non-Financials"):
        # Tables 12 and 13. Source index durations retain their supplied precision.
        result[f"{sector} CQS 0"] = [
            (d, y * (0.85 if y >= 0 else 1.15))
            for d, y in result[f"{sector} CQS 1"]
        ]
        result[f"{sector} CQS 6"] = result[f"{sector} CQS 5"]
    return result


def reference_portfolios(sheet):
    result = {}
    current = None
    for row, cells in cells_by_row(sheet).items():
        label = cells.get("F")
        if isinstance(label, str):
            match = re.match(r"(Currency|Country) RCS ([A-Z]+) -", label)
            if match:
                current = (match[1], match[2])
                result[current] = []
                continue
        weight = cells.get("G", 0.0)
        if current and numeric(weight) and weight > 0:
            duration = float(Decimal(str(cells["H"])).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            result[current].append({
                "issuer": label, "weight": weight, "duration": duration,
                "cashflows": tuple(cells[c] for c in ("I", "J", "K")),
            })
    for portfolio in result.values():
        if not math.isclose(math.fsum(p["weight"] for p in portfolio), 1.0, abs_tol=1e-12):
            raise ValueError("Reference composition does not sum to one")
    return result


def risk_correction(spread, ltas, eea_government):
    """G.6.2/G.6.4: positive parts, marginal bands, LTAS cap."""
    s = max(spread, 0.0)
    l = max(ltas, 0.0)
    cap, first, second, third = ((0.65, 0.30, 0.20, 0.15) if eea_government
                                else (1.25, 0.50, 0.40, 0.30))
    return min(cap * l, first * min(s, l)
               + second * max(0.0, min(s - l, l))
               + third * max(0.0, s - 2.0 * l))


def portfolio_irr(cashflows, durations, yields):
    """F.3.4: preserve the supplied, yield-specific frozen cash flows."""
    logs = [math.log1p(y) for y in yields]
    present_value = math.fsum(cf * math.exp(-d * y) for cf, d, y in zip(cashflows, durations, logs))

    def residual(log_yield):
        return math.fsum(cf * math.exp(-d * log_yield) for cf, d in zip(cashflows, durations)) - present_value

    low, high = min(logs), max(logs)
    if low == high:
        root = low
    else:
        root = brentq(residual, low - 1e-14, high + 1e-14, xtol=5e-16, rtol=9e-16)
    if abs(residual(root)) > 2e-13 * max(1.0, abs(present_value)):
        raise ArithmeticError("Portfolio IRR does not reproduce present value")
    return math.expm1(root)


class PortfolioModel:
    def __init__(self, workbook):
        self.gov = table_curves(workbook["Gov Rates"], 8)
        self.rfr = table_curves(workbook["RFR"], 10)
        self.gov_ltas = table_curves(workbook["LTAS"], 10)
        self.corp_ltas = {}
        for row, cells in cells_by_row(workbook["LTAS"]).items():
            label = cells.get("F")
            if isinstance(label, str):
                match = re.fullmatch(r"([A-Z]+) ((?:Non-)?Financials)", label)
                if match:
                    for rating, points in table_curves(workbook["LTAS"], row + 2).items():
                        self.corp_ltas[(match[1], match[2] + " " + rating)] = points
        self.corp = corporate_curves(workbook["Corp Data"])
        self.gov_portfolios = reference_portfolios(workbook["Government Bond Ref. Portfolios"])
        self.corp_portfolios = reference_portfolios(workbook["Corporate Bond Ref. Portfolio"])
        self.weights = {}
        for row, cells in cells_by_row(workbook["Reference Portfolio Weights"]).items():
            if numeric(cells.get("G")) and numeric(cells.get("H")):
                total = cells["G"] + cells["H"]
                self.weights[cells["F"]] = (cells["G"] / total, cells["H"] / total)

    def government_yields(self, key, model_bond):
        portfolio_type, currency_or_country = key
        issuer = model_bond["issuer"]
        d = model_bond["duration"]
        rfr = linear(self.rfr[LOCAL_CURRENCY[issuer]], d)
        if portfolio_type == "Currency" and currency_or_country == "EUR" and issuer in EURO_AREA:
            market = linear(self.gov["ECB Curve"], d)
            ltas = linear(self.gov_ltas["EUR"], d)
        else:
            source = PEER.get(issuer, issuer)
            market = linear(self.gov[source], d)
            ltas = linear(self.gov_ltas[source], d)
        correction = risk_correction(market - rfr, ltas, issuer in EEA)
        return market, rfr, market - correction

    def corporate_yields(self, key, model_bond):
        portfolio_type, currency_or_country = key
        currency = currency_or_country if portfolio_type == "Currency" else LOCAL_CURRENCY[currency_or_country]
        issuer = model_bond["issuer"]
        d = model_bond["duration"]
        rfr = linear(self.rfr[currency], d)
        market = linear(self.corp[issuer], d)
        if currency in ("GBP", "USD") and int(issuer[-1]) >= 4:
            # G.5.3 and G.5.5: the supplied high-yield blocks are EUR proxies.
            euro_rfr = linear(self.rfr["EUR"], d)
            market = rfr + max(0.0, market - euro_rfr + 0.5 * (rfr - euro_rfr))
        ltas = linear(self.corp_ltas[(currency, issuer)], d)
        correction = risk_correction(market - rfr, ltas, False)
        return market, rfr, market - correction

    def bond_portfolio_yields(self, key, kind):
        if kind == "gov":
            bonds = self.gov_portfolios[key]
            yield_function = self.government_yields
        else:
            bonds = self.corp_portfolios[key]
            yield_function = self.corporate_yields
        yields = [yield_function(key, bond) for bond in bonds]
        durations = [bond["duration"] for bond in bonds]
        return tuple(portfolio_irr([bond["cashflows"][j] for bond in bonds], durations,
                                   [ys[j] for ys in yields]) for j in range(3))

    def calculate(self, key):
        w_gov, w_corp = self.weights[key[1]]
        gov = self.bond_portfolio_yields(key, "gov")
        corp = self.bond_portfolio_yields(key, "corp")
        s_gov, s_corp = gov[0] - gov[1], corp[0] - corp[1]
        rc_gov, rc_corp = gov[0] - gov[2], corp[0] - corp[2]
        s = w_gov * s_gov + w_corp * s_corp
        rc = w_gov * rc_gov + w_corp * rc_corp
        return {"w_gov": w_gov, "w_corp": w_corp, "s_gov": s_gov, "s_corp": s_corp,
                "rc_gov": rc_gov, "rc_corp": rc_corp, "s": s, "rc": rc, "rcs": s - rc}


def calculate_portfolio_examples(book2, book3):
    model2, model3 = PortfolioModel(book2), PortfolioModel(book3)
    currency2 = next(key for key in model2.gov_portfolios if key[0] == "Currency")
    country2 = next(key for key in model2.gov_portfolios if key[0] == "Country")
    currency3 = next(key for key in model3.gov_portfolios if key[0] == "Currency")
    return model2.calculate(currency2), model2.calculate(country2), model3.calculate(currency3)
