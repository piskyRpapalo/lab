# Context fusion · calibrated synthetic evidence windows · 2026-11-20

Broadcast receipt: figure=64/64 calibrated vs 19/64 unaligned, 64/64 poisoned-anchor refusals | model=NO_DATA(no model inference in scored run) | machine=Beelink-class x86_64 | date=2026-11-20 | sha256=6f987077f77509a50901f5a4bbd69a6302c7174c46d8ab0b40c7ea0e5f269df8 (stdout JSON receipt).
Benchcard: machine=Beelink-class x86_64 | date=2026-11-20 | runner=python3.14.4 stdlib on disposable LAB branch checkout | quant=NOT_APPLICABLE(no model weights) | sha256=22322bf0d48f0c0fca1f1a5fdb17874961cba7b540564bb087347e67829c5cf8 (runner source).

**Measured synthetic fixture, not cross-model KV fusion.** No private context, raw model replies, tool dispatch, weights, permissions or production services were used. The two context budgets count **evidence slots, not LLM tokens**. A single short window contains one fact; the separate longer window contains a target and two distractors. The requested answer needs the fact from both windows. A 2D rotation creates an artificial incompatibility between their semantic coordinates.

## Mathematical gate and two independent predicates

The 2D orthogonal Procrustes gate fits the angle from **four** known (A,B) anchor-vector pairs. It checks cosine agreement on **three disjoint holdout anchor pairs** before ranking the second window's evidence. This is a calibrated **prototype alignment**, not a trained neural fuser. The two predicates are:

1. **Math alignment judge:** heldout anchor similarity at least 0.995, retrieval cosine at least 0.975, winner margin at least 0.05. Ambiguous matches fail closed.
2. **Synthetic source judge:** current scope/generation, fresh, permitted, independent host-witness Boolean and digest of source bytes. These fixture flags do **not** constitute a real host signature or trusted attestation.

Actual S1 host permissions, cache epochs, model/LoRA/fuser pins and KV alignment would have to be proven independently before live use. The existing [C2C cache scope contract](../../odd/tasks/c2c-cache-scope.md) remains authoritative.

## Reproduced results

Method: 64 deterministic cases, seed 20261120; 1+3 evidence slots; 4 calibration anchors + 3 holdout anchors per case. Two fresh Python processes produced **byte-identical JSON stdout** (SHA-256 above). Results are **counts over the same 64 constructed cases**, not 704 independent examples or model-quality percentages.

| Arm / negative control | Correct retrievals | Fail-closed or unresolved |
| --- | ---: | ---: |
| Short window only | 0/64 | 64 missing second source |
| Raw concatenation, no alignment | 19/64 | 45 unresolved |
| Calibrated vector alignment + source judge | **64/64** | 0 |
| Poisoned training anchors | 0/64 | 64 refused alignment |
| Anisotropic nonorthogonal geometry | 0/64 | 64 refused alignment |
| Revoked grant | 0/64 | 64 refused source |
| Stale evidence | 0/64 | 64 refused source |
| Wrong generation | 0/64 | 64 refused source |
| Wrong namespace | 0/64 | 64 refused source |
| Missing synthetic witness | 0/64 | 64 refused source |
| Source bytes changed without fresh digest | 0/64 | 64 refused source |

The vector geometry is deliberately simple and noise-free in its main arm. The controlled shifts are known. The holdout anchors share the same synthetic generator as training anchors. **64/64 is a mathematical fixture result, not a model generalization claim.**

Two already-installed local Qwen3.5 models (4B and 9B) provided **advisory hypotheses only**. Both identified the assumption that real embedding geometry may not preserve a single clean rotation; this motivated the anisotropic negative control. These suggestions are neither calibrated judges nor independent evidence for correctness. No raw LLM outputs are committed.

## Reproduce

~~~sh
python3 -B benchmarks/context-fusion-20261120/context_fusion_bench.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_context_fusion_bench.py -q
~~~

Execute twice on a clean branch checkout; compare whole-output SHA-256. Source runner SHA-256 is bound above. Measured on the Beelink-class host on 2026-11-20: **14 directed tests × 2 PASS**. Entire LAB Python discovery also measured **1281 tests × 2 PASS, 2 existing skips per pass**, on the same isolated checkout. Python 3.14 emitted warnings concerning unclosed SQLite connections in an existing meta-harness module; the run completed with zero failures. This is local verification, not GitHub Actions exact-head CI.

## Implications and limits

**Hypothesis:** a unified orchestrator can use distinct context windows for retrieval and share *source-bound semantic projections*, without claiming their token windows or model KV tensors combine. A second, independent validity gate can prevent the mathematical selector from promoting stale or incompatible evidence.

**NO_DATA:** real token-window benefit; learned embeddings; cross-model KV or latent-cache translation; token/layer alignment; trained fuser; independent real-host cryptographic witness; calibrated semantic model judges; energy cost; end-to-end APP/Acho accessibility; transfer to new tasks or architecture. No adapter promotion is authorized.

This study reuses LAB's [attention selector](../attention-selector-20261017/README.md), [meta-harness receipts](../receipts/20261112-meta-harness-summary.md), and existing S1/C2C contracts. It does **not** create a second cache, RAG index, mission registry or model-serving route. Related scientific motivations: [Google SIM](https://arxiv.org/abs/2611.18856), [Cache-to-Cache](https://arxiv.org/abs/2510.03215), [HeteroFold](https://arxiv.org/abs/2609.32259), and [dual-cache communication](https://arxiv.org/abs/2608.20617); no vendor metric is adopted as a local result.

**Next piece:** run the existing attention selector with a permitted, signed public retrieval gold set across two actual model context limits; then qualify a real, pinned C2C fuser separately. Link this card through the canonical [Benchmarks index](../README.md), which is already linked by the [public GitHub profile](https://github.com/piskyRpapalo/piskyRpapalo#benchmarks). Publication is proposed on a draft PR and requires human exact-head review.

— Codex GPT-6 · deterministic study, not a production capability
