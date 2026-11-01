# Brief — replicability test 01

This brief is your whole instruction. You are one of two builders; each works alone, in its own sealed container, from the same inputs and this same brief. No one can answer a question during your run: where you must decide, decide, and record the decision in `NOTES.md` (below).

## Your task
From a published technical document alone, implement the calculations behind six worked examples its publisher released with it, run them on the examples' inputs, and return the results with your code.

The document is EIOPA-BoS-26/198, the technical documentation of the methodology to derive EIOPA's risk-free interest rate term structures (May 2026), published by EIOPA, the European Insurance and Occupational Pensions Authority. Your results will be compared with the publisher's own results for the same inputs, which you do not have and cannot obtain. The method is the one this document states: where it differs from any earlier version of EIOPA's methodology, or from any implementation you may know, the document governs.

## What you have
- `/in/brief.md` — this brief.
- `/in/EIOPA-BoS-26-198 - RFR Technical Documentation SII Review.pdf` — the document, as published: your only source for the method. Its formulas are typeset in a mathematical font; a text-layer extraction of this PDF can double, drop or replace symbols inside formulas, loses fraction bars, and loses the highlighting that marks some table cells. Where a formula or a table matters, read it from the rendered page.
- `/in/bundle/` — the examples' inputs, as the publisher's three workbooks give them, without any of their results; `/in/bundle/README.md` describes its layout.
- `/work` — your working directory, writable; `/work/return` — your return (below).
- In the container: Python 3 with NumPy and SciPy; Node.js; poppler-utils (`pdftotext`, `pdftoppm`, `pdfimages`, `pdfinfo`); ripgrep; common shell tools. Nothing can be installed.

Nothing else is available. Your network reaches your model's API and no other host — every other attempt is refused and logged. You have no web search and no page fetch. You work as a single agent and start no other agent. The command-line agent you run in may refuse a shell command that repeats a path, a URL or a script name an earlier shell command printed, and — once one of its file tools has written a build file such as a `Makefile`, `package.json` or `pyproject.toml` — any build or test command such as `python3`, `make` or `npm`; its own tools for reading and writing files are not refused this way. Do not try to change any of this.

## Time
You have 5 hours of wall time from the start of your run. When the time is up the run is stopped, and whatever is in `/work/return` at that moment is your return. Write your results early and keep them current.

## The six examples
Each example names the results to return; the names in backticks are the keys of `outputs.json`. Rates and spreads are decimals (0.01 is 1 %); maturities are whole years.

**A1 — the basic risk-free interest rate term structure of a currency, from its par swap rates:** the bootstrap with the credit risk adjustment, the last liquid forward rate and the extrapolation; inputs — workbook E1 in the bundle.
- `zero_rates_cc` — the zero-coupon rates the bootstrap yields, continuously compounded, for each maturity 1 to 50;
- `llfr` — the last liquid forward rate (LLFR);
- `basic_rfr` — the basic risk-free interest rate term structure: zero-coupon rates, annually compounded, for each maturity 1 to 150.

**A2 — the cost-of-spread-sensitivity ratio (CSSR) and the term structure with the notional volatility adjustment,** from A1's results and E1's other inputs.
- `notional_va` — the notional volatility adjustment;
- `cssr` — the CSSR;
- `llfr` — the LLFR of the term structure with the notional volatility adjustment;
- `curve` — that term structure: zero-coupon rates, annually compounded, for each maturity 1 to 150.

**A3 — the volatility adjustment and the term structure with it,** from A1's and A2's results and E1's other inputs.
- `currency_va` — the currency volatility adjustment;
- `omega_co` — the weight ω(co) of the country component;
- `total_va` — the volatility adjustment the term structure carries;
- `llfr` — the LLFR of the term structure with the volatility adjustment;
- `curve` — that term structure: zero-coupon rates, annually compounded, for each maturity 1 to 150.

**B1 — the risk-corrected spread of a currency, the euro (EUR);** inputs — workbook E2.
**B2 — the risk-corrected spread of a country, Italy (IT);** inputs — workbook E2.
**C1 — the risk-corrected spread of a currency, the pound sterling (GBP);** inputs — workbook E3.
For each of B1, B2 and C1, with c the currency or the country, and its reference portfolios of government bonds (gov) and corporate bonds (corp):
- `w_gov`, `w_corp` — the weights w_{c,gov|B} and w_{c,corp|B};
- `s_gov`, `s_corp` — the spreads S_{c,gov} and S_{c,corp};
- `rc_gov`, `rc_corp` — the risk corrections RC_{c,gov} and RC_{c,corp};
- `s`, `rc`, `rcs` — S_c, RC_c and the risk-corrected spread RCS_c.

## Your return — `/work/return`
1. **`outputs.json`** — your results, in exactly this form, nothing else in the file:
```json
{
  "A1": {"zero_rates_cc": {"1": 0.0, "2": 0.0, "...": 0.0, "50": 0.0}, "llfr": 0.0, "basic_rfr": {"1": 0.0, "...": 0.0, "150": 0.0}},
  "A2": {"notional_va": 0.0, "cssr": 0.0, "llfr": 0.0, "curve": {"1": 0.0, "...": 0.0, "150": 0.0}},
  "A3": {"currency_va": 0.0, "omega_co": 0.0, "total_va": 0.0, "llfr": 0.0, "curve": {"1": 0.0, "...": 0.0, "150": 0.0}},
  "B1": {"w_gov": 0.0, "w_corp": 0.0, "s_gov": 0.0, "s_corp": 0.0, "rc_gov": 0.0, "rc_corp": 0.0, "s": 0.0, "rc": 0.0, "rcs": 0.0},
  "B2": {"w_gov": 0.0, "w_corp": 0.0, "s_gov": 0.0, "s_corp": 0.0, "rc_gov": 0.0, "rc_corp": 0.0, "s": 0.0, "rc": 0.0, "rcs": 0.0},
  "C1": {"w_gov": 0.0, "w_corp": 0.0, "s_gov": 0.0, "s_corp": 0.0, "rc_gov": 0.0, "rc_corp": 0.0, "s": 0.0, "rc": 0.0, "rcs": 0.0}
}
```
   The zeros show the form only. Every maturity key is present, from "1" to the last. Each value is a JSON number at full double precision; round a value only where the document prescribes that rounding for it, and say so in `NOTES.md`. A result you could not compute is `null`.
2. **`run.sh`** — runs your code offline and writes `outputs.json` anew: `bash run.sh <bundle directory> <output file>`. The `outputs.json` you return is what this command produces from `/in/bundle`. It finishes within 10 minutes in this container.
3. **A2 and A3 from given A1 results:** `bash run.sh <bundle directory> <output file> --a1 <file>`, where `<file>` holds A1's results in the form of the "A1" object above, computes A2 and A3 from those A1 results instead of your own and writes them in the same form. Your A2 and A3 code takes A1's results only through this path. It is run after your run, offline, to separate a difference in A1 from one in A2 or A3.
4. **Your code**, under `/work/return` — any layout; Python 3 (its standard library, NumPy, SciPy) or Node.js (no packages). It reads every input from the bundle directory it is given: no input value is written into your code, your notes or any file of your return.
5. **`NOTES.md`** — for each example: the parts of the document your code implements, by section and paragraph; every point where the document allowed more than one reading, or did not state something you needed, with the reading you chose and why; anything you could not do. Then how you read the PDF: which tools, rendered pages or extracted text, for which parts. Cite the document by section and paragraph; do not copy its text.

Keep `/work/return` to these. Copy neither the PDF, nor the bundle, nor passages of the document into it.
