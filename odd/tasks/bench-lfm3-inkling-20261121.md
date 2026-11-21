# LAB · Multimodel bench: LFM3 vs Inkling 2 Mini · 2026-11-21

> **State:** IN_PROGRESS / isolated remote experiments. This document is an experiment card, not a deployment authorization or model endorsement. **Authority:** Sovereign; Codex GPT-6 author. Coordination: [Mesa #51](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51#issuecomment-7068884645).

## Decision boundary

- Keep the existing Android MINI unchanged, including SmolLM2-135M base and its fallback. One APP per device. Future model packs are **optional**; no bundled replacement, no unsigned download, no second APP.
- Private LAB aims to compare base models on their **actual resident remote hosts**, then separately qualify instruction/LoRA specialization, Acho/H state mapping and cache-to-cache. Model capability never grants execution privileges; the existing Sovereign S1/host policy decides.
- Lab first; publication to contributors only after license, package integrity, physical Android E2E, a11y and thermal/battery gates. No training from revealed independent holdouts.

## Existing instruments, no new benchmark framework

- Reuse [BENCH-REPRO-01](bench-repro-01.md), its [`smoke.py`](../../benchmarks/station-96-first-pass-20261029/smoke.py), [public fixture](../../benchmarks/fixtures/throughput-public-v1.json), and [benchmark contributor guidance](../../docs/contributing-local-benchmarks.md).
- Two attempts per invocation, two independent invocations (4 total); fixed public controls: `temperature=0`, `seed=42`, `num_ctx=2048`, `num_predict=64`, `stream=false`, `think=false`, `keep_alive=0`; local loopback on the target; never pull implicitly; response body not persisted, only SHA and sizes.
- Distinguish runtime-provided counters (`eval_count`, `eval_duration`, `load_duration`, wall time) from host sensors; performance != task quality. Do not sum GPU/CPU memory, or call power (W) energy (J/token). Report failure/skip in denominator.
- For planner quality, use the pre-existing `meta_harness` / `task_binding` / `context_window_projection` and a **new** family-separated host-supplied gold set. Previous 24-case holdout (17/24) is exposed and must not be trained against.

## Hardware preflight (remote SSH, 2026-11-21 UTC)

| Host class | RAM available | Disk available | Ollama | Installed test candidate | Model preflight |
|---|---:|---:|---|---|---|
| AMD unified-memory station, x86_64 | 27 GiB visible OS RAM | 85 GB | 0.40.3 | existing 71 GB checkpoint (not a comparable small control) | Inkling 2 Mini **NO_DATA(runtime_and_gpu_precision_unqualified)** |
| NVIDIA ARM64 edge node | 5.7 GiB | 64 GB | 0.33.2 | Qwen2.5 1.5B, among existing models | LFM3 **HOLD(runtime_too_old)** |
| ARM64 edge board | 13 GiB | 27 GB | 0.24.0 | Qwen3 1.7B, among existing models | LFM3 **HOLD(runtime_too_old)** |

Direct remote identities were verified through the owner's existing SSH known_hosts with `StrictHostKeyChecking=yes`. The Beelink was an SSH pass-through only; inference for the above cohort belongs on the remote endpoints. OS RAM and GPU memory are separate accounting domains.

**Upstream compatibility:** LiquidAI's [LFM3 GGUF model card](https://huggingface.co/LiquidAI/LFM3-1.7B-GGUF) requires **Ollama >= 0.40.12**. Do not attempt to run it with any older version; test a portable, isolated recent llama.cpp build or private Ollama runtime without upgrading live services. [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini) (Apache-2.0; 26.4B total, 3.4B active, ~20 GB mixed NVFP4/MXFP8) has published inference support, but AMD device/backend/precision and memory residency remain unqualified. 3.4B active does not mean 3.4B resident.

## Measurement matrix

| Model | Intended host | State | Repetitions | Throughput | Quality/Acho |
|---|---|---|---:|---|---|
| Current SmolLM2 135M Q4 (APP) | Android reference | **NOT RUN** (mini preserved) | 0 | NO_DATA | NO_DATA |
| Qwen3 1.7B control | ARM64 edge board | **MEASURED** | 2 x 2 = 4 | 9.228603 / 10.007279 / 9.989695 / 9.395382 tok/s; median **9.692539 tok/s** | NO_DATA(no_quality_eval) |
| Qwen2.5 1.5B control | NVIDIA ARM64 edge | **MEASURED** | 2 x 2 = 4 | 35.630617 / 35.871705 / 33.270639 / 35.834387 tok/s; median **35.732502 tok/s** | NO_DATA(no_quality_eval) |
| LFM3 1.7B Q4_K_M | Orange Pi CPU, Onexstation CPU; Jetson pending | **MEASURED** on two hosts | 2x2 Orange; 1x2 Onex | Orange 12.451633 decode tok/s; Onex 51.747535 decode tok/s | NO_DATA(quality_not_independently_judged) |
| Inkling 2 Mini IQ4_NL | AMD station | **MEASURED_CPU_ONLY** (GPU HOLD) | 2 x 2 (prefill/decode) | prefill 61.923764 tok/s, decode 12.455315 tok/s | NO_DATA(pending_quality_exploratory) |

**Research axes for the follow-on benchmark:** exact plan, correct NO_DATA/false abstention, refusal and revocation by S1, typed source/TTL, intelligible ACHO text/voice/machine equivalence, serial adapter changes, context pinning and cache epoch. A semantic cache or projected H state **is not** a validated shared KV cache across heterogeneous model architectures. Rotation of LoRA heads is hypothetical until the exact trained adapters, model base revision, tokenizer, binding, cache invalidation, rollback and independent judging have all passed.

## Inkling 2 Mini CPU-only GGUF receipt (2026-11-21)

On remote AMD x86_64 unified-memory station, isolated `llama.cpp` compiled at source commit `e6d624b9a4b95c6b52f5ca384d70b75581f9821a`, standalone binary digest SHA256 `74aadfd64422a6f749878e9d10455149345dad70098303cc052600c52ef9339c`; **not** the installed Ollama service. Official ggml-org Inkling-2-Mini `IQ4_NL` file size **17,627,940,768 bytes**, independently matched official LFS SHA256 `cbdf3fa9dc50a4124977980f37da4f1fa764b0cfe800d275cd43d26ce2a81af4`. This is **not** the original mixed NVFP4/MXFP8 checkpoint and makes no claim for its performance.

Direct `llama-bench` CPU-only `-p 128 -n 32 -r 2 -t 8 -ngl 0 -o jsonl` exit 0, 16.093 s wall. Prefill 128-token samples **64.3852 / 59.4624 tok/s**, average **61.923764** (SD 3.480928); generation 32-token samples **12.2757 / 12.6349 tok/s**, average **12.455315** (SD 0.254022). Raw benchmark result stays private with exact SHA256 `a68a5b5a1ffa589b8b7179dee4e54560f4d508624c11ea96521a98a55ee6ca7e`. No power or RAM peak sensor capture in this first test. **NO_DATA(Inkling_GPU;Inkling_model_quality;LoRA_trainability;Android_run;cross_model_KV)**. This is a new `llama-bench` yardstick and **not comparable to the Ollama 64-generation-token controls without re-running both in the same engine and settings**.

## First remote receipts (2026-11-21; exact existing LAB runner)

Two independent runs of the two-sample `bench-repro-01-v1` harness completed directly on the two ARM64 nodes. Both reported `MEASURED` and stable model digest, 4/4 valid generated samples, 0 failures. Throughput is a separate axis from accuracy. The model identities differ and the GPU/CPU placement was **not** independently attested, therefore **do not treat the two medians as a normalized speed ranking**.

- ARM64 board / Qwen3 1.7B: on-device receipt SHA-256 `8b49954d8f271cc35b2fddb7485d9af2d6d41c21dfc01cd174f25e448d9fb931`.
- NVIDIA ARM64 / Qwen2.5 1.5B: on-device receipt SHA-256 `816753c2d09ea1995de112843a269e67e7871fd258874e9f0010ec654a106101`.
- Shared runner SHA-256: `5353703ce37fc9563c0e0a30b6f2478cf42ecc93617c9db0a37c1276bf178819`; fixture SHA-256: `5bf9fa9a054054d541696c016b04f340bed289700cbd2b8ebeb9826e88020f8c`.
- These exact receipts remain private and owner-readable on their respective hosts; GitHub carries only sanitized counters and digests, not private output text or host user paths. No APP change, training, or model downloads occurred during these two control runs.

## Existing C2C & LoRA contract

Reuse [`c2c-cache-scope.md`](c2c-cache-scope.md), `c2c_preflight`, `head_eligibility` from merged LAB [#207](https://github.com/piskyRpapalo/lab/pull/207), and the `ModelWindow` + `BoundWorker` from Brain Fabric. Do **not** create parallel adapters or a cache store. Bind `base_ref`, `head_ref`, tokenizer/runtime refs, `fuser_revision`, source `selection_ref`, policy/permission epoch, device and session in the decision key; invalidate on head change/revocation/context drift. Existing readiness checks explicitly set `cache_reuse_authorized=false`; no real intermodel KV has been proven. ACHO/H projects the same evidence state to text/voice/machine and must keep `NO_DATA(cause)` after a failed witness; model-generated persona is not permission.

## LFM3-1.7B Q4_K_M on two physical CPU architectures (2026-11-21)

Identical **verified** GGUF binary on both hosts: 1,099,627,808 bytes, SHA-256 `3793e1e6e2266919d6e015287221b41100175a98eddaba92e111aed3b05c93c4` from LiquidAI's pinned release. Source code: `llama.cpp` `e6d624b9a4b95c6b52f5ca384d70b75581f9821a`. No active Ollama service updated, unloaded or modified. Both used `llama-bench`, CPU-only, `-p 128 -n 32 -ngl 0`.

- **Onexstation**, AMD x86_64 station, **8 CPU threads**, binary SHA-256 `74aadfd64422a6f749878e9d10455149345dad70098303cc052600c52ef9339c`: two prefill samples **402.809 / 402.478 tokens/s**, mean **402.643532**; two decode samples **51.7483 / 51.7468 tokens/s**, mean **51.747535**; exit 0. Receipt SHA-256 `22c402f688edfcaf2d2e960bf33f6ead39a1b7b4d4ee037a202227760debc63b`.
- **Orange Pi**, ARM64 node, **4 CPU threads**, binary SHA-256 `cc0f944b327a3445bc9f5b82c699ce344cd7572511f9b3d0c5845c4b2a9ca1d3`: two independent executions, two samples each. Prefill **17.0966, 17.0768, 16.9890, 17.0309 tokens/s**, median **17.05385**, mean of two per-run means **17.0483135**. Decode **12.3459, 12.3498, 12.5567, 12.5542 tokens/s**, median **12.452**, mean of per-run means **12.451633**; 0 failures. Receipt SHA-256 `c23651f8408cdd4e97488b0ca09d3494d8ff6c3eb8a77d09b80e40b98c892714`.

**Comparison limits:** same model/quantization and benchmark settings except thread count and host, not a hardware-normalized inference comparison. The Onexstation Inkling and LFM3 experiments match backend, threads and prompt settings, but differ substantially in size/architecture. Report the ~4.15x CPU decode throughput only as this *one* bounded experiment, not intelligence, tool competence or energy ranking. Thermal and power capture were not included. The earlier Orange/Jetson Ollama throughput controls have a different generation length/runner and must not be compared as identical experiments. **NO_DATA(physical_Android_LFM3;Jetson_LFM3_bench;independent_tool_use_quality;GPU_backend;energy;LoRA_training;cross_model_KV).**

## CLI structured-output exploratory failure (not model-quality verdict)

An unqualified exploratory `llama-cli` prompt-only trial on Inkling reported 0/6 unique JSON objects; inspection showed interactive chat/reasoning/prompt echo in captured stdout, and stopping at the generation limit, making the parser/answer boundary unsuitable for semantic scoring. Its private receipt digest is `07a4719b0682f1a7528f68262ff011a959433035d277bf02f9f3c351813d72aa`. Preserve this failure as **NO_DATA(valid_semantic_evaluator)** rather than asserting that Inkling cannot follow instructions. Next evaluator uses isolated `llama-server` OpenAI-compatible chat messages, explicit output grammar, sealed synthetic tasks, and retains separate validity/exactness metrics. Even then labels authored for this study are *not* independent held-out gold.

## Data hygiene and gates

1. Keep full machine-local receipts private under owner-only permissions. Store only counts, digests, commands, sanitized capability descriptions, failures and source/version hashes in PR.
2. Record `NO_DATA` with cause for energy, sensor provenance, placement, model download, runtime/weights verification and any missing benchmark. Failure is an output, not something to hide.
3. A new fit-for-purpose quality holdout must have independent host-owned gold labels and positive/negative sabotage, two repetitions and independent judge; no prompt/result telemetry or secrets.
4. Proposed LoRA family: APP/NODES/ACHO adapters on a **qualified** small checkpoint first. Rotation must invalidate stale task/tool/cache epochs, and must not carry authorization between heads. C2C model-to-model KV stays **HOLD** until layout/dtype/tokenizer/position/head compatibility and leak/revocation tests are measured.
5. PR and CI are **not deployment**. Sovereign holds exact-head HITL for any merge; deployments require separate verified owner action.

## Next action

Remote controls, Inkling CPU-only, and LFM3 CPU-only on Onexstation and Orange Pi are recorded above. Jetson LFM3 compilation, GPU acceleration and host-independent task-quality suites remain pending. Study LoRA only with exact trained-compatible checkpoint and unexposed holdout.

— Codex GPT-6 · benchmark owner for this isolated study only.
