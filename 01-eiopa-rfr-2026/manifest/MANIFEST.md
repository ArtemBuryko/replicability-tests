# The manifest — every declared range, pinned by its digest

The input-to-oracle manifest of the six declared cases (`../preregistration/PREREGISTRATION.md`, §3): every range a case reads or the oracle answers, with the ranges withheld from the builders and those left out of the cases — by case, role, workbook, sheet and range, selection, cells, sha256 and label. Each sha256 is the digest of the range's canonical lines: one line per non-empty cell, row-major, `<sheet>!<cell>`, a tab, the value the workbook stores in it. The values themselves are not here; the workbooks are named by their URLs and sha256 in `../source/README.md`.

`manifest.py` re-derives every row from copies of the pinned workbooks:

    python3 -I manifest/manifest.py <a folder holding E1.xlsm, E2.xlsm and E3.xlsm — copies of the pinned files>

It also prints each range's first and last value, the completeness check of the workbooks' numeric constants, the check of their defined names and of the three first cases' references to the sheets left out, and the CQS 0 rule against the CQS 1 yields it reads — each check with its positive control. The rows below are its run, without the first and last values.

Roles: *input* — given to the builders; *output* — the oracle; *intermediate* — computed by the workbook on the way, withheld; *residual* — the Solver objectives behind the intermediates, withheld; *excluded* — outside the declared cases; *version* — the workbook's version cell. Selection: *const* — the cells holding constants; *formula* — the cells a formula computes; *all* — every non-empty cell. `*` — the whole sheet.

```text
case · role · workbook · sheet!range · selection · cells · sha256 · label
A1 · input · E1 · 'Input Data & Extrapolation'!H10:H12 · const · 3 · 31d82cb2c3c5f818f2c904abc0b4b01657dcfd65e20efab4037a3998a6683c27 · extrapolation?, instrument, coupon frequency
A1 · input · E1 · 'Input Data & Extrapolation'!H14:H16 · const · 3 · 6e8ac08cd95aa946ea1a3232328331cb5ac6c37374d918f834e20260bb61ab15 · UFR, alpha, CRA (bp)
A1 · input · E1 · 'Input Data & Extrapolation'!G25:G174 · const · 150 · 5e99e61353f4adbea5082782105731f783b05f30a2672eb278bf1ca62f2f9ae7 · maturities
A1 · input · E1 · 'Input Data & Extrapolation'!H25:H174 · const · 150 · 2d6120205d07908c0b9d04a564c090f848ac1e0a33019a3b2179d2fecc392008 · DLT flags
A1 · input · E1 · 'Input Data & Extrapolation'!I25:I174 · const · 150 · 5942b62233ff53954c83a3caca0ac042d56c119d9adea850819b9c4caa520a85 · LLFR weights
A1 · input · E1 · 'Input Data & Extrapolation'!J25:J174 · const · 32 · cf0879038d9595da7965e24d83754eaa927e6f75d8aaab6fc9efe1a69583f725 · par swap rates — 32 published; the DLT flags select 19
A1 · excluded · E1 · 'Input Data & Extrapolation'!H17 · const · 1 · 8c1333b1d10e2ac5ac0d0249efa961b0330d4ce3ffade49abe33c6aa3003fd1e · input LLFR - used only when Extrapolation? is FALSE
A1 · intermediate · E1 · 'Input Data & Extrapolation'!H13 · all · 1 · 3ad584a62275900128f094116b84d3c1b0e61d92966dfcca7bc65df7d92798de · FSP
A1 · output · E1 · 'Input Data & Extrapolation'!K25:K74 · all · 50 · 96232d2dea9b0c4e1d63db632e92cd63850073ca1f876f942cbd2ea60f661047 · bootstrapped zero rates, CC
A1 · output · E1 · 'Input Data & Extrapolation'!L22 · all · 1 · 677d9248545407a75f99e8daab8e2666dbdefaa5f9d2dd344ac354711f8ab081 · LLFR
A1 · output · E1 · 'Input Data & Extrapolation'!L25:L174 · all · 150 · 3e9e75dd0948f02edc133d7206ee8479e74796c087820b0e2f9a78c8be8bbb1d · basic RFR, AC, 5 dp
A2 · input · E1 · 'Input Data & Extrapolation'!L10 · const · 1 · 6e51995833fa6918c6c9cd2fba06b9f20954dcfe2ef7d96922090447efb4f124 · currency RCS
A2 · input · E1 · 'CSSR Calculation'!G24:G173 · const · 150 · fdac9b3435e409387be726e363e5430061571d217471197580c574859edfbed1 · maturities, as in A1
A2 · input · E1 · 'CSSR Calculation'!L10:L11 · const · 2 · 2bb9c85ebf46fbbdb241a6ad30411fd7940b3d526d311e49832817fbe458a137 · FI: MV, MV at the notional VA
A2 · input · E1 · 'CSSR Calculation'!L13:L14 · const · 2 · 1b1b2755091bc357eba153f39140407cd381512b2ad17f7a3b34c59681ae5e07 · BEL: MV, at the notional VA
A2 · excluded · E1 · 'CSSR Calculation'!L12 · all · 1 · 24571d20687f18c647b26b1b1fe76c90615ecb81a005142d7e867dc93c9fa358 · PVBP of FI - the workbook's construct, not the text's
A2 · excluded · E1 · 'CSSR Calculation'!L15 · all · 1 · 88d17e81ccf83b270e6212eb853f3211622b9819c761fcc2b8e440d18f96f6dd · PVBP of BEL - the workbook's construct, not the text's
A2 · output · E1 · 'CSSR Calculation'!H10 · all · 1 · 15b3167bfb5dc3e6d39a5c16161a4371c23b4fd3f076650f14814c72dd0a8ea3 · notional VA
A2 · output · E1 · 'CSSR Calculation'!L16 · all · 1 · 9178426e93df025b8d6925387c4de9fb27cdc44d88e79c245b60d1a7b694e1f1 · CSSR
A2 · output · E1 · 'CSSR Calculation'!K20 · all · 1 · a3bd25b3f2826cc92caeddd3168c9a8956fe5a641b61f9c36d18438d88e36816 · LLFR of the CSSR curve
A2 · output · E1 · 'CSSR Calculation'!L24:L173 · all · 150 · ac5c8cbc44f7d0b2c3a26bca1929a64c8d134074c7f3529463303700a8c6a996 · CSSR curve, 5 dp
A3 · input · E1 · 'Input Data & Extrapolation'!L11:L12 · const · 2 · eb540ed836ed017521c377bd09bff263198e754b821021971c242dda92f8a68c · country RCS, debt to total assets
A3 · input · E1 · 'VA Term Structures'!H10:H12 · const · 3 · 3b319d4c99782977058ce8f942f86aab474eb5505c27a84b1a5ddfc57e17af61 · macro VA?, USA?, USA
A3 · input · E1 · 'VA Term Structures'!G23:G172 · const · 150 · f396499d9f9f19ef58b8255d024e6b97057adb49fbff813f40871a5a9cfabc42 · maturities, as in A1
A3 · excluded · E1 · 'VA Term Structures'!L12 · all · 1 · 331082ed00d41a21237723e769adc15e1feeaadd3173caaca537b9062236d2e0 · macro VA - not selected
A3 · output · E1 · 'VA Term Structures'!L10:L11 · all · 2 · be1d25c6f3dc23a4f7f5d211e5a693c1c66199e4d334e85f0ff59c62c756be21 · currency VA, omega(co)
A3 · output · E1 · 'VA Term Structures'!L13 · all · 1 · dfa1b298e482bb79530d29c398d1273fddc7fc8fa1d0237a2019645756a0bc98 · total VA, 4 dp
A3 · output · E1 · 'VA Term Structures'!K20 · all · 1 · 1aca118e81d2b9f77682b8e8194317cb5b3a6ea877913f1033bb1c9f5655c674 · LLFR of the VA curve
A3 · output · E1 · 'VA Term Structures'!L23:L172 · all · 150 · 6ee36fe691cc448076583e2e2d61aa3dc2e859ac247c2ec61d697e6f93a01c74 · VA curve, 5 dp
A4-A5 · excluded · E1 · 'IRR Up Shock'!* · const · 167 · 5a8867fedc05d069185b01b2a10bdfbe2d05d914628080cf311bb593e67e3271 · IRR up - out of the declared cases
A4-A5 · excluded · E1 · 'IRR Down Shock'!* · const · 167 · c8dc093437731073bdf0a63c230c821eb07f54dd749a7e2d35fa75027106f977 · IRR down - out of the declared cases
A4-A5 · excluded · E1 · 'Parameters'!* · const · 807 · 95ab005f28bd0ec55ec7ced4084d8dac2bfa86e7fbfc12a6ef7889bd97178aa8 · the IRR shocks s, b and the floor r_m - out of the declared cases
- · version · E1 · 'Overview'!F21:H21 · all · 2 · 467721f42dd6e44e362e3003a10734671e68fefa2f78790a29115bb29041f3d1 · the workbook's version and date
- · version · E2 · 'Overview'!F16:H16 · all · 2 · 31ebd7cc25c890a726f30579b4402690cb7e04225a147efa939194d2a2e5ebc1 · the workbook's version and date
- · version · E3 · 'Overview'!F16:H16 · all · 2 · 31ebd7cc25c890a726f30579b4402690cb7e04225a147efa939194d2a2e5ebc1 · the workbook's version and date
B · input · E2 · 'Gov Rates'!* · const · 317 · 7ac5c696e3a4cc8be19b0c8e720eae605113771b667ee6c518bf5f54b4f0ff91 · input sheet, constants
B · input · E2 · 'Corp Data'!* · const · 211 · 40c4806de9cd2b7c152558d6abed0f3bfbc48f25f911c3f7494db77ed58bd11c · input sheet, constants
B · input · E2 · 'RFR'!* · const · 96 · f0ecf5573e46ed76e716f4af0f3aebcb40eb9be9832b2ec16335d16a6daa34ad · input sheet, constants
B · input · E2 · 'LTAS'!* · const · 905 · 8e95f7dca07da03734e4379b1564f9bf9de07940c579e6348b6697d661d82337 · input sheet, constants
B · input · E2 · 'Reference Portfolio Weights'!* · const · 16 · 6445b5e877a8e739cc76719c2c975ac292faec72667da31b1813008d431d6ef8 · input sheet, constants
B · input · E2 · 'Government Bond Ref. Portfolios'!* · const · 366 · f640c30fd7244e4a36e752baf5c077420efc8d8b3e96872631f9e088b09266b9 · input sheet, constants
B · input · E2 · 'Corporate Bond Ref. Portfolio'!* · const · 170 · 89e973b3ca53893b448415ee3299503ccb26cd2ab96b8fd1c93b0017838f4dd4 · input sheet, constants
B · intermediate · E2 · 'Corp Data'!* · formula · 20 · e65e0179676e97f36879b0491c43fe8189fb545dd3540b9b7f1aa56496ce221f · CQS 0 rows by formula
B · intermediate · E2 · 'S&RC Gov Currency'!W45:W47 · const · 3 · 8202f186d97be947c24bada26f3da8bfb67e8cd7b1ba3bdecd267615f9b74066 · IERs set by Solver
B · intermediate · E2 · 'S&RC Corp Currency'!U47:U49 · const · 3 · e726ff65a21f126ec94913d9ba0783bceb03e2469bf0ece822c1c0db05b34a49 · IERs set by Solver
B · intermediate · E2 · 'S&RC Gov Country'!U45:U47 · const · 3 · 87ded3281107d77a102e6243e049347c63812f231e8c49ddb576765c349775da · IERs set by Solver
B · intermediate · E2 · 'S&RC Corp Country'!U47:U49 · const · 3 · 89a3168b38fbfe5a80ee1ed0bd25d2fcfe7fe9e1f9d6498d7ec68046b91de873 · IERs set by Solver
B · residual · E2 · 'S&RC Gov Currency'!V45:V47 · all · 3 · 4c195521c1a51d19c271a7d58b7c6fcdd9b0c5d63637cef619c0d33277d782b8 · Solver objective, squared gap
B · residual · E2 · 'S&RC Corp Currency'!T47:T49 · all · 3 · b2782461eb914663f4201b2aa3a80a5e8a48c7aa1e1b8b16086f021f53ebc349 · Solver objective, squared gap
B · residual · E2 · 'S&RC Gov Country'!T45:T47 · all · 3 · 44712b1539fc2023a36d400867663d9c4740fb7a8a41f83a9b2f87ffee4fc9e6 · Solver objective, squared gap
B · residual · E2 · 'S&RC Corp Country'!T47:T49 · all · 3 · 62d8350d8243ab0613137cd29f79c9e964309bc82501b8645a509e72fac4c33f · Solver objective, squared gap
B1 · output · E2 · 'RCS'!G11:G19 · all · 9 · 6be9886b59c9fdbadfbf7eab5bc3f907caffad2414fcd80f524ff5bfbc9dae8d · EUR: weights, portfolio S and RC, S, RC, RCS
B2 · output · E2 · 'RCS'!K11:K19 · all · 9 · 4a49547d2871680e9cab2b08a7cba9f8d5429f8c9898403cb2d4fb80f3a139b9 · IT: weights, portfolio S and RC, S, RC, RCS
C1 · input · E3 · 'Gov Rates'!* · const · 102 · 71439174866e9630364952113c18e22a00249ba1624b0787a914031eb3ec1479 · input sheet, constants
C1 · input · E3 · 'Corp Data'!* · const · 245 · 8425904e1fa937091f8659af35bfdc08c9b0a798ee34ed92886bf01326d9f4ce · input sheet, constants
C1 · input · E3 · 'RFR'!* · const · 96 · 239ac180c896c55504be3938fd97ac520fa1ee51fb48a4164e66d047179994a3 · input sheet, constants
C1 · input · E3 · 'LTAS'!* · const · 626 · 634e79d968fe619e396e5f3b370f4d04a05b8aa4155af8d8f17edb29bc512b1b · input sheet, constants
C1 · input · E3 · 'Reference Portfolio Weights'!* · const · 9 · 7d590a0539a63186e54ace3b86debb4e684cf1530ae812e7a3507cf7d995497a · input sheet, constants
C1 · input · E3 · 'Government Bond Ref. Portfolios'!* · const · 95 · 03f90df0da6587ef7cd6234cb9d6432f9eb1062cff4500e7579548e3a5f110e4 · input sheet, constants
C1 · input · E3 · 'Corporate Bond Ref. Portfolio'!* · const · 82 · 4876793e14a4ad1f8e75f66e9a94752e1e7dedd7e97b005654bb1be5e7737845 · input sheet, constants
C1 · intermediate · E3 · 'Corp Data'!* · formula · 24 · 032402f4e6e584cb8564378bb552bb6c61a52abcd8ca092d7ba858e8884f82d2 · CQS 0 rows by formula
C1 · intermediate · E3 · 'S&RC Gov Currency'!M45:M47 · const · 3 · 5401157a7e2dda589df8544dd25f59b74f774e8d492a492e767a097c903b66b7 · IERs set by Solver
C1 · intermediate · E3 · 'S&RC Corp Currency'!T47:T49 · const · 3 · 49ebc3668ec4bc4adcdf9561f26f5394042040435076422521145e5a81099876 · IERs set by Solver
C1 · residual · E3 · 'S&RC Gov Currency'!L45:L47 · all · 3 · b8c4b2069ec9c6f893ffc1e9a2192dff3576837bcdae33c802bc6b699bccb4c1 · Solver objective, squared gap
C1 · residual · E3 · 'S&RC Corp Currency'!S47:S49 · all · 3 · 57e0076e7105e3115a34c66a5b8a50af924ea0224994946be71914005bb09b20 · Solver objective, squared gap
C1 · output · E3 · 'RCS'!G11:G19 · all · 9 · 6892f9004c331cbc904d4835e5c0999dc30c2b6987df627466825e24cf44882a · GBP: weights, portfolio S and RC, S, RC, RCS
```
