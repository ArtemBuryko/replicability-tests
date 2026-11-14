RT01 · the independent review · return · FILES.sha256: 30e77a1b4f0b56c7b323f528cf8471145851dfd5219256d0265f737631e82917

# Independent review — replicability test 01, after the third commit

## 1. What was read and run

No search ran. No network access ran: no web search, no fetch, no download, no package install, and no command that opens a connection. Timestamp checks, hash checks, the table made again, and the reference run used only files in this folder and the system's temporary directory. Outside knowledge is marked where it is used.

Python on this machine is 3.9.6 (`python3 --version`). `python3.10` through `python3.14` are absent. `openpyxl` is absent (`ModuleNotFoundError`). `pdftotext` and `pdfinfo` are absent. `openssl version` prints `LibreSSL 3.3.6`. `shasum -a 256` was used where `CLAIMS.md` writes `sha256sum`.

### Files read whole

`PROMPT.md`, `README.md`, `CLAIMS.md`, `01-eiopa-rfr-2026/divergences.md`, `01-eiopa-rfr-2026/divergences/variants.py`, `01-eiopa-rfr-2026/divergences/variants.out`, `01-eiopa-rfr-2026/table/cases.tsv`, `01-eiopa-rfr-2026/table/divergences.tsv`, `01-eiopa-rfr-2026/preregistration/PREREGISTRATION.md`, `01-eiopa-rfr-2026/preregistration/brief.md`, `01-eiopa-rfr-2026/comparison/SECOND-PARTY-CHECK.md`, `01-eiopa-rfr-2026/source/README.md`, `01-eiopa-rfr-2026/timestamps/i.list`, `01-eiopa-rfr-2026/timestamps/ii.list`, `01-eiopa-rfr-2026/timestamps/iii.list`, `01-eiopa-rfr-2026/builds/build-a1/work/return/NOTES.md`, `01-eiopa-rfr-2026/builds/build-a1/work/return/run.sh`, `01-eiopa-rfr-2026/builds/build-b1/work/return/run.sh`, `01-eiopa-rfr-2026/builds/build-a1/run-build-a1.sha256`, `01-eiopa-rfr-2026/builds/build-b1/run-build-b1.sha256`, `bundle/E3/reference-portfolio-weights.tsv`, `bundle/E2/reference-portfolio-weights.tsv`.

### Files read in part

- `01-eiopa-rfr-2026/comparison/compare.py:1-160` and `:1280-1398`. The rest of its 1,398 lines was not read line by line. `ast.parse` of the whole file succeeded on Python 3.9.6; the source contains neither a `match` statement nor a walrus operator.
- `01-eiopa-rfr-2026/preregistration/tools/bands.py:1-40`.
- `01-eiopa-rfr-2026/manifest/MANIFEST.md:1-40`, plus the role of the file as the frozen range list.
- `01-eiopa-rfr-2026/preregistration/envelope/SPEC.md:174-176`. The file has 177 lines. The image-id string occurs once.
- `01-eiopa-rfr-2026/builds/build-a1/work/return/portfolios.py:190-246`.
- `01-eiopa-rfr-2026/builds/build-b1/work/return/calculate.py:1-30`, `:370-408`, `:490-571`, `:620-706`.
- `01-eiopa-rfr-2026/table/table.tsv:1-12`, then every data row aggregated by a local script (1,684 data rows). The script did not print official values.
- `01-eiopa-rfr-2026/builds/build-a1/egress/egress.jsonl` and `01-eiopa-rfr-2026/builds/build-b1/egress/egress.jsonl`, parsed by a local script for hosts, verdicts, models, tools, statuses and the spend fields. Neither log was read as prose line by line.
- `01-eiopa-rfr-2026/isolated/build-a1.json` and `01-eiopa-rfr-2026/isolated/build-b1.json`, compared by a local script with the matching returned `outputs.json`.
- `01-eiopa-rfr-2026/timestamps/chain/DigiCert_Trusted_Root_G4.pem:1-5`, then its subject and issuer by `openssl x509`.
- Workbook sheets, through the xlsx as ZIP and XML, not through `openpyxl`: E3 `Corp Data`, E3 `S&RC Corp Currency`, E2 `Corp Data`, E2 and E3 `Reference Portfolio Weights`, and `docProps/core.xml` of E1, E2 and E3 for the presence and length of creator fields. No person's name from that metadata was printed. No input value of E1 was printed.
- `bundle/E3/corp-data.tsv` and `bundle/E2/corp-data.tsv` for the high-yield labels and the spelling of those yields; `bundle/E3/rfr.tsv` for the two risk-free curves used in a local G.5.3 probe.
- `text/T.pdf`, by the local PDF reader's text extraction: pages 39–41, 80–91, and, in the same reading of the file, the remaining prose pages through page 115. Pages 41, 87 and 89–91 were also read as rendered images in the earlier part of this review. Formula glyphs in Annex D and in G.5.3 come out doubled or dropped in the text layer. The prose paragraph numbers used below were readable. A separate local inflate of the PDF streams, and a local ToUnicode decode of content streams, did not recover a reliable word count; that probe is not used as a count of any word in the text.

### Files not read

`01-eiopa-rfr-2026/comparison/test_compare.py` (5,797 lines) was not read. The envelope's other scripts — `compose.yaml`, `allowlist.py`, `entry.sh`, `run.sh`, `builder.Dockerfile`, and the CLI configuration files — were not read beyond the file count (17 files under `01-eiopa-rfr-2026/preregistration/envelope/`) and `SPEC.md:176`. `manifest/manifest.py`, `preregistration/tools/bundle.py` and `bundle_check.py` were not read. `01-eiopa-rfr-2026/builds/build-a1/work/return/calculate.py` was not read. `verify.sh` is not in this folder. The run archives named by `run-build-a1.sha256` and `run-build-b1.sha256` are not in this folder. The second-party return documents named by sha256 in `comparison/SECOND-PARTY-CHECK.md:11-16` are not in this folder.

### Commands run, and what they printed

1. `shasum -a 256 -c FILES.sha256` — exit 0. 92 lines, each ending `OK`.
2. `python3 --version` — `Python 3.9.6`. `python3 -c "import openpyxl"` — `ModuleNotFoundError: No module named 'openpyxl'`.
3. `shasum -a 256 text/T.pdf workbooks/E1.xlsm workbooks/E2.xlsm workbooks/E3.xlsm` printed the four digests at `01-eiopa-rfr-2026/source/README.md:7-10`: `4d3f5e0a…be53`, `c1ce32a3…dc4`, `5302c91b…e07`, `67bf3478…b81`.
4. `shasum -a 256 01-eiopa-rfr-2026/comparison/compare.py` printed `d36b8649aadaff8958e0baff6164e5717f401e6c68b55144a2a92fe3c9d8f498`. `shasum -a 256 01-eiopa-rfr-2026/divergences/variants.py` printed `b56396c2a4e055d894a923d33ea46fc901d105715527c18f14324069e456f71f`.
5. `grep -c -v '^#' 01-eiopa-rfr-2026/table/table.tsv` printed `1685`.
6. For each of `i`, `ii` and `iii`, the command `CLAIMS.md` writes — `openssl ts -verify -in 01-eiopa-rfr-2026/timestamps/<n>.tsr -data 01-eiopa-rfr-2026/timestamps/<n>.list -CAfile 01-eiopa-rfr-2026/timestamps/chain/DigiCert_Trusted_Root_G4.pem` — printed `Verification: FAILED` and `unable to get local issuer certificate`, exit 1.
7. `openssl ts -reply -in 01-eiopa-rfr-2026/timestamps/<n>.tsr -text` printed `Status: Granted.` and `Time stamp: Nov  1 08:15:16 2026 GMT`, `Nov  1 22:00:21 2026 GMT`, and `Nov 13 21:24:03 2026 GMT`. The message imprint of each token is the sha256 of that token's list: `cf11b988…70fa`, `70207baf…5429`, `f77fb1d0…d08a`.
8. A further local check, not the command `CLAIMS.md` writes: the intermediate and cross-certificate embedded in each token were extracted under the system's temporary directory and passed with `-untrusted`, the chain file remaining the `-CAfile`. Each of the three then printed `Verification: OK`, exit 0. The chain directory holds only `DigiCert_Trusted_Root_G4.pem`. Its subject and issuer are both DigiCert Trusted Root G4. Each token's signer is DigiCert SHA256 RSA4096 Timestamp Responder 2026 1, issued by DigiCert Trusted G4 TimeStamping RSA4096 SHA256 2025 CA1, which is issued by DigiCert Trusted Root G4. A cross-certificate of that root, issued by DigiCert Assured ID Root CA, is also embedded. This is a fact about LibreSSL 3.3.6 on this machine: it does not walk the certificates embedded in the token unless they are passed in. It is not a fact about another OpenSSL build.
9. `tail -n +2 01-eiopa-rfr-2026/timestamps/<n>.list | awk '{print $2"  "$3}' | shasum -a 256 -c` — exit 0 for each list. 27, 41 and 54 lines, each `OK`.
10. `python3 -I -B 01-eiopa-rfr-2026/divergences/variants.py bundle 01-eiopa-rfr-2026/builds/build-a1/work/return/outputs.json 01-eiopa-rfr-2026/builds/build-b1/work/return/outputs.json | cmp - 01-eiopa-rfr-2026/divergences/variants.out` — printed nothing, exit 0. The two streams are the same bytes (3,939 bytes).
11. `python3 -I 01-eiopa-rfr-2026/preregistration/tools/bands.py workbooks/E2.xlsm workbooks/E3.xlsm` — `ModuleNotFoundError: No module named 'openpyxl'`, exit 1. Not installed. The residual magnitudes in `divergences.md:23` and `:54` were not recomputed.
12. The table command of `CLAIMS.md`, with the output folder under `mktemp -d` (`/var/folders/vh/kkcgwtvj07gdtvqgv4v50ln00000gq/T/tmp.iuftXzFWYz/table`), on Python 3.9.6:

    `cd 01-eiopa-rfr-2026 && python3 -I -B comparison/compare.py table ../workbooks manifest/MANIFEST.md <temp> --build build-a1 builds/build-a1/work/return/outputs.json --build build-b1 builds/build-b1/work/return/outputs.json --isolated build-a1 isolated/build-a1.json --isolated build-b1 isolated/build-b1.json`

    Exit 0. It printed the sixteen case lines of `table/cases.tsv:13-28`, then three sha256 lines: `table.tsv` `63f7fdbb…c5b0` (1,696 lines, 174,592 bytes), `cases.tsv` `2befdcf4…2925` (28 lines, 2,270 bytes), `divergences.tsv` `33d965c0…cd98` (17 lines, 2,370 bytes). `cmp` of each against `01-eiopa-rfr-2026/table/` printed each file identical.

13. Local scripts, writing only to the terminal or to the system's temporary directory, aggregated `table.tsv`, parsed both egress logs, read the workbook XML named above, compared isolated and returned JSON, recomputed the additions in `divergences.md:36-41` from the figures that file states, and applied G.5.3 at the four index durations using `bundle/E3/rfr.tsv`. Their results are cited in §§2–6 where they are grounds.

### Commands not run

- `bands.py` did not run, for the reason in item 11. No residual magnitude from that tool is reported here as recomputed.
- `verify.sh` is not in this folder. The outcome by §8 is not computed here.
- No git command was run. Commit ids, parents and dates were not inspected.
- The publisher URLs and the Wayback snapshots were not fetched.
- `manifest.py` was not re-run. The table command already held the seventeen ranges to the manifest's digests (`table/table.tsv:5`).

## 2. R1

D1 · build-a1 · s_corp · DOES NOT HOLD
D2 · build-a1 · rc_corp · DOES NOT HOLD
D3 · build-a1 · s · DOES NOT HOLD
D4 · build-a1 · rc · DOES NOT HOLD
D5 · build-b1 · rcs · HOLDS WITH QUALIFICATION

The five rows of `table/divergences.tsv:13-17` are the five rows of `divergences.md:9-13`. All five are returned C1 outputs on the corporate portfolio. No isolated row fails. The cells, bands, values and differences in the log match the table.

### D1 to D4 — the status B does not hold

The numerical account holds. The status letter does not, on the rule the log itself cites.

`divergences.md:43-49` attributes the four to the builder. The code does what the log says it does. `builds/build-a1/work/return/portfolios.py:209-212` puts a GBP or USD yield of credit quality step 4 or higher through G.5.3 with the bundle's two risk-free curves, and the comment there treats the supplied high-yield blocks as euro proxies. `NOTES.md:81-87` records the same choice, names the other reading, and says the chosen reading lets the construction be performed from the inputs. `NOTES.md:91` records that index durations are not rounded. `variants.out:14` shows build-a1 equal to the as-supplied-plus-proxy reading to about 1e-17. `variants.out:16` shows build-b1 equal to the as-supplied reading to about 1e-16. `variants.out:22` shows the proxy step moving `s_corp`, `rc_corp`, `s` and `rc` by +5.390e-05, +2.611e-05, +4.121e-05 and +1.996e-05.

Adding the parts `divergences.md:23` states to the parts `variants.out:21-22` states reproduces the log's signed differences to the three digits the log prints, with two display points. For `rc_corp`, sheet + (2 − 1) is 9.26e-05 on the three-digit parts, and the log prints 9.27e-05. For `rcs`, the same addition is −2.708e-05, and the table's magnitude is 2.70e-05. The log's fractions without the proxy step — 0.72, 0.84, 0.71 and 0.90 of the four bands — match those parts. With the step, the four are 1.39, 1.08, 1.37 and 1.15 of their bands, which matches `divergences.tsv:13-16`. With the sheet's rounding and the step together, the log's 1.67, 1.65 and 1.25 match sheet + proxy. The log's 1.18 for `rc_corp` on that path is 1.17 when the same three-digit parts are divided (1.1736). That is a display rounding. It does not change which side of the band the output is on. `s` and `rc` are the weighted sums of ¶9.2.5 and ¶9.2.6 (text, page 41). Their failures are the corporate term's, times the corporate weight. That mechanism holds.

The status does not. §6, as the log applies it at `divergences.md:49` by the candidate at `PREREGISTRATION.md:78`, is B where the text's definition, read against the bundle's labels, singles the reading out, and T where it does not. The log's chosen reading is that the heading and the label together say the rows are already constructed yields in pounds, so the code applies G.5.3 a second time. The other reading the log names is that the labels leave the mapping open, in which case the status is T by the same rule.

The files support the other reading, and they add a fact the log does not measure.

G.5.5 (text, page 91) sources GBP and USD corporate market yields from Tables 13 and 14, and constructs a missing type under G.5.3. A missing type is an entry in the first column of Table 12 that is absent from Table 13 or Table 14. Tables 13 and 14 stop at credit quality step 3. Steps 4 to 6 are missing. G.5.3 (text, pages 89–90) builds the missing yield from the euro corporate yield of the type, the local risk-free yield and the euro risk-free yield, with κ = 0.5, and floors it at the local risk-free yield. On the method, that construction is what the text requires for a missing type. The open question is what the supplied rows are: the euro corporate yield the formula takes, or the constructed pound yield the formula returns.

The labels do not close that question.

- `Corp Data`!F8 in workbook E3, and the same cell in `bundle/E3/corp-data.tsv`, is the heading "GBP Corporate Bonds". That heading can be read as saying the block is already in pounds.
- `Corp Data`!R20 and `Corp Data`!R41, beside Financials CQS 4 and 5 and beside Non-Financials CQS 4 and 5, say "Derived with the k-factor approach". That phrase can be read as saying a derivation has been done. The phrase does not occur in the text. κ of G.5.3 is the one factor the text names. The label does not say whether the derivation is still to be applied or has already been applied.
- The workbook uses the rows as stored. On `S&RC Corp Currency`, O19 and O21 take `Corp Data`!L44, P19 and P21 take `Corp Data`!P44, and O22 and P22 equal O21 and P21. Rows 18 and 20 round durations. There is no G.5.3 formula on that sheet. The builders did not see the workbook (`PREREGISTRATION.md:39`). What the sheet does is the publisher's implementation. It is not, by itself, the text's mapping of the label.
- The rows have the form of an index: one duration and one yield, repeated across the maturity buckets. Table 12 (text, page 90) says the CQS 4 and CQS 5 indices do not discriminate by duration and are used irrespective of duration, by the flat extrapolation of G.1.2. A G.5.3 result, applied to one euro yield at successive maturities, moves with the maturity. A local probe on `bundle/E3/rfr.tsv` at integer maturities 1, 5, 10 and 15, treating each supplied yield as the euro corporate yield, spans about 1.1e-2 across those maturities. At the index duration itself the constructed yield differs from the supplied yield by about 8e-4 (Non-Financials CQS 4) to 8e-3 (Non-Financials CQS 5). The repeated rows therefore do not have the numerical form of a G.5.3 result evaluated across buckets. They have the form Table 12 assigns to these steps. That form is also the form of a flat fill of an already constructed yield. Form alone does not decide.
- The yields equal the euro index. In workbook E2, `Corp Data`!F8 is "EUR Corporate Bonds". Its Financials CQS 4 and CQS 5 yields (L22:L26 and P22:P26) and its Non-Financials CQS 4 and CQS 5 yields (L41:L45 and P41:P45) have the same spelling as E3's corresponding buckets (L23:L27, P23:P27, L44:L48, P44:P48). E3's last bucket, labelled 15+, differs in spelling by about 1e-17 to 5e-17. That gap is far below every band and does not change a flat interpolation. The same identity is in the bundle files the builders read. A yield already constructed in pounds under G.5.3 would not equal the euro index yield. These do. That is the strongest ground the files add, and `divergences.md:46` does not state it as a measured identity. It states the form and the foreign term. The identity is what makes the "already constructed" reading fail to single itself out.

A recorded choice is not evidence that the text is open, and it is not evidence that the text is closed (`PREREGISTRATION.md:71`). The build recorded a choice (`NOTES.md:86-87`). The rule the log cites then turns on the labels. The heading can be read one way. The phrase, whose term is not the text's, can be read either way. The numbers are the euro index's numbers, under a pound heading, beside a phrase the text does not use. That does not single the reading out. By the rule at `divergences.md:49`, the status is T.

D3 and D4 are the same step, carried by the corporate weight (`divergences.md:48`; ¶9.2.5 and ¶9.2.6). They do not become B because they are downstream of D1 and D2. If the upstream status is T, these two are T as well. The log's letter P is not used, and the isolation re-run does not apply: these are not A2 or A3 outputs (`PREREGISTRATION.md:72`).

An unnamed reading would call the four O: the text requires the construction for a missing type, the rows are the euro observations, and the workbook applies another rule by using them as stored. That reading fails the precedence at `PREREGISTRATION.md:66`. Where the text, read against the labels, allows more than one reading at the point, the divergence is T, whatever the workbook does. The workbook's use of the rows as stored is recorded above. It does not take the status from T to O, and it does not restore B.

What would change the letter back to B is a label, in the text or in the bundle, that says these rows are the constructed pound yields and not the euro observations. The folder does not contain that label.

### D5 — the status T holds

`divergences.md:51-57` attributes build-b1's `rcs` to the text, passage G.1.2. That attribution holds.

G.1.2 (text, page 87) rounds durations of model bonds to one decimal, and takes a model bond's yield by linear interpolation inside the available maturities and by flat extrapolation outside them. G.1.1 says yield curves and yield indices are available for a limited list of maturities or of buckets. E.6.10 (text, page 83) rounds final durations to one decimal. That sentence sits with the durations of portfolios, not with an index's published duration. Neither passage states a rounding of an index's duration before interpolation. The log's count of the word "decimal" — twice, both for portfolios and model bonds (`divergences.md:53`) — was not independently counted. The local stream decode did not recover a reliable count, and `pdftotext` is absent. The attribution does not need that count. It needs the absence of a stated rounding for an index duration, which the cited passages show.

The two readings the log names are both open on those passages: the index stands at the duration the input gives, or that duration is rounded to one decimal as a model bond's is. `builds/build-b1/work/return/calculate.py:387-397` interpolates at the query abscissa as supplied. `:509-525` reads the duration and the yield as stored. `:636-644` interpolates the corporate curve at the stored duration and applies no G.5.3 step. build-a1 records the same duration reading (`NOTES.md:91`). build-b1 returned no notes. Its reading is the code.

The sheet does the other reading. On E3 `S&RC Corp Currency`, rows 18 and 20 are `ROUND` of the `Corp Data` durations to one decimal; rows 19 and 21 take the yields as stored; row 22 takes the row above. E2's cached outputs agree with the unrounded reading to the extent this folder can show without `bands.py`: `variants.out:24-37` shows both builds equal to as-supplied for B1 and B2 to about 1e-16, and the rounded reading about 1e-5 to 3.6e-5 away. In `table.tsv`, every returned B1 and B2 output passes, and the largest displayed difference among them is 2.59e-07 (B2 `rc_corp`). The log's "up to a whole band" for E2's exact sheet (`divergences.md:54`, bands 8.6e-06 and 7.4e-06) was not recomputed.

Under the unrounded reading, `table/divergences.tsv:17` shows build-b1's `rcs` at a difference of 2.70e-05, against a band of 1.8e-05, 1.50 of the band. `variants.out:16-17` matches: the rounded reading is 9.279e-06 closer, about 0.52 of the band. The log says the rest is the cached rate's distance from the exact root of the sheet's own equation, 0.986 of the band, and that this distance is the oracle's own, named and banded before any build (`divergences.md:56-57`; `PREREGISTRATION.md:58`). Those residual magnitudes were not recomputed here. The direction and the reading's own effect are in `variants.out` and in the table, and do not depend on `bands.py`.

§6's precedence (`PREREGISTRATION.md:66`) is that where the text is silent or allows more than one reading, the divergence is T, whatever the workbook does. The text is silent on rounding an index duration. T holds even if a later run of `bands.py` moved the residual share.

An unnamed reading would call this O: G.1.2 states a rule only for model bonds, the builder followed that rule, and the workbook rounds an index duration the text does not tell it to round, so the oracle is what departs. That reading is the one §6's precedence closes. Silence at the point is T, whatever the workbook does. A second unnamed reading would take a bucket index at its bucket, and would not interpolate an index duration at all. G.1.1 and Tables 12 and 13 leave the abscissa of a bucket index unstated. That reading is also open. It does not displace T.

The qualification is the unrecomputed residual share, and those two unnamed readings. Neither changes the letter.

## 3. R2

A1 · build-a1 · as returned · FOLLOWS
A2 · build-a1 · as returned · FOLLOWS
A3 · build-a1 · as returned · FOLLOWS
B1 · build-a1 · as returned · FOLLOWS
B2 · build-a1 · as returned · FOLLOWS
C1 · build-a1 · as returned · FOLLOWS
A2 · build-a1 · isolated · FOLLOWS
A3 · build-a1 · isolated · FOLLOWS
A1 · build-b1 · as returned · FOLLOWS
A2 · build-b1 · as returned · FOLLOWS
A3 · build-b1 · as returned · FOLLOWS
B1 · build-b1 · as returned · FOLLOWS
B2 · build-b1 · as returned · FOLLOWS
C1 · build-b1 · as returned · FOLLOWS
A2 · build-b1 · isolated · FOLLOWS
A3 · build-b1 · isolated · FOLLOWS
§8 · SOUND WITH QUALIFICATION

§5 (`PREREGISTRATION.md:53`) says a case passes for a builder when every one of its declared outputs passes. `compare.py:1307-1314` counts failures in that case's rows and writes PASS when the count is zero. A local aggregation of `table.tsv` produced the same sixteen counts as `cases.tsv:13-28`: 201, 153, 154, 9, 9 and 9 outputs, the isolated rows 153 and 154, build-a1's returned C1 failing 4 of 9, build-b1's returned C1 failing 1 of 9, and every other case row failing none. The regenerated table was byte-identical, so those verdicts are the tool's on these bytes. Each case row follows.

The §8 reading in the assignment — A1, A2, A3, B1 and B2 reproduced, C1 not, provisional until the dispositions — is sound on the pass and fail, and qualified on the cause.

`PREREGISTRATION.md:95` defines reproduced as both builders passing, and not reproduced — the text as a divergence attributed to a passage. Both builds pass A1, A2, A3, B1 and B2, as returned. Both pass A2 and A3 isolated. No divergence exists for those cases, so no T, O, C, B, P or U is there to apply. They are reproduced on the table. C1 fails for both builds. D5 is T on G.1.2, and that one T is enough for "not reproduced — the text" under §8, whatever letter D1 to D4 carry. The outcome itself is not computed here: `verify.sh` arrives in the fifth commit (`PREREGISTRATION.md:109`) and is not in this folder.

The qualification is claim 25's split of causes, which is the prose the log offers for that provisional reading (`divergences.md:9-13`; `CLAIMS.md:91`). If the dispositions keep D1 to D4 as B, build-a1's four are other causes and build-b1's `rcs` is the text. If the dispositions follow the rule the log cites, and change D1 to D4 to T, then build-a1's four are also the text, on G.5.3 and G.5.5, and "other causes" does not describe them. C1 remains not reproduced either way. The pass and fail reading does not depend on that letter. The cause sentence does.

## 4. R3

C1 · SUPPORTED
C2 · SUPPORTED
C3 · SUPPORTED
C4 · OVERSTATED
C5 · SUPPORTED
C6 · SUPPORTED
C7 · SUPPORTED
C8 · OVERSTATED
C9 · OVERSTATED
C10 · OVERSTATED
C11 · SUPPORTED
C12 · SUPPORTED
C13 · SUPPORTED
C14 · SUPPORTED
C15 · SUPPORTED
C16 · SUPPORTED
C17 · SUPPORTED
C18 · SUPPORTED
C19 · SUPPORTED
C20 · SUPPORTED
C21 · SUPPORTED
C22 · SUPPORTED
C23 · OVERSTATED
C24 · SUPPORTED
C25 · OVERSTATED
C26 · SUPPORTED
C27 · SUPPORTED
C28 · OVERSTATED
C29 · SUPPORTED
C30 · SUPPORTED
C31 · SUPPORTED

### Claims that are not supported

**C4.** The times, the imprints and the list checks hold. The command cited as printing `Verification: OK` does not print that on this machine. Each of the three tokens, verified as `CLAIMS.md:21` writes the command, printed `Verification: FAILED` and `unable to get local issuer certificate`. The chain file is the root alone. With the token's own embedded intermediate passed as `-untrusted`, each printed `Verification: OK`. The reply times match the claim: 2026-11-01 08:15:16 GMT, 2026-11-01 22:00:21 GMT, 2026-11-13 21:24:03 GMT. Each imprint equals the sha256 of its list. The list check found 27, 41 and 54 files at their sha256. The claim that a token dates bytes, not acts, is the preregistration's own sentence (`PREREGISTRATION.md:110`). The overstatement is the cited verify command, written as if it prints OK against the chain file alone. On LibreSSL 3.3.6 it does not. The commits' ids, parents and dates are marked as the author's statement. Nothing in the folder contradicts them. This review did not inspect a git history. To be shown, they need that history.

**C8.** The file counts hold: build-a1's return has five files, build-b1's has three, and the two `run-*.sha256` files name archives that are not in this folder (`bfe005f1…` and `a1de8796…`). The claim then states, as fact, that build-a1 ended by its CLI's own end and that build-b1 ended by the builder with its code changed after its outputs were written. The consoles and full logs that would show those endings stay out of the repository (`PREREGISTRATION.md:111`), and the claim marks their reading as the author's statement. The file counts do not show an ending, and they do not show that code changed after outputs. Nothing in the folder contradicts the author's statement. The wording states the endings as what the folder shows. To be shown, they need the archives' consoles and the record of when build-b1's code was written relative to its outputs.

**C9.** `timestamps/ii.list` pins the build files at their sha256 under the second token, and claim 4's list check found those files at those digests. That is what the token verifies. The sentence "a builder run again would write other code" is a counterfactual. `ii.list` does not show it. `PREREGISTRATION.md:121` says `verify.sh` does not re-run the builders, and that a builder run again writes other code. That is the preregistration's statement of a limit, not evidence from the second token. The claim's evidence line cites only `ii.list` and claim 4. To be shown as more than that limit, it would need a second run, which the preregistration does not provide (`PREREGISTRATION.md:103`).

**C10.** The isolated files exist, and `PREREGISTRATION.md:72` describes the isolation re-run. The claim states that in an offline re-run build-a1's outputs came out equal to its return byte for byte, and build-b1's within 1.8e-16. The isolated JSON files are A2 and A3 only. They do not contain that equality, and they do not contain 1.8e-16. A local comparison of isolated A2 and A3 with the returned A2 and A3 found the scalars `notional_va`, `cssr`, `currency_va`, `omega_co` and `total_va` equal, and the curves differing by up to about 4.83e-06. That comparison is the official-A1 re-run against the builder's own A1, which is a different comparison from a re-run of each build against its own returned outputs. The claim marks the re-run as the author's statement. Nothing in the folder contradicts it. The wording states the equality as fact, and the evidence line points at files that do not show it. To be shown, it needs the offline re-run's record: a comparison of each build's re-run outputs with its returned `outputs.json`, with the 1.8e-16 figure in that record.

**C23.** The mechanism holds, as §2 says for D1 to D4. The status B does not hold on the rule the claim and the log cite. The four are outside their bands because of the extra G.5.3 step (`portfolios.py:209-212`; `variants.out:14` and `:22`). Without that step they lie inside, on the parts the log states. The labels do not single that step out as a second application, for the grounds in §2. By the rule at `divergences.md:49`, the status is T. The claim states B.

**C25.** The pass and fail half holds: A1, A2, A3, B1 and B2 pass for both builds, and C1 fails for both (`cases.tsv:13-28`). C1 is not reproduced, because D5 is T. The sentence "build-a1's four of other causes" states the log's letter B as the provisional cause. That letter does not hold (§2). The claim says the statuses are the author's and may change after the review, and that the outcome is computed by `verify.sh` once the dispositions are made. Those two sentences hold as a description of the procedure (`PREREGISTRATION.md:95-96`). The overstatement is the cause split, written as what §8 gives now.

**C28.** The egress carries the count the claim marks as only the author's statement. The last `use` line of `builds/build-b1/egress/egress.jsonl` has `usd_sum` 5.119680, `answers_priced` 75, `answers_bound` 0, `answers_unread` 0 and `cap` 55. The sum of the `usd` fields on the 75 `use` lines equals 5.119680. The vendor's bill, NOK 95.02, and builder A's share of a plan are not in the folder. Those two remain the author's statement, and the claim words them as that. The count does not. To be shown, the bill needs the vendor's bill, and the plan share needs the plan's record. The count needs nothing further.

### Author's statements, including those inside claims marked supported

Nothing in the folder contradicts any of them. Each is worded as the author's statement, except where a claim above is marked overstated for stating the same fact as shown by the pack.

- **C4**, the commits' ids, parents and dates. Needs the repository history. Not inspected here.
- **C6**, the date 10 November 2026, and the earlier reads of the builds' returns, including one table of build-a1's return made and removed unread. `comparison/SECOND-PARTY-CHECK.md:23` supports, as its own sentence, that the table was made once by these bytes after the first check's return and before the second's, and that no byte of the tool has changed since the first check. It does not date that making, and it does not record the removed table. Needs the author's run log of that day.
- **C8**, the consoles and the full logs, and the reading that build-b1's code changed after its outputs. Needs those archives.
- **C10**, the offline re-run's equality and the 1.8e-16 figure. Needs that re-run's record.
- **C16**, the four return documents and the seventeen earlier checks. The folder shows the sha256 of `compare.py` matching `SECOND-PARTY-CHECK.md:7` and line 2 of each file of `table/`, and it shows the check file's account of four STAMP returns and seventeen earlier NO STAMP checks. The returns themselves are not here. Needs those documents, at the sha256 the check file names.
- **C19**, the twenty-five changes and the twenty-eight changes, and their runs on the real inputs. Nothing in the folder shows them. Needs the change list and the run records.
- **C26**, the inference that what §5 calls the Solver's residuals is, for the second workbook, the rounding's effect. The pattern the inference rests on is in the folder to the extent §5 of this review states: both builds match the unrounded reading for B1 and B2 (`variants.out:24-37`), and they reproduce those outputs to 2.59e-07 or closer. The "whole band" residual was not recomputed. The claim marks the inference as the author's statement and says the bands stand as frozen (`PREREGISTRATION.md:58`). That wording holds. The inference would be shown as a measured residual by a run of `bands.py`, which this machine could not run.
- **C28**, the bill and the plan share, as above. The count is in the egress.
- **C31**, zero hits from the leak check. The deny-list stays out by design (`PREREGISTRATION.md:111`). Needs the check's output. Nothing in the folder is a copy of a publisher input value that this review printed, and this review did not rerun the check.

C22 is supported for what this machine could rerun. `variants.out` was made again, byte for byte, and it shows build-b1 equal to the as-supplied reading to about 2.5e-16 and build-a1 equal to the proxy reading to about 1.4e-17, which is the claim's second sentence. The sheet-solved-exactly half is `divergences.md:23`, sourced from `bands.py`, which did not run here. The claim remains supported because its evidence line names that command as the source of the log's figure, and the identities that do not need the command were rerun. The limit is in §1 and in F3. It is not a contradiction of the claim.

C27 is supported on the as-supplied half by the table and by `variants.out:12-19`: build-b1's `rcs` is outside the band, so the cached rate is not the as-supplied reading's root. The rounded half — that the cached rates are not roots of the rounded equations either — is the log's residual, not recomputed. The claim's evidence is the log and `variants.out`. The log states the residual. The qualification is F3, not an unsupported claim.

C2 is supported as a claim about the test repository. `source/README.md:1-19` points and does not copy, and the four digests match the files in this review folder. This review folder does hold the copies, which `README.md:6` says are here for the review alone. That is a fact about this pack, not a failure of the claim about the test repository. It is recorded in §5.

## 5. R4

What the folder shows, bearing on the outcome or on what the test can claim, that no claim states:

- The cited timestamp command fails on this machine's LibreSSL unless the token's embedded intermediate is passed as `-untrusted`. Verification then succeeds. The chain file is the root alone. Claim 4 writes the command as printing OK.
- `bands.py` could not be run. The residual magnitudes in the log, including "exact root departs by a whole band" for E2 and the 0.986 share for C1's `rcs`, are not recomputed. The reading's own effect on C1's `rcs`, about 0.52 of the band, is in `variants.out` and does not need that tool.
- Python here is 3.9.6, not 3.10 or later. `compare.py` and `variants.py` ran on 3.9.6 and reproduced their outputs byte for byte. The preregistration's stated requirement of 3.10 was not what this review ran.
- `pdftotext` and `pdfinfo` are absent. The formula glyphs in the PDF text layer are corrupted. The prose of G.1.2, E.6.10, G.5.3, G.5.5 and ¶9.2.5 to ¶9.2.7 was read from the local PDF text extraction and, for the formula pages, from rendered images. The log's count of the word "decimal" was not independently counted.
- E3's CQS 4 and CQS 5 yields equal E2's euro CQS 4 and CQS 5 yields, apart from an ulp on E3's last bucket. That identity is the ground that most supports leaving the G.5.3 mapping open. The log names the form of the rows and the foreign term of the label. It does not state the identity as a measured fact.
- The last-bucket spelling gap, about 1e-17 to 5e-17, is below every band. It does not move an interpolation of a flat yield.
- Isolated A2 and A3 curves differ from the returned curves by up to about 4.83e-06, inside the 1e-5 curve band, and the isolated cases still pass. Claim 14 holds. Claim 10's byte-for-byte statement is a different re-run and is not shown by the isolated files.
- build-a1's egress has two refused requests, both GET, both to `chatgpt.com`, paths under `/backend-api/codex/responses` and `/backend-api/wham/settings/user`, at 19:34:15 UTC. `PREREGISTRATION.md:100` says a refused request reached nothing and does not void the run. No claim states the refusals.
- build-b1's egress has eight responses with status 400, each a POST to `countTokens` on `generativelanguage.googleapis.com`, between 19:55 and 20:03 UTC. Every request's host is that vendor host. No claim states the 400s. They do not void the run under §8.
- Both builders' weight choice passed. The preregistration named ¶9.2.5 as a candidate that is B or T according to the labels (`PREREGISTRATION.md:78`). ¶9.1.13 defines corporate bonds as bonds other than government bonds, plus loans, mortgages and securitisations, and leaves other assets as the remainder. E.5.3 defines the conditional weights inside bonds. The bundle labels the second column "Other Assets" (`bundle/E3/reference-portfolio-weights.tsv:5-6`; the same labels on E2). Both builders treat that column as the corporate category and normalise it with government (`NOTES.md:58`; `calculate.py:563-571`). C1's weights differ by 0 (`table.tsv`). The named candidate did not fire. No claim states that.
- build-b1 returned no `NOTES.md`. Its duration reading and its decision not to reapply G.5.3 are shown by `calculate.py` only.
- The image is identified by the id at `SPEC.md:176`, and the Debian packages, `poppler-utils` among them, are unpinned. Claim 11 states that limit. The launch prints that would show the id at run time are in the archives, which are not here. The spec states the id. That is what the claim cites, and it is what was read.
- One run per builder is one sample (`PREREGISTRATION.md:103`). The contamination caveat at `PREREGISTRATION.md:83-91` is claim 29's content: the cutoffs are the preregistration's account of vendor pages. Those pages were not fetched. No claim adds an independent check of the cutoffs, and this review has none.
- The comparison tool's stamp limits — how a stream's count is read, how far an encoding probe reaches, and a caller-supplied standard-output descriptor that can overwrite completed outputs — are stated (`SECOND-PARTY-CHECK.md:27-31`; `compare.py:2-154`). The tests in the folder carry no second-party check (`SECOND-PARTY-CHECK.md:33-39`). No claim says the tests were read by this review. They were not.
- This review pack contains the publisher's four files. The test repository, by `source/README.md:3`, does not. Claim 2 is about that repository. A reader of this pack can hash the copies. A reader of the test repository cannot, without a fetch this review did not do.

## 6. Findings

**F1.** D1 to D4 should be T if the dispositions follow the rule the log cites. Grounds: `divergences.md:49`; `PREREGISTRATION.md:66` and `:78`; `portfolios.py:209-212`; `NOTES.md:81-87`; `variants.out:14` and `:22`; E3 `Corp Data`!F8, R20 and R41; E2 `Corp Data`!F8 and the CQS 4 and CQS 5 yield cells named in §2; G.5.3 and G.5.5 (text, pages 89–91). The extra G.5.3 step is what puts the four outside their bands. The labels plus the numerical identity with the euro index leave the mapping open, so the rule gives T. This changes the log's statuses for those four rows, claim 23, and the "other causes" sentence of claim 25. It does not change `table.tsv` or `cases.tsv`. C1 remains not reproduced — the text, with G.5.3 and G.5.5 added to G.1.2 if the dispositions adopt T. It does not become reproduced, and it does not become undecided.

**F2.** The timestamp command as cited fails on this LibreSSL; verification succeeds with the token's embedded intermediate. Grounds: the two `openssl ts -verify` runs in §1, items 6 and 8; `timestamps/chain/` holding only the root; each token's signer issued by DigiCert Trusted G4 TimeStamping RSA4096 SHA256 2025 CA1. This qualifies claim 4. It does not change the table, the log or the outcome. The times and the list hashes stand.

**F3.** `bands.py` did not run, because `openpyxl` is absent and was not installed. The residual magnitudes in `divergences.md:23` and `:54` are not recomputed. This qualifies the sheet-solved half of claim 22, the residual share in claim 24's grounds, the "whole band" half of claim 26, and the rounded half of claim 27. It does not change the table. The as-supplied identities in `variants.out` were rerun.

**F4.** Isolated A2 and A3 differ from returned A2 and A3 by up to about 4.83e-06 on the curves, and they pass. Grounds: local comparison of `isolated/build-a1.json` and `isolated/build-b1.json` with the returned `outputs.json`; `cases.tsv:19-20` and `:27-28`; the curve band at `PREREGISTRATION.md:56`. This does not change claim 14. It shows that claim 10's equality is not the comparison the isolated files support.

**F5.** build-a1's two refused requests, and build-b1's eight `countTokens` responses of status 400, are in the egress and in no claim. Grounds: `builds/build-a1/egress/egress.jsonl`, the two request lines at 19:34:15 UTC; `builds/build-b1/egress/egress.jsonl`, the eight response lines of status 400; `PREREGISTRATION.md:100`. Neither voids the run. No change to the table or the outcome. A run record that names refused requests, as §8 asks, would name the two.

**F6.** E3's high-yield constants equal E2's euro high-yield constants, to an ulp on the last bucket. Grounds: E2 `Corp Data` L22:L26, P22:P26, L41:L45, P41:P45 against E3 `Corp Data` L23:L27, P23:P27, L44:L48, P44:P48, and E3's 15+ bucket at L28, P28, L49 and P49; the same spellings in `bundle/E2/corp-data.tsv` and `bundle/E3/corp-data.tsv`. This is a ground for F1. The log does not state the identity. Adding it would not change the table. It would strengthen the case for changing D1 to D4 from B to T.

**F7.** The log's "1.18 of the band" for `rc_corp` with rounded durations and the proxy step is 1.17 on the log's own three-digit parts (1.291e-04 / 1.1e-04). Grounds: `divergences.md:48` against `divergences.md:38` and the proxy part at `:41`. Display rounding. The output remains outside the band. No change to the table or the status.

**F8.** Claim 28 marks the spend count as the author's statement. The egress last `use` line carries `usd_sum` 5.119680, and the sum of the `usd` fields equals it. Grounds: `builds/build-b1/egress/egress.jsonl`, the last `use` event; `CLAIMS.md:104-105`. The bill and the plan share remain outside the folder. No change to the table or the outcome.

END OF REVIEW
