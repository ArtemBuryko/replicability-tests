# The input bundle

The inputs of the six examples, as the publisher's three workbooks give them: the cells of each workbook's input ranges, and, for workbook E1, whose input cells carry no labels of their own, the labels its sheets show beside them. No result of any example is here; the input files hold no cell whose value a workbook computes by a formula.

## The files
Each `.tsv` file holds one line per non-empty cell, in row order, left to right: the cell as `<sheet>!<cell>`, a tab, and the value the workbook stores in it — a number at full precision, `TRUE` or `FALSE`, a date as `YYYY-MM-DDTHH:MM:SS`, text with a backslash written `\\`, a tab `\t` and a line break `\n`.

| file | workbook | sheet | cells | lines |
|---|---|---|---|---|
| `E1/input-data-and-extrapolation.H10-H12.tsv` | E1 | Input Data & Extrapolation | H10:H12 | 3 |
| `E1/input-data-and-extrapolation.H14-H16.tsv` | E1 | Input Data & Extrapolation | H14:H16 | 3 |
| `E1/input-data-and-extrapolation.G25-G174.tsv` | E1 | Input Data & Extrapolation | G25:G174 | 150 |
| `E1/input-data-and-extrapolation.H25-H174.tsv` | E1 | Input Data & Extrapolation | H25:H174 | 150 |
| `E1/input-data-and-extrapolation.I25-I174.tsv` | E1 | Input Data & Extrapolation | I25:I174 | 150 |
| `E1/input-data-and-extrapolation.J25-J174.tsv` | E1 | Input Data & Extrapolation | J25:J174 | 32 |
| `E1/input-data-and-extrapolation.L10.tsv` | E1 | Input Data & Extrapolation | L10 | 1 |
| `E1/cssr-calculation.G24-G173.tsv` | E1 | CSSR Calculation | G24:G173 | 150 |
| `E1/cssr-calculation.L10-L11.tsv` | E1 | CSSR Calculation | L10:L11 | 2 |
| `E1/cssr-calculation.L13-L14.tsv` | E1 | CSSR Calculation | L13:L14 | 2 |
| `E1/input-data-and-extrapolation.L11-L12.tsv` | E1 | Input Data & Extrapolation | L11:L12 | 2 |
| `E1/va-term-structures.H10-H12.tsv` | E1 | VA Term Structures | H10:H12 | 3 |
| `E1/va-term-structures.G23-G172.tsv` | E1 | VA Term Structures | G23:G172 | 150 |
| `E2/gov-rates.tsv` | E2 | Gov Rates | the sheet's constants | 317 |
| `E2/corp-data.tsv` | E2 | Corp Data | the sheet's constants | 211 |
| `E2/rfr.tsv` | E2 | RFR | the sheet's constants | 96 |
| `E2/ltas.tsv` | E2 | LTAS | the sheet's constants | 905 |
| `E2/reference-portfolio-weights.tsv` | E2 | Reference Portfolio Weights | the sheet's constants | 16 |
| `E2/government-bond-ref-portfolios.tsv` | E2 | Government Bond Ref. Portfolios | the sheet's constants | 366 |
| `E2/corporate-bond-ref-portfolio.tsv` | E2 | Corporate Bond Ref. Portfolio | the sheet's constants | 170 |
| `E3/gov-rates.tsv` | E3 | Gov Rates | the sheet's constants | 102 |
| `E3/corp-data.tsv` | E3 | Corp Data | the sheet's constants | 245 |
| `E3/rfr.tsv` | E3 | RFR | the sheet's constants | 96 |
| `E3/ltas.tsv` | E3 | LTAS | the sheet's constants | 626 |
| `E3/reference-portfolio-weights.tsv` | E3 | Reference Portfolio Weights | the sheet's constants | 9 |
| `E3/government-bond-ref-portfolios.tsv` | E3 | Government Bond Ref. Portfolios | the sheet's constants | 95 |
| `E3/corporate-bond-ref-portfolio.tsv` | E3 | Corporate Bond Ref. Portfolio | the sheet's constants | 82 |

`E1/labels.tsv` — E1's labels, 22 lines in the same form: the cell beside each single input, or at the top of each column of inputs; and the four formula labels the sheet `CSSR Calculation` draws as text boxes beside inputs, each given by the cells its box spans, `<sheet>!<from>:<to> (text box)`, then its text in Excel's linear notation.

`SHA256SUMS` — the sha256 of every other file here.

## The workbooks
| id | file | sha256 |
|---|---|---|
| E1 | RFR extrapolation and VA calculation (19 May 2026).xlsm | `c1ce32a3f76cf50f4d3de267292ee5af355fea9d31b60c4d2a01a98dff777dc4` |
| E2 | RFR risk-corrected spread calculation (21 May 2026)- RFR TD formulas.xlsm | `5302c91ba000568fd99adb0c98a08af9cb3089b412f0200a77c5488fb85cfe07` |
| E3 | RFR risk-corrected spread calculation Non-EEA (21 May 2026) + RFR TD formulas.xlsm | `67bf3478293b810691460569cf79751cf4c90e57a2773cbbd4da9f92b2486b81` |

Each workbook's own source line, as its reproduction clause asks:
- E1: Source: EIOPA - European Insurance and Occupational Pensions Authority
- E2: Source: © EIOPA – European Insurance and Occupational Pensions Authority
- E3: Source: © EIOPA – European Insurance and Occupational Pensions Authority
