# Declared-depth budget baseline · 2026-10-21

Status: PROPUESTA. The two current guides disagree, so the manifest records both mappings instead of selecting a canon. The checker accepts explicit target roots and budgets; an absent aggregate budget returns `NO_DATA` (exit 2).

| Guide | Depth | Targets | Bytes | Budget | Result |
|---|---:|---:|---:|---:|---|
| profile README | 0 | profile/README.md | 8,917 | 16,384 | LIVE |
| profile README | 1 | depth 0 + profile/llms.txt + four repository READMEs | 32,924 | NO_DATA | NO_DATA |
| product AGENTS | 0 | profile/README.md + web/README.md | 14,261 | 16,384 | LIVE |
| product AGENTS | 1 | depth 0 + study/01-governance.md, 02-legislation.md, 04-measurement.md + lab/README.md | 25,364 | NO_DATA | NO_DATA |

The profile mapping's depth-1 file sizes are 8,917 + 835 + 5,344 + 10,291 + 3,500 + 4,037 B. The product mapping adds 2,678 + 2,792 + 2,133 + 3,500 B to its depth 0. No budget is inferred from these totals. Depths 2–4 remain `NO_DATA`: target suites vary by commission, the active commission is in the Comando, and depth 4 is an event payload rather than a repository tree.

Measured 2026-10-21, local Linux session, Python 3.14; source heads: profile `eb0488a`, web `0240a22`, app `154dd54`, lab `e068fbd`, study `81eb77c`. Manifest SHA-256: `ec61b94124f3fe0bbc8548766f8f23b1ce304638d79a952235c14e313f598c95`. Depth digests: profile D0 `55d69d291dff6d2c59a751c54d025bc58a2c02688a46137d618eddfcee675847`; profile D1 `7c58df53fe5c463d71c073e66c4472f013ee5dc5769c98bbd9d3c64c98eface6`; product D0 `da1c0cb542eb0fa2d754392a148e2503b29e7a249fee70d39c720360767dec79`; product D1 `afd9303673c19a9f1aad6e18b6c37e7cd0f30076a767f30c6f16cda307bed3c6`.

The run is not a green all-depth receipt: D0 passes both mappings; D1 cannot be judged without the missing signed budget and unified target declaration. No targets were edited to fit. The measured total is not an energy result.

Validation on this branch: sabotage (`depth 0 budget=1 B`) returned RED, exit 1; focused tests 6/6 ×2; lab suite 81 passed, 1 skipped ×2; `git diff --check` clean. The compact measurement receipt is 722 B and exits 2 because both depth-1 aggregate budgets are undeclared. This is the expected fail-closed result, not a full-depth pass.
