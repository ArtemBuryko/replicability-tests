# Replicability tests

A replicability test asks whether a public text that publishes worked examples can be implemented from its documentation alone. Two blind builders of different model families each build it; their outputs are set against the publisher's own examples; every divergence is attributed on stated grounds; a separate AI review — using Grok in test 01 — reads the attributions; and one command checks the record. The command checks artifact integrity, regenerates the comparison table and computes the outcome from the recorded attribution statuses. It does not assess the grounds of those attributions. Each test is a folder, complete in itself. A test makes no regulatory-accountability claim of any kind, and it attributes no error to a text's owner.

## The tests

| test | the text | the result |
|---|---|---|
| [`01-eiopa-rfr-2026/`](01-eiopa-rfr-2026/README.md) | EIOPA's RFR Technical Documentation (EIOPA-BoS-26/198), with its three workbooks of worked examples | `outcome: not reproduced` — five of the six declared cases reproduced; `C1: not reproduced — the text: G.5.5 with G.5.3; G.1.2` |

The result is given in the words `verify.sh` prints; what they mean, and what the test does not show, is in the folder's `README.md`.

## To check a test

```sh
sh 01-eiopa-rfr-2026/verify.sh "$HOME/eiopa-rfr-files"
```

The folder named last is where the command keeps the publisher's four files, which this repository does not hold: it fetches each one there, and a later run finds them there. `$HOME/eiopa-rfr-files` is an example; any folder will do, and the command makes it if it is not there.

It needs Python 3.9 or later and `openssl`, and `git` where the repository is a clone. It fetches the publisher's files, checks every hash and every timestamp token, makes the pass-or-fail table again and computes the outcome from the recorded attribution statuses. It does not assess the grounds of those attributions.

## Licence

Code under the Apache License 2.0; text, tables and records under CC BY 4.0; the publisher's material, and whatever else is another's, named and left under its own terms — `LICENSE.md`.
