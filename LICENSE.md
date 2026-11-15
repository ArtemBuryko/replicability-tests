# Licence

This repository holds one replicability test and what a reader needs to check it. What its author can license is licensed here by the kind of file; what is another's is named and left under that other's terms.

## Code — Apache License 2.0

The programs and the configuration the test's author wrote: every `.py` and `.sh` file outside `01-eiopa-rfr-2026/builds/`, and, under `01-eiopa-rfr-2026/preregistration/envelope/`, the container definition, the compose file and the settings files. They are licensed under the Apache License, Version 2.0; its text is `LICENSES/Apache-2.0.txt`.

## Text, tables and records — Creative Commons Attribution 4.0 International

Everything else the author wrote or the test produced: the `.md` files, the tables under `table/`, the manifests and lists, the isolated outputs, the egress logs and the hash files. They are licensed under the Creative Commons Attribution 4.0 International licence (CC BY 4.0); its text is `LICENSES/CC-BY-4.0.txt`. To attribute: the repository's name and address, and the commit.

## What the builders returned, and the review

The files under `01-eiopa-rfr-2026/builds/` are kept as the two builders returned them, and `01-eiopa-rfr-2026/review/REVIEW.md` as the review was received. To the extent the author holds rights in them, the two sections above apply to them by kind of file — code under Apache-2.0, the rest under CC BY 4.0.

## Not the author's — named, and left under their own terms

- **The publisher's material.** The technical documentation and the three workbooks the test reads are EIOPA's. No copy of them is in this repository: `01-eiopa-rfr-2026/source/README.md` points to each by its address and its sha256, and gives each workbook's own source line. Nothing here grants a right in them.
- **Official outputs and the publisher's labels.** Where a file here carries or reproduces a label, the name of a sheet or of a cell, or a value of the publisher's files, that content stays under the publisher's terms, with the source line `01-eiopa-rfr-2026/source/README.md` gives.
- **The timestamp authority's certificate and tokens.** `01-eiopa-rfr-2026/timestamps/chain/DigiCert_Trusted_Root_G4.pem` and the files `01-eiopa-rfr-2026/timestamps/*.tsr` are DigiCert's; they are carried so that a reader can check the dates.
- **The model catalogue.** `01-eiopa-rfr-2026/preregistration/envelope/codex/models-catalog.json` is taken unchanged from the command-line tool builder A ran, at the version the preregistration pins, and stays under that project's licence.
- **Names and marks** of the vendors, products and models the files mention are their owners'.
- **The two licences' texts** in `LICENSES/` are their stewards'.

## The texts in `LICENSES/`

Each is a verbatim copy, taken by command and never typed, from the SPDX licence list's data — `https://github.com/spdx/license-list-data`, tag `v3.29.0`:

| file | from | sha256 |
|---|---|---|
| `LICENSES/Apache-2.0.txt` | `text/Apache-2.0.txt` | `074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff` |
| `LICENSES/CC-BY-4.0.txt` | `text/CC-BY-4.0.txt` | `d557539df68e771cc1eedcc91d13f70fca930e508d11eedcafa4b15db49e3744` |

## The author

No person's name stands in any file of this repository. «The author» is one person: the one recorded in the author field of its commits — the same name and e-mail address on every commit from the first, `61cccd36145e454e643fb1f01a64bcd13840fa50`, to the one that adds this file. `git log -1 --format='%an <%ae>' 61cccd36145e454e643fb1f01a64bcd13840fa50` prints them.
