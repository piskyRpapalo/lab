# TRAIN-01 → TRAIN-02 · physical training readiness (2026-11-23 UTC)

**Measured preparation, not another training run.** Agent: Codex GPT-6 · CEREBRO. Owner: Soberano. Scope: reuse existing deterministic TRAIN-01 oracle, TRAIN-02 A science contracts, B guarded PEFT/LoRA runners, C owner-scoped OS fence and training outputs. Source: ONEXSTATION owner-local readback via existing authorized SSH, original A v1.2 archived source; local receipt `hexelion.train01-train02.training-readiness/1` SHA-256 **`d532cb3fc6220ac276e0997484a66fe2a6b2acbde574a9ac17a1ddc0fcb2b7f3`**. No prompts, sample text, weights, private host addresses or owner filesystem paths published.

## TRAIN-01 is a deterministic oracle, not a trained model

The original `reference_train01/acho_h02_oracle.py` is physically present **inside the already-staged TRAIN-02 A v1.2 source bundle**. Verified source SHA-256 `9e79c4760a6429d3839f8dfe380808d3d2b307a0e10fdd116d58764f51fdcb73`; original A bundle SHA-256 `f8f3042489be4b372a4145dd929283eac0afaa663ccabeb97d74b52128ef2883`. No new oracle built.

Its scope is the *synthetic DEV* H02 canonical state to Acho's accessible `explain_state` contract. Controls include exact missing-data causes, fail-closed fake LIVE/grants, state-reference digest, ES/PT identity, readable output equivalence and bounded JSON bytes. **It does not authenticate an OS host, validate natural-language quality, or authorize tools.**

**Reproduction executed ONEXSTATION, isolated temporary extraction, read-only originals:** `PYTHONPATH=reference_train01:. python3 -B -m unittest -q reference_train01.test_acho_h02_oracle test_a_train02 test_hardening test_multiskill_dev test_bridge_and_ablation test_historical_audit` → **191/191 PASS ×2**. No GPU/model effect. Archive's A v1.2 five-target matrix and evaluation protocols remain the canonical training plan; not replaced by a new schema.

## TRAIN-02: two physical ROCm LoRA runs already happened

| Job / target | Base model / LoRA | Physical outcome | Promotion gate |
| --- | --- | --- | --- |
| `hexvigia-smoke-20261121-first` · Raspberry Pi witness | SmolLM2-135M-Instruct, LoRA-r8 | 2 steps, loss **3.1369 → 3.1148**, gradients finite; C owner witness, exit 0, OS fence | **NO_DATA(target_inference_x2; blind_holdout)** |
| `hex-jetson-acho-guide-20261122-01` · Jetson Acho GUIDE6 | Qwen2.5-0.5B-Instruct, LoRA-r8 (q_proj/v_proj) | 2 steps, loss **2.472406 → 2.402648**, gradients finite, **540,672 trainable parameters**; C owner witness, exit 0, OS fence | **FAIL(exposed_DEV_quality_no_gain_and_false_LIVE)**, **NO_DATA(target_inference_x2; blind_holdout)** |

**New physical verification this session:** re-hashed each original base checkpoint and training dataset, both `loss.jsonl`, `adapter_model.safetensors`, `adapter_config.json`, merged weights/config/tokenizer, train receipts and independent C-owner witness binding. **All recorded SHA-256 values matched** for both jobs; C witnesses declare `child_exit_code=0`, `trained=true`, `os_fenced=true`, and `promotion_authorized=false`. The user-scoped systemd fence limits RAM, but PyTorch allocator limits are not a universal AMD UMA GPU quota.

**Independent quality warning:** existing [A07 physical CPU evaluation](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51) already compared Qwen baseline and merged adapter on **exposed training examples**: 4/4 H02-guide responses failed strict JSON and exact six-field target; on missing-provenance DEV case, both BASE and merged emitted an unsupported online/LIVE claim. Same output hashes for several BASE/merged pairs. This does **not** warrant longer SFT or promotion. The reported 64 synthetic GUIDE examples are train-only, with **zero independent blind gold**; the two optimizer steps touched four declared samples, not proof of mastery of 64.

## Safety regression discovered during preflight

Original `test_c_owner_os_fence.py` ran **10 PASS / 1 FAIL** on the current owner-side SSH context. The failing assertion expected only `owner_uid_not_authentic|host_identity_mismatch`, but the actual C guard **correctly denied execution** with `NO_DATA(systemd_cgroup_not_bound)` outside its authorized training scope. This is a **test expectation defect, not a proven security bypass**.

Original test SHA-256 `2d08601cb0b1a922ba80ff46d0c066fbaa1d90981765d3a601f22a27916aad7c` **untouched**. In a temporary throwaway copy, accepting that additional known fail-closed cause produced **11/11 PASS ×2**; temporary SHA-256 `1bd6a70586bb57f5e8c6975c095942bed960bf8ac93ee4f1b422d82a6d6b0d71`. Follow-up is a narrowly reviewed source-test correction, not relaxation of C permission guards.

## Host/readiness snapshot and target nodes

At **2026-11-23 ~01:04 UTC**, ONEXSTATION GPU system VRAM used `612,917,248 B` of `103,079,215,104 B` and free disk approximately **89.5 GB**. CineK queue `0/0`, both Ollama resident-model lists empty, advisory GPU lock momentarily available; **no OS training lease was taken**, so this is not ongoing exclusive authority.

Two physical read-only target checks from the rack confirm:
- **Jetson / la-torre:** Linux `aarch64`, **7.4 GiB RAM total**, ~4.5 GiB available, **62 GiB storage free**. Neither target inference nor model installation was performed in this check.
- **Raspberry Pi 5 / el-vigia:** Linux `aarch64`, **4.0 GiB RAM total**, ~3.5 GiB available, **46 GiB storage free**. Neither target inference nor model installation was performed in this check.

## Five A v1.2 task skills and next bounded actions

1. `HEX_PLAN_CRITIQUE_REPAIR_TYPED` (ONEX planner): **NO_DATA(trainable Qwen3-4B base checkpoint; blind gold; promotion)**.
2. `ACHO_CANONICAL_STATE_TO_INTENT_GUIDE_ESPT_VIEW_HINT` (Jetson): physical Qwen2.5-0.5B LoRA **trained DEV**, **quality FAIL**; first compare D0 deterministic template, D1 base with output grammar, D2 merged LoRA with identical prompt/decoding and a new independent family-split holdout.
3. `HEX_MCP_TOOL_SELECT_TYPED_NO_GRANT` (Orange Pi): **NO_DATA(license, suitable trainable base, physical train and holdout)**; **never** equate model selection with an OS grant.
4. `ACHO_SENSOR_ALERT_NO_DATA_EPOCH_TYPED` (Raspberry Pi): physical SmolLM2-135M LoRA **trained DEV**; **NO_DATA(target inference ×2 and independent holdout)**.
5. `HEX_APP_OWNER_HELP_DIAGNOSTIC_ROUTING` (Beelink): **NO_DATA(new task-scoped trainable model/data and eval)**.

**Next work item before any optimizer steps:** custody/freeze of **independent source-family holdout** with missing-witness, revoked grant, false LIVE, inaccessible view/audio mismatch and ES/PT paired provenance; compare the existing D0/D1/D2 outputs first; preserve the hard-veto negatives and raw samples on the owner host. Use existing LAB evaluator and TRAIN-02 executors, *not another trainer*. Pre-registered effect-size thresholds in A are proposed, **not signed GOLD**.

**Large-brain distinction:** the ~78 GB Nemotron Super 120B `Q4_K_S` GGUF just downloaded is an **inference artifact**. It is not proof of a trainable ONEX ROCm PEFT checkpoint. No full-120B training runtime, optimizer memory budget, licensed exact training source, or blind task-specific gold has been verified. **NO_DATA(large_120b_training_ready)** until those concrete items exist; model choice awaits the same-cohort benchmark.

**Disposition:** `PASS(preflight_source_and_artifact_integrity)`; `PASS(TRAIN01_synthetic_oracle_191x2)`; `FAIL(original_C_test_expectation)`; `PASS(isolated_negative_C_test_11x2)`; `NO_DATA(blind_gold_and_edge_x2)`; **TRAINING_NOT_STARTED_THIS_TURN; PROMOTION=NONE**. No APP/WEB/CineK deployment or signature.
