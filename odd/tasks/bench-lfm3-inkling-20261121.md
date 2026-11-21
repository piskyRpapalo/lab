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

**Upstream compatibility:** LiquidAI's [LFM3 GGUF model card](https://huggingface.co/LiquidAI/LFM3-1.7B-GGUF) requires **Ollama >= 0.40.12**. Do not attempt to run it with any version above; test a portable, isolated recent llama.cpp build or private Ollama runtime without upgrading live services. [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini) (Apache-2.0; 26.4B total, 3.4B active, ~20 GB mixed NVFP4/MXFP8) has published inference support, but AMD device/backend/precision and memory residency remain unqualified. 3.4B active does not mean 3.4B resident.

## Measurement matrix

| Model | Intended host | State | Repetitions | Throughput | Quality/Acho |
|---|---|---|---:|---|---|
| Current SmolLM2 135M Q4 (APP) | Android reference | **NOT RUN** (mini preserved) | 0 | NO_DATA | NO_DATA |
| Qwen3 1.7B control | ARM64 edge board | **RUNNING** | planned 2 x 2 | NO_DATA(pending_remote_receipt) | NO_DATA |
| Qwen2.5 1.5B control | NVIDIA ARM64 edge | **RUNNING** | planned 2 x 2 | NO_DATA(pending_remote_receipt) | NO_DATA |
| LFM3 1.7B Q4 | ARM64 edge board + NVIDIA edge | **HOLD** (new runtime required) | 0 | NO_DATA(no_inference) | NO_DATA |
| Inkling 2 Mini | AMD station | **HOLD** (runtime/format/GPU qualification) | 0 | NO_DATA(no_inference) | NO_DATA |

**Research axes for the follow-on benchmark:** exact plan, correct NO_DATA/false abstention, refusal and revocation by S1, typed source/TTL, intelligible ACHO text/voice/machine equivalence, serial adapter changes, context pinning and cache epoch. A semantic cache or projected H state **is not** a validated shared KV cache across heterogeneous model architectures. Rotation of LoRA heads is hypothetical until the exact trained adapters, model base revision, tokenizer, binding, cache invalidation, rollback and independent judging have all passed.

## Data hygiene and gates

1. Keep full machine-local receipts private under owner-only permissions. Store only counts, digests, commands, sanitized capability descriptions, failures and source/version hashes in PR.
2. Record `NO_DATA` with cause for energy, sensor provenance, placement, model download, runtime/weights verification and any missing benchmark. Failure is an output, not something to hide.
3. A new fit-for-purpose quality holdout must have independent host-owned gold labels and positive/negative sabotage, two repetitions and independent judge; no prompt/result telemetry or secrets.
4. Proposed LoRA family: APP/NODES/ACHO adapters on a **qualified** small checkpoint first. Rotation must invalidate stale task/tool/cache epochs, and must not carry authorization between heads. C2C model-to-model KV stays **HOLD** until layout/dtype/tokenizer/position/head compatibility and leak/revocation tests are measured.
5. PR and CI are **not deployment**. Sovereign holds exact-head HITL for any merge; deployments require separate verified owner action.

## Next action

Finish remote control receipts; qualify private compatible LFM3 runtime without changing the installed Ollama service; confirm Inkling's local runtime against AMD unified memory before 20 GB download; then append exact hashes, sample counts, failures, and narrow verdicts. **NO_DATA(new_models_measured)** until the inference actually occurs.

— Codex GPT-6 · benchmark owner for this isolated study only.
