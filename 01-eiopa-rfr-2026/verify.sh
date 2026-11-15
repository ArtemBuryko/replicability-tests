#!/bin/sh
# verify.sh — checks this folder (the preregistration, section 12). Standard library only.
#
#   sh 01-eiopa-rfr-2026/verify.sh [--offline] [<a folder for the publisher's four files>]
#
# It needs Python 3.9 or later and openssl (OpenSSL 3 or LibreSSL 3.3); git, where the folder is a checkout.
# Five steps, each saying what it checked; a step that fails or is not run is named, and the exit status is 0
# only when every step holds:
#   (a) the publisher's four files, each held to its sha256 in source/README.md — taken from the folder given,
#       or fetched: the publisher's address first, then the snapshot; a file fetched is kept in the folder given;
#   (b) the manifest's digests (manifest/MANIFEST.md), each made again from the workbooks' own XML;
#   (c) the chain and the tokens — each commit's list, its files, its commit's tree, its timestamp token —
#       and MANIFEST.sha256;
#   (d) the pass-or-fail table, made again by comparison/compare.py, held to its sha256, byte for byte;
#   (e) the outcome by section 8, from table/cases.tsv and dispositions/statuses.tsv.
# It does not run the builders again, and it cannot judge an attribution's grounds: the reader does.
# It writes nothing in this folder; a file it fetches goes to the folder given, or stays in memory.
set -u
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || { echo "verify.sh: cannot find its own folder" >&2; exit 2; }
PY=
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then PY=$c; break; fi
done
[ -n "$PY" ] || { echo "verify.sh: Python 3.9 or later is needed, as python3 — not found; nothing checked" >&2; exit 2; }
command -v openssl >/dev/null 2>&1 || { echo "verify.sh: openssl is needed — not found; nothing checked" >&2; exit 2; }
exec "$PY" -I -B - "$DIR" "$@" <<'VERIFY_PY'
import datetime, gzip, hashlib, io, os, posixpath, re, shutil, subprocess, sys, tempfile, zipfile
import urllib.request
import xml.etree.ElementTree as ET

FOLDER = os.path.realpath(sys.argv[1])
ROOT, NAME = os.path.dirname(FOLDER), os.path.basename(FOLDER)
ARGS = sys.argv[2:]
OFFLINE = '--offline' in ARGS
REST = [a for a in ARGS if a != '--offline']
if len(REST) > 1 or any(a.startswith('-') for a in REST):
    print("usage: sh verify.sh [--offline] [<a folder for the publisher's four files>]")
    sys.exit(2)
FILES = os.path.abspath(REST[0]) if REST else None
IDS = ('T', 'E1', 'E2', 'E3')
LISTS = ('i', 'ii', 'iii', 'iv', 'v')
TABLES = ('table.tsv', 'cases.tsv', 'divergences.tsv')
LETTERS = ('T', 'O', 'C', 'B', 'P', 'U')
STATE = {}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rd(*parts):
    with open(os.path.join(FOLDER, *parts), 'rb') as f:
        return f.read()


def step(k, title):
    print('\n== (%s) %s' % (k, title))
    STATE[k] = 'ok'


def bad(k, msg):
    print('   FAIL: ' + msg)
    STATE[k] = 'FAILED'


def say(msg):
    print('   ' + msg)


def last_line(out):
    lines = [l for l in out.decode('utf-8', 'replace').split('\n') if l.strip()]
    return lines[-1][:240] if lines else '(no output)'


# ---- (a) the four files ----------------------------------------------------------------------------------------------

def step_a():
    step('a', "the publisher's four files, each held to its sha256 in source/README.md")
    pins, snaps = {}, {}
    for line in rd('source', 'README.md').decode('utf-8').split('\n'):
        m = re.match(r'^\| (T|E[123]) \| `([^`]+)` \| `(https://[^`]+)` \| [^|]* \| ([0-9,]+) \| `([0-9a-f]{64})` \|$', line)
        if m:
            pins[m.group(1)] = {'url': m.group(3), 'bytes': int(m.group(4).replace(',', '')), 'sha': m.group(5)}
        m = re.match(r'^\| (T|E[123]) \| `(https://web\.archive\.org/[^`]+)` \| [^|]* \|$', line)
        if m:
            snaps[m.group(1)] = m.group(2)
    if sorted(pins) != sorted(IDS) or sorted(snaps) != sorted(IDS):
        bad('a', 'source/README.md does not give the four files, each with its address, its snapshot and its sha256')
        return None
    have = {}
    if FILES is not None and os.path.isdir(FILES):
        for n in sorted(os.listdir(FILES)):
            p = os.path.join(FILES, n)
            if not os.path.isfile(p):
                continue
            for i in IDS:
                if i not in have and os.path.getsize(p) == pins[i]['bytes']:
                    with open(p, 'rb') as f:
                        b = f.read()
                    if sha(b) == pins[i]['sha']:
                        have[i] = b
                        say('%s: sha256 equal — found in the folder given, as %s' % (i, n))
    for i in IDS:
        if i in have:
            continue
        if OFFLINE:
            bad('a', '%s: not in the folder given, and --offline: not fetched' % i)
            continue
        why = []
        for label, url in (("the publisher's address", pins[i]['url']), ('the snapshot', snaps[i])):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (verify.sh; replicability test 01)'})
                with urllib.request.urlopen(req, timeout=180) as r:
                    b = r.read()
                if sha(b) != pins[i]['sha'] and b[:2] == b'\x1f\x8b':
                    try:
                        b = gzip.decompress(b)
                    except Exception:
                        pass
                if sha(b) == pins[i]['sha']:
                    have[i] = b
                    kept = ''
                    if FILES is not None:
                        os.makedirs(FILES, exist_ok=True)
                        p = os.path.join(FILES, i + ('.pdf' if i == 'T' else '.xlsm'))
                        if not os.path.exists(p):
                            with open(p, 'wb') as f:
                                f.write(b)
                            kept = ', kept as ' + p
                    say('%s: sha256 equal — fetched from %s%s' % (i, label, kept))
                    break
                why.append('%s answered %d bytes, sha256 %s — not the file' % (label, len(b), sha(b)))
            except Exception as e:
                why.append('%s did not answer (%s: %s)' % (label, type(e).__name__, e))
        if i not in have:
            bad('a', '%s: %s' % (i, '; '.join(why)))
            say('   by hand: save the file from %s' % pins[i]['url'])
            say('   or from %s' % snaps[i])
            say('   into a folder, and give that folder to this script')
    if any(i not in have for i in IDS):
        return None
    return have


# ---- (b) the manifest's digests, from the workbooks' own XML ----------------------------------------------------------

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
WINDOWS = datetime.datetime(1899, 12, 30)
DATE_IDS = {14: 'mm-dd-yy', 15: 'd-mmm-yy', 16: 'd-mmm', 17: 'mmm-yy', 18: 'h:mm AM/PM', 19: 'h:mm:ss AM/PM',
            20: 'h:mm', 21: 'h:mm:ss', 22: 'm/d/yy h:mm', 45: 'mm:ss', 46: '[h]:mm:ss', 47: 'mmss.0'}
STRIP = re.compile(r'".*?"|\[(?!hh?\]|mm?\]|ss?\])[^\]]*\]')
DELTA = re.compile(r'\[hh?\](:mm(:ss(\.0*)?)?)?|\[mm?\](:ss(\.0*)?)?|\[ss?\](\.0*)?', re.I)
MROW = re.compile(r"^(\S+) · (\w+) · (E[123]) · '((?:[^']|'')+)'!(\*|[A-Z]+[0-9]+(?::[A-Z]+[0-9]+)?) · (\w+) · ([0-9]+) · "
                  r"([0-9a-f]{64}) · (.*)$")


def is_date(fmt):
    if fmt is None:
        return False
    return re.search(r'(?<![_\\])[dmhysDMHYS]', STRIP.sub('', fmt.split(';')[0])) is not None


def is_delta(fmt):
    return fmt is not None and DELTA.search(fmt.split(';')[0]) is not None


def from_serial(value, epoch, delta):
    """A date cell's serial number as a date, a time or a duration — the conversion the manifest's reader makes."""
    if delta:
        td = datetime.timedelta(days=value)
        if td.microseconds:
            td = datetime.timedelta(seconds=td.total_seconds() // 1, microseconds=round(td.microseconds, -3))
        return td
    day, fraction = divmod(value, 1)
    diff = datetime.timedelta(milliseconds=round(fraction * 86400 * 1000))
    if 0 <= value < 1 and diff.days == 0:
        mins, seconds = divmod(diff.seconds, 60)
        hours, mins = divmod(mins, 60)
        return datetime.time(hours, mins, seconds, diff.microseconds)
    if 0 < value < 60 and epoch == WINDOWS:
        day += 1
    return epoch + datetime.timedelta(days=day) + diff


def split_ref(ref):
    m = re.fullmatch(r'([A-Z]{1,3})([0-9]+)', ref or '')
    if not m:
        raise ValueError('a cell reference this reader does not read: %r' % (ref,))
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)), col


def bounds(rng):
    a, _, b = rng.partition(':')
    (r0, c0), (r1, c1) = split_ref(a), split_ref(b or a)
    return min(r0, r1), min(c0, c1), max(r0, r1), max(c0, c1)


def text_of(el):
    """The text of an <si> or an <is>: its own <t>, then its runs' <t>; phonetic runs left out."""
    out = []
    t = el.find(NS + 't')
    if t is not None and t.text is not None:
        out.append(t.text)
    for r in el.findall(NS + 'r'):
        rt = r.find(NS + 't')
        if rt is not None and rt.text is not None:
            out.append(rt.text)
    return ''.join(out)


def render(v):
    """The manifest's canonical rendering of a cached value."""
    if isinstance(v, bool):
        return 'TRUE' if v else 'FALSE'
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, int):
        return str(v)
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    return str(v).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')


class Book:
    """A workbook's cached values, read from its own XML as the manifest's reader yields them."""

    def __init__(self, data):
        self.z = zipfile.ZipFile(io.BytesIO(data))
        wb = ET.fromstring(self.z.read('xl/workbook.xml'))
        rels = ET.fromstring(self.z.read('xl/_rels/workbook.xml.rels'))
        target = {r.get('Id'): r.get('Target') for r in rels.iter(REL)}
        self.paths = {}
        for s in wb.iter(NS + 'sheet'):
            t = target[s.get(RID)]
            self.paths[s.get('name')] = t[1:] if t.startswith('/') else posixpath.normpath(posixpath.join('xl', t))
        pr = wb.find(NS + 'workbookPr')
        mac = pr is not None and pr.get('date1904') in ('1', 'true')
        self.epoch = datetime.datetime(1904, 1, 1) if mac else WINDOWS
        try:
            sst = ET.fromstring(self.z.read('xl/sharedStrings.xml'))
            self.sst = [text_of(si).replace('x005F_', '') for si in sst.findall(NS + 'si')]
        except KeyError:
            self.sst = []
        self.dates, self.deltas = set(), set()
        try:
            st = ET.fromstring(self.z.read('xl/styles.xml'))
        except KeyError:
            st = None
        if st is not None:
            custom = {}
            nf = st.find(NS + 'numFmts')
            if nf is not None:
                for n in nf.findall(NS + 'numFmt'):
                    custom[int(n.get('numFmtId'))] = n.get('formatCode')
            xfs = st.find(NS + 'cellXfs')
            if xfs is not None:
                for idx, xf in enumerate(xfs.findall(NS + 'xf')):
                    i = int(xf.get('numFmtId') or 0)
                    fmt = custom[i] if i in custom else DATE_IDS.get(i)
                    if is_date(fmt):
                        self.dates.add(idx)
                    if is_delta(fmt):
                        self.deltas.add(idx)
        self.sheets = {}

    def sheet(self, name):
        if name not in self.sheets:
            x = ET.fromstring(self.z.read(self.paths[name]))
            cells, arrays, merged = {}, [], set()
            for c in x.iter(NS + 'c'):
                f, v = c.find(NS + 'f'), c.find(NS + 'v')
                ftype = None if f is None else (f.get('t') or 'normal')
                if ftype == 'array' and f.get('ref'):
                    arrays.append(bounds(f.get('ref')))
                vtext = None if v is None else (v.text or None)
                cells[split_ref(c.get('r'))] = (c.get('r'), c.get('t', 'n'), int(c.get('s') or 0), ftype, vtext,
                                                c.find(NS + 'is'))
            for m in x.iter(NS + 'mergeCell'):
                r0, c0, r1, c1 = bounds(m.get('ref'))
                merged.update((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if (r, c) != (r0, c0))
            self.sheets[name] = (cells, arrays, merged)
        return self.sheets[name]

    def cached(self, t, s, vtext, inline):
        if t == 'inlineStr':
            return text_of(inline) if inline is not None else None
        if vtext is None:
            return None
        if t == 'n':
            v = float(vtext) if ('.' in vtext or 'E' in vtext or 'e' in vtext) else int(vtext)
            if s in self.dates:
                try:
                    return from_serial(v, self.epoch, s in self.deltas)
                except (OverflowError, ValueError):
                    return '#VALUE!'
            return v
        if t == 's':
            return self.sst[int(vtext)]
        if t == 'b':
            return bool(int(vtext))
        if t in ('str', 'e'):
            return vtext
        raise ValueError('a cell type this reader does not read: %r' % (t,))

    def cells(self, name, rng, selection):
        """[(cell, cached value)] row by row: the cells that are not empty in the workbook's formula view — a merged
        range's cells other than its first are empty there; with 'const', those that carry no formula and lie in no
        array formula; with 'formula', the others."""
        if selection not in ('all', 'const', 'formula'):
            raise ValueError('a selection this reader does not read: %r' % (selection,))
        cells, arrays, merged = self.sheet(name)
        if rng == '*':
            keys = sorted(cells)
        else:
            r0, c0, r1, c1 = bounds(rng)
            keys = sorted(k for k in cells if r0 <= k[0] <= r1 and c0 <= k[1] <= c1)
        out = []
        for (r, c) in keys:
            if (r, c) in merged:
                continue
            ref, t, s, ftype, vtext, inline = cells[(r, c)]
            value = self.cached(t, s, vtext, inline)
            if ftype is not None:
                derived = ftype != 'dataTable'
            elif value is None:
                continue
            else:
                derived = isinstance(value, str) and value.startswith('=')
            derived = derived or any(a <= r <= b and x <= c <= y for a, x, b, y in arrays)
            if (selection == 'const' and derived) or (selection == 'formula' and not derived):
                continue
            out.append((ref, value))
        return out


def step_b(files):
    step('b', "the manifest's digests, each made again from the workbooks' own XML")
    if files is None:
        STATE['b'] = 'NOT RUN'
        say('not run — the four files are not at hand')
        return
    rows = [m.groups() for m in (MROW.match(l) for l in rd('manifest', 'MANIFEST.md').decode('utf-8').split('\n')) if m]
    if not rows:
        bad('b', 'manifest/MANIFEST.md carries no row this script reads')
        return
    books, equal = {}, 0
    for case, role, wb, sheet, rng, sel, n, digest, _ in rows:
        sheet = sheet.replace("''", "'")
        try:
            if wb not in books:
                books[wb] = Book(files[wb])
            cells = books[wb].cells(sheet, rng, sel)
            got = sha(''.join('%s!%s\t%s\n' % (sheet, ref, render(v)) for ref, v in cells).encode('utf-8'))
            why = None
            if len(cells) != int(n) or got != digest:
                why = '%d cells, sha256 %s — the manifest has %s cells, %s' % (len(cells), got, n, digest)
        except Exception as e:
            why = 'not read (%s: %s)' % (type(e).__name__, e)
        if why is None:
            equal += 1
        else:
            bad('b', "%s '%s'!%s · %s (%s, %s): %s" % (wb, sheet, rng, sel, case, role, why))
    say('%d rows of %d made again equal to the manifest — by their cells and by their sha256' % (equal, len(rows)))
    if equal != len(rows):
        say('a row named above is not made again here; manifest/manifest.py makes every row, with a library beyond the '
            'standard one: python3 -I manifest/manifest.py <a folder holding E1.xlsm, E2.xlsm and E3.xlsm>')


# ---- (c) the chain and the tokens ------------------------------------------------------------------------------------

LROW = re.compile(r'^(100644|100755)  ([0-9a-f]{64})  (.+)$')


def git(*args, data=None):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', LC_ALL='C')
    p = subprocess.run(['git', '-C', ROOT] + list(args), input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
    return p.returncode, p.stdout


def checkout():
    if shutil.which('git') is None:
        return False, 'git is not installed'
    code, out = git('rev-parse', '--show-toplevel')
    if code != 0:
        return False, 'the folder is not a git checkout'
    if os.path.realpath(out.decode('utf-8', 'replace').strip()) != ROOT:
        return False, "the checkout's top folder is not the folder above this one"
    code, out = git('rev-parse', 'HEAD')
    return True, 'a git checkout at commit ' + out.decode().strip()


def tree_problems(commit, rows, rl, rt, lb, tb):
    """The list against the tree of the commit that added it: every file of that tree once, at git's mode and sha256."""
    code, out = git('ls-tree', '-r', '-z', commit)
    if code != 0:
        return ["git could not read the commit's tree"]
    entries = {}
    for rec in out.split(b'\0'):
        if rec:
            meta, path = rec.split(b'\t', 1)
            mode, _, oid = meta.decode().split()
            entries[path.decode('utf-8', 'surrogateescape')] = (mode, oid)
    probs = []
    names = set(entries) - {rl, rt}
    if names != set(rows):
        probs.append("the list and its commit's tree do not name the same files — in the list alone: %s; in the tree alone: %s"
                     % (sorted(set(rows) - names)[:3] or 'none', sorted(names - set(rows))[:3] or 'none'))
    want = sorted(names & set(rows)) + [p for p in (rl, rt) if p in entries]
    code, out = git('cat-file', '--batch', data=''.join(entries[p][1] + '\n' for p in want).encode())
    if code != 0:
        return probs + ["git could not read the commit's files"]
    pos, wrong = 0, []
    for p in want:
        end = out.index(b'\n', pos)
        size = int(out[pos:end].split()[2])
        blob = out[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
        if p == rl:
            same = blob == lb
        elif p == rt:
            same = tb is not None and blob == tb
        else:
            same = entries[p][0] == rows[p][0] and sha(blob) == rows[p][1]
        if not same:
            wrong.append(p)
    if rl not in entries or rt not in entries:
        probs.append('its commit does not carry the list and the token')
    if wrong:
        probs.append("%d files differ from the commit's tree by mode or sha256: %s" % (len(wrong), wrong[:3]))
    return probs


def token_check(n, pl, pt, lb, rootcert, tmp):
    """The token: its imprint the list's sha256; openssl ts -verify with the token's own certificates as -untrusted,
    the folder's root the only trust anchor. Returns the token's time and what did not hold."""
    if not os.path.isfile(pt):
        return None, ['the token is not here']
    with open(pt, 'rb') as f:
        tb = f.read()
    probs = []
    if hashlib.sha256(lb).digest() not in tb:
        probs.append("the token does not carry the list's sha256 as its imprint")
    tok, certs = os.path.join(tmp, n + '.token'), os.path.join(tmp, n + '.pem')
    both = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p1 = subprocess.run(['openssl', 'ts', '-reply', '-in', pt, '-token_out', '-out', tok], **both)
    p2 = subprocess.run(['openssl', 'pkcs7', '-inform', 'DER', '-in', tok, '-print_certs', '-out', certs], **both)
    if p1.returncode != 0 or p2.returncode != 0 or not os.path.isfile(certs):
        return None, probs + ['openssl could not read the token and its certificates']
    p3 = subprocess.run(['openssl', 'ts', '-verify', '-in', pt, '-data', pl, '-CAfile', rootcert, '-untrusted', certs],
                        **both)
    if p3.returncode != 0 or b'Verification: OK' not in p3.stdout:
        probs.append('openssl ts -verify does not hold: ' + last_line(p3.stdout))
    p4 = subprocess.run(['openssl', 'ts', '-reply', '-in', pt, '-text'], **both)
    m = re.search(r'Time stamp: (.+)', p4.stdout.decode('utf-8', 'replace'))
    return (m.group(1).strip() if m else None), probs


def step_c():
    step('c', "the chain and the tokens — each commit's list, its files, its commit's tree, its token; MANIFEST.sha256")
    isgit, what = checkout()
    say(what + ('' if isgit else " — the lists are not held against their commits' trees, and the modes are not checked"))
    rootcert = os.path.join(FOLDER, 'timestamps', 'chain', 'DigiCert_Trusted_Root_G4.pem')
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    say("each token checked at this machine's clock, %s; its own time is shown beside it" % now)
    tmp = tempfile.mkdtemp(prefix='verify-')
    try:
        prev = None
        for n in LISTS:
            rl, rt = '%s/timestamps/%s.list' % (NAME, n), '%s/timestamps/%s.tsr' % (NAME, n)
            pl, pt = os.path.join(ROOT, *rl.split('/')), os.path.join(ROOT, *rt.split('/'))
            if not os.path.isfile(pl):
                bad('c', '(%s) the list is not here: %s — its files, its tree and its token not checked' % (n, rl))
                prev = n
                continue
            with open(pl, 'rb') as f:
                lb = f.read()
            lines = lb.decode('utf-8', 'replace').split('\n')
            probs = [] if lines[-1] == '' else ['the list does not end with a newline']
            lines = lines[:-1] if lines[-1] == '' else lines
            if not lines or lines[0] != '# leaves out: %s %s' % (rl, rt):
                probs.append('its first line is not the one section 10 defines')
            rows, order = {}, []
            for l in lines[1:]:
                m = LROW.match(l)
                if not m:
                    probs.append('a line not in the form «mode  sha256  path»')
                    continue
                if m.group(3) in rows:
                    probs.append('a path twice: ' + m.group(3))
                rows[m.group(3)] = (m.group(1), m.group(2))
                order.append(m.group(3))
            if order != sorted(order, key=lambda p: p.encode('utf-8')):
                probs.append('its paths are not sorted bytewise')
            if rl in rows or rt in rows:
                probs.append('it names its own list or token')
            if prev is not None:
                for q in ('%s/timestamps/%s.list' % (NAME, prev), '%s/timestamps/%s.tsr' % (NAME, prev)):
                    if q not in rows:
                        probs.append("the chain's link is missing: it does not carry %s" % q)
            off = []
            for path, (_, h) in rows.items():
                try:
                    with open(os.path.join(ROOT, *path.split('/')), 'rb') as f:
                        same = sha(f.read()) == h
                except OSError:
                    same = False
                if not same:
                    off.append(path)
            if off:
                probs.append('%d files are not at their sha256: %s' % (len(off), off[:3]))
            tree = 'not checked'
            if isgit:
                code, out = git('log', '--diff-filter=A', '--format=%H', '--', rl)
                ids = out.decode().split()
                if code != 0 or not ids:
                    probs.append("git's history has no commit that adds the list")
                    tree = 'no commit'
                else:
                    tb = None
                    if os.path.isfile(pt):
                        with open(pt, 'rb') as f:
                            tb = f.read()
                    gp = tree_problems(ids[-1], rows, rl, rt, lb, tb)
                    probs += gp
                    tree = 'commit %s — %s' % (ids[-1][:12], 'NOT equal' if gp else 'every file once, at its mode and sha256')
            when, tp = token_check(n, pl, pt, lb, rootcert, tmp)
            probs += tp
            for p in probs:
                bad('c', '(%s) %s' % (n, p))
            say("(%s) %d rows · files at their sha256: %d · its commit's tree: %s · token: %s%s"
                % (n, len(rows), len(rows) - len(off), tree, 'does NOT hold' if tp else 'Verification: OK',
                   ' · its time: %s' % when if when else ''))
            prev = n
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    mp = os.path.join(FOLDER, 'MANIFEST.sha256')
    if not os.path.isfile(mp):
        bad('c', 'MANIFEST.sha256 is not here — the folder not held to it')
        return
    skip = {'MANIFEST.sha256', 'timestamps/v.list', 'timestamps/v.tsr'}
    rows, off, form = {}, [], 0
    for l in rd('MANIFEST.sha256').decode('utf-8', 'replace').split('\n'):
        m = re.match(r'^([0-9a-f]{64})  (.+)$', l)
        if m:
            rows[m.group(2)] = m.group(1)
        elif l:
            form += 1
    for path, h in rows.items():
        try:
            same = sha(rd(*path.split('/'))) == h
        except OSError:
            same = False
        if not same:
            off.append(path)
    if form or off or skip & set(rows):
        bad('c', 'MANIFEST.sha256: %d lines not in the form «sha256  path», %d files not at their sha256 %s, '
                 'its own three left-out paths named: %s' % (form, len(off), off[:3], sorted(skip & set(rows)) or 'no'))
    if isgit:
        code, out = git('ls-files', '-z', '--', NAME)
        here = {p.decode('utf-8', 'surrogateescape')[len(NAME) + 1:] for p in out.split(b'\0') if p} - skip
        unnamed, kind = sorted(here - set(rows)), 'tracked files'
        if unnamed:
            bad('c', 'MANIFEST.sha256 does not name %d of the folder\'s tracked files: %s' % (len(unnamed), unnamed[:3]))
    else:
        here = set()
        for base, _, names in os.walk(FOLDER):
            for nm in names:
                here.add(os.path.relpath(os.path.join(base, nm), FOLDER).replace(os.sep, '/'))
        unnamed, kind = sorted(here - skip - set(rows)), 'files'
        if unnamed:
            say('files here that MANIFEST.sha256 does not name, not checked: %d %s' % (len(unnamed), unnamed[:3]))
    say('MANIFEST.sha256: %d lines · files at their sha256: %d · the folder\'s %s it does not name: %d'
        % (len(rows), len(rows) - len(off), kind, len(unnamed)))


# ---- (d) the table ---------------------------------------------------------------------------------------------------

def step_d(files):
    step('d', 'the pass-or-fail table, made again by the checked comparison tool, byte for byte')
    if files is None:
        STATE['d'] = 'NOT RUN'
        say('not run — the four files are not at hand')
        return
    h = sha(rd('comparison', 'compare.py'))
    command = None
    for n in TABLES:
        b = rd('table', n)
        m = re.search(rb'^# tool: compare\.py sha256 ([0-9a-f]{64})$', b, re.M)
        if m is None or m.group(1).decode() != h:
            bad('d', "table/%s names another tool's sha256 than comparison/compare.py's %s" % (n, h))
        m = re.search(rb'^# command: (.*)$', b, re.M)
        command = m.group(1).decode('utf-8') if m else command
    if h not in rd('comparison', 'SECOND-PARTY-CHECK.md').decode('utf-8'):
        bad('d', 'comparison/SECOND-PARTY-CHECK.md does not name comparison/compare.py by its sha256 %s' % h)
    if STATE['d'] != 'ok' or command is None:
        if command is None:
            bad('d', "the table's head carries no command line")
        say('the tool not run')
        return
    say("comparison/compare.py sha256 %s — the one the table's three heads and comparison/SECOND-PARTY-CHECK.md name" % h)
    tmp = tempfile.mkdtemp(prefix='verify-')
    try:
        wb, out = os.path.join(tmp, 'wb'), os.path.join(tmp, 'table')
        os.mkdir(wb)
        for i in ('E1', 'E2', 'E3'):
            with open(os.path.join(wb, i + '.xlsm'), 'wb') as f:
                f.write(files[i])
        cmd = [sys.executable, '-I', '-B', os.path.join('comparison', 'compare.py'), 'table', wb,
               os.path.join('manifest', 'MANIFEST.md'), out]
        for b in re.findall(r'--build (\S+)', command):
            cmd += ['--build', b, os.path.join('builds', b, 'work', 'return', 'outputs.json')]
        for b in re.findall(r'--isolated (\S+)', command):
            cmd += ['--isolated', b, os.path.join('isolated', b + '.json')]
        p = subprocess.run(cmd, cwd=FOLDER, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1800)
        if p.returncode != 0:
            bad('d', 'the tool ended with exit status %d: %s' % (p.returncode, last_line(p.stdout)))
            return
        for n in TABLES:
            try:
                with open(os.path.join(out, n), 'rb') as f:
                    made = f.read()
            except OSError:
                made = None
            if made == rd('table', n):
                say('table/%s: made again, the same bytes — sha256 %s' % (n, sha(made)))
            else:
                bad('d', 'table/%s: the file made again differs from the one here' % n)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- (e) the outcome -------------------------------------------------------------------------------------------------

def tsv(b):
    lines = b.decode('utf-8').split('\n')
    head = [l for l in lines if l.startswith('#')]
    body = [l for l in lines if l and not l.startswith('#')]
    cols = body[0].split('\t')
    return head, [dict(zip(cols, l.split('\t'))) for l in body[1:]]


def step_e():
    step('e', 'the outcome — section 8, from table/cases.tsv and dispositions/statuses.tsv')
    try:
        sb = rd('dispositions', 'statuses.tsv')
    except OSError:
        bad('e', 'dispositions/statuses.tsv is not here — no outcome computed')
        return None
    _, cases = tsv(rd('table', 'cases.tsv'))
    _, divs = tsv(rd('table', 'divergences.tsv'))
    shead, sts = tsv(sb)
    probs = []
    for label, parts in (('divergences', ('table', 'divergences.tsv')), ('log', ('divergences.md',))):
        found = [re.search(r'sha256 ([0-9a-f]{64})', l) for l in shead if l.startswith('# %s: ' % label)]
        if len(found) != 1 or found[0] is None or found[0].group(1) != sha(rd(*parts)):
            probs.append("the statuses' head does not name %s by its sha256" % '/'.join(parts))
    builds, void = [], None
    for c in cases:
        if c['build'] not in builds:
            builds.append(c['build'])
    for l in shead:
        if l.startswith('# void builds:'):
            v = l.split(':', 1)[1].strip()
            void = [] if v == 'none' else [x for x in re.split(r'[,\s]+', v) if x]
    if void is None:
        probs.append("the statuses' head has no «void builds» line")
    for b in void or []:
        if b not in builds:
            probs.append('a void build the table does not have: ' + b)
    ids, sid = [d['id'] for d in divs], [s.get('id') for s in sts]
    for i in ids:
        if sid.count(i) != 1:
            probs.append("the table's divergence %s has %d rows among the statuses, not one" % (i, sid.count(i)))
    for s in sts:
        if s.get('id') not in ids:
            probs.append('a status without a divergence of the table: %s' % s.get('id'))
        if s.get('status') not in LETTERS:
            probs.append('%s: a status outside the six letters: %r' % (s.get('id'), s.get('status')))
        elif s['status'] == 'T' and (s.get('passage') or '').strip() in ('', '-'):
            probs.append('%s: a T without its passage' % s.get('id'))
    for c in cases:
        n = sum(1 for d in divs if (d['build'], d['kind'], d['case']) == (c['build'], c['kind'], c['case']))
        if c['result'] not in ('PASS', 'FAIL') or int(c['failed']) != n or (c['result'] == 'FAIL') != (n > 0):
            probs.append("table/cases.tsv's row %s %s %s does not agree with table/divergences.tsv's rows"
                         % (c['build'], c['kind'], c['case']))
    if probs:
        for p in probs:
            bad('e', p)
        say('no outcome computed')
        return None
    status = {s['id']: s for s in sts}
    names, lines, every = [], [], True
    for c in cases:
        if c['kind'] == 'returned' and c['case'] not in names:
            names.append(c['case'])
    for case in names:
        tested = [b for b in builds if b not in void and
                  any((c['build'], c['kind'], c['case']) == (b, 'returned', case) for c in cases)]
        rep = False
        if not tested:
            cat = 'not tested — every build void'
        else:
            dv = [d for d in divs if d['kind'] == 'returned' and d['case'] == case and d['build'] in tested]
            letters = [status[d['id']]['status'] for d in dv]
            if not dv:
                cat, rep = 'reproduced', True
            elif 'T' in letters:
                ps = []
                for d in dv:
                    s = status[d['id']]
                    if s['status'] == 'T' and s['passage'].strip() not in ps:
                        ps.append(s['passage'].strip())
                cat = 'not reproduced — the text: ' + '; '.join(ps)
                rest = sorted(set(letters) - {'T'})
                if rest:
                    cat += ' (other divergences: %s)' % ', '.join(rest)
            elif 'U' in letters:
                cat = 'undecided'
            else:
                cat = 'not reproduced — other causes: ' + ', '.join(sorted(set(letters)))
            if void:
                cat += ' — by %s alone; %s void, not tested' % (', '.join(tested), ', '.join(void))
        every = every and rep
        lines.append('%s: %s' % (case, cat))
    for l in lines:
        say(l)
    outcome = 'all reproduced' if every else 'not reproduced'
    say('outcome: ' + outcome)
    return outcome


# ---- the run ---------------------------------------------------------------------------------------------------------

def guarded(k, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        bad(k, 'the step stopped (%s: %s)' % (type(e).__name__, e))
        return None


def main():
    v = subprocess.run(['openssl', 'version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print('verify.sh — replicability test 01 · the folder %s' % FOLDER)
    print('Python %s · %s' % (sys.version.split()[0], v.stdout.decode('utf-8', 'replace').strip()))
    files = guarded('a', step_a)
    guarded('b', step_b, files)
    guarded('c', step_c)
    guarded('d', step_d, files)
    outcome = guarded('e', step_e)
    print('\n== result')
    for k, what in (('a', 'the four files'), ('b', "the manifest's digests"), ('c', 'the chain and the tokens'),
                    ('d', 'the table'), ('e', 'the outcome')):
        extra = ' — ' + outcome if k == 'e' and outcome else ''
        say('(%s) %s: %s%s' % (k, what, STATE.get(k, 'NOT RUN'), extra))
    held = all(STATE.get(k) == 'ok' for k in 'abcde')
    say('every step holds' if held else 'NOT every step holds — see the lines marked FAIL or NOT RUN above')
    sys.exit(0 if held else 1)


main()
VERIFY_PY
