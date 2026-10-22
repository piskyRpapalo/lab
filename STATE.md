# STATE · LAB ecosystem

> Snapshot date 2026-10-22 · measurement hour: NO_DATA (not captured). Proposal, unsigned; values link to dated evidence.

## Live repositories

- WEB `01f8b077` · [preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web)
- APP `d1c8084e` · [PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS)
- LAB `ee537371` · this repository

## Measurements

Machine: Linux x86_64, AMD Ryzen 7 255, 16 logical CPUs; Python 3.14.4.

- LAB `unittest discover -s tests -p 'test_*.py'`: 138 tests, 137 pass, 1 skip, 0 fail ×2 separate runs at `ee537371`.
- LAB live PR workflow, Python 3.10/3.11/3.12: all three jobs RED before tests complete. Each ran 138 tests (137 pass, 1 skip), then `test_llms.py` 2/2; tree verifier rejected INDEX total **13,684 B > 12,109 B**. The same verifier is already RED on clean main: **13,071 B > 12,109 B**. This card compaction is intended to restore the index budget; do not alter the declared budget.
- `.github/workflows/pruebas.yml` exists despite `AGENTS.md` saying remote CI is not configured. Conflict recorded; neither policy changed.
- WEB site counter: **1,429,750 B** at `01f8b077`, from `public/counters.json`; method at WEB `contadores.py:55-65`. WEB and APP suites: `NO_DATA`, cause: not run in this LAB refresh.

## Rack snapshot

Read-only aggregate on this machine, 2026-10-22: Ollama lists **45 models**, summed size **253,307,000,000 B**, with **0 active**; `~/.preceptoros` has **263 files / 49 directories / 5,060,141,941 B**; port 8740 has a listener, PID unavailable; process-name scan found **0** `preceptoros` processes; Tailscale is Running, self online, **5/8 peers online**. No model or peer names copied into this public card.

## Archived benchmark evidence

Measurements remain dated and scoped; they were not rerun for this snapshot. Source cards retain raw provenance:

- Qwen 35B-A3B, 2026-10-16: Vulkan generation 20.760 tok/s (2 samples); CPU 2.114 tok/s (2). [`qwen36-35b`](benchmarks/qwen36-35b-20261016/README.md).
- Local role check, 2026-10-16: unavailable-engine sabotage rejected; two responses matched by hash. One narrow task, not a general capability score. [`preceptor-g0`](benchmarks/preceptor-g0-20261016/README.md).
- H9 synthetic readability, 2026-10-16: map 4/8 exact reads; dense stimulus 0/8 vs prose 2/8. Association only; documents differ. [`h9`](benchmarks/h9-readability-20261016/README.md).
- Embedding, 2026-10-11: embeddinggemma-2 6,459 tok/s, prompt-pair 512. [`bench_20261011`](benchmarks/bench_20261011/README.md).
- Older `tg32` values remain reported; date, machine, command and repetitions are `NO_DATA` because the session log is absent. See [`tg32`](benchmarks/tg32/README.md).

Current temperature, energy, sustained-load behavior, general model quality and live browser performance: `NO_DATA`; these sources do not measure them. Benchmark index: [`benchmarks/README.md`](benchmarks/README.md).
