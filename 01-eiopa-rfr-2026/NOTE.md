# Note — replicability test 01

EIOPA's RFR Technical Documentation of 2026 (EIOPA-BoS-26/198) and its three workbooks of worked examples. The first section is the test in short. After it: the claims, numbered, each beside its evidence; what was added after the review; then the limits and the record's further items, each under its own heading. Paths are this folder's; commands run from the repository's root.

## The test in short

**The question.** From the published documentation alone, can two blind builders of different model families reproduce the text's own worked examples — and where they cannot, which passages caused it, on what grounds? Six cases were declared before any build — A1, A2 and A3 on the first workbook, B1 and B2 on the second, C1 on the third —, 535 official outputs in all.

**The method.** This is a replicability test: two independent implementations of a public text, each set against the publisher's own worked examples. The examples are withheld as the oracle — the workbooks' cached outputs, read by a manifest frozen before any build. Each builder received the same brief, the text's PDF and the input bundle — the values the worked examples start from —, and built the cases once. Every declared output of both builds was compared with its official value within a band set before any build. Every failing output is a divergence, none chosen; each is attributed on stated grounds, by a rule frozen with the bands — to the text, the oracle, the channel, a builder or propagation, or left unresolved. One review — a separate AI review using Grok, the «independent review» of the preregistration — then read the table, the attributions with their grounds and the claims beside their evidence; it was committed as received before any disposition was written. The record is five commits, each a stage frozen before the next under an RFC 3161 timestamp token; one command, `verify.sh`, checks artifact integrity — every hash and every token —, regenerates the comparison table and computes the outcome from the recorded attribution statuses. It does not assess the grounds of those attributions.

**«Independent».** Three things carry the word here. *The builders* — two model families, OpenAI's `gpt-6-astra` and Google's `gemini-4-argon`, each run once, as one agent, and blind: from the documentation only, with no official output, no workbook, no repository and nothing of the other builder's work, its network reaching its vendor's interface alone. *The oracle* — the publisher's own computation, never the author's. *The review* — a separate AI review using Grok: one session of an AI model of a family other than the builders', outside the builds; not a review by a person or an organisation. None of the three means independent of the author, who designed the test, wrote its tools, its attributions and its dispositions, prepared what the review read and started its session.

**The result.** In the lines `verify.sh` prints:

```text
A1: reproduced
A2: reproduced
A3: reproduced
B1: reproduced
B2: reproduced
C1: not reproduced — the text: G.5.5 with G.5.3; G.1.2
outcome: not reproduced
```

Both builders reproduce every official output of A1, A2, A3, B1 and B2 within its band. C1 fails for both — four of build-a1's nine outputs and one of build-b1's lie outside their bands — and after the review and the dispositions each of the five divergences is attributed to the text:

- **G.1.2** — the text names no rounding of an index's duration, and the workbook's own sheet rounds it to one decimal.
- **G.5.5 with G.5.3** — the text constructs the yield of a type its Table 13 lacks from the euro yield of that type, and does not say what the rows the input supplies for credit quality steps 4 and 5 are.

A divergence attributed to a passage is a reading the passage allows, set beside the publisher's own example; the test attributes no error to the text's owner.

**What the test does not show.**

- It makes no regulatory-accountability claim of any kind, and it says nothing about the publisher's production curves, whose inputs are licensed market data, or about the shocks this text does not carry.
- One run per builder is one sample: no rate of success, no ranking of model families.
- A «reproduced» is weaker evidence that the text suffices than a «not reproduced» attributed to a passage is evidence that it does not: the text was published after both builders' stated training cutoffs, and the method it documents was public before both.
- The method is not compared with human reviewers or with established providers.
- What is verified is the archive: each builder's code and outputs as returned. Repeating the agent generation may produce different code. This verification uses the archived outputs and does not rerun generation.
- The comparison tool carries a second party's check; its tests carry none; `verify.sh` carries its author's own controls and no second party's check.
- The review is one AI review, one round; its product, its version and its settings, and what it did not read or run, are under «The review's reach» below.

Each sentence of this section rests on a numbered claim below — claims 1, 3, 7, 9, 12, 13, 16, 17, 20, 23 to 25, 29 and 30 — or, where it speaks of the review, the dispositions, the outcome or `verify.sh`, on what was added after the review.

## The claims — each beside its evidence

The preregistration gave the review «the claims of this folder's README and note beside their evidence» (`preregistration/PREREGISTRATION.md`, §9). The review read thirty-one claims, numbered as here. Twenty-three stand in the words it read — one of them, 14, with its last clause narrowed by the author after the review, as it says —; eight — 4, 8, 9, 10, 22, 23, 25 and 28 — stand in the words the dispositions leave them (`dispositions/DISPOSITIONS.md`), written after the review; where a sentence counted the commits made, it now counts five. What the review read in its own layout is set here in this repository's. A path without a folder named lies inside `01-eiopa-rfr-2026/`; `file:a-b` cites lines a to b. `<files>` is the folder that holds the publisher's four files as `T.pdf`, `E1.xlsm`, `E2.xlsm` and `E3.xlsm` — the folder `verify.sh` keeps them in, `$HOME/eiopa-rfr-files` in the READMEs' example —, given by its full path. `<bundle>` is the input bundle both builders read, written again by `python3 -I -B 01-eiopa-rfr-2026/preregistration/tools/bundle.py <files> <bundle>` and held by `python3 -I -B 01-eiopa-rfr-2026/preregistration/tools/bundle_check.py <bundle> 01-eiopa-rfr-2026/manifest/MANIFEST.md`. The author ran the commands as given here on Python 3.10; `bundle.py` and `bands.py` need the `openpyxl` library. A claim whose evidence is not in this repository rests on the author's own records and is marked **the author's statement**.

### The question and its material

**1.** For each of six declared cases of EIOPA's RFR Technical Documentation of 2026 — A1, A2 and A3 on the first workbook, B1 and B2 on the second, C1 on the third — the test asks whether the published documentation suffices to reproduce the case's official outputs: 535 declared outputs in all.
*Evidence:* `preregistration/PREREGISTRATION.md:7`, `:94`; `table/cases.tsv:13-18` — the six cases and their outputs, 201, 153, 154, 9, 9 and 9.

**2.** The publisher's four files are pointed to, never copied: each by its URL, its snapshot in the Wayback Machine and its sha256.
*Evidence:* `source/README.md:5-19`; `sha256sum <files>/T.pdf <files>/E1.xlsm <files>/E2.xlsm <files>/E3.xlsm` prints the four sha256 of `source/README.md:7-10`.

**3.** The oracle is the workbooks' cached outputs, read by the frozen manifest's ranges, each range held to its digest.
*Evidence:* `table/table.tsv:4-5`; `manifest/MANIFEST.md`.

### The order — each stage frozen before the next

**4.** The record is five commits, each a stage frozen before the next, each under an RFC 3161 timestamp token over its own file list. All five are made: the first — the text's pointers, the manifest and the preregistration with the brief and the envelope, under a token of 2026-11-01 08:15:16 UTC; the second — the builds as returned and their egress logs, 2026-11-01 22:00:21 UTC; the third — the comparison tool with its tests and its second party's check, the table and the divergence log, 2026-11-13 21:24:03 UTC; the fourth — the review as received, 2026-11-14 16:21:59 UTC; the fifth — the dispositions, the model spend, the README and this note, `verify.sh`, the folder's manifest and the licence, under the token in `timestamps/v.tsr`. A token dates the files' bytes, not the acts before them.
*Evidence:* `preregistration/PREREGISTRATION.md:109-110`. For each token `<n>`: `openssl ts -reply -in 01-eiopa-rfr-2026/timestamps/<n>.tsr -token_out -out <tmp>/<n>.token` and `openssl pkcs7 -inform DER -in <tmp>/<n>.token -print_certs -out <tmp>/<n>.certs.pem` take out the certificates the token itself carries; `openssl ts -verify -in 01-eiopa-rfr-2026/timestamps/<n>.tsr -data 01-eiopa-rfr-2026/timestamps/<n>.list -CAfile 01-eiopa-rfr-2026/timestamps/chain/DigiCert_Trusted_Root_G4.pem -untrusted <tmp>/<n>.certs.pem` prints `Verification: OK` — the folder's root the only trust anchor. OpenSSL 3 prints beside it a warning that the responder's certificate «is not a CA cert». No file is added to the chain folder. Checked by the author on the first four tokens, on LibreSSL 3.3.6 and on OpenSSL 3.0.13 — **the author's statement**; `verify.sh` runs the command on every token. For each token, `openssl ts -reply -in 01-eiopa-rfr-2026/timestamps/<n>.tsr -text` prints its time, and `tail -n +2 01-eiopa-rfr-2026/timestamps/<n>.list | awk '{print $2"  "$3}' | sha256sum -c` finds every listed file at its sha256 — 27, 41, 54 and 57 rows for the first four lists. The commits themselves — their ids, parents and dates — are in the repository's history: **the author's statement**.

**5.** Both builds ran after the first token and before the second: build-a1 from 19:33 to 19:46 UTC on 1 November 2026, build-b1 from 19:51 to 20:50.
*Evidence:* the first and last line of `builds/build-a1/egress/egress.jsonl` and of `builds/build-b1/egress/egress.jsonl`, their field `t`.

**6.** The table was made once, by the comparison tool's stamped bytes, on 10 November 2026 — after the first second-party check's return and before the second's. Before it, earlier bytes of the tool read the builds' returns for their form and for their sameness to their own offline re-runs; and once, in a check of the tool, a table of build-a1's return was made and removed unread.
*Evidence:* `comparison/SECOND-PARTY-CHECK.md:23`; the date and the earlier reads — **the author's statement**.

### The builders and their runs

**7.** Two builders, of two model families: builder A, OpenAI's `gpt-6-astra` at reasoning effort `xhigh`, through the Codex CLI `rust-v0.164.0`; builder B, Google's `gemini-4-argon` at thinking level `high`, through the Gemini CLI `v0.65.0`. Each ran as one agent and blind: the brief, the text's PDF and the input bundle its only material, its network its vendor's API alone, no web search or fetch.
*Evidence:* `preregistration/PREREGISTRATION.md:45-48`; `preregistration/brief.md`; `preregistration/envelope/`; the egress logs, every request's host and verdict.

**8.** One run per builder, neither void, neither restarted. build-a1's return is the brief's five items; build-b1's is three files, without its notes. How each run ended — build-a1 by its CLI's own end, build-b1 by the builder, its code changed after its outputs were written — is **the author's statement**: the runs' consoles and full logs stay out of this repository.
*Evidence:* the two return folders, five files and three; `builds/*/run-*.sha256`; `preregistration/PREREGISTRATION.md:111`.

**9.** The builds are kept as returned: their files stand at their sha256 under the second token. Repeating the agent generation may produce different code. This verification uses the archived outputs and does not rerun generation. (These two sentences are the author's later words, written after the review and before the fifth commit; the preregistration's own limit, frozen, says it more strongly — «a builder run again writes other code», §12.)
*Evidence:* `timestamps/ii.list` (claim 4); `preregistration/PREREGISTRATION.md:121`.

**10.** The isolated outputs are each build's own A2 and A3 code, run again offline in the same image on the official A1 curve. Beside the same build's returned A2 and A3, which rest on its own A1, the scalars `cssr`, `notional_va`, `currency_va`, `omega_co` and `total_va` are equal, `llfr` lies within 1.1e-15 and the curves within 4.9e-06 — inside the curves' band. Apart from the isolated files, each build's own code was run again offline whole: build-a1's outputs came out equal to its return byte for byte; build-b1's apart in 21 of its 535 numbers, by 1.84e-16 at most, its code having changed after its outputs were written — **the author's statement**: that re-run's record holds the official A1 results and stays out of this repository.
*Evidence:* `isolated/build-a1.json`, `isolated/build-b1.json` against each `outputs.json`; `preregistration/PREREGISTRATION.md:56`, `:72`. An earlier «1.8e-16» is the same figure, 1.839e-16, at two digits.

**11.** Both builders ran on one image, identified by its id `sha256:9f8fd127…`, not rebuilt; its Debian packages were installed without pinned versions — a limit.
*Evidence:* `preregistration/envelope/SPEC.md:176`.

### The table

**12.** Every declared output of both builds was compared with its official value within the band the preregistration set before any build: 1,684 rows — 535 outputs as returned and 307 isolated for each build.
*Evidence:* `preregistration/PREREGISTRATION.md:52-60`; `table/table.tsv:6-9`; `grep -c -v '^#' 01-eiopa-rfr-2026/table/table.tsv` prints 1685 — the rows and their column line.

**13.** A1, A2, A3, B1 and B2 pass for both builds; C1 fails for both — build-a1 with four of its nine outputs outside their bands, build-b1 with one.
*Evidence:* `table/cases.tsv:13-18`, `:21-26`.

**14.** Each builder's own A2 and A3 code, run on the official A1 curve, passes both cases: A2 and A3 also pass when supplied with the official A1 curve. (This last clause is the author's, written after the review, which read «nothing in A2 or A3 rests on a builder's own A1»: the returned A2 and A3 use each builder's own A1.)
*Evidence:* `table/cases.tsv:19-20`, `:27-28`; `table/table.tsv:7`, `:9`.

**15.** The table can be made again from this folder and the three workbooks, the same byte for byte.
*Evidence:* `cd 01-eiopa-rfr-2026 && python3 -I -B comparison/compare.py table <files> manifest/MANIFEST.md <new folder> --build build-a1 builds/build-a1/work/return/outputs.json --build build-b1 builds/build-b1/work/return/outputs.json --isolated build-a1 isolated/build-a1.json --isolated build-b1 isolated/build-b1.json`, then `cmp` of each of the three files it writes against `table/`.

### The comparison tool and its tests

**16.** The tool that made the table, `comparison/compare.py`, carries a second party's check: four checks in a row on its unchanged bytes, each returning STAMP within the limits it states. They are the last of twenty-one: the seventeen before them read earlier bytes and returned NO STAMP; after each, every finding was tested against the bytes it named, none was set aside, and the tool was revised. The note carries the twenty-one as a table — each check's tool and tests by their sha256 and its two verdicts.
*Evidence:* `sha256sum 01-eiopa-rfr-2026/comparison/compare.py` — the sha256 at `comparison/SECOND-PARTY-CHECK.md:7` and at line 2 of each file of `table/`; `comparison/SECOND-PARTY-CHECK.md:5-25` — the four returns by their sha256 and their first lines. The returns themselves, and the seventeen earlier checks — **the author's statement**.

**17.** The tests in the folder, `comparison/test_compare.py`, carry no second party's check. Each of the four checks returned NO STAMP on the tests it read; the tests kept here were revised after the fourth to hold its findings and were read by no second party; the checks ended by the author's decision. The preregistration asks a second party's check of the tool alone.
*Evidence:* `comparison/SECOND-PARTY-CHECK.md:33-39`; `preregistration/PREREGISTRATION.md:60`.

**18.** The stamp holds within stated limits: how a stream's count of what it took is read; how far the probe of a stream's encoding reaches; and the descriptor a caller supplies for standard output, taken at its word — a run can be made to overwrite its own completed outputs.
*Evidence:* `comparison/SECOND-PARTY-CHECK.md:27-31`; the tool's docstring, `comparison/compare.py:2-154`.

**19.** A check on the real inputs: each of the twenty-five changes of the tool's code that the four checks showed passing every test of their day, and each of the twenty-eight changes the author had named equivalent, was run by the table's command on the real inputs. None moved a row of `table.tsv` or `divergences.tsv`. One — a case's failures counted across builds — moved two counts of `cases.tsv` in C1, the verdict FAIL either way; the stamped counts were right by a recomputation apart from the tool.
*Evidence:* **the author's statement** — the changes and their runs are in the author's records.

### The divergences and their attribution

**20.** Five divergences — every failing output, none chosen —, all in C1, all on its corporate reference portfolio.
*Evidence:* `table/divergences.tsv:13-17`; `divergences.md:3`, `:9-13`, `:19`.

**21.** The reference `divergences/variants.py` is written apart from both builds' code and from the comparison tool, uses the standard library alone and reads no official output; its run `divergences/variants.out` is made again from this folder and the input bundle, byte for byte.
*Evidence:* `divergences/variants.py:1-12`; `python3 -I -B 01-eiopa-rfr-2026/divergences/variants.py <bundle> 01-eiopa-rfr-2026/builds/build-a1/work/return/outputs.json 01-eiopa-rfr-2026/builds/build-b1/work/return/outputs.json | cmp - 01-eiopa-rfr-2026/divergences/variants.out` prints nothing and exits 0.

**22.** Each divergence is a sum of known parts: the workbook's own sheet solved exactly, the reading of the index durations, and — for build-a1 — G.5.3's construction applied to the rows the input supplies for credit quality steps 4 and 5. build-b1's five outputs are the text's method with the durations as supplied, to 2.5e-16; build-a1's are the same with G.5.3 applied, to 1.4e-17.
*Evidence:* `divergences.md:21-41`; `divergences/variants.out:12-23`; the sheet solved exactly — `python3 -I 01-eiopa-rfr-2026/preregistration/tools/bands.py <files>/E2.xlsm <files>/E3.xlsm`, the source of `divergences.md:23`.

**23.** build-a1's four — `s_corp`, `rc_corp`, `s` and `rc` — are attributed to the text (T), the passage G.5.5 with G.5.3. The text constructs the yield of a type its Table 13 lacks from the euro yield of that type; it does not say what the rows the input supplies for credit quality steps 4 and 5 are. The input's heading says pounds; its label's term is not the text's; and the rows' yields are those of the second workbook's euro block, cell for cell. The build took the rows for the euro observations and applied the construction — its notes name both readings —; without that step the four lie inside their bands. The log, frozen with the third commit, attributes the four to the builder (B) and names this reading for the review; the status is as the review and the dispositions leave it.
*Evidence:* `divergences.md:43-49`; `review/REVIEW.md`, its §2 and its findings F1 and F6; `builds/build-a1/work/return/portfolios.py:209-212`; `builds/build-a1/work/return/NOTES.md:81-88`; the cells by their addresses — E2 `Corp Data` L22:L26, P22:P26, L41:L45, P41:P45 and E3 `Corp Data` L23:L27, P23:P27, L44:L48, P44:P48.

**24.** build-b1's `rcs` is attributed to the text (T), the passage G.1.2: the text names no rounding of an index's duration, and the workbook's sheet rounds it to one decimal. Under that rounding the output lies inside its band; under the reading both builds took — the duration as supplied — outside.
*Evidence:* `divergences.md:51-57`; `builds/build-b1/work/return/calculate.py:387-397`, `:509-525`; `divergences/variants.out:16-17`.

**25.** After the review and the dispositions, by §8: A1, A2, A3, B1 and B2 reproduced; C1 not reproduced — the text: the passage G.1.2, by build-b1's `rcs`, and the passage G.5.5 with G.5.3, by build-a1's four. The outcome is computed by `verify.sh` from the table and the statuses the dispositions carry.
*Evidence:* `preregistration/PREREGISTRATION.md:95-96`; `table/cases.tsv:13-28`; `dispositions/statuses.tsv`; `verify.sh`.

### What the oracle shows of itself

**26.** For the second workbook the bands rest on another reason than §5 gives. Its cached outputs agree with the reading that does not round the index durations — both builds reproduce every output of B1 and B2 to 2.6e-07 or closer —, while its own sheet, which rounds them, solved exactly, lies up to a whole band away. What §5 calls the Solver's residuals is, for that workbook, the rounding's effect: an inference, not a fact the folder shows. The bands stand as frozen.
*Evidence:* `divergences.md:54`; `divergences/variants.out:24-37`; `table/table.tsv`, B1's and B2's rows; `preregistration/PREREGISTRATION.md:58`; the inference — **the author's statement**.

**27.** The third workbook's cached rates are roots of its equations under neither reading of the durations; by what state of its inputs they came is not known.
*Evidence:* `divergences.md:61`; `divergences/variants.out:12-19`.

### Limits, and what the test does not show

**28.** Builder B's spend: the egress counted every generation at the vendor's rates — $5.119680 before tax, the sum of its 75 priced answers, none priced at a bound, under a cap of $55. The vendor's bill for the day, NOK 95.02 with tax, is near 1.6 times that count; its cause not read — a limit. Builder A ran under a plan of its vendor's, its share of the plan's weekly window. No hours are given here; the model spend is given in `effort.md`.
*Evidence:* `builds/build-b1/egress/egress.jsonl` — its 75 `use` lines' `usd` fields sum to its last line's `usd_sum`, by the command `effort.md` gives; the bill and the plan's share — **the author's statement**.

**29.** Both builders' stated training cutoffs fall before the text's publication on 26 May 2026; the method it documents was public before both. A «reproduced» is therefore weaker evidence that the text suffices than a «not reproduced» attributed to a passage is evidence that it does not.
*Evidence:* `preregistration/PREREGISTRATION.md:83-91`.

**30.** One run per builder is one sample: no rate of success, no ranking of model families; no regulatory-accountability claim; a divergence attributed to a passage is a reading the passage allows, never an error of the text's owner.
*Evidence:* `preregistration/PREREGISTRATION.md:103`, `:114-118`.

**31.** Before each commit, every file it carries was read by the leak check: zero hits.
*Evidence:* **the author's statement** — the check's deny-list stays out of this repository (`preregistration/PREREGISTRATION.md:111`).

## Added after the review — read by no review

The review read this folder as its third commit holds it, and the thirty-one claims in their first words. What follows was written after it and has been read by no review.

- **The fourth commit.** `review/REVIEW.md` — the review as received, sha256 `1141a1baa86591b1215a5b0138cfe34d599163b689ee089fe88c09743614b9a5` —, committed before any disposition was written, under a token of 2026-11-14 16:21:59 UTC. *Evidence:* `timestamps/iv.list`, `timestamps/iv.tsr`; `sha256sum 01-eiopa-rfr-2026/review/REVIEW.md`.
- **The dispositions.** `dispositions/DISPOSITIONS.md` — 76 rows, every line of the review answered, none rejected —, and `dispositions/statuses.tsv` — the status of each of the five divergences after the review, each T. *Evidence:* the two files; the count in the dispositions' last line.
- **The new words of eight claims** — 4, 8, 9, 10, 22, 23, 25 and 28 above —, **and claim 14's last clause**.
- **Wording changed on a later reading, before the fifth commit** — by the author, on no finding of the review: claim 14's last clause, narrowed to what the isolated run shows; in claim 9, in `README.md` and in this note's first section, a repeated agent generation said as a possibility; what `verify.sh` checks and what it does not, said in full in both READMEs and in this note's first section; the review named for what it is — a separate AI review using Grok — in both READMEs and in this note, with its product, its version and its settings under «The review's reach»; the command's folder given as an example a reader can copy; and the tools of the review's session as the review states them.
- **The outcome.** The seven lines `verify.sh` prints, quoted in the first section — computed from `table/cases.tsv` and `dispositions/statuses.tsv` by the preregistration's §8. *Evidence:* `verify.sh`, run by the reader.
- **`verify.sh` itself** — what it does is said below; it carries its author's own controls and no second party's check.
- **The fifth commit** — the dispositions, the model spend (`effort.md`), `README.md` and this note, `verify.sh`, the folder's `MANIFEST.sha256` and the licence, under the token in `timestamps/v.tsr`.
- **The words on «independent»** in `README.md` and in this note's first section — that none of the three senses means independent of the author, and what stands between the author and the result — are the author's own, in no claim the review read.
- **This note's first section and every section below.**

## The status change and its ground

The divergence log, frozen with the third commit, attributed build-a1's four divergences — `s_corp`, `rc_corp`, `s` and `rc` — to the builder (B) and named the other reading, the passage, for the review. The review found that by the log's own rule the four are the text's: the rule (`preregistration/PREREGISTRATION.md`, §6) gives T where the text, read against the input's labels, singles out no reading. The dispositions accept it. The text is plain on the method — G.5.5 constructs by G.5.3 the yield of a type its Table 13 lacks, from the euro yield of that type — and silent on what the supplied rows are: the input's heading says pounds, its label's term is not the text's, and the rows' yields are those of the second workbook's euro block, cell for cell — twenty cells of twenty, their addresses under claim 23. An attribution to the oracle is closed by §6's precedence; one to the builder would need a label saying that the rows are the constructed yields, and there is none. `s` and `rc` follow the corporate term.

The log is not rewritten — a frozen stage is not amended: its B stands in it as the status before the review, and `dispositions/statuses.tsv` carries the statuses as they stand after it, in the form `verify.sh` reads. build-b1's `rcs` stood — T, the passage G.1.2; the review added two readings to it: the oracle, closed by §6's precedence, and a bucket's index taken at its bucket, open, not displacing T. Nothing in the review moved a row of `table/table.tsv` or of `table/cases.tsv`.

## The second-party checks — twenty-one

Claim 16's table. Each check received the tool and the tests of its day and returned its decision in writing. The returns stay with the author; each is bound here by its sha256. The last four rows are the checks 1 to 4 of `comparison/SECOND-PARTY-CHECK.md`.

| check | the tool it read · sha256 | the tests it read · sha256 | its return · sha256 | on the tool | on the tests |
|---|---|---|---|---|---|
| 1 | `3410cf52e9bab8516d986bb0ecea54c1ea513dda29b85e38113fb6efa77e319d` | `99e9012d31fdab45ab7408ffbe8237206655c3c2e29f6747115a51982bb8cd5e` | `194bcb38584f8271dd49dfaa164d30519406255604aa2deb30fc46b7276c9f8f` | NO STAMP | NO STAMP |
| 2 | `6a5bf5c70fc5a550a74ddb2292cfe6f5acb90fcd18a42472759a06888da553e4` | `25215d9cb007f4cf42e614b7ba70120dd87f3d1e43a45e1cac0bee61e7069dfa` | `32dfc8a8d29fc697f26ee663c3ca8508017ce28ab4c8c0803b577e0e88b8d678` | NO STAMP | NO STAMP |
| 3 | `54da452b014209fc200d4240cd33f8c6e6abe6366f5b4776a2ff61230eb2a76c` | `70cbbe54c353c9d73961453ed4ba1112db4eb872a1812dcf5c090f4ccd9211f9` | `307d621f41f276f611c8ddbaea970b170fb70965724902911809714a5cbc1473` | NO STAMP | NO STAMP |
| 4 | `54f3eb4e55ebbd185859ba45af6d9179c2c29d7a0c304a4656cd6dc7bc6464e4` | `2eadfe6cf9d43ee2038d96fa40c65c6dadb6cd0d042c4ffbfe03887e3f35d50f` | `1567a607757f9ebbc2cd28d3824ed09339b50de31eb13b140b616c921df87b84` | NO STAMP | NO STAMP |
| 5 | `22b12715147e003049060774275524f6509c22ce50e3137c749916db18e6317c` | `4ebc28715826117f67e279481cbefd5db4a8a589135f5678356c85123e3e9add` | `1682ead51046df3c306f542d4aca292ac6d821218e5d1f30598f6837a9d0d1a5` | NO STAMP | NO STAMP |
| 6 | `0017de6f5739fe089c62801053050ecd8df94d134664a2af01f33880436cec34` | `484d200c11adba4b82d788eb675c639a173bbfa078cd1f9bac9c80fb37e26e71` | `56894221fb5b0ffc4cac21b0456e9f3a17ce8a439779780442bb79dccec5c6e6` | NO STAMP | NO STAMP |
| 7 | `c6cfc48449cf363565d702f409393ec4924bc531c334601c6cab2b9278683462` | `9f4f988372f2a503e694ea6636ef4b089f565fdaf2205031c7ee894d5239d340` | `1b11f43cf32df562941dcf2a62834ec9d8f45545eb4ff9aaf9743a4860c7a59d` | NO STAMP | NO STAMP |
| 8 | `06d2df54ab48bc3325ca1e22e0767592b77d76ff31f3a1aa824961c767b6a006` | `6692437df5f64a56eaebd404e9e40b834919822173010330974d36c3254f43fd` | `e1bbe1a8b62ac7a4bed96499c838fecaca7286f786cec4f214549cc8fa5957c8` | NO STAMP | NO STAMP |
| 9 | `e33f0283eb9606926d2100a59d6a2cf5162f626703261faa3c76a2447e0d1835` | `7119278c9f0568d59fd9a86514b2ced51ae111d251876e0fa9b5a8849c090f99` | `216c92f006149792c9d426f1e667d267f623f8a0ae7e6310a03986675f93578b` | NO STAMP | NO STAMP |
| 10 | `5ae0e2c67f360fa98146e2f3cd7f7fdea73cdbec1a0f22ecf0cced873433fa49` | `de9e89a9bb5f0664931379a83aab37359f1e3167c6f598ba48920ccf6ea9b9c2` | `86560b104d1d114403cd70a4f3c2221b16b0be98dfc2a9e4732b41bebf0f9762` | NO STAMP | NO STAMP |
| 11 | `b943485cabc17b6afce8f16121d80b4e9583ae8aed0043e43c845b92f6f13134` | `c7edc54ddef6e34e00d0305d74e5631d872308224f049ba83649a4c396401f05` | `8786b63069f0e2d83e7ebd0ab22792d78f67f8f33ba5b55e93b0917e735d7ff9` | NO STAMP | NO STAMP |
| 12 | `4ec180270ca7dac8c3286bd55a45d4e8c67fa943d958d13ce956a0ad5c031177` | `df81176cd2f560ba0789963420d90238221a56d8f5642047384b378a3448ca3f` | `d0b1c5abfb587d5101acaec29ddb2179ec53a4031fa1a548e861c06f310d9a92` | NO STAMP | NO STAMP |
| 13 | `2d07461fba4b79c7833691ef0502f182ec782f5ba02c115ac3babfd8b6e7422d` | `b8a3d8e0830090dece659ef08d752fb54e567101520a1db31c7913d44024c26f` | `022888ef28aba0e7e8ed1c8ff5b9da51579868f728f7511b23603bf97370b4e6` | NO STAMP | NO STAMP |
| 14 | `adc0f18a6481fc4b9486997c90ba093370e5b7703d45f5807b992095414c0e3a` | `7ed03e2ffd48834c39b98e6a93638b817db04ec7fcdcccaab8768ff86b4b3a5f` | `e76cb442fd35280632fb7ff7fad71dd5c2856f0b8a352fa65e9ba5a49fa2ab27` | NO STAMP | NO STAMP |
| 15 | `d622abf1ebd520998be776c92f8698547a89d10e18204be0f8dcd7b9b9261ebe` | `baca8b9002e3bd997e033ba74d6c93c025e1604334950ff180bf68a02c571a7f` | `a541dcc3e83b276310c1179b021444bbcedc4dbf55efcf227104bc6f473e5b9c` | NO STAMP | NO STAMP |
| 16 | `94628baf5e20a1cedd198024fb1c32045f4b7c0546e2fb61d0e8fefcb5d09359` | `8854cd5883152bf4ac7a2ebaa9e7674f5c07a04d1cb1ef11cfdca00fd60df28b` | `8b3085ffcbc0bbec8b173b7a20d2c6e8b79cab0c2a525812b77512f2534c8f4c` | NO STAMP | NO STAMP |
| 17 | `6f2440ee85d43ef9c68830bdcb6ab37bfce637695696ae1255ea77d1e0953fc8` | `994878ab53b8bf280c2941ebeaca465443aec56f2c04515a5005879624c339f8` | `77e74449ba4ddb5fdfaf18af8e982691e3f8a83d1a1d79f139ed36634dbd4bd1` | NO STAMP | NO STAMP |
| 18 | `d36b8649aadaff8958e0baff6164e5717f401e6c68b55144a2a92fe3c9d8f498` | `02f92279fab48716cd6d13255485509074dd3b5e3a8184b957896590ee4c4607` | `741e8427d5e5b4ad6a5a70f9648effd6cad8bb5659f827935c93bf16fc79dc93` | STAMP | NO STAMP |
| 19 | `d36b8649aadaff8958e0baff6164e5717f401e6c68b55144a2a92fe3c9d8f498` | `3fe150f6e6922bbc5ff9102a01d71768f72b71e4e1f45ec4d116cc8c4f5f935a` | `cd6d526385fbf6c2c3aa963b16137c54838eb42c88f8bd88764b500e12aca60d` | STAMP | NO STAMP |
| 20 | `d36b8649aadaff8958e0baff6164e5717f401e6c68b55144a2a92fe3c9d8f498` | `1ef3801f001c3724365e13fdab635f0992c2b91bf3d5233596bf9f39e0a2c2e9` | `3d1894ab1b1b99df8afd752cb632a233912d5c8f080f5868bb018c7967919ae8` | STAMP | NO STAMP |
| 21 | `d36b8649aadaff8958e0baff6164e5717f401e6c68b55144a2a92fe3c9d8f498` | `0d141c551cf80b1c4d6269a25acab529f32381af32b788cbed984ad4fb038707` | `8587348f9219cdf3e7ce355513f2653efb170b660096e936651c178c862d02b8` | STAMP | NO STAMP |

Every row is **the author's statement**, bound by its three hashes: the two verdicts are read from each return's first lines, the tool's and the tests' sha256 from the list of the files each check received. The tool's bytes are the same in the last four rows.

## The tests — read by no reviewer

`comparison/test_compare.py`, as this folder carries it — sha256 `0eab8582631b2445ab3c77625fedfef82ed5b5859761a773bf30307c82850c0d` —, is in no row above: it is the revision made after check 21 to hold what that check showed, and no second party has read it. Each of the last four checks returned NO STAMP on the tests it read: each showed changes of the tool's code — twenty-five across the four — that altered what the tool does and still passed every test of that day; after each, the tests were revised. The checks ended there by the author's decision, not by a stamp on the tests (`comparison/SECOND-PARTY-CHECK.md:37`). The review did not read the tests either. The preregistration asks a second party's check of the tool's code, and none of the tests (§5).

What that leaves open, in plain words: no one but the author has checked that the tests in this folder hold what the last check showed; and the limits each stamp names are limits of the tool itself, which no test closes.

## The check on the real inputs

Claim 19, and why it was made: because the tests were left without a second party's check, the author ran every change of the tool's code that the four checks had shown passing the tests — twenty-five — and every change the author had named equivalent — twenty-eight — through the table's own command on the real inputs. None moved a row of `table/table.tsv` or of `table/divergences.tsv`. One moved two counts of `table/cases.tsv` in C1, the verdict FAIL either way; the counts as the table has them were right by a recomputation apart from the tool. The changes and their runs are in the author's records: **the author's statement**.

## «Made once»

Claim 6. The table in `table/` was made once, by the tool's bytes as this folder carries them, after the first of the four checks had returned and before the second (`comparison/SECOND-PARTY-CHECK.md:23`). It was not the first time the tool read a build's return: earlier bytes of the tool had read both returns for their form and for their sameness to their own offline re-runs; and once, in a check of the tool, a table of build-a1's return was made and removed unread.

## The limits the stamp names

Claim 18. Each stamp is on the tool's bytes within limits it states: how a stream's count of what it took is read; how far the probe of a stream's encoding reaches — a finite set; and the descriptor a caller supplies for standard output, taken at its word, so that a run can be made to overwrite its own completed outputs. The last check's own sentence is quoted whole in `comparison/SECOND-PARTY-CHECK.md:29`.

## The review's reach

One review, one round: a separate AI review using Grok — one session of an AI model, not a review by a person or an organisation. The product was Grok Build, xAI's terminal agent — by its own version line `grok 1.0.77 (50ca579fa996) [stable]` —; the model, as the product displayed it, `grok-4-7` at the setting `xhigh`, reached through its vendor's API. Asked for its model id and its training cutoff, the model answered «Grok (xAI); no training cutoff is stated in this session.»: it names no id and states no cutoff — a limit. The review's own file names none of these: the product, the version, the model and the setting displayed, and that answer, were read from the session by the author — **the author's statement**. By its own account (`review/REVIEW.md:7-9`, `:29`, `:227`) it used no search and no network, and ran on Python 3.9.6 and LibreSSL 3.3.6, without `openpyxl` and without `pdftotext` and `pdfinfo`: it read the text's PDF through its local PDF reader's text extraction and, for the formula pages, as rendered images. It did not read `comparison/test_compare.py`, the envelope's files beyond their count and one line of the spec, `manifest/manifest.py`, the bundle's two tools or build-a1's `calculate.py`; it read `comparison/compare.py` at its lines 1 to 160 and 1280 to 1398. It did not run `bands.py` or `manifest.py`, any git command or any fetch.

So some figures were not recomputed by it and rest on the author's runs of `preregistration/tools/bands.py`: C1's five exact roots at 0.999, 0.938, 0.985, 0.998 and 0.986 of their bands; the second workbook's RCS, its exact root against its cached value — +8.599289e-06 of a band of 8.6e-06 (B1) and +7.307365e-06 of 7.4e-06 (B2); and with them the sheet-solved half of claims 22, 24, 26 and 27. A reader with `openpyxl` runs the command claim 22 gives. The log's count of the word «decimal» in the text was not counted by the review either; the attribution to G.1.2 rests on the absence of a stated rounding, which the review read.

What it held by its own runs: the 92 files it was given, each at its sha256; the four pins; the tool and the reference at their sha256; the table made again byte for byte; the reference's run made again byte for byte; the first three lists' files at their sha256; each token's time and imprint.

What it was given held the publisher's four files, for the review alone; this repository holds none of them (claim 2). Its session, as the author set it: Grok Build ran in its `strict` sandbox with web search, fetch and cross-session memory switched off, from a configuration folder made new for the session. By its vendor's own account that sandbox does not block a child process's network on the machine it ran on: «no network» rests on the prompt, which forbade it, and on the review's own line. Nothing but the prompt confined its reading to the folder it was given, which stood apart from the author's other files, or its writing to the one file it returned; after the session the 92 files were at their sha256 and the review was the one file added. This paragraph is **the author's statement**.

## Each run's refused and failed requests

No claim stated them; the review found them in the egress logs, and the dispositions accept the finding. build-a1: 42 requests, 40 allowed and 2 refused, both in the run at 19:34:15 UTC — a WebSocket upgrade, which the envelope refuses so that every request crosses as HTTP, and a path outside the route; and, the author's own addition, ten responses of status 403 before the run began — the sign-in's polls before its approval. build-b1: 83 requests, all allowed, one host; eight responses of status 400, each to a request ending `countTokens`. None voids a run: a refused request reached nothing (`preregistration/PREREGISTRATION.md:100`). *Evidence:* `builds/build-a1/egress/egress.jsonl` and `builds/build-b1/egress/egress.jsonl` — a reader counts the logs' lines.

## The display rounding

The log's «1.18 of the band» for `rc_corp`, under the rounded durations with the construction, is 1.17 on the three-digit parts the log shows. The log's ratios are computed before its figures are rounded: 1.1751 on the fuller parts, 1.1736 on the parts shown; outside the band either way. Two more display points of the same kind are in the dispositions' row F7.

## Builder B's bill against its count

Claim 28 and `effort.md`. The egress priced each of build-b1's 75 answers by its own use at the vendor's rates: $5.119680 before tax, under a cap of $55 a run. The vendor's bill for the day of the run was NOK 95.02 with tax — near 1.6 times that count. The cause of the gap was not read: a limit. The count is what the folder shows; the bill is **the author's statement**.

## The image

Claim 11. Both builders ran on one image, identified by its id and not rebuilt. Its Debian packages were installed without pinned versions: an image built again from the folder's files would carry the packages of its own day — a limit. The launch prints of the two runs are in the runs' archives, not in the folder.

## Noted from the review

What the dispositions mark NOTED and no section above carries — none changes a status or a claim's substance:

- The table and the reference's run were made again byte for byte on Python 3.9.6, an earlier version than the claims named when the review read them.
- A candidate divergence named before any build did not arise: the weights (`preregistration/PREREGISTRATION.md:78`) — both builders take the column labelled «Other Assets» as the corporate one, normalised with government; C1's weights are 0 apart.
- build-b1 returned no notes: its reading of the durations, and its not applying G.5.3 a second time, are shown by its code alone.
- The third workbook's sixth bucket, which the second workbook's blocks do not have, lies an ulp from its fifth — −4.9e-17 to +4.2e-17 —, below every band.
- The builders' training cutoffs are their vendors' own statements as the preregistration records them (§7), checked by no one else.

## `verify.sh` — what it does, and what it rests on

`verify.sh` is one file and uses the standard library alone. Where the preregistration's §12 leaves the manner open, it does this:

- **The digests.** It makes each digest of the manifest again with a reader of its own, from the workbooks' own XML, and holds each by its cell count and its sha256 against `manifest/MANIFEST.md` — 66 rows of 66, none left out — and not with `manifest/manifest.py`, which needs `openpyxl`. The frozen tool's own run: `python3 -I 01-eiopa-rfr-2026/manifest/manifest.py <files>`. That the digests come out equal holds that reader — its reading of dates among the rest — on these files, and no further.
- **The four files.** It finds each in the folder given by its sha256, whatever its name; one it does not find it fetches — the publisher's address first, then the snapshot — and keeps there. A file it cannot have is said, the steps that need it are marked `NOT RUN`, the other steps run, and the exit is not clean.
- **The folder's manifest.** A tracked file of the folder that `MANIFEST.sha256` does not name is a failure; a file that is not tracked is named and fails nothing.
- **The tokens.** Each is checked with the certificates the token itself carries and the folder's root as the only trust anchor (claim 4), at the reader's clock; that time is printed, with the token's own. A check made after the responder's certificate has run out will fail by that certificate; the token's time and its imprint — its list's sha256 — can still be read.
- **The outcome.** §8's rule over the returned rows of `table/cases.tsv` and the statuses — twelve case rows and five statuses: a reader can make it again by eye.

It carries its author's controls alone — planted failures, each caught as expected, «controls: 34 of 34 as expected», kept with the author — and no second party's check; the preregistration asks one of the comparison tool. Two things no control could show before the fifth commit existed: a clean exit, which needs the fifth token, and a fetch that succeeds, which needs a machine that reaches the publisher's addresses. A reader's own run shows both. `verify.sh` does not run the builders again, and it cannot judge an attribution's grounds: the reader does.

## Where the fifth commit reads the frozen text

Nothing is changed in the brief, the bands, the cases, the attribution rule or the stop rule. Named above, each in its place: the digests made by a reader of `verify.sh`'s own, within §12's «standard library only»; the tokens verified with their own certificates (claim 4); the statuses after the review carried by `dispositions/statuses.tsv`, the log left as frozen; and the tests' checks ended by the author's decision, where the preregistration asks a check of the tool alone.
