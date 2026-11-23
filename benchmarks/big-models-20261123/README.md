# Big Models · Hexelion TRAIN-03 · 2026-11-23

Broadcast receipt: figure=GPT-OSS 120B 12/12 exact DEV on 6 cases ×2; Maxwell 0/12 **strict** and 8/12 prefix-exact diagnostic, DIFFERENT RUNTIME | model=ONEXSTATION large-model cohort | machine=ONEXSTATION AMD Radeon 8060S, 96 GiB UMA configured | date=2026-11-23 | sha256=b6d5ee23a126ce46af2fe91a8e542ed4cb1fe935272c68093c15090bb96b1c17 (six-case local summary digest, not a signature).

Benchcard: machine=ONEXSTATION Strix Halo AMD Radeon 8060S | date=2026-11-23 | runner=TRAIN-03 private owner-local E0 two-pass GPU-fenced pilot, sha256 1e3aa556617b654ea8f76e85ad3ec98fb28231d2e5bf52b3d604c3c717cf301f | quant=mixed MXFP4/Q4/BF16 | sha256=b6d5ee23a126ce46af2fe91a8e542ed4cb1fe935272c68093c15090bb96b1c17

**Status:** dated physical DEV scorecard plus incomplete gates; **NOT GOLD**, no winner, no LoRA promoted, no remote dispatch, no real C2C tensor reuse, no autonomous application update. This is the sole new BIG MODELS card in the canonical LAB benchmark index. Prior preflights already merged as [TRAIN-03 report](../../reports/train03-large-model-preflight-20261123.md) and [TRAIN-01/02 readiness](../../reports/train01-train02-training-readiness-20261123.md); do not repeat them.

## What the sovereign brain is being measured for

The target is **one local main orchestrator on ONEX**, not a generic question-answering leaderboard: exact maths grounded in the TRAIN-01 deterministic H02 oracle; complete host-filtered tool plans with no false refusal; safe refusal on revoked or unverified state; ACHO ES/PT machine/voice/visual parity; source-referenced Atlas/RAG; route selection across heterogeneous hardware; bounded rotating LoRA heads, no leak on changed epoch/head; Cache-to-Cache transfer subject to exact manifests; CALM architecture audits; SIM improvements and DREAM replay subject to independent judgement. A model proposal is never a host grant. The alternatives, judge, timestamps and device constraints must remain measurable separately.

### Physical DEV results — incompatible cohorts must not become one ranking

| Model | Cohort | Exact | Strict JSON | Median response | Sampled GPU VRAM peak |
|---|---|---:|---:|---:|---:|
| GPT-OSS 120B MXFP4 | 6×2 | **12/12** | 12/12 | 8.335 s | 65.394 GB |
| Qwen3-Coder-Next 79.7B Q4 | 6×2 | 8/12 | 12/12 | 1.026 s | 52.850 GB |
| Qwen3-Coder 30B Q4 | 6×2 | 8/12 | 12/12 | 0.643 s | 19.958 GB |
| Qwen3.8 27B Q4 | 6×2 | 8/12 | 12/12 | 4.114 s | 18.529 GB |
| DeepSeek-Coder 33B | 6×2 | 6/12 | 12/12 | 4.143 s | 20.869 GB |
| Llama 3.3 70B (historical; tag removed by owner) | 6×2 | 4/12 | 12/12 | 5.604 s | 44.514 GB |
| Mistral Medium 3.5 128B Q4XL | 9×2 | 12/18 | 18/18 | 10.135 s | 77.518 GB |
| LFM3-Omni 2B BF16 | 9×2 | 6/18 | 18/18 | NO_DATA(comparable_latency_not_in_receipt) | 5.465 GB |
| Maxwell V1 Flash BF16 | 6×2 cached, different backend | **0/12 strict** | **0/12** | NO_DATA(per-turn_median_not_in_summary) | 78.150 GB |

**Maxwell important nuance:** its 35 shards/34,270 tensors load fully (~76.12 s); a first real token answered 2+2=4. The cached DEV produced twelve full text generations in 1,042.83 s; all failed the **full output contract** due to trailing think/repeats. Independent diagnostic parsing of just the first JSON object found 12/12 *prefix schema* and 8/12 *prefix exact*, **not** 8 accepted replies. The failures by case also include arithmetic and Portuguese missing-witness answers. Do not promote a prefix parser as a security policy or suppress the strict failure. Preserve weights, investigate EOS/chat template/stop sequences with an unchanged scorecard.

**Untested / not scoring quality:** SenseNova-Loop 9B BF16 = `NO_DATA(unknown Ollama architecture, zero samples)`; Nemotron Super 120B Q4_K_S = two full verified shards (78,040,156,800 bytes), `STAGED_PASS`, no first token; Nemotron 3.5 Lightning 30B Q4_0 = 19,063,900,128-byte SHA-pinned GGUF, no first token; Qwen3.8 Flash Next = `NO_DATA(unsupported tensor importer)`; Kimi Linear 48B has a separate older throughput trial only. Missing samples never score zero quality. No second GPU process may infer from this card's publication.

## Reproduction source, scoring and protections

Physical owner-local original E0 pilot: `train03_brain_pilot.py` SHA-256 `1e3aa556617b654ea8f76e85ad3ec98fb28231d2e5bf52b3d604c3c717cf301f`. Six-case fixture SHA-256 `0094a9b72db89ef84f20f0f252ba5e0f46396022e1276cdd3fbfe4a007dcad1b`. Mistral 9-case fixture SHA-256 `6379e0e15f769b826e47b96d27c5020a1b60ec12fbed959f63c082c6d1c5f2db`. Two repeats, fixed decoding (`temperature=0`, `num_ctx=8192`, `num_predict=512` for Ollama), hard GPU sensor fence, CineK empty-queue check, model unload `PASS_UNLOADED_DMEM0` for the Ollama cohort, **no tool effects**. Direct Transformers/ROCm Maxwell had a distinct cache and timeout path; its elapsed time is not comparable to warmed Ollama medians. The full private receipts, natural language stimuli and raw completions remain on the owner machine and are not sent to GitHub.

### Hard DEV round 2 · started physically, result pending at this cut

- Four installed/pinned Ollama models: GPT-OSS120, Qwen3-Coder-Next, Qwen3-Coder30B, Qwen3.8-27B.
- **14 cases ×2 =28 responses per model; 112 planned**, sealed fixture hash `31b6f48357e4794d7df5f7567a7ebbf061d72b11779e867b64b94d16664f4f25`. Runner wrapper SHA `c5cd51d95a89a7219ecd99043de1a14b5534c2bb8aaae370898bf0e8c5ae361e`; E0 harness unchanged.
- Six independently recomputed mathematical answers (CRT, modular exponent, inclusion–exclusion, combinatorics, weighted shortest path, recurrence); eight controls (host grants, false abstention, revocation race, fake LIVE ES/PT, stale head/epoch KV, Acho field-wise causal isolation, untrusted tool output). No answers published. **`RUNNING_AT_CUT_NO_FINAL`**; scoring, p50/p95, violations and final exit are `NO_DATA(run_not_finished)`.
- Provisional hard cases are **DEV**, not blind gold. The judge must publish a distinct, sealed holdout created independently and must not tune heads on these cases. A GPU lock prevents concurrent model benchmarks/training; the OS memory fence applies to the Ollama service, not all processes.

### TRAIN-01 → TRAIN-02 training reality

TRAIN-01 source H02 oracle and 191 synthetic checks ×2 already passed in the existing training readiness report. TRAIN-02 has **two physically trained LoRA-r8 pilot jobs**: SmolLM2-135M (2 steps, loss 3.1369→3.1148) and Qwen2.5-0.5B (2 steps, loss 2.472406→2.402648). They have C witness, original/adapter hashes and rollback, but **zero demonstrated blind-gold improvement**, no proven destination-device inference ×2, and Qwen's DEV false-LIVE/JSON regression means **NOT PROMOTED**. A lower loss alone does not certify a better brain. Other intended specialists retain explicit readiness gates; do not report an existing GGUF as a trainable PEFT checkpoint.

### Not one monolithic model: mandatory adversarial tracks

| Capability | Existing component and source | Required measured positive + negative comparison | Current gate |
|---|---|---|---|
| Acho H02 mathematics and accessible state | TRAIN-01 H02 oracle; LAB resource/host witness | ES/PT same state+cause+source, field-wise NO_DATA, byte ceiling, visual/speech/machine parity, explicit fake-LIVE controls | Synthetic oracle PASS; real physical audio/UI `NO_DATA` |
| C2C-0 semantic transport | Atlas, `context_window_projection`, `attention_selector`, H02 refs | Plain re-prefill vs typed source refs; useful answers, source fidelity, token/byte use, false permissions | `NO_DATA(cross_model_E2E)` |
| C2C-1 same base/prefix/KV | `head_eligibility`, `c2c-cache-scope` | Same exact base/head/runtime/epoch positive vs adapter 999, changed head, revoked epoch, stale source and hot-cache bleed; require physical readback | Synthetic/old regressions; `NO_DATA(real_KV_readback)` |
| C2C-2 trained exact-pair fuser | `c2c_preflight` pins Qwen3-1.7B receiver / Qwen2.5-1.5B sharer / `nics-efc/C2C_Fuser` | receiver/sharer/text/C2C, same-host first; physical KV/timing/quality, exact revision, tool/permission check | `NO_DATA(real_paired_fuser_evaluation)` |
| Rotating LoRA | `head_eligibility` + `lora_runtime_probe` | Base↔r8↔r16 with cache invalidation and actual active-head readback; compare base/adapter gold, regression and rollback | `NO_DATA(active_head_attestation)` |
| Heterogeneous devices | Existing resource admission / Brain Fabric / host probes | Same task over ONEX, Beelink, Jetson, Fragua, Pi, Android with actual selected runtime, quality, grant witness, p95, energy when measured | `NO_DATA(same_task_distributed_E2E)` |
| CALM architecture | FINOS CALM 1.3 via LAB `calm_atlas_projection.py` (#240/#241 merged) | Reject direct and transitive PUBLIC_REMOTE→PRIVILEGED_NATIVE graph paths; compare actual wiring against declared state | Code/synthetic tests, `NO_DATA(host_runtime_topology_witness)` |
| SIM + DREAM | `improvement.py`, `memory_draft.py`, historical `sueno.py` replay | Four arms: historical observed-alternative replay (time-cut), deterministic H02 metamorphic, bounded random, generative REM. Independent future holdout; unique confirmed failures per CPU-s/1k tokens | Historical source recovered, legacy runtime absent; `NO_DATA(new_DREAM_gold)` |
| Sovereign S1 tool routing | LAB `tool_plan_quality.py` and existing S1 grant/Session | No false grants, no false abstentions, revocation beats MCP ERROR, tool output injection is data not orders, actual host E2E witness | Synthetic/DEV only for these scores; `NO_DATA(full_MODEL→S1→MCP_E2E)` |

**Failure of any safety veto = not eligible for main orchestrator**, irrespective of mathematical score. A model may offer a plan; only the host can verify grants, leases, effects and rollback. Sleep/DREAM may propose DEV samples, never invent measurements or train directly on sealed gold. CALM is the architecture auditor, **not** CALM-theorem inference and **not** a model trainer.

## Next physical gates before training or distribution

1. Complete hard Round 2, evaluate strict JSON and semantic accuracy separately, retain all failures, stop/unload/check GPU; append a dated receipt and CI/test replay under this same card.
2. Reproduce the same cohort on additional model architectures **one at a time** (Maxwell, Mistral, Nemotron, LFM3, SenseNova where loader works) before selecting a local orchestrator; no ranking across heterogeneous prompts and decode settings.
3. Freeze independent source-family gold with an external judge and `meta_harness/improvement.py`. Train only eligible **HF trainable original weights** with base/tokenizer/target/license SHA, a bounded owner OS-fenced lease, untouched fallback and a measurable baseline-vs-adapter increase; quantized inference-only GGUF is **not** training proof. Fine-tune **per exact base family**, distribute compatible, verified adapters only after target-device inference ×2 and rollback. No bulk training on all currently installed weights.
4. Explicit privacy-preserving receipts for C2C 0/1/2, CALM audit, SIM/DREAM and multi-host effect witness; report absent data as `NO_DATA(cause)`. Do not claim 24/7 autonomy, E2E physical voice or full self-modifying APP on this pilot.

[Sanitized per-model observations](observations.json) preserve original numbers, cohort identity and checksum without raw prompts/answers. Existing LAB harnesses, not a second benchmark service, remain the sole executable evaluation authority. **Author:** Codex GPT-6 · **product/final decision:** Soberano. Related science: [Mesa scientific commission](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51#issuecomment-7069629730), [TRAIN-01 recovery](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51#issuecomment-7069720688), [TRAIN-03 claim](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51#issuecomment-7088989595).
