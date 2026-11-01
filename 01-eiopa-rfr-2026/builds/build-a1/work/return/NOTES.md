# Implementation notes

The sole methodological source is EIOPA-BoS-26/198, May 2026. The supplied control parameters, compositions, durations, frozen cash flows, risk-free curves and LTAS are treated as inputs. They are not reconstructed from historical observations or supervisory reports. No publisher result was available or consulted.

Input attribution: E1 — Source: EIOPA - European Insurance and Occupational Pensions Authority. E2 and E3 — Source: © EIOPA – European Insurance and Occupational Pensions Authority.

## Running and the A1 interface

Run `bash run.sh <bundle directory> <output file>`, optionally followed by `--a1 <file>`. Only Python's standard library and SciPy are required. The runner works from other working directories too. It reads the TSV cells from the supplied directory, never from a fixed input path. `calculate.py` implements A1–A3 and `portfolios.py` implements B1, B2 and C1.

The optional file contains the bare A1 object specified in the brief. A2 and A3 obtain A1 only through `downstream_from_a1_file`. Ordinary execution serializes the calculated A1 to a temporary file and calls that same interface. With `--a1`, the bootstrap is skipped, the supplied A1 is preserved in the output, and its basic curve and LLFR determine A2/A3. B1, B2 and C1 use their own workbook inputs and are independent of A1.

## A1

Implemented Sections 6.2 (6.2.1–6.2.2), 8.1 (8.1.1–8.1.4), 8.3 (8.3.1–8.3.4), 8.4 (8.4.1), 8.5 (8.5.1–8.5.8), and Annex D (D.1.1–D.1.3, D.2.1–D.3.5, D.4.1–D.4.9, D.5.1–D.5.14).

CRA is deducted from DLT par swap rates before bootstrapping. The bootstrap solves the par-pricing equation with a constant forward over each DLT interval, respecting the supplied coupon frequency. The first interval uses the first corrected par quote. Discount factors give the continuous zero rates. The LLFR uses the last forward before the FSP and forwards starting at the FSP to the subsequent weighted maturities. Extrapolation follows the prescribed convergence function and converts zero rates to annual compounding.

Decisions and interpretation:

- No separate FSP cell is supplied. The first maturity with a positive LLFR weight is treated as the FSP, using the convention in 5.2.7–5.2.8 and Table 2. The example's DLT flags and weights are the controls, rather than the provisional currency-specific values in that table. The example does not identify a currency for choosing another set of controls.
- Non-DLT quotes are ignored even where supplied. Paragraphs 8.1.3 and D.1.2–D.1.3 make DLT quotes the constraints; missing integer maturities are derived with constant forwards.
- The CRA cell is interpreted as basis points; swap quotes, UFR and convergence are decimals. CRA is already supplied, so its historical estimation and final estimation-stage rounding in 6.7.1 are not repeated. No CURA is supplied or inferred.
- Returned `llfr` is continuously compounded, following 8.5.6. The first forward there can be read as the preceding DLT interval, whereas 10.2.1 describes a one-year forward. Constant-forward interpolation makes them equal at the FSP here.
- The unknown interval forward is solved in logarithmic form using Brent's method. D.5.11 permits a validated root finder; D.5.12 describes the Excel algorithm as informational. Solving the original pricing equation avoids division by a forward in the rearranged equation and remains well defined at a zero forward. Every root is checked by repricing.

## A2

Implemented Section 9.3 (9.3.2), Section 10.1 (10.1.2–10.1.6) and Section 10.2 (10.2.1–10.2.4), using 8.5.5–8.5.8 for extrapolation.

The notional VA is derived from the supplied currency RCS. CSSR is the clipped ratio of the two valuation changes. The notional VA is converted with the logarithmic conversion in 10.1.6 and added to continuous forwards through the FSP. Equivalently, it adds the same amount to all continuous zero rates through the FSP. The adjusted LLFR changes only through its first weight, and the curve is extrapolated anew.

Decisions and interpretation:

- Starred asset and liability inputs are the valuations using the CSSR curve; unstarred values are the corresponding base valuations. The bundle supplies these valuations, not cash flows, so they enter 9.3.2(b)–(d) directly.
- The scope of the undertaking-specific adjustment (USA) is not explicit when 9.3.2 and 9.3.3–9.3.5 are read together. This implementation uses the published currency-RCS input for the notional CSSR scenario and applies the USA election to the actual currency VA in A3. This reads 9.3.3–9.3.5 as qualifying the actual-VA formula in 9.3.1. The input layout, which places the USA election on VA Term Structures rather than CSSR Calculation, supports this reading. Applying USA to the notional scenario too is an alternative reading and is not implemented.
- The original basic zero rates through the FSP and original LLFR come from the A1 JSON file. The bootstrap's internal discount factors and par rates are not used.

## A3

Implemented Section 9.3 (9.3.1, 9.3.3–9.3.6), Section 9.4 (9.4.1–9.4.3), Section 10.1 (10.1.2–10.1.6) and Section 10.2 (10.2.1–10.2.4).

Decisions and interpretation:

- USA is the supplied undertaking-specific multiplier, subject to the documentary upper cap. Its underlying own-portfolio RCS is not supplied and is not reconstructed. `currency_va` includes this multiplier when enabled, because 9.3.5 changes the RCS used in 9.3.1. It is not the intermediate currency VA before that election.
- The macro-VA election is honored. Macro VA and USA are mutually exclusive under 9.3.4; an enabled USA excludes the macro component. Otherwise the country component follows 9.4.1–9.4.3 using the currency RCS, country RCS and debt-to-total-assets input.
- `omega_co` always reports the weight defined in 9.4.2, even when the country component is not selected. The election gates the macro contribution to `total_va`, not omega's definition.
- `total_va` is the adjustment carried by the curve. Its continuous equivalent adjusts the basic zero rates and first LLFR component as in A2. UFR and convergence remain the A1 controls.

## Common method for B1, B2 and C1

Implemented Section 9.2 (9.2.1–9.2.7), Annex E (E.5.3, E.6.4, E.6.9–E.6.10), Annex F (F.1.1–F.1.3, F.2.1–F.2.2, F.3.1–F.3.4, F.4.1–F.4.4), and Annex G (G.1.1–G.1.2, G.4.1–G.4.2, G.6.1–G.6.4). Issuer/currency mappings use Table 1 and its indicated euro-area membership.

Government and corporate shares are conditioned on their combined bond exposure under E.5.3. Each active model bond receives market, risk-free and risk-corrected yields. For each yield type, the supplied matching frozen cash flows are discounted at the model-bond yields. A separate portfolio IRR reproduces that total present value. Differences between the appropriate IRRs give each bond portfolio's spread and correction. Conditional weights combine them into S and RC; RCS is their difference.

Decisions and interpretation:

- The input column described as other assets is the corporate/debt category represented by the corporate reference portfolio, consistent with 9.1.13. Its share and the government share are normalized together. Model-bond compositions are already normalized and are checked rather than renormalized.
- Rows with absent/zero composition are inactive. Their blank durations are not treated as observed zero durations and need no yield proxy.
- The three cash-flow columns are the yield-specific frozen cash flows of F.3.2, even when they cannot be reconciled to the supplied composition using current yields. They are neither rebuilt from current yields nor multiplied by composition again. The right-hand side of F.3.4 is current present value, not a hard-coded par value. This is particularly material for C1.
- Market, risk-free and LTAS curves are interpolated linearly at each rounded model-bond duration, with flat extrapolation outside available observations (G.1.2). Those interpolated values enter the nonlinear correction formulas. An alternative would interpolate an already-calculated integer-tenor correction curve; it is not used because G.6.2/G.6.4 define the correction for the bond's maturity itself.
- Supplied market yields and risk-free zero rates are annually compounded decimal yields, consistently with F.3.1–F.3.4. Corporate index durations are interpolation knots and retain source precision; they are distinct from the reference model-bond durations rounded under G.1.2.
- Risk-free yields use each government's issuing-country currency under G.4.1, including foreign governments in another currency's or country's portfolio. Corporate issuances use the portfolio's corporate currency.
- Positive parts and caps in G.6.2/G.6.4 apply at the model-bond level. EEA government issuers use G.6.2; other government issuers and corporate bonds use G.6.4. No floor is added to S or RCS.
- LTAS is supplied, so historical reconstruction in G.6.5–G.6.17 is not repeated. Historical GBP adjustment factors are not applied again to supplied LTAS.
- The unidentified-annex reference in G.6.4 is read in light of the categories immediately specified by G.6.3. The inconsistent EEA qualifier on one LTAS identity in G.6.4 does not override that division. The concluding identity in G.6.2 does not override its explicit EUR/ECB special case.
- IRRs are solved in log-yield space, bracketed by constituent yields, and verified by pricing residuals. The six portfolio yields per example are computed independently with the corresponding cash-flow column.

## B1 — EUR currency portfolio

In addition to the common method, implemented G.2.1–G.2.3, G.5.1–G.5.4 and Table 12, and the EUR special case in G.6.2.

Euro-area government issuers use the ECB curve and corresponding EUR government LTAS. Issuer-country distinctions determine membership but do not replace the ECB proxy with domestic government yields. Corporate yields use EUR index data. CQS-zero proxies are derived from CQS-one yields with the sign-dependent factor in Table 12 and the same index durations. Single indices for the higher CQS categories are flat across maturities; CQS six uses the CQS-five proxy. Repeated rows of a single index are treated as one observation.

## B2 — IT country portfolio

In addition to the common method, implemented G.2.4–G.2.5, G.3.1, G.5.1–G.5.4 and Table 12, and G.6.2–G.6.4.

Each active government issuer uses its domestic government curve and LTAS, with the peer mapping of Table 1/G.3.1 where applicable. The home country does not replace foreign issuers' yield or risk-free proxies. The non-EEA government category uses G.6.4. The corporate portfolio uses the same EUR market indices as B1, evaluated at its own supplied model-bond durations and with its own frozen cash flows.

## C1 — GBP currency portfolio

In addition to the common method, implemented G.2.1–G.2.3, G.5.1–G.5.5, Tables 12–13, and G.6.2–G.6.4.

Government yields are issuer-specific. Euro-area issuers here do not use the ECB currency-portfolio special case. Their risk-free yields remain EUR, while UK government risk-free yields use GBP. EEA government correction applies to EEA issuers and the other-government correction applies to the UK issuer.

GBP corporate categories in Table 13 use their supplied GBP index data, with CQS zero derived as stated there. Missing high-yield categories require the EUR-based construction in G.5.3/G.5.5. The input blocks for these categories contain constants and are annotated with the k-factor approach. They are interpreted as underlying EUR index observations for that construction, rather than GBP yields to which it has already been applied. This permits performing G.5.5 from the provided inputs; the alternative interpretation would skip the currency construction entirely. Both risk-free curves for that construction come from E3. C1 never borrows values from E2. Supplied GBP corporate LTAS is used directly.

## Rounding and precision

Model-bond durations are rounded to one decimal place under E.6.10 and G.1.2. The tie convention, not specified there, is nearest with halves away from zero; supplied model durations already have the required precision. Index durations are not rounded.

Paragraph 10.1.3 assumes a VA expressed in integer basis points, and 10.1.6 converts those units. It does not state a separate rounding operator or tie rule for the calculated VA. The implementation retains the calculated decimal adjustment and applies the equivalent logarithmic conversion directly. For these inputs the notional and actual total adjustments already correspond to whole basis points in exact decimal arithmetic, so there is no substantive rounding choice at the curve-construction step.

No returned rates, spreads, weights, CSSR or omega are rounded or clamped beyond the formulas' explicit caps/floors. JSON preserves full binary64 values, including a possible floating-point residual for a theoretically zero difference between independently solved IRRs.

## Verification and limits

All requested outputs have been computed; none is null. The runner finishes well inside the ten-minute limit and uses no network access. No files, packages or external methodology are needed beyond the bundle and stated Python environment.

Checks performed:

- Complete output schema, exact maturity coverage and finite JSON numbers.
- Independent high-precision decimal bootstrap, solving a polynomial in the interval discount factor, and high-precision extrapolation. Maximum differences from returned rates were below `2e-16`.
- Repricing every DLT swap from returned zero rates; maximum par-value residual was below `3e-16`.
- Independent high-precision IRR solves for every government/corporate and market/risk-free/risk-corrected combination; differences were below `1e-16`.
- Normal execution and `--a1` with identical A1 produced identical outputs. Changing the supplied basic curve and LLFR propagated into A2/A3 by the analytical Chapter 10 response and left B1/B2/C1 unchanged.

These are internal mathematical and interface checks, not comparisons against unavailable publisher results. The interpretations above remain the substantive limitations of replication from this document and bundle alone.

## Reading the PDF

Used Poppler `pdftotext -layout` to locate sections, search terminology and read prose. Used `pdftoppm` and the image viewer to inspect rendered mathematics and tables. Formulas were read from rendered pages rather than relying on corrupted text-layer symbols or lost fraction bars.

Rendered pages inspected (PDF and printed page numbers agree):

- 19–20: Table 1, country/currency and peer mappings.
- 23–24: 5.2.7–5.2.8 and Table 2, including DLT highlighting and the first-weight/FSP convention.
- 35–37: 8.5.3–8.5.8, convergence function, LLFR weights and extrapolated zero rates.
- 41–43: 9.2.5–9.4.3, aggregation, CSSR, currency VA, macro VA and omega.
- 45–46: Chapter 10, logarithmic VA conversion, changed LLFR and annual-compounding conversion.
- 51: Annex A's currency classifications and country associations.
- 67–73: Annex D, swap pricing, constant-forward bootstrap and numerical solutions.
- 81–86: conditional weights, model-bond definitions, duration rounding, frozen cash flows, IRRs and their mapping to spreads/corrections.
- 87–92 and 94–95: interpolation and yield proxies, corporate index Tables 12–14, and both piecewise correction formulas. Surrounding G.6.2 prose on page 93 was read in the text extraction; its formula is on page 94.
- 114: Annex J's dependency diagram for an overall consistency check.

Prose in Sections 6.2, 8.1–8.4, 9.1 and Annexes E/G was also read from the layout extraction to establish scope. Historical LTAS tables were not used to alter the supplied LTAS. Renderings and extracted text remain outside the return directory.
