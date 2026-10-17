# STATE · LAB ecosystem

> Status: PROPOSAL, unsigned. Measurement snapshot: 2026-10-17. This card records
> measured values and links to their source; it is not a promise.

## Repositories

- **WEB** · [preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web), measured at `e1aafeeb`.
- **APP** · [PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS), measured at `3c39596`.
- **LAB** · this repository, measured at `2cb70d8`.

## Measurements taken 2026-10-17

Machine for local test and file measurements: Linux x86_64, AMD Ryzen 7 255 with Radeon 780M Graphics, 16 logical CPUs.

- WEB Node suite: `node --test` at WEB `e1aafeeb` — **244 tests: 234 passed, 10 skipped, 0 failed**. This is the Node test runner only; it is not the Python `test_web.py` yardstick.
- APP Python discovery: `python3 -m unittest discover` at APP `3c39596` — **867 tests: 856 passed, 11 skipped, 0 failed**. This is not `./bin/pruebas`.
- WEB public-site weight: **1,237,121 B across 186 counted files**, recomputed read-only from `public/` with the `contadores.py` exclusions (`downloads/`, `counters.json`, `historial/`; method at WEB `contadores.py:55-65`). The value agrees with WEB `public/counters.json` (`peso_sitio`); no counter was rewritten.

## Recorded benchmark evidence

No inference was re-run for this card. These are dated records in this repository; their yardsticks remain separate.

- Qwen 35B-A3B GGUF, 2026-10-16, `llama-bench`: Vulkan generation **20.760 tok/s** (two samples, SD 0.197); CPU generation **2.114 tok/s** (two samples, SD 1.747). Prefill: Vulkan **294.271 tok/s**, CPU **92.295 tok/s**. Hardware, model and runner hashes, parameters and scope: [`benchmarks/qwen36-35b-20261016/README.md:3-19`](benchmarks/qwen36-35b-20261016/README.md).
- Local role check, 2026-10-16: one unavailable-engine sabotage was rejected; two local responses matched by hash, each with 75 prompt-evaluation tokens and 33 output tokens. Timings were **14.698 s** (13.209 s load) and **1.037 s** (0.002 s load). This is one narrow authority task, not a general capability score: [`benchmarks/preceptor-g0-20261016/README.md:3-15`](benchmarks/preceptor-g0-20261016/README.md).
- H9 readability, 2026-10-16, synthetic fixtures: explicit map without dictionary **4/8** exact reads; dense stimulus **0/8** versus prose **2/8** exact reads. The documents differ in length and content, so this is an observed association, not an isolated causal estimate: [`benchmarks/h9-readability-20261016/README.md:7-17`](benchmarks/h9-readability-20261016/README.md).
- Embedding record, 2026-10-11: embeddinggemma-2 **6,459 tok/s** at prompt-pair 512, sanity cosine similarity **0.908**; raw record and provenance are cited in [`benchmarks/bench_20261011/README.md:3-18`](benchmarks/bench_20261011/README.md).
- The retained inventory and limits of each record are indexed in [`benchmarks/README.md:1-20`](benchmarks/README.md). Older throughput in [`benchmarks/tg32/README.md:1-15`](benchmarks/tg32/README.md) is preserved as reported; exact session date, command, machine detail and repetitions are `NO_DATA` because its source session log is absent.

## Honest limits

- Remote CI for LAB: `NO_DATA` / not configured, as declared in `AGENTS.md`; the LAB yardstick is `python3 -m unittest discover -s tests -p "test_*.py"` and is not represented by the WEB or APP suites.
- Current physical temperature, energy, sustained-load behavior, general model quality and live browser/device performance: `NO_DATA` with cause — the cited benchmark records do not measure those fields.
- The benchmark figures above are archived measurements, not re-measured on 2026-10-17. Each source retains its own date, machine, method and scope.
