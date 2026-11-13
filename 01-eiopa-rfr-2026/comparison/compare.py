#!/usr/bin/env python3
"""compare.py — replicability test 01's comparison (the preregistration, §5 and §6): every declared output of each build
against the oracle, the publisher's workbooks' own cached outputs, within the bands frozen in §5. Standard library only,
Python 3.10 or later. It reads the workbooks as ZIP and XML, runs nothing in them, and writes only the files it is told to.

  python3 -I compare.py form <outputs.json> [--isolated]
      the file against the brief's form (`preregistration/brief.md`, «Your return», item 1); with --isolated, the A2 and
      A3 objects of a file written by the brief's item 3, its other keys left alone; a null — the brief's «a result you
      could not compute» — is counted beside the numbers, not a departure; exit 0 conforming, 1 not
  python3 -I compare.py a1 <workbooks> <MANIFEST.md> <out.json>
      the official A1 results in the form of the brief's "A1" object, for the isolated re-run (§6); a new file; exit 0
  python3 -I compare.py table <workbooks> <MANIFEST.md> <out folder> --build <name> <outputs.json>
                              [--isolated <name> <file>] ...
      in a new folder: table.tsv — one row per declared output per build, as returned and, where given, isolated;
      cases.tsv — per build, kind and case; divergences.tsv — every failing output, none chosen (§6); exit 0. Each
      file opens with the tool's sha256, the command — every file and folder in it shown by its role —, the pins and
      each input's sha256 and form; nothing in them depends on the time, the machine or where the files lie. A build's
      <name>: letters, digits, '.', '_' and '-', a letter or a digit first, 64 characters at most
  python3 -I compare.py same <outputs.json> <outputs.json>
      the declared outputs of two files compared value by value, exactly: an output is equal only where both files
      hold a number there and the two are the same rational; exit 0 all 535 equal, 1 not

<workbooks> is a folder holding E1.xlsm, E2.xlsm and E3.xlsm, copies of the pinned files: each is read once and held
to its pin — the bytes so held are the bytes then read —, and MANIFEST.md to the frozen manifest's sha256, before
anything is read. Every range the tool reads — each declared output
and the maturities a curve is keyed by — is rendered as the manifest's canonical lines, '<sheet>!<cell>\\t<value>\\n' row by
row: the cached value, an integer as str, a float as repr, a bool as TRUE or FALSE, a string with \\ \\t \\n escaped, an
empty cell skipped, the maturities' range its constants alone; its cell count and sha256 are held to the manifest's row:
the oracle compared with is the frozen manifest's, value for value. A number cell styled as a date, which the manifest's
reader would render as a date, is read here as its number: such a range differs from its digest and stops the run. On
bytes other than the pins this reader can part from the manifest's on an explicit empty value and on _xHHHH_ escapes;
every range is held to its digest, so such a difference stops the run — it never admits a value. A cached value its
type cannot read — a number, a boolean or a shared string's index given as an empty or a malformed <v>, an index
past the shared strings — stops the run, naming its cell; so does an official value that is not a finite number,
a boolean, or an integer past the double range, held to that range as a builder's value is.

A builder's value counts when it is a JSON number within the double range, not a boolean — an integer token judged on
its digits before any conversion, its magnitude above the largest finite double a failure; a decimal token judged as
the double it parses to, so that one rounding to the largest finite double counts and one rounding past it fails —;
an output missing,
null, non-numeric, beyond the double range, given twice in its object or under another key fails (§5). The bands (§5):
the curves |b - o| <= 1.0e-5; the two VA values rounded to 4 decimals |b - o| < 0.5e-4; every other output of A1-A3
<= 1.0e-9; the 27 outputs of B1, B2 and C1 by output, as §5 lists them, each band reached inclusive. Each difference is
exact: both values taken as rationals, the band as its decimal, so no rounding decides a result. The table carries each
builder value and the magnitude of its difference to three significant digits — rounded half to even from the exact
rational under a decimal context of its own, so that no caller's context changes or stops it —, not the official
value: the oracle is pinned by its digests, not copied (§2). Each build's file is read once: the sha256 a table or a
check names is that of the very bytes it judged.
Exit 2 — a pin, a digest, a range's shape, a name, a file the tool needs or any other error stops the run. Its outputs
are composed in full before the first write; the descriptor of the folder they go into is taken inside the region whose
stop removes and closes; the folder is made new in its existing parent and opened at once, never through a link, and
checked empty; each file is created exclusively inside the folder so opened, never over another, never through a link,
and written whole — a write that writes fewer bytes than it was given carried on from where it stopped, one that
writes no byte an error the run stops for, as for the commands' own lines —; each thing the run makes is entered
before it is made; after the last write the folder and then each of its files —
or the A1 file — at its path, as given and resolved then, its last component not a link, is checked to be the one the
run made and wrote into. An error before those checks end, or a SIGINT the run stops for, removes what the run made,
newest first, each file and the folder only while it is still the run's own — known by its device and inode, held open
by the run until it ends so that no other file can take them; never another's put in its place —, and the stop names
anything it did not remove: left in place, another's in its place, not found where the run made it, made but its
identity not read, or found where its making was under way and not opened as the run's own — a making that fails,
before its effect or after it, keeps its entry, its path read before the stop is composed, a thing found there named
as left —; a removal that fails is read again at its path: found gone, it is named as removed, its failure beside it;
still there, or its path not read, as not removed. Then every descriptor is
closed, newest first — the order they were taken in, reversed —, the parent's last, each close in its own try; a close
that fails — whatever Exception it raises — is named in the stop and the closing goes on — after the checks it leaves
what was written whole and checked: no longer held, it is named, not removed. The stop is said once; nothing is
written after it.
Each command's own lines are said once its work is done — for table and a1 once their outputs are written whole and
checked —, inside the run's account: composed, encoded by stdout's own encoding and written through its descriptor,
what the stream's buffer holds flushed first, every byte counted — a write that writes fewer bytes than it was given
carried on from where it stopped —; where that encoding marks its start or carries a state from one write to the
next — a byte-order mark, a shift between character sets, a character held back for the one after it: probed by
its incremental encoder after each of a few first pieces against the lines encoded afresh (stateful) —, they are
written through the stream object itself instead, its own encoder continuing what it wrote, every character counted
and the stream flushed, its binary layer a native buffered writer — or, where it is not, a failure before any
line —; a stdout with no descriptor of its own is written line by line and flushed as a
stream, every character counted by what each write returns — a write that takes fewer characters than it was given
carried on from where it stopped; one that takes none, or returns no count of what it was given, a failure — one
helper's rule (carry), which a stop's line to stderr keeps too. A stream
that cannot take them — not open, a pipe whose reader has gone, a full pipe that does not block, a full disk, a write
that writes no byte or takes no character — is an error the run stops for, exit 2, the stop naming it and, for table
and a1, naming their outputs as left — written whole and checked, no longer held, nothing removed —; the stream is first
left with nothing for the interpreter's own flush at exit to fail on (the Python documentation's note on SIGPIPE): its
descriptor pointed at the null device, so that what its buffer still holds goes nowhere — where the null device's
descriptor takes the stream's own number, the stream's descriptor was already closed and that one stays open as the
stream's —; where the null device cannot be opened — whatever Exception its opening raises — or pointed to, or the
stream has no descriptor of its own, the
stream object closed, the failure of its last flush caught — and where its close fails and leaves it open, or its
state cannot be read, the stream taken from that flush instead: the sys attribute that holds it, stdout or stderr, set
to None, which CPython's flush at exit passes over, so that exit 2 stays the stop's sign; a stream object whose own
flush still fails once its descriptor is pointed — or once the null device's descriptor has taken the stream's own
number — is taken from that flush the same way, and a fileno that returns
no int is no descriptor of its own. The null device's descriptor, once pointed, is closed: a
close that fails — whatever Exception it raises, before the descriptor is released or after — is caught, nothing
raised, and named in the stop
beside the stream's failure, table's and a1's outputs named as left with them, exit 2 kept. A stop's line is written
to stderr as a stream by the same helper (carry) — every character stderr takes counted, a write that takes fewer
carried on from where it stopped, one that takes none or returns no count of what it was given a failure —; a stderr
that cannot take it — absent, not open, a write that fails, takes none or returns no count, any Exception its own
calls raise — is named, not held: the stop is then unsaid, or said as far as it went, the exit status 2 its only
sign, that stream left the same way — no Exception leaves the run. Each standard stream is read once where the tool
acts on it — the stream sys holds, or None where it holds none: one deleted from sys is taken as None is (std); shut,
taking a stream from the exit's flush, reads stdout and stderr by the same rule —, and the stream so read is the one
written and, failing, left with nothing for the exit's flush; any Exception that stream object's own calls raise —
its write, flush, fileno or close — is a failure of that stream, taken in. Every exception the tool takes and names —
a stream's; the operating system's at a making, an opening or a removal; a close's, whatever it raises; the decoder's
and the JSON parser's on a build's bytes; an error it did not foresee — is
rendered inside the guard that took it (rendered): its class and its message, or its message alone where that is a
stop's own words or the system's — an OSError's reason, where it holds one, by the same guard (reason) —; a message,
or a reason, that raises when it is rendered is named by the exception's class alone. Where undo itself raises, the
stop names it and what the run made, as not all looked at, and every descriptor the run holds is still closed.
The decoder's and the JSON parser's own errors on a build's bytes are named in the words those modules give them.
The command line's parser is built with sys.stdout set to None — the stream read once before and
put back after, one deleted from sys put back as None —, so that it reads
nothing of the stream before the run — Python 3.14's argparse probes stdout for colour as each parser and formatter is
made —; argparse's own help and usage, said by argparse before any run, stand outside the run's account.
SIGINT is held: from before the parent's descriptor is taken until the stop is said — for table and a1 until their own
lines are said and looked after, the writer's hold inside theirs, one restore —, a handler of the run's own, installed
in the main thread, only takes the signal in; the handler it displaces is read before it and restored when the hold
ends, however the run ends. The run looks for a taken signal only where its state is whole: before the folder or the
file is made, after each thing is opened, after each write, after the checks at the paths, once the closing is done
and, for table and a1, once their own lines are said. Found while the displaced handler is Python's default, it stops
the run there as its interrupt — what was made removed, every descriptor closed, the stop said once and naming it;
found once the closing is done or once the lines are said, the outputs written whole and checked are named, not
removed; a stop for an error, a signal taken meanwhile, names both —; under any other handler the run goes on. When
the hold ends, a taken signal is sent again to the restored handler: Python's default then raises KeyboardInterrupt,
after the stop. Not held, named: an
exception the process raises in itself otherwise than through its SIGINT handler — a trace or profile function's, or
one set on the thread —, which can fall anywhere and cut the stop short; a run outside the main thread, which SIGINT's
KeyboardInterrupt never reaches, and a run under a handler not set from Python, which cannot be restored — both run
unheld; a signal that comes after the run's last look — once the closing is done; for table and a1 once their lines
are said and looked after —, raised as the hold ends, its coming unnamed; a second signal while one is held, taken
with it; SIGTERM, a kill or a crash, which leave what was written; a close of the null device's descriptor that
fails before the descriptor is released, which leaves it open — named in the stop; a stream object whose close fails
and leaves it open, taken from sys but not closed: what its buffer holds is not written, its finalization left to
the interpreter; a stdout whose encoding carries a state none of the probe's first pieces reaches, taken as
stateless, its lines encoded afresh; a restore of the displaced handler that fails — signal.signal raising, which
valid arguments in the
main thread do not —, which leaves the run's own handler installed, a later SIGINT taken in by it and never passed
on, and stops the run with that error, the outputs unnamed; an exception a stream object's own calls raise that is
no Exception — a direct BaseException, SystemExit among them —, which the run's catches let pass: it leaves the run
as it was raised, the stop unsaid. What POSIX leaves open, named: a
process that can
write the parent and puts an empty folder of its own in place of the new one between its making and its opening
receives the files; a
replacement in the instant between a removal's check and the removal is removed; a link another process makes to a file
of the run's keeps its bytes when the run removes its name; a removal that fails leaves what was written; the paths are
checked once, one after another, after the last write — a rename after a path's check is not seen; the tool's own
sha256 is that of its file as read when it starts; an exclusive create that fails with EEXIST is taken at its word —
what is at its path is not the run's own, never removed, the stop naming it as existing —: a create that made its
folder or its file and then said EEXIST leaves it named so, and a file of table's it made unnamed among what is left;
one that says EEXIST where nothing is names its path as existing all the same.
"""
import argparse
import codecs
import decimal
import hashlib
import io
import json
import math
import os
import posixpath
import re
import signal
import sys
import threading
import xml.etree.ElementTree as ET
import zipfile
from fractions import Fraction

PINS = {'E1': 'c1ce32a3f76cf50f4d3de267292ee5af355fea9d31b60c4d2a01a98dff777dc4',
        'E2': '5302c91ba000568fd99adb0c98a08af9cb3089b412f0200a77c5488fb85cfe07',
        'E3': '67bf3478293b810691460569cf79751cf4c90e57a2773cbbd4da9f92b2486b81'}
MANIFEST_SHA256 = '9326a27c65613fe0187c1d21bd9242999c242b5ee0720923e7b5357f5750ed55'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
IDE, CSS, VAT = 'Input Data & Extrapolation', 'CSSR Calculation', 'VA Term Structures'
CURVE, VA4, EXACT = ('<=', '1.0e-5'), ('<', '0.5e-4'), ('<=', '1.0e-9')
RCS_KEYS = ('w_gov', 'w_corp', 's_gov', 's_corp', 'rc_gov', 'rc_corp', 's', 'rc', 'rcs')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}')
MAX_INT = int(sys.float_info.max)
MAX_DIGITS = len(str(MAX_INT))
PRIOR = ('', 'a', 'é', 'Ê', 'α', 'か', '日', '中', '한', 'ｱ')
FD_OPS = all(f in os.supports_dir_fd for f in (os.open, os.mkdir, os.stat, os.unlink, os.rmdir)) and \
    os.listdir in os.supports_fd
with open(os.path.abspath(__file__), 'rb') as _own:
    TOOL_SHA256 = hashlib.sha256(_own.read()).hexdigest()


def rcs_items(col, s_corp, rc_corp, s, rc, rcs):
    bands = (EXACT, EXACT, EXACT, ('<=', s_corp), EXACT, ('<=', rc_corp), ('<=', s), ('<=', rc), ('<=', rcs))
    return [(f'{col}{11 + i}', key, band) for i, (key, band) in enumerate(zip(RCS_KEYS, bands))]


# Each row of the manifest the tool reads: case, workbook, sheet, range, and what it holds — a curve keyed by the
# maturity its rows carry in the maturities' range, or scalars named by their cells (the brief's keys, §5's bands).
ROWS = [
    ('A1', 'E1', IDE, 'K25:K74', ('curve', 'zero_rates_cc', EXACT, 'G25:G174', 50)),
    ('A1', 'E1', IDE, 'L22', [('L22', 'llfr', EXACT)]),
    ('A1', 'E1', IDE, 'L25:L174', ('curve', 'basic_rfr', CURVE, 'G25:G174', 150)),
    ('A2', 'E1', CSS, 'H10', [('H10', 'notional_va', VA4)]),
    ('A2', 'E1', CSS, 'L16', [('L16', 'cssr', EXACT)]),
    ('A2', 'E1', CSS, 'K20', [('K20', 'llfr', EXACT)]),
    ('A2', 'E1', CSS, 'L24:L173', ('curve', 'curve', CURVE, 'G24:G173', 150)),
    ('A3', 'E1', VAT, 'L10:L11', [('L10', 'currency_va', EXACT), ('L11', 'omega_co', EXACT)]),
    ('A3', 'E1', VAT, 'L13', [('L13', 'total_va', VA4)]),
    ('A3', 'E1', VAT, 'K20', [('K20', 'llfr', EXACT)]),
    ('A3', 'E1', VAT, 'L23:L172', ('curve', 'curve', CURVE, 'G23:G172', 150)),
    ('B1', 'E2', 'RCS', 'G11:G19', rcs_items('G', '2.8e-5', '4.2e-5', '1.7e-5', '2.6e-5', '8.6e-6')),
    ('B2', 'E2', 'RCS', 'K11:K19', rcs_items('K', '3.7e-5', '5.5e-5', '1.5e-5', '2.2e-5', '7.4e-6')),
    ('C1', 'E3', 'RCS', 'G11:G19', rcs_items('G', '8.0e-5', '1.1e-4', '6.2e-5', '7.9e-5', '1.8e-5')),
]
CASES = ('A1', 'A2', 'A3', 'B1', 'B2', 'C1')
# the brief's form: each case's keys in order, a curve with its number of maturities, a scalar with None
FORM = {'A1': [('zero_rates_cc', 50), ('llfr', None), ('basic_rfr', 150)],
        'A2': [('notional_va', None), ('cssr', None), ('llfr', None), ('curve', 150)],
        'A3': [('currency_va', None), ('omega_co', None), ('total_va', None), ('llfr', None), ('curve', 150)],
        'B1': [(k, None) for k in RCS_KEYS], 'B2': [(k, None) for k in RCS_KEYS], 'C1': [(k, None) for k in RCS_KEYS]}
SOURCE = 'Source: EIOPA - European Insurance and Occupational Pensions Authority (the oracle: the workbooks\' cached outputs, read and compared here, not reproduced)'


class Stop(Exception):
    """A pin, a digest, a range's shape or a needed file fails: the run stops, nothing more is written. said: the stop
    already said where it was raised — main does not say it again."""

    def __init__(self, *args, said=False):
        super().__init__(*args)
        self.said = said


class NonNumber:
    def __init__(self, why):
        self.why = why


class Twice:
    def __init__(self, values):
        self.values = values


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_bytes(path):
    """A file's bytes, read once: whatever is hashed, parsed or judged of it comes from these."""
    with open(path, 'rb') as f:
        return f.read()


# ---- the workbooks: their cached values as the manifest's reader gives them ------------------------------------------

def split_ref(ref):
    m = re.fullmatch(r'([A-Z]{1,3})([0-9]+)', ref or '')
    if not m:
        raise Stop(f'a cell reference the tool does not read: {ref!r}')
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)), col


def bounds(rng):
    a, _, b = rng.partition(':')
    (r0, c0), (r1, c1) = split_ref(a), split_ref(b or a)
    return min(r0, r1), min(c0, c1), max(r0, r1), max(c0, c1)


def rich(el):
    """The text of an <si> or an <is>: its own <t>, else its runs' <t> joined; phonetic runs left out."""
    t = el.find(NS + 't')
    if t is not None:
        return t.text or ''
    return ''.join(r.findtext(NS + 't') or '' for r in el.findall(NS + 'r'))


def number(text):
    """A cached number as the manifest's reader casts it: a float where its text has '.', 'E' or 'e', else an int."""
    return float(text) if ('.' in text or 'E' in text or 'e' in text) else int(text)


def render(v):
    """The manifest's canonical rendering of a cached value."""
    if isinstance(v, bool):
        return 'TRUE' if v else 'FALSE'
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, int):
        return str(v)
    return str(v).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')


class Book:
    def __init__(self, src, name=None):
        """src: a path, or the bytes already read and held to their pin, as a file object; name: what a stop calls it."""
        name = src if name is None else name
        self.z = zipfile.ZipFile(src)
        wb = ET.fromstring(self.z.read('xl/workbook.xml'))
        rels = ET.fromstring(self.z.read('xl/_rels/workbook.xml.rels'))
        target = {r.get('Id'): r.get('Target') for r in rels.iter(REL)}
        self.paths = {}
        for s in wb.iter(NS + 'sheet'):
            t = target.get(s.get(RID))
            if t is None:
                raise Stop(f'{name}: sheet {s.get("name")!r} has no target')
            self.paths[s.get('name')] = t[1:] if t.startswith('/') else posixpath.normpath(posixpath.join('xl', t))
        try:
            sst = ET.fromstring(self.z.read('xl/sharedStrings.xml'))
            self.sst = [rich(si) for si in sst.findall(NS + 'si')]
        except KeyError:
            self.sst = []
        self.sheets = {}

    def sheet(self, name):
        if name not in self.sheets:
            if name not in self.paths:
                raise Stop(f'no sheet {name!r}')
            x = ET.fromstring(self.z.read(self.paths[name]))
            cells, arrays = {}, []
            for c in x.iter(NS + 'c'):
                f, v, t = c.find(NS + 'f'), c.find(NS + 'v'), c.get('t', 'n')
                if f is not None and f.get('t') == 'array' and f.get('ref'):
                    arrays.append(bounds(f.get('ref')))
                cells[split_ref(c.get('r'))] = (c.get('r'), t, f is not None, None if v is None else (v.text or ''),
                                                c.find(NS + 'is'))
            self.sheets[name] = (cells, arrays)
        return self.sheets[name]

    def cached(self, t, vtext, inline):
        if t == 'inlineStr':
            return rich(inline) if inline is not None else None
        if vtext is None:
            return None
        if t == 'n':
            return number(vtext)
        if t == 's':
            return self.sst[int(vtext)]
        if t == 'b':
            return bool(int(vtext))
        if t in ('str', 'e'):
            return vtext
        raise Stop(f'a cell type the tool does not read: {t!r}')

    def cells(self, sheet, rng, selection):
        """[(cell, cached value)] row by row, as the manifest's reader yields them: the cells that are not empty
        in the workbook's formula view; with 'const', those that carry no formula and lie in no array formula. A
        cached value its type cannot read — an empty or a malformed <v>, an index past the shared strings — stops the
        run, naming its cell; so does a cell of a type the tool does not read."""
        cells, arrays = self.sheet(sheet)
        r0, c0, r1, c1 = bounds(rng)
        out = []
        for (r, c) in sorted(k for k in cells if r0 <= k[0] <= r1 and c0 <= k[1] <= c1):
            ref, t, has_f, vtext, inline = cells[(r, c)]
            try:
                value = self.cached(t, vtext, inline)
            except (ValueError, IndexError):
                raise Stop(f"'{sheet}'!{ref}: a cached value the tool does not read as its type {t!r}: "
                           f'{vtext!r}') from None
            except Stop as x:
                raise Stop(f"'{sheet}'!{ref}: {rendered(x, False)}") from None
            if not has_f and vtext is None and not (t == 'inlineStr' and inline is not None):
                continue
            derived = has_f or any(a <= r <= b and x <= c <= y for a, x, b, y in arrays) \
                or (isinstance(value, str) and value.startswith('='))
            if selection == 'const' and derived:
                continue
            out.append((ref, value))
        return out


def digest(sheet, cells):
    return sha256_bytes(''.join(f'{sheet}!{ref}\t{render(v)}\n' for ref, v in cells).encode('utf-8'))


ROW = re.compile(r"^(\S+) · (\w+) · (E[123]) · '((?:[^']|'')+)'!([A-Z]+[0-9]+(?::[A-Z]+[0-9]+)?) · (\w+) · ([0-9]+) · "
                 r"([0-9a-f]{64}) · (.*)$")


def manifest_rows(path, sha):
    with open(path, 'rb') as f:
        data = f.read()
    if sha256_bytes(data) != sha:
        raise Stop(f'{path}: sha256 {sha256_bytes(data)} is not the frozen manifest\'s {sha}')
    rows = {}
    for line in data.decode('utf-8').split('\n'):
        m = ROW.match(line)
        if m:
            key = (m.group(3), m.group(4).replace("''", "'"), m.group(5))
            rows.setdefault(key, []).append({'case': m.group(1), 'role': m.group(2), 'selection': m.group(6),
                                             'cells': int(m.group(7)), 'sha256': m.group(8)})
    return rows


def hold(rows, wb, sheet, rng, role, selection, cells, held):
    """The range as read, held to its one row of the manifest: its role, selection, cell count and digest."""
    found = rows.get((wb, sheet, rng), [])
    if len(found) != 1:
        raise Stop(f"{wb} '{sheet}'!{rng}: {len(found)} rows in the manifest, not one")
    row = found[0]
    if (row['role'], row['selection']) != (role, selection):
        raise Stop(f"{wb} '{sheet}'!{rng}: the manifest's row is {row['role']}/{row['selection']}, not {role}/{selection}")
    got = digest(sheet, cells)
    if len(cells) != row['cells'] or got != row['sha256']:
        raise Stop(f"{wb} '{sheet}'!{rng}: {len(cells)} cells, sha256 {got} — the manifest's row {row['cells']} cells, "
                   f"{row['sha256']}: the range differs from its digest")
    held.append((wb, sheet, rng, role, len(cells), got))


def official_number(where, v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)):
        raise Stop(f'{where}: the official value is not a finite number: {v!r}')
    if abs(v) > MAX_INT:
        raise Stop(f'{where}: the official value is an integer past the double range')
    return v


def read_oracle(folder, manifest, pins=None, manifest_sha=None):
    """{(case, key, maturity or None): (cell, band, official value)} in the brief's order, and the ranges held."""
    pins = PINS if pins is None else pins
    manifest_sha = MANIFEST_SHA256 if manifest_sha is None else manifest_sha
    raws = {}
    for k in ('E1', 'E2', 'E3'):
        p = os.path.join(folder, k + '.xlsm')
        if not os.path.isfile(p):
            raise Stop(f'{p}: missing')
        raw = read_bytes(p)
        h = sha256_bytes(raw)
        if h != pins[k]:
            raise Stop(f'{k}.xlsm: sha256 {h} is not its pin {pins[k]}')
        raws[k] = (p, raw)
    rows = manifest_rows(manifest, manifest_sha)
    books = {k: Book(io.BytesIO(raw), p) for k, (p, raw) in raws.items()}
    oracle, held, mats_held = {}, [], {}
    for case, wb, sheet, rng, items in ROWS:
        cells = books[wb].cells(sheet, rng, 'all')
        hold(rows, wb, sheet, rng, 'output', 'all', cells, held)
        if isinstance(items, tuple):
            _, key, band, mrng, n = items
            if (wb, sheet, mrng) not in mats_held:
                mcells = books[wb].cells(sheet, mrng, 'const')
                hold(rows, wb, sheet, mrng, 'input', 'const', mcells, held)
                mats_held[(wb, sheet, mrng)] = {split_ref(ref)[0]: v for ref, v in mcells}
            mats = mats_held[(wb, sheet, mrng)]
            r0, c0, r1, c1 = bounds(rng)
            if c0 != c1 or len(cells) != r1 - r0 + 1 or len(cells) != n:
                raise Stop(f"{wb} '{sheet}'!{rng}: {len(cells)} cells — a curve of {n} maturities, one cell a row")
            seen = []
            for ref, v in cells:
                r = split_ref(ref)[0]
                m = mats.get(r)
                if isinstance(m, bool) or not isinstance(m, int):
                    raise Stop(f"{wb} '{sheet}'!{ref}: its row carries no integer maturity in {mrng}: {m!r}")
                seen.append(m)
                oracle[(case, key, m)] = (f"'{sheet}'!{ref}", band, official_number(f"'{sheet}'!{ref}", v))
            if seen != list(range(1, n + 1)):
                raise Stop(f"{wb} '{sheet}'!{rng}: its maturities are not 1 to {n} in order")
        else:
            got = dict(cells)
            if set(got) != {c for c, _, _ in items}:
                raise Stop(f"{wb} '{sheet}'!{rng}: cells {sorted(got)}, not {[c for c, _, _ in items]}")
            for c, key, band in items:
                oracle[(case, key, None)] = (f"'{sheet}'!{c}", band, official_number(f"'{sheet}'!{c}", got[c]))
    order = {(case, key): i for i, (case, key) in enumerate((c, k) for c in CASES for k, _ in FORM[c])}
    ordered = dict(sorted(oracle.items(), key=lambda kv: (order[kv[0][:2]], kv[0][2] or 0)))
    if len(ordered) != 535:
        raise Stop(f'{len(ordered)} declared outputs read, not 535')
    return ordered, held


# ---- a build's file: its values as JSON gives them, nothing coerced -------------------------------------------------

def load_hashed(path):
    """(the parsed file or None, notes on its form, why it does not parse or None, the sha256 of the very bytes
    parsed): the file read once."""
    raw = read_bytes(path)
    return parse(raw) + (sha256_bytes(raw),)


def load(path):
    """(the parsed file or None, notes on its form, why it does not parse or None)."""
    return load_hashed(path)[:3]


def parse(raw):
    """(the parsed bytes or None, notes on their form, why they do not parse or None): why in the decoder's or the
    JSON parser's own words, rendered inside the guard that took them (rendered)."""
    notes = []
    if raw[:3] == b'\xef\xbb\xbf':
        notes.append('a UTF-8 byte-order mark before the JSON')
        raw = raw[3:]
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return None, notes, f'the file is not UTF-8 ({rendered(e, False)})'

    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                prev = d[k]
                d[k] = Twice((prev.values if isinstance(prev, Twice) else [prev]) + [v])
            else:
                d[k] = v
        return d

    def token(s):
        return s if len(s) <= 24 else f'{s[:8]}…{s[-4:]} ({len(s)} characters)'

    def as_float(s):
        x = float(s)
        return x if math.isfinite(x) else NonNumber(f'{token(s)}, past the double range')

    def as_int(s):
        digits = s.lstrip('-')
        if len(digits) > MAX_DIGITS or abs(int(s)) > MAX_INT:
            return NonNumber(f'{token(s)}, past the double range')
        return int(s)

    try:
        data = json.loads(text, object_pairs_hook=pairs, parse_float=as_float, parse_int=as_int,
                          parse_constant=lambda s: NonNumber(f'{s}, not a JSON number'))
    except ValueError as e:
        return None, notes, f'the file does not parse as JSON ({rendered(e, False)})'
    return data, notes, None


def kind_of(v):
    if isinstance(v, Twice):
        return 'given twice'
    if isinstance(v, NonNumber):
        return 'non-numeric: ' + v.why
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'non-numeric: a JSON boolean'
    if isinstance(v, (int, float)):
        return None
    return 'non-numeric: a JSON ' + {str: 'string', dict: 'object', list: 'array'}.get(type(v), type(v).__name__)


def value_at(data, why, case, key, index):
    """(the number, None), or (None, why the output fails)."""
    if why is not None:
        return None, 'the file does not parse'
    node, path = data, [case, key] + ([str(index)] if index is not None else [])
    for i, k in enumerate(path):
        where = '.'.join(path[:i]) or 'the file'
        if isinstance(node, Twice):
            return None, f'{where} given twice'
        if not isinstance(node, dict):
            return None, f'{where} is not a JSON object'
        if k not in node:
            return None, 'missing'
        node = node[k]
    k = kind_of(node)
    return (node, None) if k is None else (None, k)


def form(data, notes, why, isolated=False):
    """(the deviations from the brief's form, the count of numbers it holds where the form expects one, the count of
    nulls there — the brief's «a result you could not compute», not a deviation)."""
    dev, numbers, nulls = list(notes), 0, 0
    if why is not None:
        return dev + [why], 0, 0
    if not isinstance(data, dict):
        return dev + ['the file is not a JSON object'], 0, 0
    cases = ('A2', 'A3') if isolated else CASES
    if not isolated:
        extra = [k for k in data if k not in FORM]
        if extra:
            dev.append(f'keys beyond the brief\'s six: {extra}')
    for case in cases:
        obj = data.get(case)
        if case not in data:
            dev.append(f'{case} missing')
            continue
        if not isinstance(obj, dict):
            dev.append(f'{case}: {kind_of(obj) or "a number"}, not an object')
            continue
        want = [k for k, _ in FORM[case]]
        extra = [k for k in obj if k not in want]
        if extra:
            dev.append(f'{case}: keys beyond the brief\'s: {extra}')
        for key, n in FORM[case]:
            if key not in obj:
                dev.append(f'{case}.{key} missing')
                continue
            v = obj[key]
            if n is None:
                k = kind_of(v)
                if k is None:
                    numbers += 1
                elif v is None:
                    nulls += 1
                else:
                    dev.append(f'{case}.{key}: {k}')
                continue
            if not isinstance(v, dict):
                dev.append(f'{case}.{key}: {kind_of(v) or "a number"}, not an object of maturities')
                continue
            names = [str(m) for m in range(1, n + 1)]
            missing = [m for m in names if m not in v]
            extra = [m for m in v if m not in names]
            if missing:
                dev.append(f'{case}.{key}: maturities missing {missing}')
            if extra:
                dev.append(f'{case}.{key}: keys beyond maturities 1 to {n}: {extra}')
            for m in names:
                if m in v:
                    k = kind_of(v[m])
                    if k is None:
                        numbers += 1
                    elif v[m] is None:
                        nulls += 1
                    else:
                        dev.append(f'{case}.{key}.{m}: {k}')
    return dev, numbers, nulls


def within(op, band, d):
    return d <= band if op == '<=' else d < band


def judge(value, official, band):
    """(passes, the exact |difference|)."""
    d = abs(Fraction(value) - Fraction(official))
    return within(band[0], Fraction(band[1]), d), d


def sig3(d):
    """A magnitude to three significant digits, rounded half to even from the exact rational: d.dde±XX — under a
    decimal context of its own, made whole: precision 3, half to even, the widest exponent bounds, clamp 0, no trap
    and no flag taken from anywhere, so that its caller's context — its traps, flags, bounds, clamp and rounding, or
    the module's default — neither changes nor stops the display and is left as it was: the tool's only decimal
    arithmetic."""
    if d == 0:
        return '0.00e+00'
    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_HALF_EVEN, Emin=decimal.MIN_EMIN, Emax=decimal.MAX_EMAX,
                          capitals=1, clamp=0, flags=[], traps=[])
    q = ctx.divide(decimal.Decimal(d.numerator), decimal.Decimal(d.denominator))
    digits = ''.join(map(str, q.as_tuple().digits)).ljust(3, '0')[:3]
    return f'{digits[0]}.{digits[1:]}e{q.adjusted():+03d}'


# ---- the commands -----------------------------------------------------------------------------------------------------

def need_fd_ops():
    if not FD_OPS:
        raise Stop('this platform cannot bind the writes to the folder the run makes: os.open and its kin take no dir_fd')


def own(dir_fd, name, ident):
    """Whether name in the folder dir_fd is still the file or folder this run made, by its device and inode: True;
    False — another's in its place —; None — not found there."""
    try:
        st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    return (st.st_dev, st.st_ino) == ident


class Made:
    """A file or folder the run makes, entered before it is made: the folder it is made in, by its descriptor, and its
    name there; how a stop shows it; its kind; once made, the descriptor the run holds on it and its device and inode."""

    def __init__(self, dir_fd, name, shown, kind):
        self.dir_fd, self.name, self.shown, self.kind, self.fd, self.ident = dir_fd, name, shown, kind, None, None


def identity(fd):
    st = os.fstat(fd)
    return st.st_dev, st.st_ino


def at_path(path, ident, what):
    """After the last write: what is at the path, as given and resolved now — its last component not a link — is the
    file or folder the run made and wrote into, by its device and inode."""
    try:
        st = os.stat(path.rstrip(os.sep) or path, follow_symlinks=False)
        same = (st.st_dev, st.st_ino) == ident
    except FileNotFoundError:
        same = False
    if not same:
        raise OSError(f'the {what} at its path is no longer the {what} the run made and wrote into')


def undo(made):
    """Remove what this run made, newest first, each only while it is still the run's own — known by its device and
    inode, its descriptor held so that no other file can take them —; a thing made and held whose identity was not yet
    read is read now; a thing whose making was under way, not yet held — its making cut short, or failing before its
    effect or after it —, is looked for and, found, named, never removed. A removal that fails is read again at its
    path: found gone, it is named as removed, its failure beside it; still there, or its path not read, as not removed.
    Says what is left, and what was removed though its removal failed."""
    left, done = [], []
    for m in reversed(made):
        if m.fd is not None and m.ident is None:
            try:
                m.ident = identity(m.fd)
            except OSError as e:
                left.append(f'{m.shown} — made by the run, its identity not read '
                            f'({reason(e)}): not removed')
                continue
        if m.fd is None:
            try:
                os.stat(m.name, dir_fd=m.dir_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError as e:
                left.append(f'{m.shown} — its making under way, not looked for: {reason(e)}')
                continue
            left.append(f'{m.shown} — not opened as the {m.kind} the run made: not removed')
            continue
        try:
            mine = own(m.dir_fd, m.name, m.ident)
            if mine:
                try:
                    (os.rmdir if m.kind == 'folder' else os.unlink)(m.name, dir_fd=m.dir_fd)
                except OSError as e:
                    try:
                        gone = own(m.dir_fd, m.name, m.ident) is None
                    except OSError:
                        gone = False
                    if not gone:
                        raise e
                    done.append(f'{m.shown} — removed, its removal failing after its effect: '
                                f'{reason(e)}')
            elif mine is None:
                left.append(f'{m.shown} — not found where the run made it')
            else:
                left.append(f"{m.shown} — another's in its place, not removed; the run's own not found there")
        except OSError as e:
            left.append(f'{m.shown} — not removed: {reason(e)}')
    said = 'nothing it wrote is left' if not left else 'left: ' + '; '.join(left)
    return said if not done else said + ' — ' + '; '.join(done)


class Taken(BaseException):
    """A SIGINT the run took in, found at a look: the run stops there as its interrupt."""


HOLD = {'depth': 0, 'old': None, 'taken': 0, 'thread': None}


def take(signum, frame):
    """The run's own SIGINT handler while it holds: the signal taken in, nothing raised."""
    HOLD['taken'] += 1


def holding(fn, *args):
    """fn(*args) with SIGINT held: in the main thread, the handler in place read, then the run's own installed, and the
    displaced one restored however fn ends — a SIGINT taken in meanwhile then sent to it again, Python's default
    raising KeyboardInterrupt there; inside a hold already, fn runs under it, one restore; outside the main thread, or
    where the handler in place was not set from Python, fn runs unheld."""
    if threading.current_thread() is not threading.main_thread():
        return fn(*args)
    if HOLD['depth']:
        HOLD['depth'] += 1
        try:
            return fn(*args)
        finally:
            HOLD['depth'] -= 1
    old = signal.getsignal(signal.SIGINT)
    if old is None:
        return fn(*args)
    HOLD['taken'] = 0
    try:
        HOLD.update(depth=1, old=old, thread=threading.get_ident())
        signal.signal(signal.SIGINT, take)
        return fn(*args)
    finally:
        HOLD['depth'] = 0
        signal.signal(signal.SIGINT, old)
        taken = HOLD['taken']
        HOLD.update(old=None, taken=0, thread=None)
        if taken:
            signal.raise_signal(signal.SIGINT)


def found():
    """Whether a SIGINT was taken in while the run holds, the handler it displaced Python's default, in its thread."""
    return HOLD['depth'] > 0 and HOLD['taken'] > 0 and HOLD['old'] is signal.default_int_handler and \
        HOLD['thread'] == threading.get_ident()


def look():
    """Where the run's state is whole: a SIGINT taken in and found stops the run here, as its interrupt."""
    if found():
        raise Taken()


def std(name):
    """The standard stream sys holds as name — 'stdout' or 'stderr' —, read once where the tool acts on it: one deleted
    from sys is taken as None, as one set to None is."""
    return getattr(sys, name, None)


def rendered(e, named=True):
    """A taken exception as a stop names it — its class and its message, or its message alone where named is false
    (a stop's own words) —, rendered inside the guard that took it: a message that raises when it is rendered,
    whatever Exception it raises, named by the exception's class alone, and a class whose own name cannot be read by
    these words alone. Raises no Exception."""
    try:
        return f'{type(e).__name__}: {e}' if named else str(e)
    except Exception:
        pass
    try:
        return f'{type(e).__name__}, its message not rendered'
    except Exception:
        return 'an exception whose class and message could not be rendered'


def reason(e):
    """A taken OSError's reason as a stop names it — its strerror where it holds one —, rendered inside the guard that
    took it: a reason that raises when it is rendered, or whose truth cannot be read, whatever Exception it raises,
    gives way to the exception's message (rendered), and a message so to the exception's class alone; an exception
    with no reason named by its message. Raises no Exception."""
    try:
        s = e.strerror
        if s:
            return str(s)
    except Exception:
        pass
    return rendered(e, False)


def shut(stream):
    """The stream object closed, the failure of its last flush caught: the interpreter flushes no closed stream at
    exit. A stream object whose close fails and leaves it open, or whose state cannot be read, is taken from that flush
    instead: the sys attribute that holds it — stdout or stderr — set to None, which CPython's flush at exit passes
    over (flush_std_files in Python/pylifecycle.c, read at 3.10.12, 3.12.10, 3.13.18 and 3.14.6: a standard stream
    that is None or closed is not flushed), so that a stop's exit 2 is not turned into 120 there. A stream neither
    attribute holds — or none at all — is left as it is."""
    try:
        stream.close()
    except Exception:
        pass
    try:
        if stream.closed:
            return
    except Exception:
        pass
    for name in ('stdout', 'stderr'):
        if getattr(sys, name, None) is stream:
            setattr(sys, name, None)


def quiet(stream):
    """The stream left with nothing for the interpreter's own flush at exit to fail on — the Python documentation's
    note on SIGPIPE: its descriptor pointed at the null device, so that what its buffer still holds goes nowhere. Where
    the null device's descriptor takes the stream's own number — the stream's descriptor already closed —, it is the
    stream's descriptor now and stays open, the stream object's own flush tried there too. Where the null device cannot
    be opened — whatever Exception its opening raises — or pointed to, or the stream has no
    descriptor of its own, the stream object is closed instead — or, its close failing and leaving it open, taken from
    sys (shut). The null device's descriptor is then closed:
    quiet leaves no descriptor of its own open unless that close fails. quiet raises nothing: a close that fails —
    whatever Exception it raises, before the descriptor is released or after — is caught and returned, its text for
    the stop to name; None when
    nothing failed. Whatever the stream object's own fileno raises, or returns that is no int, leaves it with no
    descriptor of its own, and an int the null device cannot be pointed at closes it instead; a stream object whose own
    flush still fails once its descriptor points at the null device — pointed there, or the null device's own at the
    stream's number — is taken from the interpreter's flush at exit the
    same way (shut), so that a stop's exit 2 is not turned into 120 there."""
    try:
        fd = stream.fileno()
        if type(fd) is not int:
            fd = None
    except Exception:
        fd = None
    try:
        null = None if fd is None else os.open(os.devnull, os.O_WRONLY)
    except Exception:
        null = None
    if null is None:
        shut(stream)
        return
    if null == fd:
        try:
            stream.flush()
        except Exception:
            shut(stream)
        return
    failed = None
    try:
        os.dup2(null, fd)
    except Exception:
        shut(stream)
    else:
        try:
            stream.flush()
        except Exception:
            shut(stream)
    finally:
        try:
            os.close(null)
        except Exception as e:
            failed = f"the null device's descriptor could not be closed ({rendered(e)})"
    return failed


def carry(stream, text):
    """text written to a stream object as a stream, every character it takes counted by what each write returns — a
    write that takes fewer characters than it was given carried on from where it stopped; one that takes none is a
    failure, and so is one that returns no count of what it was given: not an int, below zero or above what it was
    given. The one home of that rule for every writer to a stream: the commands' own lines where stdout has no
    descriptor of its own (say), and a stop's line to stderr (tell). Raises OSError for a count it cannot carry on
    from, and whatever the stream's own write raises."""
    rest = text
    while rest:
        n = stream.write(rest)
        if type(n) is not int or not 0 <= n <= len(rest):
            raise OSError(f'a write to the stream returned no count of what it was given: {n!r}')
        if not n:
            raise OSError(f'a write to the stream took no character, {len(rest)} characters left')
        rest = rest[n:]


def tell(line):
    """A stop's line to stderr, written as a stream and flushed, every character stderr takes counted (carry): a write
    that takes fewer characters than it was given carried on from where it stopped; one that takes none, or returns no
    count of what it was given, a failure. stderr is read once (std) — deleted from sys, it is None —, and the stream
    so read is the one written and, failing, quieted. A stderr that cannot take it — absent, not open, a write that
    fails, takes none or returns no count, any Exception its own calls raise — is named, not held: the stop is left
    unsaid, or said as far as it went, and the stream with nothing for the interpreter's own flush at exit to fail on
    (quiet): the exit status alone then says the run stopped. quiet raising nothing, nothing leaves tell's recovery — a
    failure of quiet's own close goes unsaid with the stop."""
    stream = std('stderr')
    try:
        carry(stream, line + '\n')
        stream.flush()
    except Exception:
        quiet(stream)


def stateful(out, text, data):
    """Whether stdout's encoding marks its start or carries a state from one write to the next — a byte-order mark, a
    shift between character sets, a character held back for the one after it —, so that text encoded afresh, data, is
    not what the stream's own encoder writes after what it wrote: probed by the encoding's incremental encoder under
    the stream's errors, given each first piece of PRIOR — nothing, a letter, and one of each of the scripts and the
    characters the standard library's encodings shift for or hold back — and then text, against data; a first piece
    the stream's errors cannot encode passed over: no stream of that policy wrote it. Where it does, the lines go
    through the stream object itself, its own encoder continuing what it wrote — and where its binary layer is not a
    native buffered writer, whose flush writes every byte it holds or raises, that account cannot be held: an OSError
    naming it, before any line is written. An encoding whose state none of PRIOR reaches is taken as stateless.
    Raises whatever the stream's own encoding, errors and buffer raise."""
    make = codecs.getincrementalencoder(out.encoding)
    for first in PRIOR:
        enc = make(out.errors)
        try:
            enc.encode(first)
        except UnicodeError:
            continue
        if enc.encode(text, True) != data:
            break
    else:
        return False
    layer = out.buffer
    if type(layer) not in (io.BufferedWriter, io.BufferedRandom):
        raise OSError(f'its encoding {out.encoding} marks its start or carries a state, and its binary layer — '
                      f'{type(layer).__name__} — cannot hold the account of every byte its encoder writes')
    return True


def say(lines):
    """A command's own lines to stdout, inside the run's account. Where stdout has a descriptor of its own: what its
    buffer holds flushed first, then the lines composed, encoded by the stream's own encoding and errors, and written
    through the descriptor by os.write, every byte counted — a write that writes fewer bytes than it was given carried
    on from where it stopped; one that writes no byte, would block or fails is a failure; each line ends in '\\n' alone,
    as a POSIX stream writes it — where the stream's encoding marks its start or carries a state from one write to
    the next (stateful), the lines written through the stream object itself instead, its own encoder continuing
    what it wrote, every character counted (carry) and the stream flushed, or, where its binary layer cannot hold
    that account, a failure before any line. Where it has none: the lines written line by line and flushed as a
    stream, every
    character counted by what each write returns — a write that takes fewer characters than it was given carried on
    from where it stopped; one that takes none is a failure, and so is one that returns no count of what it was given:
    not an int, below zero or above what it was given. A stream that cannot take them — not open, a pipe whose reader
    has gone, a full pipe that does not block, a full disk — is left with nothing for the interpreter's own flush at
    exit to fail on (quiet), and the run stops: a Stop naming the failure and, where quiet's own close failed, that
    failure beside it. The stream branch's count is carry's, the rule's one home, a stop's line's with it. stdout is
    read once (std) — deleted from sys, it is None —, and the stream so read is the one written and, failing,
    quieted; any Exception its own calls raise — its write, flush, fileno, encoding, errors or buffer — is a failure
    of it, the
    run's stop, its class and message rendered inside the guard that took it (rendered)."""
    out = std('stdout')
    try:
        if out is None:
            raise OSError('stdout is not open')
        try:
            fd = out.fileno()
        except (OSError, ValueError, AttributeError):
            fd = None
        if fd is None:
            for line in lines:
                carry(out, line + '\n')
            out.flush()
        else:
            out.flush()
            text = ''.join(line + '\n' for line in lines)
            data = text.encode(out.encoding, out.errors)
            if stateful(out, text, data):
                carry(out, text)
                out.flush()
            else:
                view = memoryview(data)
                while view:
                    n = os.write(fd, view)
                    if not n:
                        raise OSError(f'a write to its descriptor wrote no byte, {len(view)} B left')
                    view = view[n:]
    except Exception as e:
        why = rendered(e)
        closed = quiet(out)
        raise Stop(f'its own lines could not be written to stdout ({why})' +
                   ('' if closed is None else f' — {closed}')) from None


def own_lines(path, left, lines):
    """table's and a1's own lines, once their outputs are written whole and checked, inside their hold (holding): said
    (say), then a look once they are. A stream that cannot take them, or a SIGINT taken in and found at that look, stops
    the run there: the stop said once, naming the outputs as left — written whole and checked, no longer held, nothing
    removed —, a signal taken meanwhile named with the failure. Returns 0 otherwise."""
    held = ('written whole and checked at its path, its descriptors closed — no longer held, nothing removed; left: ' +
            '; '.join(left))
    try:
        say(lines)
    except Stop as e:
        what = (f'{rendered(e, False)} after writing {path} — {held}' +
                (' — interrupted before the stop was said' if found() else ''))
    else:
        if not found():
            return 0
        what = f'interrupted after writing {path} and saying its own lines — {held}'
    tell(f'STOP: {what}')
    raise Stop(what, said=True)


def stop_says(path, made, e, said, failed, irq):
    """What the stop says, or None — body returned and nothing failed or was found; or a stop came before anything was
    made, nothing failed and nothing found: raised as it is. irq: a SIGINT taken in, the run stopping for it."""
    closes = '' if not failed else ('its descriptors not all closed (' +
                                    '; '.join(rendered(x) for x in failed) + ')')
    if e is not None:
        if said is None and not failed and not irq:
            return None
        if said is None:
            why = rendered(e, False)
        elif isinstance(e, Exception):
            why = f'writing {path} failed ({rendered(e)}) — {said}'
        else:
            why = f'interrupted while writing {path} — {said}'
        return why + ('' if not failed else ' — ' + closes) + \
            (' — interrupted before the stop was said' if irq and isinstance(e, Exception) else '')
    if not failed and not irq:
        return None
    held = ('written whole and checked at its path, ' + ('but ' + closes if failed else 'its descriptors closed') +
            ' — no longer held, nothing removed; left: ' + '; '.join(m.shown for m in made))
    return f'interrupted after writing {path} — {held}' if irq else f'{path}: {held}'


def finish(path, made, pfd, e):
    """guarded's steps once body has run — e its error or its interrupt, None when it returned: what was made removed,
    after an error or an interrupt (undo) — an Exception undo itself raises named in the stop, what the run made named
    beside it as not all looked at —; every descriptor the run holds closed whatever undo raised, newest first, its
    parent's last, a loop over them as listed, each close in its own try — a close that fails, whatever Exception it
    raises, named in the stop and the loop going on —; a look once the closing is done; what the
    stop says composed (stop_says) and said once. Returns when body returned and nothing failed or was found; raises
    otherwise — a Stop once the stop is said, an interrupt the process raised in itself as it stands."""
    try:
        said = None if e is None or (isinstance(e, Stop) and not made) else undo(made)
    except Exception as x:
        said = (f'its undoing failed ({rendered(x)}) — not all looked at, left as far as it knows: ' +
                '; '.join(m.shown for m in made))
    failed = []
    for fd in [m.fd for m in reversed(made) if m.fd is not None] + ([] if pfd is None else [pfd]):
        try:
            os.close(fd)
        except Exception as x:
            failed.append(x)
    why = stop_says(path, made, e, said, failed, isinstance(e, Taken) or found())
    if why is not None:
        tell(f'STOP: {why}')
    if e is not None and not isinstance(e, (Exception, Taken)):
        raise e
    if why is not None:
        raise Stop(why, said=True) from None
    if e is not None:
        raise e


def guarded(path, parent, cannot, made, body):
    """Under the hold (holding): the descriptor of the parent taken, then body(it) — it makes and writes, each thing
    entered in made before it is made, looking where the run's state is whole, the checks at the paths its last
    acts —; then finish. An error, or a SIGINT found at a look, removes what was made, while it is still the run's
    own, and stops naming what is left; every descriptor taken is closed — a close that fails is named in the stop,
    and after the checks leaves what was written whole and checked at its path: no longer held, it is named, not
    removed."""
    def region():
        pfd = None
        try:
            try:
                pfd = os.open(parent or os.curdir, os.O_RDONLY | os.O_DIRECTORY)
            except OSError as e:
                raise Stop(f'{path}: {cannot} — {rendered(e, False)}') from None
            body(pfd)
        except BaseException as e:
            finish(path, made, pfd, e)
        else:
            finish(path, made, pfd, None)
    holding(region)


def put(fd, data):
    """data written whole through the descriptor of a file the run made, every byte counted: a write that writes fewer
    bytes than it was given carried on from where it stopped; one that writes no byte is a failure — an error the
    writer stops for, as say's is: what was made removed, the stop said once, a SIGINT taken meanwhile named there
    under Python's default handler and passed on as the hold ends."""
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        if not n:
            raise OSError(f'a write to the file wrote no byte, {len(view)} B left')
        view = view[n:]


def write_new(folder, files):
    """files: {name: bytes}, composed in full: the folder made new in its existing parent and opened at once, never
    through a link, checked empty; each file created exclusively inside it, by its descriptor, never through a link;
    after the last write the folder at its path, then each file at its path, checked to be the folder and the files the
    run made — the rest as guarded says."""
    need_fd_ops()
    parent, name = os.path.split(os.path.normpath(folder))
    made = []

    def body(pfd):
        look()
        top = Made(pfd, name, folder, 'folder')
        made.append(top)
        try:
            os.mkdir(name, dir_fd=pfd)
        except FileExistsError:
            made.clear()
            raise Stop(f'{folder}: exists — the tool writes a new folder only') from None
        except OSError as e:
            raise OSError(f'the new folder cannot be made — {reason(e)}') from None
        try:
            top.fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
        except OSError as e:
            raise OSError(f'the new folder cannot be opened as the folder made — a link or another in its place '
                          f'({reason(e)})') from None
        top.ident = identity(top.fd)
        look()
        if os.listdir(top.fd):
            raise OSError('the new folder is not empty — not the folder the run made')
        for fname, data in files.items():
            m = Made(top.fd, fname, os.path.join(folder, fname), 'file')
            made.append(m)
            try:
                m.fd = os.open(fname, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666, dir_fd=top.fd)
            except FileExistsError:
                made.pop()
                raise
            m.ident = identity(m.fd)
            look()
            put(m.fd, data)
            look()
        at_path(folder, top.ident, 'folder')
        for m in made[1:]:
            at_path(m.shown, m.ident, 'file')
        look()
    guarded(folder, parent, 'its parent cannot be opened', made, body)


def write_new_file(path, data):
    """A new file, created exclusively, never through a link; after the last write the file at its path checked to be
    that file — the rest as guarded says."""
    need_fd_ops()
    parent, name = os.path.split(path)
    made = []

    def body(pfd):
        look()
        m = Made(pfd, name, path, 'file')
        made.append(m)
        try:
            m.fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666, dir_fd=pfd)
        except FileExistsError:
            made.clear()
            raise Stop(f'{path}: exists — the tool writes a new file only') from None
        except OSError as e:
            raise OSError(f'the new file cannot be made — {reason(e)}') from None
        m.ident = identity(m.fd)
        look()
        put(m.fd, data)
        look()
        at_path(path, m.ident, 'file')
        look()
    guarded(path, parent, 'its folder cannot be opened', made, body)


def form_line(dev, numbers, nulls, expected):
    conforming = not dev and numbers + nulls == expected
    return conforming, ('conforming' if conforming else f'{len(dev)} deviation(s)') + \
        f' · numbers {numbers} of {expected}' + (f' · null, not computed: {nulls}' if nulls else '')


def cmd_form(path, isolated):
    data, notes, why, sha = load_hashed(path)
    dev, numbers, nulls = form(data, notes, why, isolated)
    expected = 307 if isolated else 535
    what = 'its A2 and A3 objects (the brief, item 3)' if isolated else 'the brief\'s form (item 1)'
    conforming, _ = form_line(dev, numbers, nulls, expected)
    say([f'{path} · sha256 {sha} · against {what}',
         f'numbers where the form expects one: {numbers} of {expected}'
         + (f' · null — a result not computed, as the brief permits: {nulls}' if nulls else '')]
        + [f'deviation: {d}' for d in dev]
        + ['FORM: conforming' if conforming else f'FORM: {len(dev)} deviation(s)'])
    return 0 if conforming else 1


def a1_object(oracle):
    a1 = {'zero_rates_cc': {}, 'llfr': None, 'basic_rfr': {}}
    for (case, key, m), (_, _, v) in oracle.items():
        if case != 'A1':
            continue
        if m is None:
            a1[key] = v
        else:
            a1[key][str(m)] = v
    return a1


def cmd_a1(workbooks, manifest, out, pins=None, manifest_sha=None):
    if os.path.lexists(out):
        raise Stop(f'{out}: exists — the tool writes a new file only')
    oracle, held = read_oracle(workbooks, manifest, pins, manifest_sha)
    text = json.dumps(a1_object(oracle), indent=2, allow_nan=False) + '\n'

    def write_and_say():
        write_new_file(out, text.encode('utf-8'))
        return own_lines(out, [out],
                         [f"held: {wb} '{sheet}'!{rng} · {role} · {n} cells · {h[:16]} — the manifest's"
                          for wb, sheet, rng, role, n, h in held] +
                         [f'{out} · the A1 object: zero_rates_cc 50, llfr 1, basic_rfr 150 · {len(text.encode())} B · '
                          f'sha256 {sha256_bytes(text.encode())}'])
    return holding(write_and_say)


def rows_for(build, kind, data, why, oracle):
    rows = []
    for (case, key, m), (cell, band, official) in oracle.items():
        if kind == 'isolated' and case not in ('A2', 'A3'):
            continue
        v, fail = value_at(data, why, case, key, m)
        if fail is None:
            ok, d = judge(v, official, band)
            rows.append([build, kind, case, key, '-' if m is None else str(m), cell, f'{band[0]} {band[1]}', repr(v),
                         sig3(d), 'PASS' if ok else 'FAIL', '' if ok else 'outside its band'])
        else:
            rows.append([build, kind, case, key, '-' if m is None else str(m), cell, f'{band[0]} {band[1]}', '-', '-',
                         'FAIL', fail])
    return rows


def tsv(head, columns, rows):
    lines = [f'# {h}' for h in head] + ['\t'.join(columns)] + ['\t'.join(r) for r in rows]
    return ('\n'.join(lines) + '\n').encode('utf-8')


def cmd_table(workbooks, manifest, out, builds, isolated, pins=None, manifest_sha=None):
    names = [n for n, _ in builds]
    bad = [n for n in names + [n for n, _ in isolated] if not NAME.fullmatch(n)]
    if bad:
        raise Stop(f"a build's name is letters, digits, '.', '_' and '-', a letter or a digit first, 64 at most: {bad!r}")
    if len(set(names)) != len(names) or any(n not in names for n, _ in isolated) or \
            len({n for n, _ in isolated}) != len(isolated):
        raise Stop('each build named once, each isolated file a named build\'s, once')
    if os.path.lexists(out):
        raise Stop(f'{out}: exists — the tool writes a new folder only')
    oracle, held = read_oracle(workbooks, manifest, pins, manifest_sha)
    inputs = [(n, 'returned', p) for n, p in builds] + [(n, 'isolated', p) for n, p in isolated]
    inputs.sort(key=lambda t: (names.index(t[0]), t[1] != 'returned'))
    shown = ['compare.py', 'table', '<workbooks>', '<manifest>', '<out>'] + \
        [a for n, _ in builds for a in ('--build', n, f'<{n} returned>')] + \
        [a for n, _ in isolated for a in ('--isolated', n, f'<{n} isolated>')]
    head = ['replicability test 01 - the pass-or-fail table (the preregistration, sections 5 and 6)',
            f'tool: compare.py sha256 {TOOL_SHA256}',
            'command: ' + ' '.join(shown) + ' — every file and folder shown by its role, the files named by their '
            'sha256 below',
            'workbooks: ' + ' · '.join(f'{k} {(pins or PINS)[k]}' for k in ('E1', 'E2', 'E3')) + ' — each equal to its pin',
            f'manifest: sha256 {manifest_sha or MANIFEST_SHA256} — the frozen manifest; ranges held to its digests: '
            f'{len(held)} ({sum(1 for h in held if h[3] == "output")} outputs, '
            f'{sum(1 for h in held if h[3] == "input")} maturities)']
    rows, forms = [], []
    for name, kind, path in inputs:
        data, notes, why, h = load_hashed(path)
        dev, numbers, nulls = form(data, notes, why, kind == 'isolated')
        expected = 307 if kind == 'isolated' else 535
        head.append(f'{name} {kind}: sha256 {h} · form: ' + form_line(dev, numbers, nulls, expected)[1])
        forms.append((name, kind, dev))
        rows += rows_for(name, kind, data, why, oracle)
    head.append(SOURCE)
    cols = ['build', 'kind', 'case', 'key', 'maturity', 'cell', 'band', 'value', 'difference', 'result', 'why']
    files = {'table.tsv': tsv(head + [
        'one row per declared output; difference: |value - official|, exact, shown to three significant digits, '
        'rounded half to even'], cols, rows)}
    cases = []
    for name, kind, _ in inputs:
        for case in CASES:
            sel = [r for r in rows if r[0] == name and r[1] == kind and r[2] == case]
            if sel:
                failed = sum(1 for r in sel if r[9] == 'FAIL')
                cases.append([name, kind, case, str(len(sel)), str(len(sel) - failed), str(failed),
                              'PASS' if not failed else 'FAIL'])
    files['cases.tsv'] = tsv(head + [
        'a case passes for a build when every one of its declared outputs passes (section 5)'],
        ['build', 'kind', 'case', 'outputs', 'passed', 'failed', 'result'], cases)
    div = [[f'{r[0]}/{r[1]}/{r[2]}.{r[3]}' + ('' if r[4] == '-' else f'[{r[4]}]')] + r[:9] + [r[10]]
           for r in rows if r[9] == 'FAIL']
    files['divergences.tsv'] = tsv(head + [
        'every failing output of table.tsv, none chosen (section 6); each attributed on stated grounds, or left unresolved'],
        ['id', 'build', 'kind', 'case', 'key', 'maturity', 'cell', 'band', 'value', 'difference', 'why'], div)

    def write_and_say():
        write_new(out, files)
        return own_lines(out, [out] + [os.path.join(out, fn) for fn in files],
                         [f'{name} {kind} · form deviation: {d}' for name, kind, dev in forms for d in dev] +
                         [f'{c[0]} · {c[1]} · {c[2]} · {c[3]} outputs · {c[4]} pass · {c[5]} fail · {c[6]}'
                          for c in cases] +
                         [f'{os.path.join(out, fn)} · {data.count(10)} L · {len(data)} B · sha256 {sha256_bytes(data)}'
                          for fn, data in files.items()])
    return holding(write_and_say)


def cmd_same(p, q):
    a, b = load_hashed(p), load_hashed(q)
    differ = []
    for case in CASES:
        for key, n in FORM[case]:
            for m in ([None] if n is None else range(1, n + 1)):
                va, fa = value_at(a[0], a[2], case, key, m)
                vb, fb = value_at(b[0], b[2], case, key, m)
                equal = fa is None and fb is None and Fraction(va) == Fraction(vb)
                if not equal:
                    differ.append(f'{case}.{key}' + ('' if m is None else f'[{m}]') +
                                  f': {repr(va) if fa is None else fa} · {repr(vb) if fb is None else fb}')
    say([f'{p} · sha256 {a[3]}', f'{q} · sha256 {b[3]}', f'the files\' bytes equal: {a[3] == b[3]}',
         f'declared outputs: 535 · equal {535 - len(differ)} · differing {len(differ)}'] +
        [f'differs: {d}' for d in differ])
    return 0 if not differ else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = std('stdout')
    sys.stdout = None
    try:
        ap = argparse.ArgumentParser(prog='compare.py', description=__doc__.split('\n\n')[0])
        sub = ap.add_subparsers(dest='cmd', required=True)
        f = sub.add_parser('form')
        f.add_argument('file')
        f.add_argument('--isolated', action='store_true')
        a = sub.add_parser('a1')
        a.add_argument('workbooks')
        a.add_argument('manifest')
        a.add_argument('out')
        t = sub.add_parser('table')
        t.add_argument('workbooks')
        t.add_argument('manifest')
        t.add_argument('out')
        t.add_argument('--build', nargs=2, action='append', required=True, metavar=('NAME', 'FILE'))
        t.add_argument('--isolated', nargs=2, action='append', default=[], metavar=('NAME', 'FILE'))
        s = sub.add_parser('same')
        s.add_argument('first')
        s.add_argument('second')
    finally:
        sys.stdout = out
    args = ap.parse_args(argv)
    try:
        if args.cmd == 'form':
            return cmd_form(args.file, args.isolated)
        if args.cmd == 'a1':
            return cmd_a1(args.workbooks, args.manifest, args.out)
        if args.cmd == 'table':
            return cmd_table(args.workbooks, args.manifest, args.out, [tuple(b) for b in args.build],
                             [tuple(i) for i in args.isolated])
        return cmd_same(args.first, args.second)
    except (Stop, OSError, zipfile.BadZipFile, ET.ParseError, KeyError) as e:
        if not getattr(e, 'said', False):
            tell(f'STOP: {rendered(e, False)}')
        return 2
    except Exception as e:
        tell(f'STOP: an error the tool did not foresee — {rendered(e)}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
