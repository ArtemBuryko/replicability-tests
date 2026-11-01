# bands.py — the pass bands of B1, B2 and C1 from the workbooks' own Solver residuals (the preregistration, §5).
# usage: python3 -I bands.py <E2 copy> <E3 copy>    · standard library and openpyxl; reads cached values and formulas, runs nothing
import sys, re, math, hashlib, warnings
warnings.filterwarnings("ignore")
import openpyxl
from openpyxl.utils import column_index_from_string as ci, get_column_letter as cl
PINS = {"E2": "5302c91ba000568fd99adb0c98a08af9cb3089b412f0200a77c5488fb85cfe07",
        "E3": "67bf3478293b810691460569cf79751cf4c90e57a2773cbbd4da9f92b2486b81"}
FLOOR = 1.0e-9   # the band of an output no residual reaches — the preregistration's band for unrounded outputs (§5)
OBJ = re.compile(r"^=\(SUM\(([A-Z]+)(\d+):([A-Z]+)(\d+)\)-([A-Z]+)(\d+)\)\^2$")
LET = re.compile(r"^=_xlfn\.LET\(_xlpm\.CF, _xlfn\.XLOOKUP\([A-Z]+\$10, T\.\w+\[Issuer\], T\.\w+\[[A-Za-z ]+Cash Flow\]\),\s*_xlpm\.IER,\s*\$([A-Z]+)\$(\d+),\s*_xlpm\.DUR,\s*([A-Z]+)13,\s*_xlpm\.CF \* \(1 \+ _xlpm\.IER\)\^\(-_xlpm\.DUR\)\)$")
CASES = [("B1", "E2", "G", "EUR", "Cur"), ("B2", "E2", "K", "IT", "Country"), ("C1", "E3", "G", "GBP", "Cur")]
LABELS = ["w gov", "w corp", "S gov", "S corp", "RC gov", "RC corp", "S", "RC", "RCS"]

def expected_rcs(x):   # the RCS formulas, rows 11–19, as the workbooks carry them
    return [f"=V.W_GOV_{x}/(V.W_GOV_{x}+V.W_CORP_{x})", f"=V.W_CORP_{x}/(V.W_GOV_{x}+V.W_CORP_{x})",
            f"=V.S_GOV_{x}", f"=V.S_CORP_{x}", f"=V.RC_GOV_{x}", f"=V.RC_CORP_{x}",
            f"=V.W_GOV_{x}_NORM * V.S_GOV_{x} + V.W_CORP_{x}_NORM * V.S_CORP_{x}",
            f"=V.W_GOV_{x}_NORM * V.RC_GOV_{x} + V.W_CORP_{x}_NORM * V.RC_CORP_{x}", f"=V.S_{x}-V.RC_{x}"]

def text(v):
    return v.text if hasattr(v, "text") and not isinstance(v, str) else v

def ier_rows(wf, wv, sheet):
    w, v, out = wf[sheet], wv[sheet], []
    for row in w.iter_rows():
        for c in row:
            m = OBJ.match(str(text(c.value)))
            if not m: continue
            c1, rmv, c2, rmv2, sc, r = m.group(1), int(m.group(2)), m.group(3), int(m.group(4)), m.group(5), int(m.group(6))
            assert rmv == rmv2 and r == c.row and ci(sc) == c.column - 1, f"{sheet}!{c.coordinate}: objective layout"
            assert text(w[f"{sc}{r}"].value) == f"=SUM({c1}{r}:{c2}{r})", f"{sheet}!{sc}{r}: sum"
            icell = f"{cl(c.column + 1)}{r}"
            W = w[icell].value
            assert isinstance(W, float), f"{sheet}!{icell}: the IER is a constant"
            vals, durs, mvs = [], [], []
            for k in range(ci(c1), ci(c2) + 1):
                f = str(text(w.cell(r, k).value)); lm = LET.match(f)
                assert lm and f"{lm.group(1)}{lm.group(2)}" == icell and lm.group(3) == cl(k), f"{sheet}!{cl(k)}{r}: discounting formula"
                vals.append(float(v.cell(r, k).value)); durs.append(float(v.cell(13, k).value)); mvs.append(float(v.cell(rmv, k).value))
            out.append(dict(sheet=sheet, cell=icell, W=W, V=float(v[c.coordinate].value), S=float(v[f"{sc}{r}"].value),
                            vals=vals, durs=durs, MV=math.fsum(mvs), n=len(vals)))
    return out

def analyse(d):
    W, vals, durs = d["W"], d["vals"], d["durs"]
    U = lambda x: math.fsum(vi * ((1 + W) / (1 + x)) ** di for vi, di in zip(vals, durs))
    dU = lambda x: -math.fsum(di * vi * ((1 + W) / (1 + x)) ** di for vi, di in zip(vals, durs)) / (1 + x)
    x = W
    for _ in range(50):
        step = (U(x) - d["MV"]) / dU(x); x -= step
        if abs(step) < 1e-18: break
    d.update(gap=math.sqrt(d["V"]), dU=dU(W), dW=math.sqrt(d["V"]) / abs(dU(W)), dW_exact=x - W,
             V_recomputed=(d["MV"] - math.fsum(vals)) ** 2, sum_err=abs(math.fsum(vals) - d["S"]))
    d["dW_use"] = max(d["dW"], abs(d["dW_exact"]))   # the linear reach, or the exact root's departure where the curvature makes it larger
    return d

def name_of(wf, sheet, cell):
    dn = wf.defined_names
    keys = list(dn.keys()) if hasattr(dn, "keys") else [x.name for x in dn.definedName]
    hits = [k for k in keys if dn[k].attr_text.replace("$", "") == f"'{sheet}'!{cell}"]
    return hits[0] if len(hits) == 1 else f"?{hits}"

def main(p2, p3):
    paths = {"E2": p2, "E3": p3}
    for k, p in paths.items():
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        print(f"{k}: sha256 {h} · equal to its pin: {'yes' if h == PINS[k] else 'NO'}"); assert h == PINS[k]
    print("=== the internal effective rates: the Solver point, its residual, the rate's linear reach (|gap| / |dU/dW|), the exact root's departure; its largest change the larger of the two")
    ier = {}
    for k in ("E2", "E3"):
        wf = openpyxl.load_workbook(paths[k], data_only=False); wv = openpyxl.load_workbook(paths[k], data_only=True)
        for sh in [s for s in wf.sheetnames if s.startswith("S&RC")]:
            for d in ier_rows(wf, wv, sh):
                d = analyse(d); d["name"] = name_of(wf, sh, d["cell"]); ier[(k, d["name"])] = d
                print(f"{k} '{sh}'!{d['cell']} {d['name']} · issuers {d['n']} · W* {d['W']!r} · objective {d['V']:.6g} (recomputed {d['V_recomputed']:.3g}; sum check {d['sum_err']:.1e}) · |dU/dW| {abs(d['dU']):.6g} · linear reach {d['dW']:.6e} · exact root − W* {d['dW_exact']:+.6e} · largest change {d['dW_use']:.6e}")
        if k == "E2": wf2, wv2 = wf, wv
        else: wf3, wv3 = wf, wv
    print("=== the outputs: formula as carried · cached value · band = max(Σ|coefficient| × each rate's largest change, 1.0e-9) · the exact root's departure")
    books = {"E2": (wf2, wv2), "E3": (wf3, wv3)}
    rows = []
    for case, k, col, x, sfx in CASES:
        wf, wv = books[k]
        got = [str(text(wf["RCS"][f"{col}{r}"].value)) for r in range(11, 20)]
        exp = expected_rcs(x)
        bad = [f"{col}{r}" for r, (a, b) in zip(range(11, 20), zip(got, exp)) if a != b]
        print(f"{case} · RCS {col}11:{col}19 formulas as expected: {'yes' if not bad else 'NO ' + str(bad)}"); assert not bad
        for part, sh in (("GOV", f"S&RC Gov {'Currency' if sfx == 'Cur' else 'Country'}"), ("CORP", f"S&RC Corp {'Currency' if sfx == 'Cur' else 'Country'}")):
            for nm, kind in ((f"V.S_{part}_{x}", "RFR"), (f"V.RC_{part}_{x}", "RCYield")):
                tgt = wf.defined_names[nm].attr_text.replace("$", "")
                s_, c_ = tgt.rsplit("!", 1); s_ = s_.strip("'")
                f = str(text(wf[s_][c_].value)); want = f"=V.IER_Yield_{part.title()}_{sfx}-V.IER_{kind}_{part.title()}_{sfx}"
                print(f"   {nm} → {tgt} = {f[1:]} · as expected: {'yes' if f == want else 'NO'}"); assert f == want
        wG, wC = float(wv["RCS"][f"{col}11"].value), float(wv["RCS"][f"{col}12"].value)
        g = lambda part, kind: ier[(k, f"V.IER_{kind}_{part}_{sfx}")]
        Y_G, R_G, C_G = g("Gov", "Yield"), g("Gov", "RFR"), g("Gov", "RCYield")
        Y_C, R_C, C_C = g("Corp", "Yield"), g("Corp", "RFR"), g("Corp", "RCYield")
        coefs = [[], [], [(Y_G, 1), (R_G, -1)], [(Y_C, 1), (R_C, -1)], [(Y_G, 1), (C_G, -1)], [(Y_C, 1), (C_C, -1)],
                 [(Y_G, wG), (R_G, -wG), (Y_C, wC), (R_C, -wC)], [(Y_G, wG), (C_G, -wG), (Y_C, wC), (C_C, -wC)],
                 [(C_G, wG), (R_G, -wG), (C_C, wC), (R_C, -wC)]]   # RCS = S − RC: the yield rates cancel
        for r, lab, cf in zip(range(11, 20), LABELS, coefs):
            raw = math.fsum(abs(c) * d["dW_use"] for d, c in cf); band = max(raw, FLOOR)
            ex = math.fsum(c * d["dW_exact"] for d, c in cf)
            val = float(wv["RCS"][f"{col}{r}"].value)
            up = float(f"{band:.1e}"); up = up if up >= band else float(f"{band + 10 ** (math.floor(math.log10(band)) - 1):.1e}")
            rows.append((case, f"{col}{r}", lab, val, raw, band, up, ex))
            print(f"{case} RCS!{col}{r} {lab:7} · {val!r} · residuals reach {raw:.6e} · band {band:.6e} → rounded up {up:.1e} · exact root departs {ex:+.6e} · within the band: {'yes' if abs(ex) <= band else 'NO'}")
    print("=== controls")
    d0 = dict(ier[("E2", "V.IER_Yield_Corp_Cur")]); d1 = analyse(dict(d0, V=4 * d0["V"]))
    print(f"a planted objective ×4 on E2 V.IER_Yield_Corp_Cur — its largest change ×{d1['dW'] / d0['dW']:.12f} (expected ×2)")
    planted = expected_rcs("EUR"); planted[8] = "=V.S_EUR+V.RC_EUR"
    seen = [str(text(wf2["RCS"][f"G{r}"].value)) for r in range(11, 20)]
    print(f"a planted formula expectation (RCS G19 as S + RC) — the check catches it: {'yes' if seen != planted else 'NO'}")
    return rows

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
