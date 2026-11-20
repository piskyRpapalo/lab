# Tool-plan quality · RETOMA DEL CEREBRO · 2026-11-20

**Contract:** deterministic, offline advisory for the existing Hexelion brain and LAB
harness. **Coordination / authority / handoff:** [RETOMA DEL CEREBRO · private Mesa
#51](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51);
[original coordination #50](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/50).
This engineering note is **not** a new mission or S1 grant service.

## What exists and why this is different

The real model **hexelion:latest** completed a local synthetic twelve-case
development battery (12/12 exact) but only **17/24** exact on a separate local
24-case policy holdout. On that holdout, 21/24 closed JSON outputs were valid,
seven authorized target operations were omitted in aggregate, and no valid
candidate named an out-of-scope target. All real host-grant and dispatch claims
remain **NO_DATA** for that holdout. See the [measured benchmark](../benchmarks/hexelion-v1-host-policy-20261120/README.md).

Existing **meta_harness/improvement.py** already handles *LoRA proposal* evidence:
OUTPUT_SCHEMA failures require contract repair, not weight updates; a
TASK_SKILL adaptation requires independent baseline/control/candidate
evaluation with pinned splits/repeats. We reuse that existing gate rather than
creating another LoRA decision maker.

This slice adds **meta_harness/tool_plan_quality.py**, a quality-only
comparison between a model's proposed symbolic native-tool plan and an
independently host-witnessed set of operations that are already requested
and eligible. It does NOT issue permissions, derive user intent, execute
tools, train weights, alter tokens or authorize cache reuse.

## Host-owned bindings

The host constructs a HostPolicy before asking the model to plan:

- exact opaque SHA-256 references for task, source, tool scope, model, base,
  optional LoRA head, and at most eight eligible (node_ref, tool_ref) pairs;
- exact generation and permission epoch;
- a **host-owned callback** to independently check fresh task intent, real
  grant, model/head pins and current source at evaluation time.

The verifier is invoked before and after parsing/scoring. False, missing,
throwing or changed witness results return NO_DATA. Self-reported text
such as "FIRMO", a digest or a model response must never supply a witness.
The host remains responsible for preventing concurrent source replacement
between these checks; this is not an atomic lease.

The model response is a closed JSON object with exactly one tasks
array of at most eight objects, each exactly node_ref and tool_ref,
both validated as SHA-256 references. Invalid type, extra fields,
duplicate JSON keys, >4096-byte output, nonfinite values and malformed
strings fail closed. Duplicate tasks yield a rejected proposal.

States: EXACT (candidate equals host gold), REVIEW_REQUIRED (missing
authorized operations), REJECTED (out-of-scope or repeated operations),
or NO_DATA (policy, source witness or schema unavailable). **EXACT is never
permission to dispatch.** The small sealed receipt contains only hashes,
counts, bounded causes and permanent execution_authorized=false,
kv_reuse_authorized=false, training_authorized=false.
The same state/ref/summary can be read by visual, speech/Acho and machine
clients through views; physical audio/UI verification is not claimed.

The existing brain, task_binding, resource_admission,
context_window_projection, app_memory_projection and S1/Session
host authority stay canonical. A real execution requires fresh
independent S1 task grant/lease and source version checks after any model
proposal. A quality receipt never promotes a tool to the host allowlist.

## Reproduce without local inference

From a clean LAB checkout:

~~~sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_tool_plan_quality.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -q
python3 test_llms.py
python3 bin/verify_llms_tree.py
~~~

Run the commands **twice** at the exact PR head. The fixtures are synthetic
and use hashes instead of host/device names or real user commands.

Negative cases: missing host witness, changed policy epoch, base/head/generation
ref shift, fake or duplicate JSON, out-of-scope node/tool, omitted eligible
targets, oversized output, forged approval text, model abstention and
independent witness revocation between checks. Source text is not committed.

## What will establish a real Hexelion V1 improvement

1. Create a **new** independent benchmark corpus with human/host-reviewed
   source intent and current real grant (where authorized), grouped by
   task family/device. Do not use the exposed 24-case holdout as training.
2. Compare baseline hexelion:latest, simpler deterministic host control,
   and prospective Tools+Limits+H adapter with two stable repeats, mixed
   requests, genuine refusals, negative controls, latency, energy if metered,
   token cost and persistent-grant correctness.
3. Feed bounded, independently witnessed failure receipts into existing
   improvement.evaluate; it may only propose LoRA under its stricter
   thresholds, license, privacy, rollback and human review gates.
4. Check exact training checkpoint/ROCm/PEFT/VRAM/RAM/disk fit separately
   from the 65 GB GGUF inference model. Keep a previous known-good adapter
   until restart/reversion and cache-invalidation tests pass.
5. Only after sustained 24h **measured** service and scoped actual S1 E2E
   may a version be called operational Hexelion V1.

**NO_DATA:** real host authorization consumed by this slice, general
natural-language quality, real MCP effects, LoRA training, 24h uptime,
Android authenticated model turns, cross-family KV transfer.

**Ownership:** Codex GPT-6 (Olin) · internal rack lane under the Soberano's
chat HITL. LAB changes remain on draft exact-head PR; do not claim agent
signature replaces owner's cryptographic or GitHub review.
