#!/usr/bin/env python3
"""The input bundle held to a closed list and re-hashed against the frozen manifest, before any mount.

    python3 -I bundle_check.py <bundle folder> <manifest/MANIFEST.md>

The folder is read by descriptors from its own: each directory opened relative to its parent's descriptor and listed
through it, each file opened relative to its directory's descriptor without blocking, by its name alone, no link
followed and no path resolved a second time; on each open descriptor its type and its identity - device and inode -
are checked against the listing's. A symbolic link of any kind, an entry that is neither a regular file nor a
directory, a directory that cannot be listed, and an entry changed between its listing and its read are each a problem
of its own; any other error of the read stops the run. The check certifies the entries as it read them, not the folder
after its run. The closed list: the 27 input files at their full paths, each by the digest, the cell count and
the sheet of its «input» row in MANIFEST.md (workbook, sheet, range); E1/labels.tsv and README.md by sha256 fixed in
this tool; SHA256SUMS - the bundle's own list of every other file, by sha256 fixed in this tool. Any other file, a
missing one, or one at another path fails the check; the bundle's own SHA256SUMS is never trusted for any other file.
Eleven controls, each built from the bundle as read and run through the same check, SHA256SUMS refreshed where it
applies: an input with one character changed, its row's cell count changed - its digest kept -, its sheet renamed in every line - its row's digest made the file's -, a manifest row withheld, a manifest row outside the closed list, a
file added, an input moved, the labels changed, the README removed, SHA256SUMS removed, SHA256SUMS alone changed (both
its problems) - each must fail. Ten more on disk, the bundle as read written into a scratch folder, one entry planted
or swapped in each copy, each copy read by the same reader and checked by the same check: a file behind a directory
symlink, README.md a symlink to an equal file, a directory that cannot be opened, a directory whose listing is refused,
a named pipe, a file added - a problem of the check, not of the reader -, and - through a listing
that swaps the entry once it is listed - a directory swapped for a link to it, a file swapped for a link to it, a file
swapped for a named pipe and a file swapped for an equal copy of itself - each must fail with its own problem. One more on the reader's comparison: a stat result with the device and inode of an
entry and another type - refused as changed. Three on the reader's refusals, each on a copy on disk: the root's
listing refused, a file whose open is refused, and an open failing with an error other than the four that mean a
changed entry - each must stop the read with its own error. Five on the command line: this tool run on copies on disk
with BUNDLE_CHECK_VERDICT_ONLY=1 - its verdict on the copy alone, its controls not run, which it prints - its exit
status, its verdict line and every line it prints held to their expected text: the bundle as read - exit 0, PASS -; a
file added; the manifest with an input row twice; README.md removed, SHA256SUMS refreshed; SHA256SUMS removed - each
exit 1, FAIL. Exit 0 only if the bundle passes and every control comes out as expected.
"""
import errno, hashlib, os, re, shutil, stat, subprocess, sys, tempfile

ROW = re.compile(r"^(\S+) · input · (E\d) · '([^']+)'!(\S+) · const · (\d+) · ([0-9a-f]{64}) · [^·]*$")
INPUTS = {  # path in the bundle: (workbook, sheet, range) of an «input» row of MANIFEST.md
    'E1/cssr-calculation.G24-G173.tsv': ('E1', 'CSSR Calculation', 'G24:G173'),
    'E1/cssr-calculation.L10-L11.tsv': ('E1', 'CSSR Calculation', 'L10:L11'),
    'E1/cssr-calculation.L13-L14.tsv': ('E1', 'CSSR Calculation', 'L13:L14'),
    'E1/input-data-and-extrapolation.G25-G174.tsv': ('E1', 'Input Data & Extrapolation', 'G25:G174'),
    'E1/input-data-and-extrapolation.H10-H12.tsv': ('E1', 'Input Data & Extrapolation', 'H10:H12'),
    'E1/input-data-and-extrapolation.H14-H16.tsv': ('E1', 'Input Data & Extrapolation', 'H14:H16'),
    'E1/input-data-and-extrapolation.H25-H174.tsv': ('E1', 'Input Data & Extrapolation', 'H25:H174'),
    'E1/input-data-and-extrapolation.I25-I174.tsv': ('E1', 'Input Data & Extrapolation', 'I25:I174'),
    'E1/input-data-and-extrapolation.J25-J174.tsv': ('E1', 'Input Data & Extrapolation', 'J25:J174'),
    'E1/input-data-and-extrapolation.L10.tsv': ('E1', 'Input Data & Extrapolation', 'L10'),
    'E1/input-data-and-extrapolation.L11-L12.tsv': ('E1', 'Input Data & Extrapolation', 'L11:L12'),
    'E1/va-term-structures.G23-G172.tsv': ('E1', 'VA Term Structures', 'G23:G172'),
    'E1/va-term-structures.H10-H12.tsv': ('E1', 'VA Term Structures', 'H10:H12'),
}
for wb in ('E2', 'E3'):
    for sheet in ('Corp Data', 'Corporate Bond Ref. Portfolio', 'Gov Rates', 'Government Bond Ref. Portfolios',
                  'LTAS', 'Reference Portfolio Weights', 'RFR'):
        name = re.sub(r'[^a-z0-9]+', '-', sheet.lower()).strip('-')
        INPUTS[f'{wb}/{name}.tsv'] = (wb, sheet, '*')
FIXED = {'E1/labels.tsv': 'df51d995538538d681be41bca83a786f6759e97e8d50fe53e44a6cd9918386d3',
         'README.md': '0ae652449b63b476cb7e996199ea11b28f4cf3326e849edccd1494cfe3fd3244'}
SUMS, SUMS_SHA = 'SHA256SUMS', '000971ac7a229150b820f1f4d1d4b21bc62dbf104ef6882845fce30bbff7e582'
CHANGE = 'changed between its listing and its read'
CHANGED = {errno.ELOOP, errno.ENOTDIR, errno.ENOENT, errno.ENXIO}   # what an open by name refuses when the entry is no longer what was listed
CLOEXEC = getattr(os, 'O_CLOEXEC', 0)
VERDICT_ONLY = 'BUNDLE_CHECK_VERDICT_ONLY'   # set to 1: the verdict on the bundle alone, the controls not run
NOT_RUN = f'controls: not run - {VERDICT_ONLY}=1: the verdict on this bundle alone, for the command-line controls of a run that runs them'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def manifest_rows(path):
    rows = []
    for ln in open(path, encoding='utf-8'):
        m = ROW.match(ln.rstrip('\n'))
        if m:
            rows.append(dict(case=m[1], wb=m[2], sheet=m[3], rng=m[4], n=int(m[5]), sha=m[6]))
    return rows


def sums_of(files):
    return ''.join(f'{sha(b)}  {p}\n' for p, b in sorted(files.items()) if p != SUMS).encode('utf-8')


def check(files, rows):
    """The bundle (path: bytes) against the closed list and the manifest's input rows: (problems, matched)."""
    problems, matched = [], []
    keyed = {(r['wb'], r['sheet'], r['rng']): r for r in rows}
    for path, key in INPUTS.items():
        r, b = keyed.get(key), files.get(path)
        if r is None:
            problems.append(('no manifest row for a listed input', path))
        elif b is None:
            problems.append(('missing', path))
        elif (sha(b) != r['sha'] or b.count(b'\n') != r['n']
              or {ln.split('!', 1)[0] for ln in b.decode('utf-8', 'replace').split('\n') if ln} != {r['sheet']}):
            problems.append(('not the manifest digest, cell count and sheet of its row', path))
        else:
            matched.append((path, r))
    listed = set(INPUTS.values())
    problems += [('a manifest input row outside the closed list', k) for k in keyed if k not in listed]
    for path, h in FIXED.items():
        b = files.get(path)
        if b is None:
            problems.append(('missing', path))
        elif sha(b) != h:
            problems.append(('not its fixed sha256', path))
    s = files.get(SUMS)
    if s is None:
        problems.append(('missing', SUMS))
    else:
        if s != sums_of(files):
            problems.append(('not the list of the bundle\'s other files', SUMS))
        if sha(s) != SUMS_SHA:
            problems.append(('not its fixed sha256', SUMS))
    problems += [('not in the closed list', p) for p in sorted(set(files) - set(INPUTS) - set(FIXED) - {SUMS})]
    return problems, matched


def refreshed(files):
    return {**files, SUMS: sums_of(files)}


def listed(dfd, rel):
    """A directory's entries through its descriptor, by name, sorted, each with its type and identity as listed."""
    return [(n, os.stat(n, dir_fd=dfd, follow_symlinks=False)) for n in sorted(os.listdir(dfd))]


def read_all(fd):
    parts = []
    while True:
        b = os.read(fd, 1 << 20)
        if not b:
            return b''.join(parts)
        parts.append(b)


def same_entry(fs, st):
    """An open descriptor's type and identity - device and inode - against the listing's."""
    return (stat.S_IFMT(fs.st_mode), fs.st_dev, fs.st_ino) == (stat.S_IFMT(st.st_mode), st.st_dev, st.st_ino)


def read_folder(root, listing=listed):
    """Every entry of the folder, read by descriptors from its own: (path: bytes of each regular file, the entries
    refused, each with its problem). Each directory and file is opened by its name relative to its parent's descriptor,
    no link followed, a file without blocking; on each open descriptor its type and identity are checked against the
    listing's. Any error other than a subfolder that cannot be listed or an entry changed since its listing is raised."""
    files, refused = {}, []
    D = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | CLOEXEC
    F = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | CLOEXEC

    def walk(dfd, rel):
        try:
            entries = listing(dfd, rel)
        except PermissionError:
            if not rel:
                raise
            refused.append(('a directory that cannot be listed', rel))
            return
        for name, st in entries:
            p = f'{rel}/{name}' if rel else name
            if stat.S_ISLNK(st.st_mode):
                refused.append(('a symbolic link', p))
            elif stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode):
                isdir = stat.S_ISDIR(st.st_mode)
                try:
                    fd = os.open(name, D if isdir else F, dir_fd=dfd)
                except PermissionError:
                    if not isdir:
                        raise
                    refused.append(('a directory that cannot be listed', p))
                    continue
                except OSError as x:
                    if x.errno not in CHANGED:
                        raise
                    refused.append((CHANGE, p))
                    continue
                try:
                    fs = os.fstat(fd)
                    if not same_entry(fs, st):
                        refused.append((CHANGE, p))
                    elif isdir:
                        walk(fd, p)
                    else:
                        files[p] = read_all(fd)
                finally:
                    os.close(fd)
            else:
                refused.append(('neither a regular file nor a directory', p))

    rfd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | CLOEXEC)
    try:
        walk(rfd, '')
    finally:
        os.close(rfd)
    return files, refused


def inspect(folder, rows, listing=listed):
    """The folder read and checked: (problems - the reader's first, then the check's -, matched, files)."""
    files, refused = read_folder(folder, listing)
    problems, matched = check(files, rows)
    return refused + problems, matched, files


def report(label, problems, wants):
    caught = all(w in problems for w in wants)
    print(f"control - {label}: fails {'yes' if problems else 'NO'} · its own problem{'s' if len(wants) > 1 else ''} among them {'yes' if caught else 'NO'} ({len(problems)} problems) (expected yes · yes)")
    return caught


def disk_controls(files, rows):
    """The bundle as read, written into a scratch folder ten times, one entry planted or swapped in each copy; each copy
    read by the same reader and checked by the same check; and an eleventh copy read by the reader alone, its listing or
    an open refused by the control - the read must stop with its error: (label, problems or what the read did, wanted
    problems) for each."""
    base, out, locked = tempfile.mkdtemp(prefix='bundle-check-'), [], []
    planted = b'{"planted": true}\n'
    try:
        def copy(name):
            d = os.path.join(base, name, 'bundle')
            for p, b in files.items():
                q = os.path.join(d, *p.split('/'))
                os.makedirs(os.path.dirname(q), exist_ok=True)
                with open(q, 'wb') as fh:
                    fh.write(b)
            os.makedirs(d, exist_ok=True)
            return d

        def run(label, d, wants, listing=listed):
            out.append((label, inspect(d, rows, listing)[0], wants))

        def swapping(rel0, name, swap):
            """A listing that swaps the entry name of the directory rel0 once it is listed, before its read."""
            def lst(dfd, rel):
                entries = listed(dfd, rel)
                if rel == rel0 and any(n == name for n, _ in entries):
                    swap()
                return entries
            return lst

        d = copy('c1')
        os.makedirs(os.path.join(base, 'c1', 'outside'))
        with open(os.path.join(base, 'c1', 'outside', 'official-output.json'), 'wb') as fh:
            fh.write(planted)
        os.symlink(os.path.join('..', 'outside'), os.path.join(d, 'answers'))
        run('a file behind a directory symlink, answers -> ../outside holding official-output.json, on disk', d,
            [('a symbolic link', 'answers')])
        d = copy('c2')
        with open(os.path.join(base, 'c2', 'README.md'), 'wb') as fh:
            fh.write(files.get('README.md', b''))
        if os.path.lexists(os.path.join(d, 'README.md')):
            os.remove(os.path.join(d, 'README.md'))
        os.symlink(os.path.join('..', 'README.md'), os.path.join(d, 'README.md'))
        run('README.md a symlink to an equal file outside the bundle, on disk', d, [('a symbolic link', 'README.md')])
        d = copy('c3')
        a = os.path.join(d, 'answers')
        os.makedirs(a)
        with open(os.path.join(a, 'official-output.json'), 'wb') as fh:
            fh.write(planted)
        os.chmod(a, 0)
        locked.append(a)
        try:
            os.listdir(a)
            lists = True
        except PermissionError:
            lists = False
        lst = listed
        if lists:  # this process lists a mode-000 directory (root): the control refuses the listing itself
            def lst(dfd, rel):
                if rel == 'answers':
                    raise PermissionError(13, 'the listing refused by the control', rel)
                return listed(dfd, rel)
        run('a directory that cannot be listed, answers/ at mode 000 holding official-output.json, on disk'
            + (' - this process lists it: the listing refused by the control' if lists else ''), d,
            [('a directory that cannot be listed', 'answers')], lst)
        d = copy('c4')
        os.mkfifo(os.path.join(d, 'pipe'))
        run('a named pipe, pipe, on disk', d, [('neither a regular file nor a directory', 'pipe')])
        d5 = copy('c5')

        def swap_dir():
            if os.path.isdir(os.path.join(d5, 'E1')):
                os.rename(os.path.join(d5, 'E1'), os.path.join(base, 'c5', 'E1'))
                os.symlink(os.path.join('..', 'E1'), os.path.join(d5, 'E1'))
        run('a directory swapped for a link to it once it is listed, E1 moved beside the bundle and E1 -> ../E1, on disk',
            d5, [(CHANGE, 'E1')], swapping('', 'E1', swap_dir))
        d9 = copy('c9')
        os.makedirs(os.path.join(d9, 'answers'))
        with open(os.path.join(d9, 'answers', 'official-output.json'), 'wb') as fh:
            fh.write(planted)

        def refusing(dfd, rel):
            if rel == 'answers':
                raise PermissionError(13, 'the listing refused by the control', rel)
            return listed(dfd, rel)
        run('a directory whose listing is refused, answers/ readable, its listing refused by the control, on disk', d9,
            [('a directory that cannot be listed', 'answers')], refusing)
        d8 = copy('c8')

        def swap_link():
            if os.path.isfile(os.path.join(d8, 'README.md')):
                os.rename(os.path.join(d8, 'README.md'), os.path.join(base, 'c8', 'README.md'))
                os.symlink(os.path.join('..', 'README.md'), os.path.join(d8, 'README.md'))
        run('a file swapped for a link to it once it is listed, README.md moved beside the bundle and README.md -> ../README.md, on disk',
            d8, [(CHANGE, 'README.md')], swapping('', 'README.md', swap_link))
        d6 = copy('c6')

        def swap_file():
            if os.path.isfile(os.path.join(d6, 'README.md')):
                os.remove(os.path.join(d6, 'README.md'))
                os.mkfifo(os.path.join(d6, 'README.md'))
        run('a file swapped for a named pipe once it is listed, README.md, on disk', d6, [(CHANGE, 'README.md')],
            swapping('', 'README.md', swap_file))
        d7 = copy('c7')

        def swap_copy():
            q = os.path.join(d7, 'README.md')
            if os.path.isfile(q):
                with open(q + '.new', 'wb') as fh:
                    fh.write(files.get('README.md', b''))
                os.replace(q + '.new', q)
        run('a file swapped for an equal copy of itself once it is listed, README.md, on disk', d7, [(CHANGE, 'README.md')],
            swapping('', 'README.md', swap_copy))
        d10 = copy('c10')
        with open(os.path.join(d10, 'official-output.json'), 'wb') as fh:
            fh.write(planted)
        run('a file added, official-output.json, SHA256SUMS as read - a problem of the check, not of the reader -, on disk',
            d10, [('not in the closed list', 'official-output.json')])
        d11 = copy('c11')

        def refusing_root(dfd, rel):
            if rel == '':
                raise PermissionError(errno.EACCES, 'the listing refused by the control', '.')
            return listed(dfd, rel)
        out.append(('the root whose listing is refused by the control, on disk: the read stops with its error',
                    raised(lambda: read_folder(d11, refusing_root)), [('raised', f'PermissionError errno {errno.EACCES}')]))
        real_open = os.open

        def opening(code):
            def op(path, flags, mode=0o777, *, dir_fd=None):
                if path == 'README.md' and dir_fd is not None:
                    raise OSError(code, os.strerror(code), path)
                return real_open(path, flags, mode, dir_fd=dir_fd)
            return op
        for code, what in ((errno.EACCES, 'a file whose open is refused'),
                           (errno.EIO, 'an open failing with an error other than the four that mean a changed entry')):
            os.open = opening(code)
            try:
                got = raised(lambda: read_folder(d11))
            finally:
                os.open = real_open
            out.append((f'{what}, README.md, errno {code} by the control, on disk: the read stops with its error', got,
                        [('raised', f'{type(OSError(code, "")).__name__} errno {code}')]))
    finally:
        for a in locked:
            os.chmod(a, 0o700)
        shutil.rmtree(base)
    return out


def raised(read):
    """What a read did: the error it stopped with, or what it returned."""
    try:
        got, refused = read()
    except OSError as x:
        return [('raised', f'{type(x).__name__} errno {x.errno}')]
    return [('returned', f'{len(got)} files, {len(refused)} refused')]


def cli_controls(files, rows, man):
    """This tool run on copies on disk with VERDICT_ONLY set to 1 - its verdict on each copy alone, its controls not run:
    its exit status, its verdict line and every line it prints against their expected text, for the bundle as read and
    for four planted copies: (what the control prints, whether it came out as expected) for each."""
    h = lambda b: hashlib.sha256(b).hexdigest()
    p0, m0 = check(files, rows)
    if p0 or len(m0) != len(INPUTS):
        return [('control - the command line: not run - the bundle as read does not pass its own check, which these controls need - NOT AS EXPECTED', False)]
    text = open(man, encoding='utf-8').read().split('\n')
    first = [k for k, ln in enumerate(text) if ROW.match(ln)][0]
    cases = [
        ('the bundle as read', files, None, rows, [], 'yes', 0, 'PASS'),
        ('a file added, official-output.json, SHA256SUMS as read', {**files, 'official-output.json': b'{"planted": true}\n'},
         None, rows, [("not the list of the bundle's other files", SUMS), ('not in the closed list', 'official-output.json')], 'no', 1, 'FAIL'),
        ('the manifest with its first input row twice', files, '\n'.join(text[:first + 1] + text[first:]), rows[:1] + rows, [],
         'yes', 1, 'FAIL'),
        ('README.md removed, SHA256SUMS refreshed', refreshed({p: b for p, b in files.items() if p != 'README.md'}), None, rows,
         [('missing', 'README.md'), ('not its fixed sha256', SUMS)], 'yes', 1, 'FAIL'),
        (f'{SUMS} removed', {p: b for p, b in files.items() if p != SUMS}, None, rows, [('missing', SUMS)], 'no', 1, 'FAIL'),
    ]
    base, out = tempfile.mkdtemp(prefix='bundle-check-cli-'), []
    try:
        for n, (label, fs, mtext, rs, problems, listed_yes, code, verdict) in enumerate(cases):
            d, m = os.path.join(base, f'v{n}', 'bundle'), man
            for p, b in fs.items():
                q = os.path.join(d, *p.split('/'))
                os.makedirs(os.path.dirname(q), exist_ok=True)
                with open(q, 'wb') as fh:
                    fh.write(b)
            if mtext is not None:
                m = os.path.join(base, f'v{n}', 'MANIFEST.md')
                with open(m, 'w', encoding='utf-8') as fh:
                    fh.write(mtext)
            keyed = {(r['wb'], r['sheet'], r['rng']): r for r in rs}
            by_wb = [(w, len([r for r in rs if r['wb'] == w])) for w in sorted({r['wb'] for r in rs})]
            want = [f"manifest input rows: {len(rs)} · by workbook {by_wb} · the closed list: {len(INPUTS)} inputs, {len(FIXED)} fixed files and {SUMS}"]
            for p, k in INPUTS.items():
                r = keyed[k]
                want.append(f"{p} · {r['n']} L · {r['sha'][:16]} = manifest {r['case']} · {r['wb']} · '{r['sheet']}'!{r['rng']}")
            want += [f"{p} · {h(fs[p])[:16] if p in fs else 'missing'} · fixed {x[:16]}" for p, x in FIXED.items()]
            want += [f"{SUMS} · {h(fs[SUMS])[:16] if SUMS in fs else 'missing'} · fixed {SUMS_SHA[:16]} · the list of the other files: {listed_yes}",
                     f"files: {len(fs)} · inputs matched {len(INPUTS)} of {len(INPUTS)} · problems {len(problems)} {problems}",
                     NOT_RUN, f'bundle check: {verdict}']
            res = subprocess.run([sys.executable, '-I', '-B', os.path.abspath(__file__), d, m], capture_output=True, timeout=60,
                                 env={**os.environ, VERDICT_ONLY: '1'})
            got = res.stdout.decode('utf-8', 'replace').split('\n')
            if got and got[-1] == '':
                got.pop()
            first_diff = next((k + 1 for k in range(max(len(got), len(want))) if got[k:k + 1] != want[k:k + 1]), None)
            fine = res.returncode == code and got == want and not res.stderr
            out.append((f"control - the command line, {label}: exit {res.returncode} · {got[-1] if got else 'nothing printed'} · its lines as expected {'yes' if got == want else 'NO, the first differing ' + str(first_diff)} ({len(got)} lines){' · stderr ' + str(len(res.stderr)) + ' B' if res.stderr else ''} (expected exit {code} · bundle check: {verdict} · yes)", fine))
    finally:
        shutil.rmtree(base)
    return out


def main(bundle, man):
    rows = manifest_rows(man)
    print(f"manifest input rows: {len(rows)} · by workbook {[(w, sum(r['wb'] == w for r in rows)) for w in sorted({r['wb'] for r in rows})]} · the closed list: {len(INPUTS)} inputs, {len(FIXED)} fixed files and {SUMS}")
    problems, matched, files = inspect(bundle, rows)
    for path, r in matched:
        print(f"{path} · {r['n']} L · {r['sha'][:16]} = manifest {r['case']} · {r['wb']} · '{r['sheet']}'!{r['rng']}")
    for path, h in FIXED.items():
        print(f"{path} · {sha(files[path])[:16] if path in files else 'missing'} · fixed {h[:16]}")
    print(f"{SUMS} · {sha(files[SUMS])[:16] if SUMS in files else 'missing'} · fixed {SUMS_SHA[:16]} · the list of the other files: {'yes' if files.get(SUMS) == sums_of(files) else 'no'}")
    print(f"files: {len(files)} · inputs matched {len(matched)} of {len(INPUTS)} · problems {len(problems)} {problems}")
    ok = not problems and len(matched) == len(INPUTS) == len(rows)
    n0 = sorted(INPUTS)[0]
    if os.environ.get(VERDICT_ONLY) == '1':
        print(NOT_RUN)
    else:
        b0 = files.get(n0, b'\t')
        i = b0.index(b'\t') + 1
        mv = 'E1/input-data-and-extrapolation.J25-J174.tsv'
        k0 = INPUTS[n0]
        bs = b0.replace(k0[1].encode('utf-8') + b'!', b'Planted!')
        C = [
            (f'{n0} with one character changed', {**files, n0: b0[:i] + (b'Y' if b0[i:i + 1] == b'X' else b'X') + b0[i + 1:]}, rows,
             [('not the manifest digest, cell count and sheet of its row', n0)]),
            (f"{n0}'s row with its cell count one more, its digest kept", files,
             [dict(r, n=r['n'] + 1) if (r['wb'], r['sheet'], r['rng']) == k0 else r for r in rows],
             [('not the manifest digest, cell count and sheet of its row', n0)]),
            (f"{n0} with its sheet named Planted in every line, its row's digest made the file's", {**files, n0: bs},
             [dict(r, sha=sha(bs)) if (r['wb'], r['sheet'], r['rng']) == k0 else r for r in rows],
             [('not the manifest digest, cell count and sheet of its row', n0)]),
            (f"the manifest without its first input row ({rows[0]['wb']} '{rows[0]['sheet']}'!{rows[0]['rng']})" if rows else 'no rows',
             files, rows[1:], [('no manifest row for a listed input', ([p for p, k in INPUTS.items() if rows and k == (rows[0]['wb'], rows[0]['sheet'], rows[0]['rng'])][:1] or [None])[0])]),
            ('a file added, official-output.json, SHA256SUMS refreshed', refreshed({**files, 'official-output.json': b'{"planted": true}\n'}), rows,
             [('not in the closed list', 'official-output.json')]),
            (f'an input moved, {mv} to E1/moved/par-rates.tsv, SHA256SUMS refreshed',
             refreshed({**{p: b for p, b in files.items() if p != mv}, 'E1/moved/par-rates.tsv': files.get(mv, b'')}), rows, [('missing', mv)]),
            ('the labels changed, one line appended to E1/labels.tsv, SHA256SUMS refreshed',
             refreshed({**files, 'E1/labels.tsv': files.get('E1/labels.tsv', b'') + b'planted\tline\n'}), rows, [('not its fixed sha256', 'E1/labels.tsv')]),
            ('the README removed, SHA256SUMS refreshed', refreshed({p: b for p, b in files.items() if p != 'README.md'}), rows, [('missing', 'README.md')]),
            ("a manifest input row outside the closed list, E1 'Planted'!A1:A2 added", files,
             rows + [dict(case='A9', wb='E1', sheet='Planted', rng='A1:A2', n=2, sha='0' * 64)],
             [('a manifest input row outside the closed list', ('E1', 'Planted', 'A1:A2'))]),
            (f'{SUMS} removed', {p: b for p, b in files.items() if p != SUMS}, rows, [('missing', SUMS)]),
            (f'{SUMS} alone changed, one line appended', {**files, SUMS: files.get(SUMS, b'') + b'0' * 64 + b'  planted.tsv\n'}, rows,
             [("not the list of the bundle's other files", SUMS), ('not its fixed sha256', SUMS)]),
        ]
        for label, f2, r2, wants in C:
            p2, _ = check(f2, r2)
            ok = report(label, p2, wants) and ok
        s0 = os.stat(man)
        s1 = os.stat_result((stat.S_IFDIR | stat.S_IMODE(s0.st_mode),) + tuple(s0)[1:])
        ok = report('a stat result with the device and inode of the manifest file and the type of a directory, against the stat of the file itself: changed between its listing and its read',
                    [] if same_entry(s0, s1) else [(CHANGE, man)], [(CHANGE, man)]) and ok
        for label, p2, wants in disk_controls(files, rows):
            ok = report(label, p2, wants) and ok
        for says, fine in cli_controls(files, rows, man):
            print(says)
            ok = fine and ok
    print('bundle check:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
