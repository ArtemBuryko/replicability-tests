#!/usr/bin/env python3
"""The builders' input bundle, written from the pinned workbooks (read-only).

    python3 -I bundle.py <folder holding E1.xlsm E2.xlsm E3.xlsm - copies of the pinned files> <output folder, new>

One file per input range the frozen manifest declares (manifest/manifest.py, SPEC, role «input»), holding the
manifest's own canonical lines of that range - '<sheet>!<cell>\\t<value>\\n', row-major, the cached values rendered
by manifest.py's render() - so that its sha256 is the manifest's digest of the range; E1's own labels beside its
input cells (E1/labels.tsv: the label cells, and the four text boxes 'CSSR Calculation' draws beside inputs); a
README naming the layout, the workbooks and their own source lines; SHA256SUMS. Nothing else of the workbooks:
no output, intermediate, residual, excluded range or version cell, and no input cell computed by a formula.
openpyxl as manifest.py opens it: no macro run, no link followed, nothing saved. bundle_check.py re-hashes the
bundle against the manifest as recorded in manifest/MANIFEST.md, before any use.
"""
import hashlib, html, os, re, sys, zipfile
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'manifest'))
import manifest as M
from openpyxl.utils import get_column_letter

NAMES = {'E1': 'RFR extrapolation and VA calculation (19 May 2026).xlsm',
         'E2': 'RFR risk-corrected spread calculation (21 May 2026)- RFR TD formulas.xlsm',
         'E3': 'RFR risk-corrected spread calculation Non-EEA (21 May 2026) + RFR TD formulas.xlsm'}
# E1's labels: the cell beside each single input (G of H, K of L), or at the top of each column of inputs
LABEL_CELLS = [(M.IDE, ['G10', 'G11', 'G12', 'G14', 'G15', 'G16', 'K10', 'K11', 'K12', 'G24', 'H24', 'I24', 'J24']),
               (M.CS, ['G23']),
               (M.VT, ['G10', 'G11', 'G12', 'G22'])]
# and the text boxes 'CSSR Calculation' draws beside its inputs L10, L11, L13, L14: those ending in K10, K11, K13, K14
BOX_SHEET, BOX_COL, BOX_ROWS = M.CS, 'K', (10, 11, 13, 14)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', 'and')).strip('-')


def line(sheet, ref, value):
    return f"{sheet}!{ref}\t{M.render(value)}\n"


def text_boxes(path, sheet):
    z = zipfile.ZipFile(path)
    wbx = z.read('xl/workbook.xml').decode('utf-8')
    rid = re.search(r'<sheet\b[^>]*\bname="' + re.escape(escape(sheet, {'"': '&quot;'})) + r'"[^>]*\br:id="([^"]+)"', wbx).group(1)
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8')
    rel = re.search(r'<Relationship\b[^>]*\bId="' + re.escape(rid) + r'"[^>]*/>', rels).group(0)
    sheet_xml = re.search(r'\bTarget="([^"]+)"', rel).group(1).split('/')[-1]
    srels = z.read(f'xl/worksheets/_rels/{sheet_xml}.rels').decode('utf-8')
    drawing = [t.split('/')[-1] for t in re.findall(r'\bTarget="([^"]+)"', srels) if '/drawings/' in t]
    assert len(drawing) == 1, drawing
    x = z.read(f'xl/drawings/{drawing[0]}').decode('utf-8')
    out = []
    for a in re.findall(r'<xdr:twoCellAnchor\b.*?</xdr:twoCellAnchor>', x, re.S):
        fr = re.search(r'<xdr:from><xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>', a, re.S)
        to = re.search(r'<xdr:to><xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>', a, re.S)
        text = html.unescape(''.join(re.findall(r'<a:t>([^<]*)</a:t>', a)))
        out.append((get_column_letter(int(fr.group(1)) + 1), int(fr.group(2)) + 1,
                    get_column_letter(int(to.group(1)) + 1), int(to.group(2)) + 1, text))
    return out


def readme(rows, sources, nlab):
    t = ['# The input bundle\n\n',
         "The inputs of the six examples, as the publisher's three workbooks give them: the cells of each workbook's "
         "input ranges, and, for workbook E1, whose input cells carry no labels of their own, the labels its sheets "
         "show beside them. No result of any example is here; the input files hold no cell whose value a workbook "
         "computes by a formula.\n\n",
         '## The files\n',
         "Each `.tsv` file holds one line per non-empty cell, in row order, left to right: the cell as `<sheet>!<cell>`, "
         "a tab, and the value the workbook stores in it — a number at full precision, `TRUE` or `FALSE`, a date as "
         "`YYYY-MM-DDTHH:MM:SS`, text with a backslash written `\\\\`, a tab `\\t` and a line break `\\n`.\n\n",
         '| file | workbook | sheet | cells | lines |\n|---|---|---|---|---|\n']
    t += [f'| `{n}` | {w} | {s} | {r} | {k} |\n' for n, w, s, r, k in rows]
    t += [f"\n`E1/labels.tsv` — E1's labels, {nlab} lines in the same form: the cell beside each single input, or at "
          "the top of each column of inputs; and the four formula labels the sheet `CSSR Calculation` draws as text "
          "boxes beside inputs, each given by the cells its box spans, `<sheet>!<from>:<to> (text box)`, then its "
          "text in Excel's linear notation.\n\n",
          '`SHA256SUMS` — the sha256 of every other file here.\n\n',
          '## The workbooks\n| id | file | sha256 |\n|---|---|---|\n']
    t += [f'| {w} | {NAMES[w]} | `{M.PINS[w]}` |\n' for w in M.PINS]
    t += ["\nEach workbook's own source line, as its reproduction clause asks:\n"]
    t += [f'- {w}: {sources[w]}\n' for w in M.PINS]
    return ''.join(t)


def main(src, out):
    for t, pin in M.PINS.items():
        h = hashlib.sha256(open(f'{src}/{t}.xlsm', 'rb').read()).hexdigest()
        print(f"pin {t}: {'equal' if h == pin else 'DIFFERENT ' + h}")
        if h != pin:
            sys.exit(2)
    os.makedirs(out)
    W = {t: M.WB(f'{src}/{t}.xlsm') for t in M.PINS}
    files, rows = {}, []
    for case, role, t, sh, rng, sel, note in M.SPEC:
        if role != 'input':
            continue
        cells = list(W[t].cells(sh, rng, sel))
        body = ''.join(line(s, k, v) for s, k, _, _, v in cells)
        assert hashlib.sha256(body.encode('utf-8')).hexdigest() == M.digest(cells), (t, sh, rng)
        name = f"{t}/{slug(sh)}{'.' + rng.replace(':', '-') if rng else ''}.tsv"
        assert name not in files, name
        files[name] = body
        rows.append((name, t, sh, rng or "the sheet's constants", len(cells)))
    lab = []
    for sh, refs in LABEL_CELLS:
        for k in refs:
            v = W['E1'].v[sh][k].value
            assert v not in (None, ''), (sh, k)
            lab.append(line(sh, k, v))
    boxes = sorted((b for b in text_boxes(f'{src}/E1.xlsm', BOX_SHEET) if b[2] == BOX_COL and b[3] in BOX_ROWS), key=lambda b: b[3])
    assert [b[3] for b in boxes] == list(BOX_ROWS) and all(b[4] for b in boxes), boxes
    lab += [f"{BOX_SHEET}!{fc}{fr}:{tc}{tr} (text box)\t{M.render(text)}\n" for fc, fr, tc, tr, text in boxes]
    files['E1/labels.tsv'] = ''.join(lab)
    sources = {}
    for t in M.PINS:
        m = re.findall(r'"(Source: [^"]+)"', str(W[t].v['Disclaimer']['F8'].value))
        assert len(m) == 1, (t, m)
        sources[t] = m[0]
    files['README.md'] = readme(rows, sources, len(lab))
    order = sorted(files, key=lambda s: s.encode('utf-8'))
    for n in order:
        p = os.path.join(out, n)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(files[n])
    sums = ''.join(f"{hashlib.sha256(files[n].encode('utf-8')).hexdigest()}  {n}\n" for n in order)
    with open(os.path.join(out, 'SHA256SUMS'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(sums)
    for n in order:
        b = files[n].encode('utf-8')
        print(f"{n} · {b.count(10)} L · {len(b)} B · sha256 {hashlib.sha256(b).hexdigest()}")
    print(f"SHA256SUMS · {sums.count(chr(10))} L · sha256 {hashlib.sha256(sums.encode('utf-8')).hexdigest()}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
