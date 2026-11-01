#!/usr/bin/env python3
"""The input-to-oracle manifest's extractions, re-derived from the pinned workbooks (read-only).

    python3 -I manifest.py <folder holding E1.xlsm E2.xlsm E3.xlsm - copies of the pinned files>

Prints the pins checked; one row per declared range (case, role, workbook, sheet!range, selection,
cells, first and last value, sha256 of its canonical lines); the completeness check of numeric
constants; every defined name with its scope, read from the workbook's own xl/workbook.xml - each one
that carries a constant reported, every formula of every sheet and every name checked for a reference
to it; the three cases' formulas against the sheets of A4-A5; the CQS 0 rule against the CQS 1 yields
it reads. Each check has a positive control planted into what the check itself reads - a name written
into a copy of the workbook's xl/workbook.xml, a formula or an array formula among a scanned sheet's cells, a value among the
scanned values - and run through the same code, each planted name read back with its kind; and a negative control where a
route must not fire: a name only inside longer names, a flag that is not a number, a constant whose text names a constant.
The run itself is a control too, run as a child process with its controls not run: on the folder given - the pins - its exit
status 0, nothing on its standard error and the sha256 of what it prints the frozen run's, whose declared rows MANIFEST.md
carries; on a folder holding a copy that is not its pin, status 2, that pin's line its last; imported as a module, as the
bundle's tool imports it, nothing run. A control that does not give its expected result ends the run with status 1.
With MANIFEST_CONTROLS_NOT_RUN=1 the run prints what it reads and checks and a line saying its controls were not run, and
exits 0 without them - the form in which its own controls run it.
Canonical line per cell, row-major: '<sheet>!<coord>\t<value>\n' - the cached value (data_only);
bool TRUE/FALSE, int str, float repr, str with \\ \t \n escaped; empty cells skipped.
openpyxl with keep_vba=False, keep_links=False: no macro run, no link followed, nothing saved.
"""
import hashlib, os, re, sys, tempfile, zipfile
import xml.etree.ElementTree as ET
from openpyxl import load_workbook
from openpyxl.utils import range_boundaries, get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

PINS = {'E1': 'c1ce32a3f76cf50f4d3de267292ee5af355fea9d31b60c4d2a01a98dff777dc4',
        'E2': '5302c91ba000568fd99adb0c98a08af9cb3089b412f0200a77c5488fb85cfe07',
        'E3': '67bf3478293b810691460569cf79751cf4c90e57a2773cbbd4da9f92b2486b81'}
IDE, CS, VT = 'Input Data & Extrapolation', 'CSSR Calculation', 'VA Term Structures'
INPUT_SHEETS = ['Gov Rates', 'Corp Data', 'RFR', 'LTAS', 'Reference Portfolio Weights',
                'Government Bond Ref. Portfolios', 'Corporate Bond Ref. Portfolio']
# case, role, workbook, sheet, range (None: the whole sheet), selection (all | const | formula), note
SPEC = [
 ('A1', 'input', 'E1', IDE, 'H10:H12', 'const', 'extrapolation?, instrument, coupon frequency'),
 ('A1', 'input', 'E1', IDE, 'H14:H16', 'const', 'UFR, alpha, CRA (bp)'),
 ('A1', 'input', 'E1', IDE, 'G25:G174', 'const', 'maturities'),
 ('A1', 'input', 'E1', IDE, 'H25:H174', 'const', 'DLT flags'),
 ('A1', 'input', 'E1', IDE, 'I25:I174', 'const', 'LLFR weights'),
 ('A1', 'input', 'E1', IDE, 'J25:J174', 'const', 'par swap rates — 32 published; the DLT flags select 19'),
 ('A1', 'excluded', 'E1', IDE, 'H17', 'const', 'input LLFR - used only when Extrapolation? is FALSE'),
 ('A1', 'intermediate', 'E1', IDE, 'H13', 'all', 'FSP'),
 ('A1', 'output', 'E1', IDE, 'K25:K74', 'all', 'bootstrapped zero rates, CC'),
 ('A1', 'output', 'E1', IDE, 'L22', 'all', 'LLFR'),
 ('A1', 'output', 'E1', IDE, 'L25:L174', 'all', 'basic RFR, AC, 5 dp'),
 ('A2', 'input', 'E1', IDE, 'L10', 'const', 'currency RCS'),
 ('A2', 'input', 'E1', CS, 'G24:G173', 'const', 'maturities, as in A1'),
 ('A2', 'input', 'E1', CS, 'L10:L11', 'const', 'FI: MV, MV at the notional VA'),
 ('A2', 'input', 'E1', CS, 'L13:L14', 'const', 'BEL: MV, at the notional VA'),
 ('A2', 'excluded', 'E1', CS, 'L12', 'all', 'PVBP of FI - the workbook\'s construct, not the text\'s'),
 ('A2', 'excluded', 'E1', CS, 'L15', 'all', 'PVBP of BEL - the workbook\'s construct, not the text\'s'),
 ('A2', 'output', 'E1', CS, 'H10', 'all', 'notional VA'),
 ('A2', 'output', 'E1', CS, 'L16', 'all', 'CSSR'),
 ('A2', 'output', 'E1', CS, 'K20', 'all', 'LLFR of the CSSR curve'),
 ('A2', 'output', 'E1', CS, 'L24:L173', 'all', 'CSSR curve, 5 dp'),
 ('A3', 'input', 'E1', IDE, 'L11:L12', 'const', 'country RCS, debt to total assets'),
 ('A3', 'input', 'E1', VT, 'H10:H12', 'const', 'macro VA?, USA?, USA'),
 ('A3', 'input', 'E1', VT, 'G23:G172', 'const', 'maturities, as in A1'),
 ('A3', 'excluded', 'E1', VT, 'L12', 'all', 'macro VA - not selected'),
 ('A3', 'output', 'E1', VT, 'L10:L11', 'all', 'currency VA, omega(co)'),
 ('A3', 'output', 'E1', VT, 'L13', 'all', 'total VA, 4 dp'),
 ('A3', 'output', 'E1', VT, 'K20', 'all', 'LLFR of the VA curve'),
 ('A3', 'output', 'E1', VT, 'L23:L172', 'all', 'VA curve, 5 dp'),
 ('A4-A5', 'excluded', 'E1', 'IRR Up Shock', None, 'const', 'IRR up - out of the declared cases'),
 ('A4-A5', 'excluded', 'E1', 'IRR Down Shock', None, 'const', 'IRR down - out of the declared cases'),
 ('A4-A5', 'excluded', 'E1', 'Parameters', None, 'const', 'the IRR shocks s, b and the floor r_m - out of the declared cases'),
 ('-', 'version', 'E1', 'Overview', 'F21:H21', 'all', 'the workbook\'s version and date'),
 ('-', 'version', 'E2', 'Overview', 'F16:H16', 'all', 'the workbook\'s version and date'),
 ('-', 'version', 'E3', 'Overview', 'F16:H16', 'all', 'the workbook\'s version and date'),
]
for wb, case, iers, objs, outs in (
    ('E2', 'B', [('S&RC Gov Currency', 'W45:W47'), ('S&RC Corp Currency', 'U47:U49'),
                 ('S&RC Gov Country', 'U45:U47'), ('S&RC Corp Country', 'U47:U49')],
                [('S&RC Gov Currency', 'V45:V47'), ('S&RC Corp Currency', 'T47:T49'),
                 ('S&RC Gov Country', 'T45:T47'), ('S&RC Corp Country', 'T47:T49')],
                [('B1', 'G11:G19', 'EUR: weights, portfolio S and RC, S, RC, RCS'),
                 ('B2', 'K11:K19', 'IT: weights, portfolio S and RC, S, RC, RCS')]),
    ('E3', 'C1', [('S&RC Gov Currency', 'M45:M47'), ('S&RC Corp Currency', 'T47:T49')],
                 [('S&RC Gov Currency', 'L45:L47'), ('S&RC Corp Currency', 'S47:S49')],
                 [('C1', 'G11:G19', 'GBP: weights, portfolio S and RC, S, RC, RCS')])):
    for sh in INPUT_SHEETS:
        SPEC.append((case, 'input', wb, sh, None, 'const', 'input sheet, constants'))
    SPEC.append((case, 'intermediate', wb, 'Corp Data', None, 'formula', 'CQS 0 rows by formula'))
    for sh, r in iers: SPEC.append((case, 'intermediate', wb, sh, r, 'const', 'IERs set by Solver'))
    for sh, r in objs: SPEC.append((case, 'residual', wb, sh, r, 'all', 'Solver objective, squared gap'))
    for c, r, n in outs: SPEC.append((c, 'output', wb, 'RCS', r, 'all', n))

def refers(fx, k):
    return re.search(r'(?<![\w.])' + re.escape(k) + r'(?![\w.])', fx) is not None

def render(v):
    if isinstance(v, bool): return 'TRUE' if v else 'FALSE'
    if isinstance(v, float): return repr(v)
    if isinstance(v, int): return str(v)
    if hasattr(v, 'isoformat'): return v.isoformat()
    return str(v).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')

class WB:
    def __init__(self, path):
        self.f = load_workbook(path, keep_vba=False, keep_links=False)
        self.v = load_workbook(path, data_only=True, keep_vba=False, keep_links=False)
        self.derived = {}
        for ws in self.f.worksheets:
            d = set()
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, ArrayFormula):
                        a, b, cc, dd = range_boundaries(c.value.ref)
                        d.update((r, k) for r in range(b, dd + 1) for k in range(a, cc + 1))
                    elif isinstance(c.value, str) and c.value.startswith('='):
                        d.add((c.row, c.column))
            self.derived[ws.title] = d
    def cells(self, sheet, rng, sel):
        wf, wv, der = self.f[sheet], self.v[sheet], self.derived[sheet]
        if rng: a, b, c, d = range_boundaries(rng); it = wf.iter_rows(min_row=b, max_row=d, min_col=a, max_col=c)
        else: it = wf.iter_rows()
        for row in it:
            for cell in row:
                if cell.value is None: continue
                isd = (cell.row, cell.column) in der
                if (sel == 'const' and isd) or (sel == 'formula' and not isd): continue
                yield sheet, cell.coordinate, cell.row, cell.column, wv[cell.coordinate].value

def digest(rows):
    return hashlib.sha256(''.join(f"{s}!{k}\t{render(v)}\n" for s, k, _, _, v in rows).encode('utf-8')).hexdigest()

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NUMBER = re.compile(r'[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?')
LITERAL = re.compile(r'"(?:[^"]|"")*"|TRUE|FALSE|#[A-Z/0!?]+|\{[^{}]*\}', re.I)
REF = re.compile(r"(?:'(?:[^']|'')+'|[^!'\s(),]+)!(?:\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?|#REF!)|#REF!")
FAR = {'Parameters', 'IRR Up Shock', 'IRR Down Shock'}

def xml_names(path):
    """Every defined name in the workbook's own xl/workbook.xml, with its scope: a sheet's title, or None."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('xl/workbook.xml'))
    sheets = [s.get('name') for s in root.iter(NS + 'sheet')]
    out = []
    for dn in root.iter(NS + 'definedName'):
        i = dn.get('localSheetId')
        out.append({'name': dn.get('name'), 'scope': sheets[int(i)] if i is not None else None,
                    'hidden': dn.get('hidden') in ('1', 'true'), 'text': (dn.text or '').strip()})
    return out

def kind_of(n):
    t = n['text']
    if n['name'].startswith(('_xlpm.', '_xleta.')) and t == '#NAME?': return 'LET/LAMBDA parameter'
    if NUMBER.fullmatch(t) or LITERAL.fullmatch(t): return 'constant'
    if t and all(REF.fullmatch(p.strip()) for p in t.strip('()').split(',')): return 'cell reference'
    return 'formula'

def formulas(wb):
    """Every formula of every sheet, as (sheet, cell, text); an array formula by its text."""
    out = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                fx = c.value.text if isinstance(c.value, ArrayFormula) else c.value
                if isinstance(fx, str) and fx.startswith('='): out.append((ws.title, c.coordinate, fx))
    return out

def name_report(names, fxs):
    """The names by scope and kind; each one carrying a constant; the formulas and the names that name one."""
    kinds = {}
    for n in names: kinds.setdefault(kind_of(n), []).append(n)
    const = kinds.get('constant', [])
    local = [n for n in names if n['scope'] is not None]
    alt = lambda ns: re.compile(r"(?<![\w.])(?:" + '|'.join(re.escape(n['name']) for n in ns) + r")(?![\w.])", re.I) if ns else None
    pc, pl = alt(const), alt(local)
    return {'names': len(names), 'global': len(names) - len(local), 'local': len(local),
            'hidden': sum(n['hidden'] for n in names), 'kinds': {k: len(v) for k, v in sorted(kinds.items())},
            'const': const, 'numeric': sum(1 for n in const if NUMBER.fullmatch(n['text'])),
            'solver': all(n['name'].lower().startswith('solver_') for n in const), 'formulas': len(fxs),
            'f_const': [f for f in fxs if pc and pc.search(f[2])], 'f_local': [f for f in fxs if pl and pl.search(f[2])],
            'f_solver': [f for f in fxs if 'solver_' in f[2].lower()],
            'n_const': [n['name'] for n in names if pc and n not in const and pc.search(n['text'])]}

def far_refs(wb):
    """The names whose cells lie on the sheets of A4-A5, and the formulas of the three cases' sheets naming them or the sheets."""
    names_far = sorted(k for k, dn in wb.defined_names.items() if any(sh in FAR for sh, _ in dn.destinations))
    hits = []
    for sh in (IDE, CS, VT):
        for row in wb[sh].iter_rows():
            for c in row:
                fx = c.value.text if isinstance(c.value, ArrayFormula) else c.value
                if isinstance(fx, str) and fx.startswith('=') and (any(x in fx for x in FAR) or any(refers(fx, k) for k in names_far)):
                    hits.append(f"{sh}!{c.coordinate} {fx[:24]}")
    return names_far, hits

def cqs0(t, W):
    """The CQS 0 rows' formula shapes, the CQS 1 yields the 85 % rule reads, and the negative ones among them."""
    shapes, ys = set(), []
    for sh, k, r, c, v in W[t].cells('Corp Data', None, 'formula'):
        fx = W[t].f['Corp Data'][k].value; shapes.add(re.sub(r'(?<=[A-Z])\d+', 'n', fx))
        m = re.fullmatch(r'=85%\*([A-Z]+\d+)', fx)
        if m: ys.append((m.group(1), W[t].v['Corp Data'][m.group(1)].value))
    return shapes, ys, [y for y in ys if y[1] < 0]

def unplant(ws, r):
    for k in [k for k in ws._cells if k[0] == r]: del ws._cells[k]

def planted_copy(path, sheet, name, value, out):
    """A copy of the workbook at out, its xl/workbook.xml carrying one more defined name, scoped to sheet - or global when sheet is None."""
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    wbx = dict((i.filename, b) for i, b in items)['xl/workbook.xml']
    sheets = [s.get('name') for s in ET.fromstring(wbx).iter(NS + 'sheet')]
    scope = '' if sheet is None else f' localSheetId="{sheets.index(sheet)}"'
    add = f'<definedName name="{name}"{scope} hidden="1">{value}</definedName></definedNames>'
    assert wbx.count(b'</definedNames>') == 1
    with zipfile.ZipFile(out, 'w') as z:
        for i, b in items:
            z.writestr(i, b.replace(b'</definedNames>', add.encode(), 1) if i.filename == 'xl/workbook.xml' else b)

def main(folder):
    for t, pin in PINS.items():
        h = hashlib.sha256(open(f'{folder}/{t}.xlsm', 'rb').read()).hexdigest()
        print(f"pin {t}: {'equal' if h == pin else 'DIFFERENT ' + h}")
        if h != pin: sys.exit(2)
    W = {t: WB(f'{folder}/{t}.xlsm') for t in PINS}
    print('=== the declared ranges: case · role · workbook · sheet!range · selection · cells · first · last · sha256')
    covered = {t: set() for t in PINS}
    for case, role, t, sh, rng, sel, note in SPEC:
        rows = list(W[t].cells(sh, rng, sel))
        covered[t].update((sh, r, c) for sh, _, r, c, _ in rows)
        f = render(rows[0][4])[:24] if rows else '-'; l = render(rows[-1][4])[:24] if rows else '-'
        print(f"{case} · {role} · {t} · '{sh}'!{rng or '*'} · {sel} · {len(rows)} · {f} · {l} · {digest(rows)} · {note}")
    print('=== completeness: numeric constants outside every declared range, by sheet')
    def undeclared(t, cov):
        out = {}
        for ws in W[t].f.worksheets:
            for sh, k, r, c, v in W[t].cells(ws.title, None, 'const'):
                if isinstance(v, (int, float)) and not isinstance(v, bool) and (sh, r, c) not in cov:
                    out.setdefault(sh, []).append(f"{k}={render(v)[:12]}")
        return out
    for t in PINS:
        u = undeclared(t, covered[t])
        print(f"{t}: {sum(map(len, u.values()))} in {len(u)} sheets")
        for sh, ks in u.items(): print(f"   '{sh}': {len(ks)} · {' '.join(ks[:10])}{' …' if len(ks) > 10 else ''}")
    print('=== defined names: every name with its scope, from xl/workbook.xml; each one that carries a constant; the formulas and the names that name one')
    N = {t: xml_names(f'{folder}/{t}.xlsm') for t in PINS}
    R = {t: name_report(N[t], formulas(W[t].f)) for t in PINS}
    for t, rep in R.items():
        print(f"{t}: names {rep['names']} · global {rep['global']} · sheet-local {rep['local']} · hidden {rep['hidden']} · by kind {rep['kinds']} · carrying a constant {len(rep['const'])}, numeric {rep['numeric']}, all named solver_*: {rep['solver']} · formulas {rep['formulas']} · naming a name that carries a constant {len(rep['f_const'])} · naming a sheet-local name {len(rep['f_local'])} · naming solver_ {len(rep['f_solver'])} · names whose value names one {len(rep['n_const'])}")
        by = {}
        for n in rep['const']: by.setdefault(n['scope'], []).append(n)
        for sc, ns in by.items():
            print(f"   {repr(sc) if sc else 'the workbook'}{' · hidden' if all(n['hidden'] for n in ns) else ''}: {len(ns)} · {' '.join(n['name'] + '=' + n['text'][:16] for n in ns)}")
        for s, c, fx in (rep['f_const'] + rep['f_local'] + rep['f_solver'])[:12]: print(f"   formula {s}!{c} {fx[:40]}")
    print('=== A1-A3 against the sheets of A4-A5: references in the formulas of the three cases\' sheets')
    names_far, hits = far_refs(W['E1'].f)
    print(f"names whose cells lie on those sheets: {len(names_far)} · formulas on the cases' sheets that reference them or the sheets: {len(hits)} {hits[:6]}")
    print('=== the CQS 0 rule against the CQS 1 yields it reads')
    Q = {}
    for t in ('E2', 'E3'):
        shapes, ys, neg = Q[t] = cqs0(t, W)
        print(f"{t}: formula shapes {sorted(shapes)} · CQS 1 yields read by the 85 % rule: {len(ys)} · min {min(v for _, v in ys)!r} · negative: {len(neg)}")
    print('=== the controls: each planted into what its check reads, run through the same code')
    if os.environ.get('MANIFEST_CONTROLS_NOT_RUN') == '1':
        print('=== controls: not run (MANIFEST_CONTROLS_NOT_RUN=1)'); return
    ran, failed = [], []
    def control(label, got, want):
        ran.append(label)
        print(f"control - {label}: {got} (expected {want}){'' if got == want else ' - FAILED'}")
        if got != want: failed.append(label)
    ctl = covered['E1'] - {(IDE, r, c) for _, _, r, c, _ in W['E1'].cells(IDE, 'J25:J174', 'const')}
    control(f"E1 with A1's par swap rates undeclared: numeric constants found undeclared in '{IDE}'", len(undeclared('E1', ctl).get(IDE, [])), 32)
    lst = undeclared('E1', ctl).get(IDE, [])
    want = [f"{k}={render(v)[:12]}" for _, k, _, _, v in W['E1'].cells(IDE, 'J25:J174', 'const') if isinstance(v, (int, float)) and not isinstance(v, bool)]
    control("the same: the cells it lists, each with its value as the run renders it", (len(lst), lst == want), (32, True))
    flags = {(sh, r, c) for ws0 in W['E1'].f.worksheets for sh, _, r, c, v in W['E1'].cells(ws0.title, None, 'const') if isinstance(v, bool)}
    control("E1 with its constants TRUE or FALSE undeclared: those cells, numeric constants found undeclared - a flag is not a number", (len(flags), sum(map(len, undeclared('E1', covered['E1'] - flags).values()))), (5, 0))
    ws = W['E1'].f[IDE]; pr = ws.max_row + 1
    tmp = tempfile.mkdtemp(); tw = os.path.join(tmp, 'E1-planted.xlsm')
    t1, t2, t3, t4, t5, t6, t7, t8 = (os.path.join(tmp, f'E1-p{i}.xlsm') for i in range(1, 9))
    planted_copy(f'{folder}/E1.xlsm', IDE, 'PLANTED_FACTOR', '0.85', t1)
    planted_copy(t1, IDE, 'PLANTED_CELL', "'" + IDE.replace('&', '&amp;') + "'!$A$1", t2)
    planted_copy(t2, IDE, 'PLANTED_DERIVED', 'PLANTED_FACTOR*2', tw)
    pn = xml_names(tw)
    ws.cell(row=pr, column=1).value = '=PLANTED_FACTOR*2'
    rep = name_report(pn, formulas(W['E1'].f))
    ws.cell(row=pr, column=1).value = '=PLANTED_CELL*2'
    rep_l = name_report(pn, formulas(W['E1'].f))
    ws.cell(row=pr, column=1).value = '=Solver_Planted+0'
    rep_s = name_report(N['E1'], formulas(W['E1'].f))
    ws.cell(row=pr, column=1).value = ArrayFormula(f'A{pr}', '=PLANTED_FACTOR*1')
    rep_a = name_report(pn, formulas(W['E1'].f))
    planted_copy(f'{folder}/E1.xlsm', None, 'PLANTED_LITERAL', '&quot;TEXT&quot;', t3)
    tn = xml_names(t3)
    ws.cell(row=pr, column=1).value = '=PLANTED_LITERAL'
    rep_t = name_report(tn, formulas(W['E1'].f))
    kt = [(n['scope'], kind_of(n)) for n in tn if n['name'] == 'PLANTED_LITERAL']
    planted_copy(f'{folder}/E1.xlsm', IDE, 'Solver_Planted', '0.85', t4)
    rep_v = name_report(xml_names(t4), [])
    planted_copy(t3, None, 'PLANTED_QUOTE', '&quot;PLANTED_LITERAL&quot;', t5)
    rep_q = name_report(xml_names(t5), [])
    planted_copy(f'{folder}/E1.xlsm', IDE, 'PLANTED_EMPTY', '', t6)
    planted_copy(t6, None, '_xlpm.PLANTED_PARAM', '0.85', t7)
    planted_copy(t7, None, 'PLANTED_ERROR', '#NAME?', t8)
    pk = xml_names(t8)
    kinds = [(n['name'], n['scope'], kind_of(n)) for n in pn + pk if n['name'].upper().startswith(('PLANTED_', '_XLPM.PLANTED_'))]
    empty = [n['text'] for n in pk if n['name'] == 'PLANTED_EMPTY']
    unplant(ws, pr)
    for p in (t1, t2, t3, t4, t5, t6, t7, t8, tw): os.remove(p)
    os.rmdir(tmp)
    pl = [n['scope'] for n in rep['const'] if n['name'] == 'PLANTED_FACTOR']
    control(f"a name PLANTED_FACTOR = 0.85, scoped to '{IDE}', written into a copy of E1's xl/workbook.xml and read back: carrying a constant, numeric, its scope", (len(rep['const']), rep['numeric'], pl), (len(R['E1']['const']) + 1, R['E1']['numeric'] + 1, [IDE]))
    control(f"a formula '=PLANTED_FACTOR*2' among the cells of '{IDE}': formulas naming a name that carries a constant", len(rep['f_const']), len(R['E1']['f_const']) + 1)
    control(f"a name PLANTED_DERIVED = PLANTED_FACTOR*2, scoped to '{IDE}', in the same copy: names defined through a name that carries a constant", len(rep['n_const']), len(R['E1']['n_const']) + 1)
    control(f"a name PLANTED_CELL, a cell reference scoped to '{IDE}', in the same copy, and a formula '=PLANTED_CELL*2' among its cells: formulas naming a sheet-local name", len(rep_l['f_local']), len(R['E1']['f_local']) + 1)
    control(f"a formula '=Solver_Planted+0' among the cells of '{IDE}': formulas naming a Solver setting by its prefix", len(rep_s['f_solver']), len(R['E1']['f_solver']) + 1)
    control(f"a global name PLANTED_LITERAL whose text is the literal string TEXT, in another copy of E1's xl/workbook.xml, and a formula '=PLANTED_LITERAL' among the cells of '{IDE}': its scope and kind, carrying a constant, formulas naming a name that carries a constant", (kt, len(rep_t['const']), len(rep_t['f_const'])), ([(None, 'constant')], len(R['E1']['const']) + 1, len(R['E1']['f_const']) + 1))
    control(f"an array formula '=PLANTED_FACTOR*1' among the cells of '{IDE}', in the copy carrying PLANTED_FACTOR: formulas, formulas naming a name that carries a constant", (rep_a['formulas'], len(rep_a['f_const'])), (R['E1']['formulas'] + 1, len(R['E1']['f_const']) + 1))
    control(f"the Solver field - the copy carrying PLANTED_FACTOR, a constant not named solver_; a copy carrying Solver_Planted = 0.85 beside E1's own names: all names carrying a constant named solver_*", (rep['solver'], rep_v['solver']), (False, True))
    control("a global name PLANTED_QUOTE whose text is the literal string PLANTED_LITERAL, in a copy of the copy carrying PLANTED_LITERAL: carrying a constant, numeric, names whose value names one - a constant whose text names a constant is not one", (len(rep_q['const']), rep_q['numeric'], len(rep_q['n_const'])), (len(R['E1']['const']) + 2, R['E1']['numeric'], len(R['E1']['n_const'])))
    control("the names planted, read back with their kinds - in the first copy a number, a cell reference and a formula through a name; in another copy of E1's xl/workbook.xml a name with no text, a LET/LAMBDA parameter's prefix carrying a number, a name carrying the error #NAME?: each name, its scope, its kind; the text read for the name with none", (kinds, empty), ([('PLANTED_FACTOR', IDE, 'constant'), ('PLANTED_CELL', IDE, 'cell reference'), ('PLANTED_DERIVED', IDE, 'formula'), ('PLANTED_EMPTY', IDE, 'formula'), ('_xlpm.PLANTED_PARAM', None, 'constant'), ('PLANTED_ERROR', None, 'constant')], ['']))
    probe = '=IF(V.X, ' + (names_far[0] if names_far else 'NONE') + ', 0)'
    ws.cell(row=pr, column=1).value = probe
    _, hits2 = far_refs(W['E1'].f)
    unplant(ws, pr)
    control(f"a formula {probe!r} among the cells of '{IDE}': formulas that reference the sheets of A4-A5 or their names", len(hits2), len(hits) + 1)
    near = '=IF(X' + (names_far[0] if names_far else 'NONE') + ', ' + (names_far[0] if names_far else 'NONE') + 'X, 0)'
    ws.cell(row=pr, column=1).value = near
    _, hits5 = far_refs(W['E1'].f)
    unplant(ws, pr)
    control(f"a formula {near!r} among the cells of '{IDE}', the name only inside longer names: formulas that reference the sheets of A4-A5 or their names", len(hits5), len(hits))
    direct = "='IRR Up Shock'!B2*1"
    ws.cell(row=pr, column=1).value = direct
    _, hits3 = far_refs(W['E1'].f)
    unplant(ws, pr)
    control(f"a formula {direct!r} among the cells of '{IDE}', naming a sheet of A4-A5 directly: formulas that reference the sheets of A4-A5 or their names", len(hits3), len(hits) + 1)
    ws.cell(row=pr, column=1).value = ArrayFormula(f'A{pr}', direct)
    _, hits4 = far_refs(W['E1'].f)
    unplant(ws, pr)
    control(f"an array formula {direct!r} among the cells of '{IDE}', naming a sheet of A4-A5 directly: formulas that reference the sheets of A4-A5 or their names", len(hits4), len(hits) + 1)
    for t in ('E2', 'E3'):
        _, ys, neg = Q[t]
        cv = W[t].v['Corp Data'][ys[-1][0]]; keep = cv.value
        cv.value = -0.001
        neg2 = cqs0(t, W)[2]
        cv.value = keep
        control(f"{t}: the CQS 1 yield 'Corp Data'!{ys[-1][0]} set to -0.001 among the scanned values: negative", len(neg2), len(neg) + 1)
    import subprocess
    me, env = os.path.abspath(__file__), dict(os.environ, MANIFEST_CONTROLS_NOT_RUN='1')
    def itself(*args):
        p = subprocess.run([sys.executable, '-I', '-B'] + list(args), capture_output=True, env=env)
        return p.returncode, p.stdout, p.stderr
    code, out, err = itself(me, folder)
    control("the run itself on the folder given, as a child process with its controls not run: its exit status, the sha256 of what it prints - the frozen run's on the pins -, the bytes on its standard error", (code, hashlib.sha256(out).hexdigest(), len(err)), (0, '7644550931de4f53b0622dd9a202e70ede5525254024184963f40659a7b26bfb', 0))
    tmp = tempfile.mkdtemp(); raw = {t: open(f'{folder}/{t}.xlsm', 'rb').read() for t in PINS}
    open(os.path.join(tmp, 'E1.xlsm'), 'wb').write(raw['E1'] + b'\n')
    got1, h1 = itself(me, tmp), hashlib.sha256(raw['E1'] + b'\n').hexdigest()
    for t in PINS: open(os.path.join(tmp, f'{t}.xlsm'), 'wb').write(raw[t] + (b'\n' if t == 'E3' else b''))
    got3, h3 = itself(me, tmp), hashlib.sha256(raw['E3'] + b'\n').hexdigest()
    for t in PINS: os.remove(os.path.join(tmp, f'{t}.xlsm'))
    os.rmdir(tmp)
    control("the run itself, as a child process, on a folder holding E1.xlsm alone - a copy of its pin with one byte more: its exit status, what it prints, its standard error", got1, (2, f'pin E1: DIFFERENT {h1}\n'.encode(), b''))
    control("the run itself, as a child process, on a folder whose E1.xlsm and E2.xlsm are their pins' bytes and E3.xlsm a copy of its pin with one byte more: its exit status, what it prints, its standard error", got3, (2, f'pin E1: equal\npin E2: equal\npin E3: DIFFERENT {h3}\n'.encode(), b''))
    imp = f"import importlib.util as u; s = u.spec_from_file_location('manifest', {me!r}); s.loader.exec_module(u.module_from_spec(s))"
    control("the tool imported as a module, as the bundle's tool imports it, in a child process given the folder: its exit status, what it prints, its standard error - nothing run", itself('-c', imp, folder), (0, b'', b''))
    print(f"=== controls: {len(ran) - len(failed)} of {len(ran)} as expected" + (f" - FAILED: {failed}" if failed else ''))
    if failed: sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1])
