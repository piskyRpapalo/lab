# Federated evidence · commissioned 2026-11-13

Explore: APP255, Private Mesa3, LAB176→177, current main3647403;
existing bench_repro runner and dated device receipts remain authoritative for
their own experiments. A catalog is not a generation/quality/resource witness.
Original three-node commission expanded by the Sovereign to five physical
nodes (Jetson and Raspberry added). Never infer shared storage or capacity.

Scope: `bin/federated_node_snapshot.py`, its negative tests, scrubbed dated
snapshots and this document. New branch from current main; no dependency on
unmerged176/177 and no APP/runtime changes. No inference, pulls, weight reads,
training, services, scheduler or permission grants. Read metadata only.

Acceptance: bounded loopback-only metadata reads, no redirects/proxy, aggregate
host telemetry without identities/paths, per-model digest/format/quantization,
declared capabilities and license-content digest (not legal approval). Explicit
NO_DATA for configured context when absent, measured task limits, inference
latency/peak memory/energy/quality and other storage/backend coverage. Empty or
failed catalogs must not mean zero installed models. Snapshot expiry is explicit.

Implementation: optional local metadata collector, split hash-bound snapshots,
independent artifact reconstruction and task/node abstention matrix in
`benchmarks/receipts/20261113-federated-summary.md`. No allocator was added.
Version/tags/ps/show are the only routes; loopback numeric address, proxies and
redirects refused. Source/license/system/template/model tags stay out of output;
only fixed capability names and content/model hashes are exported. Record age
starts before collection, not when a slow collection completes. Consumer uses
its own120s ceiling; re-sealing a longer caller TTL cannot extend it. Tunnel
mode explicitly omits host telemetry. A valid hash never authenticates a caller.

Verification 2026-11-13: 10 directed boundary/artifact tests PASS; canonical559
tests x2 (558pass/1existing skip),5.521/5.467s on localPython3.14.4. Norte5,
Node7,llms2,tree11996/12109 B x2 PASS. All new pieces under16,384 B;
snapshot parts reconstruct original canonical hashes and match exact collector
source97b0014a91647210217ea0218ee3e4adfdb00c5793e5dc9a2224608690dda5d5.
NO_DATA(remote_exact_head_CI_until_publication); no local check substitutes CI.
J mapping: NO_DATA(no_verified_mapping_for_this_commission).

CI correction before signature: inspection of run43401694565 proved checkout
was GitHub's synthetic merge0e674041, despite its association with head3d9f7cb.
Do not equate run.headSha with checked-out HEAD. This slice additionally pins
`.github/workflows/pruebas.yml` checkout to PR head SHA (push uses github.sha)
and asserts `git rev-parse HEAD` equals that SHA before the unchanged suite.
Literal exact-head CI must be verified on the resulting final head; the earlier
green run is retained as merge-ref evidence. Same correction applied to176 on
its own branch;177 is preserved until parent integration. No signature carries
across these new heads. No runtime/collector/measurement changes in this fix.

Failures/limits preserved: node-aSSH timeoutx2; node-c127.0.0.1:11434 refused
although its separately bound primary backend is reachable through the existing
tunnel. Primary17tags/14digests, secondary2tags/1digest; do not unify registries.
Other stores incomplete, license review/task quality/calibrated latency/peaks/
energy NO_DATA. Final code verification repeats metadata collection only,
without repeating a weight census or inference; original observations remain
in private operator state. Snapshots are historical after120s, not current grants.

P0 receipts were published separately without code changes:176a8a347c canonical
630x2/1skip;177631f598 canonical679x2/1skip plus14real-code mutationsx2 caught;
workflow companionsx2 and existing exact-head3.10/11/12 CI reverified.176 still
OPEN: final177 reconciliation waits Sovereign integration. No signature inferred.
Claude received existing177 record/views+witness+durable-journal handoff in
Private Mesa3; liveAPP wiring/acceptance remains NO_DATA(runtime_owner_pending).

Resource admission proposal: require fresh target-bound memory/pressure,
transport, exact model identity and a task/context/backend-bound calibrated peak
memory and latency envelope before considering a dispatch. Missing telemetry or
calibration refuses admission. Model file bytes never substitute for peak RAM;
UMA RAM/VRAM must not be summed as independent capacity. Metadata RTT never
substitutes for inference latency. No concurrency threshold is calibrated by a
single idle snapshot. Proposed classes: MODEL_FAILURE, CONTEXT_MISSING,
AUTHORIZATION, NODE_SATURATION, TRANSPORT_UNAVAILABLE, EVIDENCE_INSUFFICIENT.
Existing176 receipt taxonomy needs a separately reviewed additive mapping;
do not rewrite historical TASK_SKILL/OUTPUT_SCHEMA/PERMISSION/etc receipts.

LoRA gate: reuse176/DFA/B5; insufficient corpus/independent cases/license,
train-eval separation/baseline/regression/budget/measured benefit/rollback means
NO_DATA and no training proposal or execution. Catalog licenses alone cannot
license a future corpus. No automatic promotion.

Rollback: optional offline collector only; reviewed revert. Nothing installed.

13-Nov extension: a historical Beelink user-context entry from3-Sep records
key-based passwordless SSH to node-a; no need to alter passwords. All three
edge peers appear offline in tailnet status, but mDNS+LAN and strict verification
against existing host keys recovered node-d/e. Device-tree confirms both
physical models in private receipts. Only anonymous a-e alias admission changes
in the collector; preserve the prior three snapshots and their exact old source
hash/commit, add two current source-bound snapshots (6 and1 catalog tags).
Pressure unavailable on both remains NO_DATA, not zero. Same private tag on
node-d/c identifies different digests and sizes; no alias-based routing.
Extension validation: 12 directed tests PASS; canonical561 tests x2 (560pass,
1existing skip),5.751/5.617s; Norte5,Node7,llms2,tree11996/12109 B x2 PASS.
Original three source-versioned snapshots remain byte-identical; new node-d/e
snapshots bind collector2b23a6b9c33148c6414395aa0286eab0cd0bc54681fc2a08c902bd8911492de4.
Extension final-head CI pending publication; prior559-test/CI receipt historical.
Next: coordinate an idle, owned-resource window, use existing bench-repro runner
sequentially, match exact digest+controls, measure peak host/device memory and
pressure around each public fixture; retain negatives. Production wiring and
atomic resource reservations remain with the runtime owner.
