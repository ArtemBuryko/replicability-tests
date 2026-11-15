# Effort — replicability test 01

The model spend of the test, run by run. No hours are given: the repository's history shows how long the work took — five commits, each a stage frozen before the next, each under a timestamp token.

| run | spend | how a reader knows |
|---|---|---|
| build-a1 — builder A, `gpt-6-astra` (GPT), through its vendor's command-line tool | no price a run: the run was made under a subscription plan of the vendor's. The plan's weekly window read 39 % used at the run's first answer and 40 % at its last, over 26 answers | the vendor's own counters, as the egress log kept them on each answer — command 1. That the run itself took about one per cent of the week — **the author's statement** |
| build-b1 — builder B, `gemini-4-argon` (Gemini), through its vendor's command-line tool | **$5.119680 before tax** — the egress's count: each of 75 answers priced by its own use at the vendor's rates as the envelope holds them (`preregistration/envelope/egress/allowlist.py`), none priced at a bound, under a cap of $55 a run | the egress log's `use` lines — command 2. The vendor's bill for the day of the run, NOK 95.02 with tax, near 1.6 times that count — **the author's statement**; the cause of the gap was not read — a limit |
| the independent review | about USD 7 on its vendor's interface, one session | **the author's statement** |

Not priced here: the second-party checks of the comparison tool and of its tests, and the author's own work.

## The commands

Each is run from the repository's root, reads one file of this folder and prints one line.

Command 1 prints `26 answers; the weekly window used, per cent: first 39 last 40 ; window minutes ['10080']`:

```sh
python3 -c "import json; r=[d['limits'] for d in map(json.loads, open('01-eiopa-rfr-2026/builds/build-a1/egress/egress.jsonl', encoding='utf-8')) if 'limits' in d]; u=[x['x-codex-primary-used-percent'] for x in r]; print(len(u), 'answers; the weekly window used, per cent: first', u[0], 'last', u[-1], '; window minutes', sorted({x['x-codex-primary-window-minutes'] for x in r}))"
```

Command 2 prints `75 priced answers; sum of usd 5.119680 ; the last line: usd_sum 5.119680 priced 75 at a bound 0 unread 0 cap 55`:

```sh
python3 -c "import json; from decimal import Decimal; u=[d for d in map(json.loads, open('01-eiopa-rfr-2026/builds/build-b1/egress/egress.jsonl', encoding='utf-8')) if d.get('event')=='use']; z=u[-1]; print(len(u), 'priced answers; sum of usd', sum(Decimal(d['usd']) for d in u), '; the last line: usd_sum', z['usd_sum'], 'priced', z['answers_priced'], 'at a bound', z['answers_bound'], 'unread', z['answers_unread'], 'cap', z['cap'])"
```
