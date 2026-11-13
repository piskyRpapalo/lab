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

## Continuation · source-preserving APP consumption

Before changes:16 protected files matched published8eb0a1a byte-for-byte,
12 directed tests passed; literal-head CI43403881804 reverified3/3.176 remained
OPEN/DRAFT at7d89317 with literal-head CI43402087203;177631f598 remained stacked
and unreconciled pending Sovereign integration. No new census/probe was run.

Additional scope in this SAME178: `bin/federated_projection.py`,
`docs/federated-consumption.md`, explicit historical replay example and new
projection/preservation tests. Source schema node-metadata/1 is reused with
kind=projection and separate source/projection seals; record/views follows177.
No UI, dispatcher, live producer, source rewrite, model invocation or new node.
Current consumption distinguishes DECLARED/OBSERVED/scoped VERIFIED/STALE/
NO_DATA; legacy metadata VERIFIED is not upgraded to inference. Host pins and
host read time are required; jointly re-sealed altered packets fail recomputation.
All records abstain from admission. Pressure and calibration gaps remain caused.

The original source JSON, summary and12-test verifier stay byte-identical;
this feature log only appends. A new preservation test fixes their original byte
lengths/hashes and feature prefix. Public packets contain anonymous node/model
refs only, bounded below16KiB. Example time09:42Z is explicitly HISTORICAL_REPLAY,
not a fresh observation. Missing inputs do not mean absent machines/models.

Existing WEB mini-guide registered as a candidate with source blobs/manifest
hash,105453984 declared weight bytes and declared19/32 vs2/32; no evaluation or
download repeated. Five rack nodes exclude phones and browser candidates.
No training proposed; use existing independent evidence gates and an owned idle
calibration window. Handoff to Claude uses the existing brain-cycle task contract
separately from census context, never a fake cycle inferred from metadata.
Continuation validation/CI pending final publication; prior receipts remain dated.

10:06Z continuity order: construction continues without waiting for signatures.
176/177 stay untouched;175 was revalidated OPEN/DRAFT at444b5847f72c43e3a3eb7082a6e486dd439ff1c9,
base3647403,mergeStateUNSTABLE,no visible statusCheckRollup. Its CI is
NO_DATA(no_visible_checks_in_PR_view), not assumed red or green. It remains in
the inventory; no ownership of that independent benchmark slice is inferred.
`docs/nvidia-benchmark-proposals.md` adds N1 existing-backend throughput/GPU
attribution, N2 task/context envelope, N3 conditional pre-existing TensorRT
engine. NVIDIA primary sources consulted; no install, inference, service or
power/clock action. Mobile clients remain future consumers, not enrolled nodes.

Continuation validation: canonical581 tests x2 (580pass/1existing skip),
5.854/5.634s; all workflow companions x2 PASS (Norte5,Node7,llms2,tree11996B).
32 targeted tests cover original12 +19 consumer/CLI cases +1 preservation gate.
Full six-packet historical replay repeated byte-identically, SHA256
a1523b969788ba1dceaba11891abcedfcd827465468086b0935e7eec0da42f26.
Five physical nodes remain distinct from five backend observations: node-c has
two; node-a has no supplied current metadata snapshot. Replica input aliases,
expired/future evidence, re-sealed changes, corrupted parts, symlinks, missing
pressure, false admission and channel divergence are rejected or retain NO_DATA.
Original16 files/hashes remain protected (feature log append-only); source JSON,
summary, collector and old verifier were not altered. New files all<16384B.
Next: final-head CI, exact-SHA review, Claude read-only contract adoption, later
owned idle-window measurements. No signature was awaited to finish construction.
