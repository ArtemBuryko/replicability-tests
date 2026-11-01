#!/usr/bin/env python3
"""The stand-ins' checks — replicability test 01 · the envelope's spec DRAFT v0.5 (SPEC.md §3b, §5, §6).

run.sh runs it in the run's own image, offline, the run's folder read-only at /r:
  vault_check.py key B          before builder B's run: one key in the vault; /r/builder.env gives the
                                builder its stand-in as GEMINI_API_KEY, not the key; no real key in any
                                file under /r/state, /r/logs or /r/work
  vault_check.py signin <A|B>   after the sign-in: every token of the credential file a stand-in the vault
                                holds, none a real token; no real token of the vault in any file under
                                /r/state, /r/logs or /r/work
  vault_check.py archive <A|B>  after the archive is made: every member of /archive.tar.gz read whole, a gzip
                                member opened; no real token of the vault in any — as it is, URL-escaped or
                                JSON-escaped; the stand-ins counted by part, the egress's own counts beside them
It prints names and counts, never a value. Exit 0 when each check holds; 1 when one fails; 2 when an input
is missing or unreadable.
"""
import gzip
import json
import os
import sys
import tarfile
from urllib.parse import quote

R = "/r"
VAULT = os.path.join(R, "vault", "vault.json")
ARCHIVE = "/archive.tar.gz"
CRED = {"A": "state/codex/auth.json", "B": "state/home/.gemini/oauth_creds.json"}
TOKENS = {"A": ("tokens.access_token", "tokens.refresh_token", "tokens.id_token"),
          "B": ("access_token", "refresh_token", "id_token")}


def fail(msg):
    print(f"vault_check: {msg}")
    sys.exit(2)


def load_vault():
    try:
        with open(VAULT, encoding="utf-8") as f:
            v = json.load(f)
    except (OSError, ValueError) as e:
        fail(f"the vault: unreadable ({type(e).__name__})")
    real_by = v.get("real_by_standin") if isinstance(v, dict) else None
    if not isinstance(real_by, dict) or not real_by:
        fail("the vault holds no token")
    return v, real_by


def forms(token):
    """A real token's forms to look for: as it is, URL-escaped, JSON-escaped."""
    return [f.encode() for f in {token, quote(token, safe=""), token.replace("/", "\\/")} if f]


def hits(data, needles):
    return sum(1 for n in needles if n in data)


def get(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def signin(builder):
    v, real_by = load_vault()
    real = list(real_by.values())
    needles = [n for t in real for n in forms(t)]
    try:
        with open(os.path.join(R, CRED[builder]), encoding="utf-8") as f:
            cred = json.load(f)
    except (OSError, ValueError) as e:
        fail(f"the credential file {CRED[builder]}: unreadable ({type(e).__name__})")
    present = [k for k in TOKENS[builder] if isinstance(get(cred, k), str) and get(cred, k)]
    held = [k for k in present if get(cred, k) in real_by]
    as_real = [k for k in present if get(cred, k) in real]
    ok = bool(present) and len(held) == len(present) and not as_real
    print(f"the credential file {CRED[builder]}: token fields {present} · stand-ins the vault holds: "
          f"{len(held)} of {len(present)} · real tokens in it: {len(as_real)}")
    if builder == "A":
        mode, key = cred.get("auth_mode"), cred.get("OPENAI_API_KEY")
        print(f"auth_mode: {mode} · an API key in it: {'yes' if key else 'no'}")
        ok = ok and mode == "chatgpt" and not key
    n_files = n_hits = 0
    for part in ("state", "logs", "work"):
        for root, _dirs, files in os.walk(os.path.join(R, part)):
            for name in sorted(files):
                p = os.path.join(root, name)
                try:
                    with open(p, "rb") as f:
                        data = f.read()
                except OSError as e:
                    fail(f"{os.path.relpath(p, R)}: unreadable ({type(e).__name__})")
                n_files += 1
                h = hits(data, needles)
                if h:
                    n_hits += h
                    print(f"  a real token in {os.path.relpath(p, R)}: {h}")
    print(f"files read under state/, logs/ and work/: {n_files} · real tokens found: {n_hits}")
    print(f"the vault: real tokens {len(real)} · issued {v.get('issued', {})} · swapped {v.get('swapped', {})}")
    ok = ok and n_hits == 0
    print("the stand-ins after the sign-in: " + ("HOLD" if ok else "FAIL"))
    return 0 if ok else 1


def key(builder):
    v, real_by = load_vault()
    real = list(real_by.values())
    needles = [n for t in real for n in forms(t)]
    standin = next(iter(real_by))
    env = {}
    try:
        with open(os.path.join(R, "builder.env"), encoding="utf-8") as f:
            for line in f:
                name, sep, value = line.rstrip("\n").partition("=")
                if sep:
                    env[name] = value
    except OSError as e:
        fail(f"builder.env: unreadable ({type(e).__name__})")
    given = env.get("GEMINI_API_KEY")
    what = "its stand-in" if given == standin else ("the real key" if given in real else "NOT the stand-in")
    print(f"the vault: keys {len(real_by)} · issued {v.get('issued', {})} · builder.env: names {sorted(env)} · "
          f"GEMINI_API_KEY {what}")
    ok = builder == "B" and len(real_by) == 1 and given == standin and given not in real
    n_files = n_hits = 0
    for part in ("state", "logs", "work"):
        for root, _dirs, files in os.walk(os.path.join(R, part)):
            for name in sorted(files):
                p = os.path.join(root, name)
                try:
                    with open(p, "rb") as f:
                        data = f.read()
                except OSError as e:
                    fail(f"{os.path.relpath(p, R)}: unreadable ({type(e).__name__})")
                n_files += 1
                h = hits(data, needles)
                if h:
                    n_hits += h
                    print(f"  a real key in {os.path.relpath(p, R)}: {h}")
    print(f"files read under state/, logs/ and work/: {n_files} · real keys found: {n_hits}")
    ok = ok and n_hits == 0
    print("the key's stand-in before the run: " + ("HOLDS" if ok else "FAILS"))
    return 0 if ok else 1


def archive(builder):
    v, real_by = load_vault()
    real = list(real_by.values())
    needles = [n for t in real for n in forms(t)]
    standins = [s.encode() for s in real_by]
    n_members = n_hits = 0
    by_part = {}
    try:
        tf = tarfile.open(ARCHIVE, "r:gz")
    except (OSError, tarfile.TarError) as e:
        fail(f"the archive: unreadable ({type(e).__name__})")
    with tf:
        for m in tf:
            if not m.isfile():
                continue
            data = tf.extractfile(m).read()
            blobs = [data]
            if m.name.endswith(".gz"):
                try:
                    blobs.append(gzip.decompress(data))
                except (OSError, EOFError) as e:
                    fail(f"{m.name}: a gzip member not read ({type(e).__name__})")
            n_members += 1
            h = sum(hits(b, needles) for b in blobs)
            part = m.name.split("/", 1)[0]
            by_part[part] = by_part.get(part, 0) + sum(hits(b, standins) for b in blobs)
            if h:
                n_hits += h
                print(f"  a real token in {m.name}: {h}")
    print(f"the archive ({builder}): members read {n_members} · real tokens found: {n_hits} · "
          f"stand-ins by part: {dict(sorted(by_part.items()))}")
    print(f"the vault: real tokens {len(real)} · issued {v.get('issued', {})} · swapped {v.get('swapped', {})}")
    print("no real token in the archive: " + ("HOLDS" if n_hits == 0 else "FAILS"))
    return 0 if n_hits == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("signin", "key", "archive") or sys.argv[2] not in ("A", "B"):
        fail("usage: vault_check.py <signin|key|archive> <A|B>")
    sys.exit({"signin": signin, "key": key, "archive": archive}[sys.argv[1]](sys.argv[2]))
