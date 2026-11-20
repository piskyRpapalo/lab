# Brain Fabric · bounded heterogeneous context windows · 2026-11-20

**State:** implemented library + synthetic test doubles; no APP wiring, no cache/KV transfer and no model-dispatch permission.

## Problem and original contracts

One sovereign orchestrator may ask several local models with different available input budgets to inspect the **same canonical evidence**. Model context-window sizes are not additive, and a semantic digest or matching vector is not an authorization.

This change **reuses**:
- `attention_selector/core.py`: original stable, lexical, exclusion-aware source selection under caller byte ceilings.
- `meta_harness/context.py`: the existing APP-backed quote/TTL/source-version validation. The new projection does not duplicate its search, source store or clock. APP/H3 must bind a verified `context_ref` itself.
- `meta_harness/task_binding.py`: exact base/head/scope/selection task binding before any real execution.
- `meta_harness/resource_admission.py`: independent host witness/route/lease checks, not superseded.
- `odd/tasks/c2c-cache-scope.md`: head, source, tool policy, model/runtime and permission revisions invalidate KV reuse.
- [Existing mathematical alignment study](../benchmarks/context-fusion-20261120/README.md): 2D synthetic prototype matching, not a neuronal fuser.

No new app, database, daemon, protocol authority, RAG index, MCP registry or autonomous model launcher is introduced.

## New function

`meta_harness/context_window_projection.py` exposes `project(query, chunks, windows, verify_chunk, verify_window, tool_scope_ref, permission_epoch)`. All source chunks, model-window entries and callbacks are host supplied; data in model text must **never** supply grants or forge either witness.

Each `ModelWindow` binds a model/base/head reference, byte budget, chunk ceiling, tool-scope reference and permission epoch. The projection queries the original lexical attention selector. The host rechecks the independent sources and each model-window witness after selection. A drift results in `NO_DATA` or a scoped `PARTIAL`; complete evidence is represented by digest references only.

The output is a <1024-byte **control receipt** and separate bounded per-model details. A shared chunk has an identical reference across different windows; per-model `selection_ref` changes when model/head/policy/budget changes. The result intentionally never exports source text or query and does not activate KV reuse. A digest proves byte identity, not signing, provenance, tool authorization or freshness.

The `views` helper produces the same state reference and summary for text, speech/Acho and machine display, without claiming a physical-audio E2E test.

**Important:** budget numbers count UTF-8 **bytes**, not model tokenizer tokens. This library does not assert a model's real token-context size, nor translate its KV cache. A trusted APP host must still revalidate source version/TTL, precise current grants, the chosen model's actual configured context length and the existing S1 task/lease gates immediately before execution. Snapshot callbacks are not an atomic lock.

## Measurements and negative controls

2026-11-20 · Beelink-class Linux x86_64 · Python 3.14.4 · LAB branch `codex/brain-fabric-context-20261120`:

- Directed library tests: **12 ×2 PASS**.
- Complete Python suite: **1293 ×2 PASS** (two existing skips per pass).
- `test_llms.py` and `verify_llms_tree.py`: PASS ×2.
- Negative controls: hostile model/epoch/scope, duplicate source, model-head rotation, source witness lost before or after selection, changed window witness, malformed packet, no eligible source, missing grants. No model or tool executed by this library.
- Model-window test: one synthetic 128-byte/1-chunk context and another 700-byte/4-chunk context refer to the same canonical first chunk without source text export.

Separately, the existing [context-fusion fixture](../benchmarks/context-fusion-20261120/README.md) produced byte-identical JSON across Beelink, Onexstation, Jetson ARM64, Raspberry ARM64 and Orange Pi ARM64 (**2 passes each**; all 64/64 rotated geometric fixtures). This is host portability of **synthetic mathematics**, not network E2E inference or KV compatibility.

2026-11-20 optional five-host read-only live orchestrator smoke:
- Loopback model `hexelion:latest` is GPT-OSS architecture, 116,829,156,672 parameters and manifest SHA256 `b0593ac3ce7539470dd21d64ae7a9e181e8cc89f1528b4a89a3a9954e024e398`.
- One structured plan yielded 5/5 exact host names and allowed read-only operations in 22.63 seconds. In the **authorized Desktop Commander session**, a fixed host executor read `uname -m` from Beelink, Onexstation, Jetson, Orange Pi and Raspberry in parallel: 5/5 PASS, 0.958 s dispatch wall time.
- The model did not choose shell commands or receive authority. Receipt digest `2a7845fe58f69efa638b60642729f5727f51d1a1d4af4aed29d9234c42666262` identifies this one observation. It is **not an independent semantic judge** and not proof of continuous 24/7 operation.
- SentinelX's separate execution identity could not authenticate four SSH peers. Do not upgrade that NO_DATA based on the other connector's successful calls.
- No Android model inference, cross-model transfer, encrypted app grant, native tool execution, LoRA or real operational KV has been proven.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_context_window_projection.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -q
python3 test_llms.py
python3 bin/verify_llms_tree.py
```

Run twice from the exact reviewed HEAD. The public library only uses stdlib plus existing LAB modules; no external model or fleet access is required.

## Next measured gate before Hexelion v1 / LoRA

1. Test a **host-witnessed** authorization/nonce/replay gate for the Android private bridge; never use Tailscale presence as authority.
2. Benchmark model-selected actions against the existing native tool capability registry: compare fixed deterministic selector vs Hexelion model, with independent labeled positive/negative holdout and false-authorizations as a hard stop.
3. Measure context **tokens** on the actual model runtime, resource costs and saturation under simultaneous admissible tasks; no "sum of windows" claim.
4. Qualify an exact compatible training base and a LoRA runtime against the 96 GiB VRAM limit. The measured 65 GB GGUF inference blob does **not** demonstrate that QLoRA training fits.
5. Keep candidate LoRA versioned and reversible; signed acceptance and long-duration stability testing precede any 24/7 enablement.

**NO_DATA(real_context_window_token_capacity;cross_model_KV;actual_model_tool_selection_safety;APP_E2E;LoRA_training_runtime;continuous_24h_uptime).**

— Codex GPT-6 · Brain Fabric lane · Mesa #50. Proposal only: human signs consequential integration.
