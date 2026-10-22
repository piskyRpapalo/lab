# Recovered benchmarks

Index of the available measured material, with no new inference. Each card keeps its own yardstick; `NO_DATA` marks a value the source does not substantiate. The local base inventory was checked against `origin/main` 37cd202 on 2026-10-16; this recovery starts from `origin/main` 2cb70d8 on 2026-10-17.

Broadcast receipt: `figure=<value and unit or NO_DATA (cause)> | model=<public label or NO_DATA (cause)> | machine=<class or NO_DATA (cause)> | date=<YYYY-MM-DD or NO_DATA (cause)> | sha256=<source digest or NO_DATA (cause)>`. A digest identifies bytes; it is not a signature.

Broadcast receipts now lead all 26 top-level benchmark cards; unsupported fields retain `NO_DATA` with a cause.

- [Published bench 2026-10-11](bench_20261011/README.md): embedding performance; raw JSON in the same folder.
- [tg32 · measurement date NO_DATA](tg32/README.md): reported throughput; the source session date is absent.
- [G1R evaluation](agent-eval-g1r-20260719/README.md) and [G2](agent-eval-g2-20260719/README.md): operational runs, no quality score.
- [Tool duel](agent-tool-duel-20260718/README.md): exit codes and timeouts, with no common quality judge.
- [G0 · 2026-07-18](g0/README.md): `llama-bench`, harness smoke tests, and local engine smoke test, in separate metrics.
- [Qwen 35B-A3B, 2026-10-16](qwen36-35b-20261016/README.md): `llama-bench` run directly on the existing GGUF; CPU and Vulkan kept separate.
- [Preceptor G0 resumption, 2026-10-16](preceptor-g0-20261016/README.md): one local role test, an unavailable-engine red, and two measured responses.
- [Engine registration and unit smoke test, 2026-10-16](motor-registration-smoke-20261016/README.md): inherited availability state, kept separate from G0 and not used as a yardstick.
- [Model comparison, 2026-09-14](soberano-model-compare-20260914/README.md): four models, per-prompt latency and human judgment.
- [Model smoke test, 2026-09-13](lab-model-smoke-20260913/README.md): four synthetic responses and call metrics.
- [Vulkan series, 2026-09-07](throughput-vulkan-20260907/README.md): seven inherited rows; local identities omitted, measurements intact.
- [llama-bench series, 2026-10-05](throughput-llama-bench-20261005/README.md): runner and axis kept separate from the Ollama series.
- [Vision candidates](artemis-candidates-20260927/README.md): JSON output measurement; does not measure vision.
- [Mechanical fluency · 2026-10-15](bench-fluency/README.md): M1–M4 and all Qwen2.5-Coder receipts.
- [H9 readability](h9-readability-20261016/README.md): control/map/dictionary and dense/prose stimuli; publishes negative results against its own design; original artifacts attached with hashes.
- [M4 judge](preceptor-lora-m4-20260927/README.md): RED evaluation and a retired calibration.
- [Attention selector, 2026-10-17](attention-selector-20261017/README.md): local selector implementation measurement; 24 tests, 0 failures in two independent runs; real-task NDCG NO_DATA (no approved gold set).
- [ideas18oct validation, 2026-10-19](ideas18oct-validation-20261019/README.md): receipt for LAB contracts and live routes on the local Python runtime.
- [Red Team Benchmarks (the Crucible), 2026-10-20](redteam-20261020/README.md): adversarial probes against local open-weight models; scores, verdicts, and the F2 doctrine-smuggling route BLOCKED. Payloads live in the evidence files; read the summary first.
- [Reading-fence probes, 2026-10-21](crucible-reading-20261021/README.md): simulated P4/P5 against the real index guardian; 2/2 detected; remaining probes are NO_DATA by target scope.
- [Harness receipts · 2026-10-20](harness-receipts/README.md): two JSON receipts for the eval harness and receipt formatter (schema `preceptoros.lab.harness-receipt/1`).
- [Phase 0 training](preceptor-lora-training-20260820/README.md): CPU throughput and interpretation limits.
- [Yardstick receipts · 2026-10-19](receipts/README.md): local suite receipt, separate from inference cards.

## Naming note (declared, not renamed)

Folder names remain unchanged; this index carries dates and any missing date is stated as `NO_DATA` in the card title. `harness-receipts/` contains two receipts dated 2026-10-20; `receipts/` holds the separate yardstick receipt dated 2026-10-19.

Inventory census on this base (2026-10-21): 21 index links and 22 card README files before the new harness-receipts index page. The earlier 11/17 coverage denominator is not reproducible from a declared 17-path set; cause: no such scope list is present in this tree.

## FIRMO and recovery limits

The Sovereign's signed order of 2026-10-17 declares these recovered series covered: Vulkan 2026-09-07, llama-bench 2026-10-05, candidates 2026-09-27, Qwen 35B 2026-10-16 (round 97), G0 2026-10-16, M1–M4 fluency, and the two historical training/judge reports. FIRMO is kept as declared provenance; a per-run signature artifact is not included in the lab (`NO_DATA`), and a SHA-256 file digest is not presented as a human signature.

Five local adapters remain registered only as a future evaluation cohort: names, weights, hashes, licenses, and per-adapter results are omitted for privacy; their public availability is `NO_DATA`. The existing training and judge cards are distinct historical experiments, not a substitute for an evaluation of that cohort.

Hardware without a source specification, missing harness hashes, and unmeasured scopes are declared `NO_DATA` in each card. The hashes cited are SHA-256 digests of the indicated source, not an attribution of authorship or independent verification by the team.
