#!/usr/bin/env python3
"""Implementation of EIOPA-BoS-26/198 worked examples A1, A2, A3, B1, B2, C1."""

import argparse
import json
import math
import os
from typing import Dict, List, Tuple
from scipy.optimize import brentq

TAB = chr(9)
NL = chr(10)
CR = chr(13)
CRLF = CR + NL


def parse_cell_coord(cell_ref: str) -> Tuple[str, int]:
    col = "".join(ch for ch in cell_ref if ch.isalpha())
    row = int("".join(ch for ch in cell_ref if ch.isdigit()))
    return col, row


def load_tsv_cells(filepath: str) -> Dict[str, str]:
    cells: Dict[str, str] = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip(CRLF)
            if not line:
                continue
            parts = line.split(TAB, 1)
            if len(parts) != 2:
                continue
            sheet_cell, val = parts
            cell_coord = sheet_cell.split("!", 1)[1] if "!" in sheet_cell else sheet_cell
            cells[cell_coord] = val
    return cells


def load_e1_sheets(e1_dir: str) -> Dict[str, Dict[str, str]]:
    sheets: Dict[str, Dict[str, str]] = {}
    for fname in sorted(os.listdir(e1_dir)):
        if not fname.endswith(".tsv") or fname == "labels.tsv":
            continue
        fpath = os.path.join(e1_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip(CRLF)
                if not line:
                    continue
                sheet_cell, val = line.split(TAB, 1)
                sheet, cell = sheet_cell.split("!", 1)
                sheets.setdefault(sheet, {})[cell] = val
    return sheets


def parse_bool(val: str) -> bool:
    return val.strip().upper() == "TRUE"


def compute_a1(e1_sheets: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    ide = e1_sheets["Input Data & Extrapolation"]

    extrapolate = parse_bool(ide["H10"])
    inst_type = ide["H11"].strip().upper()
    m1 = int(float(ide["H12"]))
    ufr = float(ide["H14"])
    alpha = float(ide["H15"])
    cra = float(ide["H16"]) / 10000.0

    maturities: List[int] = []
    dlt_tenors: List[int] = []
    s_rates: Dict[int, float] = {}
    weights: Dict[int, float] = {}

    row = 25
    while f"G{row}" in ide:
        t = int(float(ide[f"G{row}"]))
        maturities.append(t)
        is_dlt = int(float(ide.get(f"H{row}", "0"))) == 1
        w = float(ide.get(f"I{row}", "0"))
        weights[t] = w
        if is_dlt and f"J{row}" in ide:
            dlt_tenors.append(t)
            raw_rate = float(ide[f"J{row}"])
            if inst_type == "OIS":
                s_rates[t] = raw_rate
            else:
                s_rates[t] = raw_rate - cra
        row += 1

    dlt_tenors.sort()
    t_L = dlt_tenors[-1]

    d_factors: Dict[float, float] = {}
    z_rates: Dict[float, float] = {}

    if inst_type in ("SWP", "OIS"):
        t1 = dlt_tenors[0]
        s_t1_m1 = s_rates[t1] / m1
        f_star_prev = s_t1_m1
        for j in range(1, m1 * t1 + 1):
            t_val = j / m1
            d_val = (1.0 + s_t1_m1) ** (-j)
            d_factors[t_val] = d_val
            z_rates[t_val] = (d_val ** (-m1 / j)) - 1.0

        for idx in range(len(dlt_tenors) - 1):
            tk = dlt_tenors[idx]
            tk1 = dlt_tenors[idx + 1]
            s_tk_m1 = s_rates[tk] / m1
            s_tk1_m1 = s_rates[tk1] / m1
            d_tk = d_factors[float(tk)]
            n_periods = m1 * (tk1 - tk)

            f_star = f_star_prev
            const_term = ((s_tk1_m1 - s_tk_m1) / s_tk_m1) * ((1.0 - d_tk) / d_tk) - 1.0
            for _ in range(200):
                d_star = (1.0 + f_star) ** (-n_periods)
                g_val = s_tk1_m1 * (1.0 - d_star) / f_star + d_star + const_term
                if abs(g_val) < 1e-15:
                    break
                d_star_prime = -n_periods * d_star / (1.0 + f_star)
                g_prime = (
                    s_tk1_m1 * ((-d_star_prime * f_star - (1.0 - d_star)) / (f_star ** 2))
                    + d_star_prime
                )
                f_star = f_star - g_val / g_prime

            f_star_prev = f_star
            for j in range(1, n_periods + 1):
                t_val = tk + j / m1
                d_val = d_tk * ((1.0 + f_star) ** (-j))
                d_factors[t_val] = d_val
                z_rates[t_val] = (d_val ** (-1.0 / t_val)) - 1.0
    elif inst_type == "GVT":
        t1 = dlt_tenors[0]
        r_t1 = s_rates[t1]
        for j in range(1, t1 + 1):
            t_val = float(j)
            d_val = (1.0 / (1.0 + r_t1)) ** j
            d_factors[t_val] = d_val
            z_rates[t_val] = r_t1
        for idx in range(len(dlt_tenors) - 1):
            tk = dlt_tenors[idx]
            tk1 = dlt_tenors[idx + 1]
            d_tk = (1.0 / (1.0 + s_rates[tk])) ** tk
            d_tk1 = (1.0 / (1.0 + s_rates[tk1])) ** tk1
            f_tk_tk1 = (d_tk / d_tk1) ** (1.0 / (tk1 - tk)) - 1.0
            for j in range(tk + 1, tk1 + 1):
                t_val = float(j)
                d_val = d_tk * ((1.0 / (1.0 + f_tk_tk1)) ** (j - tk))
                d_factors[t_val] = d_val
                z_rates[t_val] = (d_val ** (-1.0 / j)) - 1.0
    else:
        raise ValueError(f"Unsupported instrument type: {inst_type}")

    zero_rates_cc: Dict[str, float] = {}
    z_cc_int: Dict[int, float] = {}
    for t in range(1, t_L + 1):
        zc = math.log(1.0 + z_rates[float(t)])
        z_cc_int[t] = zc
        zero_rates_cc[str(t)] = zc

    dlt_with_weight = [t for t in dlt_tenors if weights.get(t, 0.0) > 0.0]
    t_F = dlt_with_weight[0] if dlt_with_weight else t_L

    fsp_dlt_tenors = [t for t in dlt_tenors if t >= t_F]
    w_sum = sum(weights.get(t, 0.0) for t in fsp_dlt_tenors)
    w_norm = {t: weights.get(t, 0.0) / w_sum for t in fsp_dlt_tenors}

    f_before_fsp = t_F * z_cc_int[t_F] - (t_F - 1) * z_cc_int[t_F - 1]
    llfr_c = w_norm[t_F] * f_before_fsp
    for tk in fsp_dlt_tenors:
        if tk > t_F:
            f_after_fsp = (tk * z_cc_int[tk] - t_F * z_cc_int[t_F]) / (tk - t_F)
            llfr_c += w_norm[tk] * f_after_fsp

    basic_rfr: Dict[str, float] = {}
    ufr_c = math.log(1.0 + ufr)
    max_mat = max(maturities)
    cutoff = t_F if extrapolate else t_L
    for t in range(1, cutoff + 1):
        basic_rfr[str(t)] = z_rates[float(t)]

    if extrapolate:
        for h in range(1, max_mat - t_F + 1):
            t = t_F + h
            b_ah = (1.0 - math.exp(-alpha * h)) / (alpha * h)
            f_c = ufr_c + (llfr_c - ufr_c) * b_ah
            z_c = (t_F * z_cc_int[t_F] + h * f_c) / (t_F + h)
            basic_rfr[str(t)] = math.exp(z_c) - 1.0

    return {
        "zero_rates_cc": zero_rates_cc,
        "llfr": llfr_c,
        "basic_rfr": basic_rfr,
    }


def build_va_curve(
    a1_res: Dict[str, object],
    va_decimal: float,
    t_F: int,
    w_tF: float,
    ufr: float,
    alpha: float,
    maturities: List[int],
) -> Tuple[float, Dict[str, float]]:
    basic_rfr: Dict[str, float] = a1_res["basic_rfr"]  # type: ignore[assignment]
    llfr_c = float(a1_res["llfr"])  # type: ignore[arg-type]

    z_c: Dict[int, float] = {}
    for t in range(1, t_F + 1):
        z_c[t] = math.log(1.0 + float(basic_rfr[str(t)]))

    f_c: Dict[int, float] = {}
    f_va_c: Dict[int, float] = {}
    va_c = math.log(1.0 + va_decimal)

    for t in range(1, t_F + 1):
        prev_zc = z_c[t - 1] if t > 1 else 0.0
        f_c[t] = t * z_c[t] - (t - 1) * prev_zc
        f_va_c[t] = f_c[t] + va_c

    llfr_va_c = llfr_c + w_tF * (f_va_c[t_F] - f_c[t_F])

    z_va_c: Dict[int, float] = {}
    for t in range(1, t_F + 1):
        prev_z_va_c = z_va_c[t - 1] if t > 1 else 0.0
        z_va_c[t] = ((t - 1) * prev_z_va_c + f_va_c[t]) / t

    ufr_c = math.log(1.0 + ufr)
    max_mat = max(maturities)
    for h in range(1, max_mat - t_F + 1):
        b_ah = (1.0 - math.exp(-alpha * h)) / (alpha * h)
        f_extrap = ufr_c + (llfr_va_c - ufr_c) * b_ah
        z_va_c[t_F + h] = (t_F * z_va_c[t_F] + h * f_extrap) / (t_F + h)

    curve: Dict[str, float] = {}
    for t in maturities:
        curve[str(t)] = math.exp(z_va_c[t]) - 1.0

    return llfr_va_c, curve


def compute_a2_a3(
    e1_sheets: Dict[str, Dict[str, str]], a1_res: Dict[str, object]
) -> Tuple[Dict[str, object], Dict[str, object]]:
    ide = e1_sheets["Input Data & Extrapolation"]
    cssr_sheet = e1_sheets["CSSR Calculation"]
    va_sheet = e1_sheets["VA Term Structures"]

    ufr = float(ide["H14"])
    alpha = float(ide["H15"])
    rcs_cu = float(ide["L10"])
    rcs_co = float(ide["L11"])
    dtar_co = float(ide["L12"])

    dlt_tenors: List[int] = []
    weights: Dict[int, float] = {}
    row = 25
    while f"G{row}" in ide:
        t = int(float(ide[f"G{row}"]))
        is_dlt = int(float(ide.get(f"H{row}", "0"))) == 1
        w = float(ide.get(f"I{row}", "0"))
        weights[t] = w
        if is_dlt and f"J{row}" in ide:
            dlt_tenors.append(t)
        row += 1
    dlt_tenors.sort()
    dlt_with_weight = [t for t in dlt_tenors if weights.get(t, 0.0) > 0.0]
    t_F = dlt_with_weight[0] if dlt_with_weight else dlt_tenors[-1]
    fsp_dlt_tenors = [t for t in dlt_tenors if t >= t_F]
    w_sum = sum(weights.get(t, 0.0) for t in fsp_dlt_tenors)
    w_tF = weights.get(t_F, 0.0) / w_sum

    cssr_mats: List[int] = []
    r = 24
    while f"G{r}" in cssr_sheet:
        cssr_mats.append(int(float(cssr_sheet[f"G{r}"])))
        r += 1

    notional_va = 0.85 * rcs_cu
    a2_llfr, a2_curve = build_va_curve(
        a1_res=a1_res,
        va_decimal=notional_va,
        t_F=t_F,
        w_tF=w_tF,
        ufr=ufr,
        alpha=alpha,
        maturities=cssr_mats,
    )

    fi_mv = float(cssr_sheet["L10"])
    fi_cssr = float(cssr_sheet["L11"])
    bel_mv = float(cssr_sheet["L13"])
    bel_cssr = float(cssr_sheet["L14"])

    delta_fi = fi_cssr - fi_mv
    delta_bel = bel_cssr - bel_mv
    cssr = max(min(delta_fi / delta_bel, 1.0), 0.0)

    a2_res: Dict[str, object] = {
        "notional_va": notional_va,
        "cssr": cssr,
        "llfr": a2_llfr,
        "curve": a2_curve,
    }

    va_mats: List[int] = []
    r = 23
    while f"G{r}" in va_sheet:
        va_mats.append(int(float(va_sheet[f"G{r}"])))
        r += 1

    use_macro_va = parse_bool(va_sheet["H10"])
    use_usa = parse_bool(va_sheet["H11"])
    usa_val = float(va_sheet["H12"])

    usa_factor = min(usa_val, 1.05) if use_usa else 1.0
    applicable_rcs_cu = rcs_cu * usa_factor
    currency_va = 0.85 * cssr * applicable_rcs_cu

    omega_co = max(min((rcs_co * dtar_co - 0.006) / 0.003, 1.0), 0.0)

    if use_macro_va and not use_usa:
        macro_va = 0.85 * cssr * max(rcs_co - 1.3 * rcs_cu, 0.0) * omega_co
    else:
        macro_va = 0.0

    total_va = currency_va + macro_va

    a3_llfr, a3_curve = build_va_curve(
        a1_res=a1_res,
        va_decimal=total_va,
        t_F=t_F,
        w_tF=w_tF,
        ufr=ufr,
        alpha=alpha,
        maturities=va_mats,
    )

    a3_res: Dict[str, object] = {
        "currency_va": currency_va,
        "omega_co": omega_co,
        "total_va": total_va,
        "llfr": a3_llfr,
        "curve": a3_curve,
    }

    return a2_res, a3_res


EEA_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
    "GR", "EL", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU", "MT",
    "NL", "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}

EURO_AREA_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "EE", "FI", "FR", "DE", "GR", "EL",
    "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PT", "SK", "SI", "ES",
}

COUNTRY_CURRENCY = {
    **{c: "EUR" for c in EURO_AREA_COUNTRIES},
    "DK": "DKK",
    "CZ": "CZK",
    "HU": "HUF",
    "IS": "ISK",
    "LI": "CHF",
    "NO": "NOK",
    "PL": "PLN",
    "RO": "RON",
    "SE": "SEK",
    "CH": "CHF",
    "UK": "GBP",
    "AU": "AUD",
    "CA": "CAD",
    "CN": "CNY",
    "HK": "HKD",
    "JP": "JPY",
    "US": "USD",
}


def interp_curve(pts: List[Tuple[float, float]], x: float) -> float:
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    return pts[-1][1]


def rc_eea_gov(s: float, ltas: float) -> float:
    sp = max(0.0, s)
    lp = max(0.0, ltas)
    term = (
        0.30 * min(sp, lp)
        + 0.20 * max(0.0, min(sp - lp, lp))
        + 0.15 * max(0.0, sp - 2.0 * lp)
    )
    return min(0.65 * lp, term)


def rc_other(s: float, ltas: float) -> float:
    sp = max(0.0, s)
    lp = max(0.0, ltas)
    term = (
        0.50 * min(sp, lp)
        + 0.40 * max(0.0, min(sp - lp, lp))
        + 0.30 * max(0.0, sp - 2.0 * lp)
    )
    return min(1.25 * lp, term)


def solve_irr(cfs: List[float], durs: List[float], yields: List[float]) -> float:
    target_pv = sum(cf * ((1.0 + y) ** (-d)) for cf, d, y in zip(cfs, durs, yields))

    def obj(y_irr: float) -> float:
        return sum(cf * ((1.0 + y_irr) ** (-d)) for cf, d in zip(cfs, durs)) - target_pv

    denom = sum(cf * d for cf, d in zip(cfs, durs))
    y_curr = sum(cf * d * y for cf, d, y in zip(cfs, durs, yields)) / denom if denom > 0.0 else 0.03
    for _ in range(50):
        f_val = obj(y_curr)
        f_prime = sum(-d * cf * ((1.0 + y_curr) ** (-d - 1.0)) for cf, d in zip(cfs, durs))
        if f_prime == 0.0:
            break
        step = f_val / f_prime
        y_curr -= step
        if abs(step) <= 1e-16:
            break
    return y_curr


def load_rcs_bundle(bundle_subdir: str):
    rfr_d = load_tsv_cells(os.path.join(bundle_subdir, "rfr.tsv"))
    gov_d = load_tsv_cells(os.path.join(bundle_subdir, "gov-rates.tsv"))
    corp_d = load_tsv_cells(os.path.join(bundle_subdir, "corp-data.tsv"))
    ltas_d = load_tsv_cells(os.path.join(bundle_subdir, "ltas.tsv"))
    weights_d = load_tsv_cells(os.path.join(bundle_subdir, "reference-portfolio-weights.tsv"))
    gov_port_d = load_tsv_cells(os.path.join(bundle_subdir, "government-bond-ref-portfolios.tsv"))
    corp_port_d = load_tsv_cells(os.path.join(bundle_subdir, "corporate-bond-ref-portfolio.tsv"))

    rfr_curves: Dict[str, List[Tuple[float, float]]] = {}
    for cell, val in rfr_d.items():
        col, row = parse_cell_coord(cell)
        if row == 10 and col != "F":
            pts: List[Tuple[float, float]] = []
            r = 11
            while f"F{r}" in rfr_d:
                if f"{col}{r}" in rfr_d:
                    pts.append((float(rfr_d[f"F{r}"]), float(rfr_d[f"{col}{r}"])))
                r += 1
            pts.sort(key=lambda x: x[0])
            rfr_curves[val.strip()] = pts

    gov_curves: Dict[str, List[Tuple[float, float]]] = {}
    for cell, val in gov_d.items():
        col, row = parse_cell_coord(cell)
        if row == 8 and col != "F":
            pts = []
            r = 9
            while f"F{r}" in gov_d:
                if f"{col}{r}" in gov_d:
                    pts.append((float(gov_d[f"F{r}"]), float(gov_d[f"{col}{r}"])))
                r += 1
            pts.sort(key=lambda x: x[0])
            gov_curves[val.strip()] = pts

    ltas_gov: Dict[str, List[Tuple[float, float]]] = {}
    for cell, val in ltas_d.items():
        col, row = parse_cell_coord(cell)
        if row == 10 and col != "F":
            pts = []
            r = 11
            while f"F{r}" in ltas_d:
                if f"{col}{r}" in ltas_d:
                    pts.append((float(ltas_d[f"F{r}"]), float(ltas_d[f"{col}{r}"])))
                r += 1
            pts.sort(key=lambda x: x[0])
            ltas_gov[val.strip()] = pts

    ltas_corp: Dict[str, List[Tuple[float, float]]] = {}
    for cell, val in ltas_d.items():
        col, row = parse_cell_coord(cell)
        if col == "F" and ("Financials" in val or "Non-Financials" in val):
            sector = "Non-Financials" if "Non-Financials" in val else "Financials"
            hrow = row + 2
            for c_cell, c_val in ltas_d.items():
                c_col, c_row = parse_cell_coord(c_cell)
                if c_row == hrow and c_col != "F":
                    cqs_label = f"{sector} {c_val.strip()}"
                    pts = []
                    r = hrow + 1
                    while f"F{r}" in ltas_d:
                        if f"{c_col}{r}" in ltas_d:
                            pts.append((float(ltas_d[f"F{r}"]), float(ltas_d[f"{c_col}{r}"])))
                        r += 1
                    pts.sort(key=lambda x: x[0])
                    ltas_corp[cqs_label] = pts

    corp_curves: Dict[str, List[Tuple[float, float]]] = {}
    col_order = ["F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R"]
    for cell, val in corp_d.items():
        val_s = val.strip()
        if (val_s.startswith("Financials CQS ") or val_s.startswith("Non-Financials CQS ")) and not val_s.endswith("CQS 0"):
            col, hrow = parse_cell_coord(cell)
            c_idx = col_order.index(col)
            col_d = col_order[c_idx + 1]
            col_y = col_order[c_idx + 2]
            pts = []
            r = hrow + 3
            while f"{col}{r}" in corp_d:
                if f"{col_d}{r}" in corp_d and f"{col_y}{r}" in corp_d:
                    pts.append((float(corp_d[f"{col_d}{r}"]), float(corp_d[f"{col_y}{r}"])))
                r += 1
            pts.sort(key=lambda x: x[0])
            corp_curves[val_s] = pts

    for sector in ("Financials", "Non-Financials"):
        c1_pts = corp_curves[f"{sector} CQS 1"]
        corp_curves[f"{sector} CQS 0"] = [
            (d, (0.85 * y if y >= 0.0 else 1.15 * y)) for d, y in c1_pts
        ]
        corp_curves[f"{sector} CQS 6"] = list(corp_curves[f"{sector} CQS 5"])

    return rfr_curves, gov_curves, corp_curves, ltas_gov, ltas_corp, weights_d, gov_port_d, corp_port_d


def extract_portfolio_rows(port_d: Dict[str, str], start_row: int) -> List[Tuple[str, float, float, float, float, float]]:
    rows: List[Tuple[str, float, float, float, float, float]] = []
    r = start_row
    while f"F{r}" in port_d:
        issuer = port_d[f"F{r}"].strip()
        if f"G{r}" in port_d and f"H{r}" in port_d:
            comp = float(port_d[f"G{r}"])
            if comp > 0.0:
                dur = float(port_d[f"H{r}"])
                cf_my = float(port_d[f"I{r}"])
                cf_rfy = float(port_d[f"J{r}"])
                cf_rcy = float(port_d[f"K{r}"])
                rows.append((issuer, comp, dur, cf_my, cf_rfy, cf_rcy))
        r += 1
    return rows


def find_portfolio_start_row(port_d: Dict[str, str], target_code: str, is_currency: bool) -> int:
    prefix = f"Currency RCS {target_code}" if is_currency else f"Country RCS {target_code}"
    for cell, val in port_d.items():
        col, row = parse_cell_coord(cell)
        if col == "F" and val.strip().startswith(prefix):
            return row + 3
    raise ValueError(f"Could not find portfolio section for {prefix}")


def find_weights(weights_d: Dict[str, str], target_code: str) -> Tuple[float, float]:
    for cell, val in weights_d.items():
        col, row = parse_cell_coord(cell)
        if col == "F" and val.strip() == target_code:
            w_gov_raw = float(weights_d[f"G{row}"])
            w_corp_raw = float(weights_d[f"H{row}"])
            total = w_gov_raw + w_corp_raw
            return w_gov_raw / total, w_corp_raw / total
    raise ValueError(f"Could not find weights for {target_code}")


def compute_rcs_example(bundle_subdir: str, target_code: str, is_currency: bool) -> Dict[str, float]:
    (
        rfr_curves,
        gov_curves,
        corp_curves,
        ltas_gov,
        ltas_corp,
        weights_d,
        gov_port_d,
        corp_port_d,
    ) = load_rcs_bundle(bundle_subdir)

    w_gov, w_corp = find_weights(weights_d, target_code)

    gov_start = find_portfolio_start_row(gov_port_d, target_code, is_currency)
    corp_start = find_portfolio_start_row(corp_port_d, target_code, is_currency)

    gov_rows = extract_portfolio_rows(gov_port_d, gov_start)
    corp_rows = extract_portfolio_rows(corp_port_d, corp_start)

    g_durs: List[float] = []
    g_cf_my: List[float] = []
    g_cf_rfy: List[float] = []
    g_cf_rcy: List[float] = []
    g_y_my: List[float] = []
    g_y_rfy: List[float] = []
    g_y_rcy: List[float] = []

    for issuer, _comp, dur, cf_my, cf_rfy, cf_rcy in gov_rows:
        if is_currency and target_code == "EUR" and issuer in EURO_AREA_COUNTRIES:
            y_my = interp_curve(gov_curves["ECB Curve"], dur)
            ltas = interp_curve(ltas_gov["EUR"], dur)
        else:
            y_my = interp_curve(gov_curves[issuer], dur)
            ltas = interp_curve(ltas_gov[issuer], dur)

        iss_cur = COUNTRY_CURRENCY[issuer]
        y_rfy = interp_curve(rfr_curves[iss_cur], dur)
        s_i = y_my - y_rfy
        rc_i = rc_eea_gov(s_i, ltas) if issuer in EEA_COUNTRIES else rc_other(s_i, ltas)
        y_rcy = y_my - rc_i

        g_durs.append(dur)
        g_cf_my.append(cf_my)
        g_cf_rfy.append(cf_rfy)
        g_cf_rcy.append(cf_rcy)
        g_y_my.append(y_my)
        g_y_rfy.append(y_rfy)
        g_y_rcy.append(y_rcy)

    Y_gov_my = solve_irr(g_cf_my, g_durs, g_y_my)
    Y_gov_rfy = solve_irr(g_cf_rfy, g_durs, g_y_rfy)
    Y_gov_rcy = solve_irr(g_cf_rcy, g_durs, g_y_rcy)

    c_durs: List[float] = []
    c_cf_my: List[float] = []
    c_cf_rfy: List[float] = []
    c_cf_rcy: List[float] = []
    c_y_my: List[float] = []
    c_y_rfy: List[float] = []
    c_y_rcy: List[float] = []

    port_currency = target_code if is_currency else COUNTRY_CURRENCY[target_code]
    for issuer, _comp, dur, cf_my, cf_rfy, cf_rcy in corp_rows:
        y_my = interp_curve(corp_curves[issuer], dur)
        y_rfy = interp_curve(rfr_curves[port_currency], dur)
        ltas = interp_curve(ltas_corp[issuer], dur)
        s_i = y_my - y_rfy
        rc_i = rc_other(s_i, ltas)
        y_rcy = y_my - rc_i

        c_durs.append(dur)
        c_cf_my.append(cf_my)
        c_cf_rfy.append(cf_rfy)
        c_cf_rcy.append(cf_rcy)
        c_y_my.append(y_my)
        c_y_rfy.append(y_rfy)
        c_y_rcy.append(y_rcy)

    Y_corp_my = solve_irr(c_cf_my, c_durs, c_y_my)
    Y_corp_rfy = solve_irr(c_cf_rfy, c_durs, c_y_rfy)
    Y_corp_rcy = solve_irr(c_cf_rcy, c_durs, c_y_rcy)

    s_gov = Y_gov_my - Y_gov_rfy
    s_corp = Y_corp_my - Y_corp_rfy
    rc_gov = Y_gov_my - Y_gov_rcy
    rc_corp = Y_corp_my - Y_corp_rcy

    s_total = w_gov * s_gov + w_corp * s_corp
    rc_total = w_gov * rc_gov + w_corp * rc_corp
    rcs_total = s_total - rc_total

    return {
        "w_gov": w_gov,
        "w_corp": w_corp,
        "s_gov": s_gov,
        "s_corp": s_corp,
        "rc_gov": rc_gov,
        "rc_corp": rc_corp,
        "s": s_total,
        "rc": rc_total,
        "rcs": rcs_total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EIOPA RFR worked examples.")
    parser.add_argument("bundle_dir", help="Path to input bundle directory")
    parser.add_argument("output_file", help="Path to output JSON file")
    parser.add_argument("--a1", dest="a1_file", default=None, help="Optional JSON file with A1 results")
    args = parser.parse_args()

    e1_dir = os.path.join(args.bundle_dir, "E1")
    e2_dir = os.path.join(args.bundle_dir, "E2")
    e3_dir = os.path.join(args.bundle_dir, "E3")

    e1_sheets = load_e1_sheets(e1_dir)

    if args.a1_file is not None:
        with open(args.a1_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if "A1" in loaded and isinstance(loaded["A1"], dict):
            a1_res = loaded["A1"]
        else:
            a1_res = loaded
    else:
        a1_res = compute_a1(e1_sheets)

    a2_res, a3_res = compute_a2_a3(e1_sheets, a1_res)

    b1_res = compute_rcs_example(e2_dir, "EUR", is_currency=True)
    b2_res = compute_rcs_example(e2_dir, "IT", is_currency=False)
    c1_res = compute_rcs_example(e3_dir, "GBP", is_currency=True)

    outputs = {
        "A1": a1_res,
        "A2": a2_res,
        "A3": a3_res,
        "B1": b1_res,
        "B2": b2_res,
        "C1": c1_res,
    }

    out_dir = os.path.dirname(os.path.abspath(args.output_file))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)
        f.write(NL)


if __name__ == "__main__":
    main()
