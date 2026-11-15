# C2C cache scope and rotating-head readiness

Existing Mesa #40 / Distributed V1 commission; technical contract, no new mission
or catalog. Reuses c2c_preflight.preflight, head_eligibility, resource_decision and
AdmissionGate. No tensors, weights, models, GPU, cache store or network loaded.

cache_preflight(cache=CacheRecord,expected=CacheKey,verify_cache=host_callback,
**native_preflight_inputs) calls the ORIGINAL preflight, then checks exact scope,
cache origin and 120s freshness, independently witnesses the cache and current
scope, repeats original preconditions and rechecks the live cache witness.
Callback arguments are isolated; primitive refs are validated before copying.
All output is preconditions only: dispatch_authorized=false,
cache_reuse_authorized=false, promotion=NOT_AUTHORIZED. No automatic fallback.

CacheKey binds exact task, pair, pin, session, selected context, MCP/tool policy
and permission revision. Pair includes both model and LoRA manifest identities,
fuser revision and trained-model binding; pin includes device/runtime/generation.
CacheRecord identifies original cache bytes via its manifest digest and time.
Changing head/base/fuser/runtime/device/session/RAG source/tool scope or permission
invalidates reuse. A matching hash or latent vector is never authentication.
verify_cache MUST independently attest original cache provenance/bytes, current
source ACL/revocation, permission epoch and authorized schema snapshot. Expected
keys are host-owned, not model JSON. Before actual reuse the native executor must
freeze scope into the original task constraints/binding and recheck grant, lease,
source freshness and session fences. Snapshot callbacks are not an atomic host
fence and readiness never authorizes consuming KV or executing a tool.

The existing S1 adapter ollama_adapter_m1._herramientas_para_ollama already builds
tools from sovereign_s1.filter_tools_list; retain that path. Model context must
receive its actual host-filtered tools/schema revision and explicit NO_DATA for
unverified availability. Knowing/seeing a tool != permission. Do not duplicate a
second MCP/tool catalog or train a head to bypass S1. Include tool_scope_ref in
cache key and bound constraints. Tool policy changes invalidate cached context;
actual calls still go through S1 every time. Junie owns that adapter/policy lane.

## LoRA preparation per device

Reuse compatible bases/adapters across devices; no requirement for six redundant
weight copies or six separately trained bases. Per-device manifests are private
projections of existing fleet inventory, not a new registry. Preserve observed,
declared, stale and missing fields. Match exact base/head/runtime/device, resources,
provenance/license, quality holdout and operator budget before any loading/training.

A local Mistral-7B-Instruct-v0.3 checkpoint has three shards checked against their
cache digest filenames and official pinned HF LFS metadata (no weight download).
This establishes bytes, not performance or adapter training lineage. Existing
five Mistral adapter configs leave revision null; original training base revision,
license/provenance and independent heldout tool-policy quality remain unqualified.
Do not promote them or call them proven security/tool heads. Historical Qwen v6
results remain a separate family with its RED product gate.

First proposed specialty remains tools-and-limits; rank16/alpha32/q-k-v-o targets
are a candidate recipe from existing adapters, not measured support per device.
Use own consented trajectories and current tool schemas; frozen family-separated
holdout, base-vs-adapter, PROTECTS/REDUNDANT/REGRESSION/UNFIXED. Current OSS round
dry-run reports 7 real pairs (6 train/1 eval) vs minimum50; no synthetic filler
relabeled as real. This is the historical OSS action protocol, not a qualified
Mistral tools dataset. Static source audit also found the Ollama adapter drops
canonical closed schemas and audit_last.n; Junie must reconcile the existing
S1 schema path before those trajectories can be used as faithful tool examples.
Training still needs exact approved data/base/node/budget/stop rules. No training,
installation, model transfer or promotion is performed by this increment.

Mistral LoRA preparation is NOT the existing Qwen3-1.7B/Qwen2.5-1.5B C2C pair.
That pair still needs exact HF checkpoints, compatible runtime/KV access, trained
fuser provenance and receiver/sharer/text/C2C heldout baselines. Do not transplant
fusers or assume LoRA/head rotation preserves KV compatibility. R0 continues to
reject unqualified sharer heads and production LoRA admission.

Junie: source producer for tool_scope/permission revisions and per-host manifests;
PI: stale/forged cache,wrong session/head/fuser,revoked RAG/tools/grant,origin spoof,
source mutation during checks. Claude: consume readiness/cause via existing frames.
NO_DATA(real_C2C_transfer;qualified_per_device_LoRA_runtime;training_budget;
independent_tool_policy_holdout;production_cache_loader). Existing LOCAL_ONLY and
native execution bridge remain unchanged.
