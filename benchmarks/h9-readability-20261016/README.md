# H9 — state readability and stimulus comparison

Original artifacts preserved in `evidence/`, copied from the durable backup of 2026-10-16; SHA-256 of each JSON in `evidence/SHA256SUMS`. This card reconstitutes measures already taken; it does not invoke the model again. The rescue source is identified as `rescate/m1-vector-audio-20261015` in the origin receipt; commit `ade5244`; web main read `258d490017cfadb5fce61453eca21aad5b3811d9`. Source vector SHA-256 `ca8371a3a62b2a4cf41b9ddf1633351fb86dfdd983bf9e4e8c2d27714151954e`.

Model Qwen2.5-Coder 1.5B SHA-256 `29d8c98fa6b098e200069bfb88b9508dc3e85586d20cba59f8dda9a808165104`; runtime llama-completion b10068 SHA-256 `7119bef261611b26f326f7c4da4dc3fdeb7bb28e2faf1ec392bda7b21215ef52`; Ryzen 7 255, CPU 1 thread, GPU layers 0, offline, temp 0, seed 14, context 4096, two passes, fresh process per read (evidence `h9-prompt-current-main.json` and `h9-stimulus-current-main.json`). Sampled token count: NO_DATA, the runtime only gives evaluation units.

## Yardstick A — state reading: 32 total reads

Each arm: 4 synthetic fixtures × 2 passes (8 reads), valid JSON output 8/8. Semantic accuracy and median: control without dictionary 2/8, 9.432 s (`evidence/h9-prompt-current-main.json:21`); control with vector dictionary 0/8, 13.115 s (`:27`); explicit map without dictionary 4/8, 11.155 s (`:33`); explicit map with dictionary 4/8, 14.831 s (`:39`). The observed contrast of the dictionary in the control is −25 percentage points; it does not demonstrate general causality.

## Yardstick B — dense llms.txt stimulus versus prose README

Same model, source, fixtures, and parameters; two passes × four fixtures per arm. Dense 5,327 B (`evidence/h9-stimulus-current-main.json:21`), SHA `69138d63ecef10b2adea5802f0a45f31ae75b9138f4a7b16ce6a4b2841dd43ac`: 0/8 exact reads, 8/8 valid format, 30/48 correct fields. Prose 7,344 B (`evidence/h9-stimulus-current-main.json:26`), SHA `4bc8a37692faff02bdf4155328b2febeddd75a4b27ed0ec3e0d26982193a13e1`: 2/8 exact, 6/8 valid format, 26/48 correct fields. Reference without stimulus: 2/8 exact. Dense −25 pp versus control; prose 0 pp. There is one Unicode format failure in two prose reads. The documents also differ in length/content: observed association, not causal isolation of density.

## Gates and coverage

Directed receipts, each repeated twice: core cases 16/16 in both (`evidence/h9-cases-1.json:3-4`, `h9-cases-2.json:3-4`); named 13/13 in both (`h9-named-1.json:3-4`, `h9-named-2.json:3-4`); geometry 12/13 in both (`evidence/h9-geometry-1.json:3-4`, `h9-geometry-2.json:3-4`), same persistent failure: the measured manifest does not match the expected source artifact (expected hash `562879f4378a7dcce6e38f65ec6f112a920ca828204d5ab7affc8cbdbc2427cd`, current source `10096864defe4c32cf77c80d966fcdd897c79505305744bbd0b5983c3ea84791`). Separate red `evidence/h9-red.json`: the UTF-8 limit test failed per fixture; the rest is preserved in the artifact. The JSON audit declares synthetic/offline scope, with no real visitor and no live SLM read. Energy data: NO_DATA.
