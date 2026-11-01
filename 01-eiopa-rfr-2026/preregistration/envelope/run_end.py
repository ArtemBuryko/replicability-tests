#!/usr/bin/env python3
"""How a run of builder B ended, read from its records alone — replicability test 01 · spec DRAFT v0.8 (SPEC.md §6).

Usage: python3 -I run_end.py <egress.jsonl> <cli-stderr.txt> <cli-events.jsonl> <exit.txt>
       — the run archive's egress/egress.jsonl, logs/cli-stderr.txt, logs/cli-events.jsonl and logs/exit.txt.

It prints each check and one verdict line, the last:
  «the run's end: stopped by the spend cap» — the egress refused a generation for the run's spend cap or for an
    answer's use it could not read — its request line marked spend_cap —, whatever the exit status;
  «the run's end: stopped by the time limit» — exit status 124 in exit.txt;
  «the run's end: ended by the plan's limit» — the CLI ended on an error, and an attempt of its last model request
    was answered 402, or 429 naming the plan's limit — the words the egress found in its error (error_terms): the
    balance, its credits, billing, a spending cap or a quota;
  «the run's end: ended by the vendor's unavailability» — the CLI ended on an error after its retries on one
    model request; its error output names those attempts — «Attempt 1 failed» onwards, «Max attempts reached»
    on the last, or the last attempt's error after its cut —; each attempt of that request in the egress log —
    the trailing requests carrying one body — ended without a 2xx: answered with 429, 499 or a 5xx, or cut by
    the CLI at its headers timeout — 60 seconds as shipped, 600 by the experiments file builder B's run carries
    (SPEC §4.2) —, no response, the egress's «Client disconnected.» 59 to 70 or 599 to 610 seconds after the
    request; no request refused by the egress from that request's first attempt on; no 400, 402 or
    404 among its answers, and none naming the plan's limit;
  «the run's end: ended by the builder» — any other end: the CLI's own, a success among them.
Exit status 0 when the four records were read, 2 when one could not be. Reads nothing else, writes nothing.
The retries it reads are the Gemini CLI v0.65.0's: ten attempts at most, «Attempt N failed», «Max attempts
reached» on a 429, 499 or 5xx at the last one; a cut at the last one thrown without that line; a 402 not retried.
"""
import datetime
import json
import re
import sys

CUTS = ((59.0, 70.0), (599.0, 610.0))   # the CLI's headers timeout: 60 s as shipped, 600 s by the experiments file
VENDOR = 'ended by the vendor\'s unavailability'
LIMIT = 'stopped by the time limit'
BUILDER = 'ended by the builder'
CAP = 'stopped by the spend cap'
PLAN = "ended by the plan's limit"
PLAN_TERMS = ('prepay', 'credit', 'balance', 'depleted', 'billing', 'spending cap', 'spend cap', 'spending limit', 'quota')


def plan_answer(status, resp):
    """An answer naming the plan's limit: 402, or 429 whose error the egress read for the plan's words."""
    terms = (resp or {}).get('error_terms') or []
    return status == 402 or (status == 429 and any(t in PLAN_TERMS for t in terms))


def when(t):
    return datetime.datetime.fromisoformat(t)


def vendor_status(s):
    return s in (429, 499) or 500 <= s < 600


def read(paths):
    egress = [json.loads(l) for l in open(paths[0], encoding='utf-8') if l.strip()]
    stderr = open(paths[1], encoding='utf-8', errors='replace').read().split('\n')
    events = [json.loads(l) for l in open(paths[2], encoding='utf-8') if l.strip()]
    exit_text = open(paths[3], encoding='utf-8').read()
    return egress, stderr, events, exit_text


def last_attempts(stderr):
    """The last run of «Attempt k failed» lines counting up from 1: [(k, line)]."""
    runs, cur = [], []
    for line in stderr:
        m = re.match(r'Attempt (\d+) failed', line)
        if not m:
            continue
        k = int(m.group(1))
        if k == 1:
            cur = [(k, line)]
            runs.append(cur)
        elif cur and k == cur[-1][0] + 1:
            cur.append((k, line))
        else:
            cur = []
    return runs[-1] if runs else []


def span_of(egress):
    """The last model request's attempts: the trailing generation requests carrying one body, with how each ended."""
    gens = [r for r in egress if r.get('event') == 'request' and r.get('kind') == 'generate']
    if not gens:
        return []
    body = gens[-1].get('sha256')
    span = []
    for r in reversed(gens):
        if r.get('sha256') != body:
            break
        span.append(r)
    span.reverse()
    out = []
    for r in span:
        seq = r.get('seq')
        resp = [x for x in egress if x.get('event') == 'response' and x.get('seq') == seq]
        err = [x for x in egress if x.get('event') == 'error' and x.get('seq') == seq]
        if resp:
            out.append((r, 'status', resp[0].get('status'), resp[0]))
        elif err:
            dt = (when(err[0]['t']) - when(r['t'])).total_seconds()
            out.append((r, 'error', err[0].get('message'), dt))
        else:
            out.append((r, 'none', None, None))
    return out


def main():
    if len(sys.argv) != 5:
        print(__doc__.split('\n\n')[1])
        return 2
    try:
        egress, stderr, events, exit_text = read(sys.argv[1:5])
    except (OSError, ValueError) as e:
        print(f'run_end: a record could not be read: {type(e).__name__}: {e}')
        return 2
    p = print
    m = re.search(r'^exit status: (\d+)', exit_text, re.M)
    rc = int(m.group(1)) if m else None
    p(f'exit.txt: exit status {rc}')
    if rc is None:
        p('run_end: exit.txt names no exit status')
        return 2
    capped = [r for r in egress if r.get('event') == 'request' and r.get('spend_cap')]
    p(f'generations refused by the egress for the spend cap: {len(capped)}'
      + (f" · the first: seq {capped[0].get('seq')} · «{capped[0].get('why')}»" if capped else ''))
    if capped:
        p(f"the run's end: {CAP}")
        return 0
    if rc == 124:
        p(f"the run's end: {LIMIT}")
        return 0
    results = [e for e in events if e.get('type') == 'result']
    status = results[-1].get('status') if results else None
    ok = {}
    ok['the CLI ended on an error'] = status == 'error'
    p(f'the CLI\'s result event: {status} · {"an error" if ok["the CLI ended on an error"] else "not an error"}')
    span = span_of(egress)
    n = len(span)
    p(f'the last model request\'s attempts in the egress log: {n}')
    ends, refused_span, plans = [], [], []
    for r, how, what, dt in span:
        if how == 'status':
            planned = isinstance(what, int) and plan_answer(what, dt)
            plans.append(planned)
            good = isinstance(what, int) and vendor_status(what) and not planned
            ends.append(good)
            terms = (dt or {}).get('error_terms')
            label = "the plan's limit" if planned else ('the vendor' if good else 'NOT the vendor')
            p(f"  seq {r.get('seq')} · {r.get('verdict')} · answered {what}{f' · its error names {terms}' if terms else ''} · {label}")
        elif how == 'error':
            good = what == 'Client disconnected.' and dt is not None and any(lo <= dt <= hi for lo, hi in CUTS)
            ends.append(good)
            label = "the CLI's cut at its headers timeout" if good else 'NOT a cut at the headers timeout'
            p(f"  seq {r.get('seq')} · {r.get('verdict')} · no response · «{what}» after {dt:.1f} s · {label}")
        else:
            ends.append(False)
            p(f"  seq {r.get('seq')} · {r.get('verdict')} · no end recorded")
        if r.get('verdict') != 'allowed':
            refused_span.append(r.get('seq'))
    ok["each attempt ended by the vendor or the CLI's headers timeout"] = n >= 1 and all(ends)
    first_t = when(span[0][0]['t']) if span else None
    refused = [r for r in egress if r.get('verdict') == 'refused' and first_t and when(r['t']) >= first_t]
    statuses = [what for _, how, what, _ in span if how == 'status']
    bad = [s for s in statuses if s in (400, 402, 404)]
    ok['none refused by the egress from the first attempt on'] = not refused and not refused_span
    ok['no 400, 402 or 404 among the answers'] = not bad
    p(f'refused by the egress from the first attempt on: {len(refused)} · 400, 402 or 404 among the answers: {bad}')
    att = last_attempts(stderr)
    ks = [k for k, _ in att]
    maxed = bool(att) and 'Max attempts reached' in att[-1][1]
    last_cut = bool(span) and span[-1][1] == 'error'
    names = (maxed and ks == list(range(1, n + 1))) or (not maxed and last_cut and ks == list(range(1, n)))
    ok['the error output names the attempts'] = n >= 1 and names
    p(f'the CLI\'s error output: attempts named {ks} · «Max attempts reached» {maxed} · the last attempt cut {last_cut} · '
      f'{"agrees with the egress log" if names else "does NOT agree with the egress log"}')
    ok["none of its answers naming the plan's limit"] = not any(plans)
    for k, v in ok.items():
        p(f'  {"yes" if v else "no "} · {k}')
    if ok['the CLI ended on an error'] and any(plans):
        p(f"the run's end: {PLAN}")
    else:
        p(f"the run's end: {VENDOR if all(ok.values()) else BUILDER}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
