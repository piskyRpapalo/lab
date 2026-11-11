# STATE · LAB ecosystem

## Latest benchmark verification · 2026-11-11 UTC

**Scope:** GitHub PR heads and completed workflows; **no new model run in this refresh**. [Dated, source-linked benchmark ledger](odd/tasks/benchmark-status-20261111.md) and [Comando receipt](https://github.com/piskyRpapalo/buzon/issues/61#issuecomment-6790565281).

- **Created and merged 2026-11-10:** LAB #144–#149 (F-08, F-09, F-01, index guard, F6 economic, F-11); each exact-head `pruebas` = SUCCESS. APP #235 exact-head `pruebas` = SUCCESS, merged. WEB #799 exact-head `phase`/`gate`/`hitl` = SUCCESS, merged.
- **Created late 2026-11-10; merged morning 2026-11-11:** LAB #150–#154; five exact-head `pruebas` = SUCCESS. Their offline fixtures are **not** live E2E.
- **Created 2026-11-11:** LAB #155–#160 merged with six exact-head `pruebas` = SUCCESS. #158's Gemma2 DFA-B5 experimental result is **RED (4/8 correct ×2)** despite green CI. #159 measured Gemma2 GPU 40.11/40.26 tok/s vs CPU 27.47/27.68 tok/s; #160 matched Qwen3 1.7B endpoints rack 56.08/55.25 vs tunnel 124.99/129.77 tok/s.
- **Still OPEN DRAFT:** LAB #161 (SWARM-01) and #162 (24-case synthetic model matrix); exact-head `pruebas` = SUCCESS for both. No merge declared.
- **NO_DATA:** human gold/calibration, model quality generalized beyond the specific fixtures, energy/J/token, solar autonomy, unattended dispatch, physical screen-reader parity and live deployment. **Reason:** not measured in the referenced receipts. Two successful synthetic test passes do not verify these outcomes.

### Historical snapshot · October 22 (retained, not current)

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
