#!/usr/bin/env python3
"""The corporate reference portfolio's spread and risk correction (the text's Annex F and G.1.2, G.5.3,
G.6.4) computed from the input bundle under named readings, and each build's returned outputs set
against them. Written apart from both builds' code and from the comparison tool; the standard library
alone; nothing here reads an official output.

The readings:
  as-supplied        an index's duration is the interpolation's abscissa as the input gives it
  rounded            that duration rounded to one decimal before the interpolation
  ...+proxy          G.5.3's formula applied to the input rows of credit quality steps 4 and 5 (C1 only)

Usage: python3 -I -B variants.py <bundle directory> <build-a1 outputs.json> <build-b1 outputs.json>
"""
import hashlib
import json
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

KEYS = ('s_corp', 'rc_corp', 's', 'rc', 'rcs')


def load(path):
    cells = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line:
                ref, value = line.split('\t', 1)
                cells[ref.rsplit('!', 1)[1]] = value
    return cells


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def split(cell):
    m = re.fullmatch(r'([A-Z]+)(\d+)', cell)
    return m.group(1), int(m.group(2))


def shift(col, by):
    n = 0
    for ch in col:
        n = n * 26 + ord(ch) - 64
    n, s = n + by, ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def round1(x):
    return float(Decimal(repr(x)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def interp(points, x):
    """G.1.2: linear inside the available points, flat outside."""
    points = sorted(points)
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) / (x1 - x0) * (x - x0)
    raise AssertionError(x)


def table(sheet, header_row):
    """The columns of a table whose first column, F, holds the maturities."""
    out = {}
    for cell, value in sheet.items():
        col, row = split(cell)
        if row == header_row and col != 'F' and num(value) is None:
            points, r = [], header_row + 1
            while num(sheet.get(f'F{r}')) is not None:
                if num(sheet.get(f'{col}{r}')) is not None:
                    points.append((float(sheet[f'F{r}']), float(sheet[f'{col}{r}'])))
                r += 1
            out[value.strip()] = points
    return out


def index_curves(sheet, rounded):
    """Each issuance type's (duration, yield) points; CQS 0 and CQS 6 by Tables 12 and 13."""
    out = {}
    for cell, value in sheet.items():
        if not re.fullmatch(r'(?:Non-)?Financials CQS [0-6]', value):
            continue
        col, row = split(cell)
        points, r = [], row + 3
        while f'{col}{r}' in sheet and num(sheet[f'{col}{r}']) is None:
            d, y = num(sheet.get(f'{shift(col, 1)}{r}')), num(sheet.get(f'{shift(col, 2)}{r}'))
            if d is not None and y is not None:
                points.append((round1(d) if rounded else d, y))
            r += 1
        if points:
            out[value] = points
    for sector in ('Financials', 'Non-Financials'):
        out[f'{sector} CQS 0'] = [(d, 0.85 * y if y >= 0 else 1.15 * y) for d, y in out[f'{sector} CQS 1']]
        out.setdefault(f'{sector} CQS 6', out[f'{sector} CQS 5'])
    return out


def ltas_curves(sheet):
    out = {}
    for cell, value in sheet.items():
        m = re.fullmatch(r'([A-Z]{3}) ((?:Non-)?Financials)', value)
        if m and split(cell)[0] == 'F':
            for cqs, points in table(sheet, split(cell)[1] + 2).items():
                out[(m.group(1), f'{m.group(2)} {cqs}')] = points
    return out


def model_bonds(sheet, heading):
    for cell, value in sheet.items():
        col, row = split(cell)
        if col == 'F' and value.startswith(heading):
            bonds, r = [], row + 3
            while f'F{r}' in sheet:
                w, d = num(sheet.get(f'G{r}')), num(sheet.get(f'H{r}'))
                if w is not None and w > 0 and d is not None:
                    bonds.append((sheet[f'F{r}'], round1(d), tuple(float(sheet[f'{c}{r}']) for c in 'IJK')))
                r += 1
            return bonds
    raise SystemExit(f'STOP: no portfolio headed {heading!r}')


def correction(spread, ltas):
    """G.6.4."""
    s, l = max(spread, 0.0), max(ltas, 0.0)
    return min(1.25 * l, 0.5 * min(s, l) + 0.4 * max(0.0, min(s - l, l)) + 0.3 * max(0.0, s - 2 * l))


def irr(flows, durations, yields):
    """F.3.4: the one yield that gives the frozen cash flows their present value at the bonds' yields."""
    target = math.fsum(cf * (1 + y) ** -d for cf, d, y in zip(flows, durations, yields))
    gap = lambda Y: math.fsum(cf * (1 + Y) ** -d for cf, d in zip(flows, durations)) - target
    Y = 0.5 * (min(yields) + max(yields))
    for _ in range(200):
        slope = math.fsum(-d * cf * (1 + Y) ** (-d - 1) for cf, d in zip(flows, durations))
        step = gap(Y) / slope
        Y -= step
        if abs(step) < 1e-17:
            break
    if abs(gap(Y)) > 1e-14:
        raise SystemExit('STOP: the root finder did not reach its root')
    return Y


def corporate(folder, heading, currency, rounded, proxy):
    sheet = lambda name: load(f'{folder}/{name}.tsv')
    rfr, curves, ltas = table(sheet('rfr'), 10), index_curves(sheet('corp-data'), rounded), ltas_curves(sheet('ltas'))
    bonds = model_bonds(sheet('corporate-bond-ref-portfolio'), heading)
    yields = []
    for issuer, d, _ in bonds:
        market, free = interp(curves[issuer], d), interp(rfr[currency], d)
        if proxy and int(issuer[-1]) >= 4:
            euro = interp(rfr['EUR'], d)
            market = free + max(0.0, market - euro + 0.5 * (free - euro))
        yields.append((market, free, market - correction(market - free, interp(ltas[(currency, issuer)], d))))
    durations = [b[1] for b in bonds]
    Y = [irr([b[2][j] for b in bonds], durations, [y[j] for y in yields]) for j in range(3)]
    return Y[0] - Y[1], Y[0] - Y[2]


def sums(build, s_corp, rc_corp):
    """9.2.5 to 9.2.7 with the build's own weights and government terms."""
    s = build['w_gov'] * build['s_gov'] + build['w_corp'] * s_corp
    rc = build['w_gov'] * build['rc_gov'] + build['w_corp'] * rc_corp
    return dict(zip(KEYS, (s_corp, rc_corp, s, rc, s - rc)))


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def main(bundle, a1, b1):
    for sub in ('E2', 'E3'):
        for name in ('corp-data', 'rfr', 'ltas', 'corporate-bond-ref-portfolio'):
            print(f'{sub}/{name}.tsv sha256 {sha(f"{bundle}/{sub}/{name}.tsv")}')
    builds = {}
    for name, path in (('build-a1', a1), ('build-b1', b1)):
        print(f'{name} outputs.json sha256 {sha(path)}')
        with open(path, encoding='utf-8') as f:
            builds[name] = json.load(f)
    diff = lambda a, b: float(Fraction(a) - Fraction(b))
    cases = (('C1', 'E3', 'Currency RCS GBP', 'GBP'), ('B1', 'E2', 'Currency RCS EUR', 'EUR'), ('B2', 'E2', 'Country RCS IT', 'EUR'))
    for case, sub, heading, currency in cases:
        readings = [('as-supplied', False, False), ('rounded', True, False)]
        if case == 'C1':
            readings += [('as-supplied+proxy', False, True), ('rounded+proxy', True, True)]
        got = {r: corporate(f'{bundle}/{sub}', heading, currency, rounded, proxy) for r, rounded, proxy in readings}
        print(f'== {case} — a build\'s returned output minus the reading\'s')
        for name, build in builds.items():
            for r, _, _ in readings:
                v = sums(build[case], *got[r])
                print(f'{name} − {r:<17} ' + ' · '.join(f'{k} {diff(build[case][k], v[k]):+.3e}' for k in KEYS))
        print(f'== {case} — one reading minus another, the sums with build-b1\'s weights and government terms')
        base = sums(builds['build-b1'][case], *got['as-supplied'])
        for r, _, _ in readings[1:]:
            v = sums(builds['build-b1'][case], *got[r])
            print(f'{r:<17} − as-supplied  ' + ' · '.join(f'{k} {diff(v[k], base[k]):+.3e}' for k in KEYS))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
