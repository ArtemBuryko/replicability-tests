# The comparison tool — its second party's check

The pass-or-fail table is produced by the comparison tool, «whose code carries a second party's check before its result is relied on» (the preregistration, section 5). This file is the record of that check: the bytes it was made on, what it returned, and what it does not cover.

## The tool — checked four times, its bytes unchanged

`compare.py` · 1,398 lines · 74,383 bytes · sha256 `d36b8649aadaff8958e0baff6164e5717f401e6c68b55144a2a92fe3c9d8f498` — the file beside this one, and the sha256 that each file of `../table/` names in its second line.

A second party — not the author of the tool — received these bytes with the tests of that day, the frozen texts they rest on and the pinned workbooks, was asked to break them, and returned its decision in writing. Four such checks followed one another on the same bytes. Each returned **STAMP** on the tool — its word for bytes whose result may be relied on within the limits it states — and **NO STAMP** on the tests it read. The returns stay with the author, whole; each is named here by its sha256, with its first two lines as returned.

| check | the tests it read · sha256 | its return · sha256 |
|---|---|---|
| 1 | `02f92279fab48716cd6d13255485509074dd3b5e3a8184b957896590ee4c4607` | `741e8427d5e5b4ad6a5a70f9648effd6cad8bb5659f827935c93bf16fc79dc93` |
| 2 | `3fe150f6e6922bbc5ff9102a01d71768f72b71e4e1f45ec4d116cc8c4f5f935a` | `cd6d526385fbf6c2c3aa963b16137c54838eb42c88f8bd88764b500e12aca60d` |
| 3 | `1ef3801f001c3724365e13fdab635f0992c2b91bf3d5233596bf9f39e0a2c2e9` | `3d1894ab1b1b99df8afd752cb632a233912d5c8f080f5868bb018c7967919ae8` |
| 4 | `0d141c551cf80b1c4d6269a25acab529f32381af32b788cbed984ad4fb038707` | `8587348f9219cdf3e7ce355513f2653efb170b660096e936651c178c862d02b8` |

1. «Comparator: STAMP on the received hash, within its stated operational limits and Q1's explicit stream interpretation.» · «Tests: NO STAMP — three non-equivalent mutants pass all 150 tests: rational equality, integer maturities, and a necessary encoding probe.»
2. «Tool: STAMP on the unchanged bytes, within the stated operational limits and Q1's counted-stream interpretation.» · «Tests: NO STAMP — five finding classes, including two falsely classified equivalent sweep survivors.»
3. «Tool: STAMP on the received bytes, within the explicit operating limits and counted-stream interpretation.» · «Tests: NO STAMP — five findings, seven non-equivalent mutants each passing all 163 tests.»
4. «Tool: STAMP on the received bytes, within the explicit operating limits qualified below.» · «Tests: NO STAMP: four behavior-changing mutations in three finding groups pass all 170 tests.»

The table in `../table/` was made once, by these bytes, after the first check's return and before the second's. No byte of the tool has changed since the first check.

These four are the last of twenty-one checks. The seventeen before them read earlier bytes of the tool and of its tests and returned NO STAMP on both; after each, every finding was tested against the bytes it named, none was set aside, and the tool was revised — until the bytes above.

## What the stamp covers — the last return's words

«The tool's stamp is on received bytes within the explicit operating limits and counted-stream interpretation, with finite codec-probe reach and caller-supplied descriptor authority **including possible overwrite of its own completed outputs**. It is not universal delivery across every codec/state, protection from arbitrary caller code or output aliases, a race-free filesystem guarantee, or fresh four-runtime certification.»

Those limits are stated in two places: in the tool's own docstring (`compare.py`, lines 2 to 154), which says what a run holds and names what it does not; and in the returns, whose qualifications go beyond it — the three named in the sentence above among them: how a stream's count of what it took is read, how far the probe of a stream's encoding reaches, and that the descriptor a caller supplies for standard output is taken at its word, so that a run can be made to overwrite its own completed outputs.

## The tests — not checked in the bytes kept here

`test_compare.py` · 5,797 lines · 361,292 bytes · sha256 `0eab8582631b2445ab3c77625fedfef82ed5b5859761a773bf30307c82850c0d` — carries **no second party's check**.

Each of the four checks returned NO STAMP on the tests it read: each showed changes to the tool's code — twenty-five across the four — that altered what the tool does and still passed every test of that day. These were gaps in the tests, not in the tool, whose bytes each of the four stamped. After each check the tests were revised to hold what it had shown. The tests kept here are the revision made after the fourth check; no second party has read them. The checks ended there by the author's decision, not by a stamp on the tests.

The preregistration asks a second party's check of the tool's code (section 5); it asks none of the tests.

## What a reader can check from here

The sha256 of `compare.py` against the one above and against the second line of each file of `../table/`. The four returns are not in this repository; their sha256 above bind the author to their bytes.
