# Distributed V1 P5a: original-context binding before native grant

Technical contract under existing private Mesa #39 commission, CLAIM in #3.
Base e08887f0343a0db69f2a09a2ff54f9e70fdcb154. No new mission, registry or authority.

BoundWorker(original_task, pin, local_node_ref=..., worker=..., witness=..., now=...)
composes existing Session and AdmissionGate. Original task uses strict meta-task/1.
Pin is closed, flat primitive metadata: session_ref, generation, node_ref, base_ref,
head_ref (canonical head_eligibility manifest digest or null), runtime_ref,
selection_ref, constraints_ref, observed_at. Refs are opaque SHA256; no raw user
request, RAG snippets, credentials, paths or endpoints are accepted in pins.
Constraints/selection references must resolve to original frozen host-owned sources.
No retrospective repair of old receipts is possible through this constructor.

Binding changes task.input_sha256 to a domain-separated hash covering the ORIGINAL
input hash and all pins. The native task hash still covers every unchanged task
field, including run_id, source, budgets and transport. This keeps equal workloads
comparable across baseline runs without granting a different run or source. BoundWorker.task() returns that new task;
the native grant must approve its exact new hash. An original-task grant cannot
approve it. Native worker receives its original task/input unchanged only inside
the host-bound wrapper; this is not a second execution or grant. No native validator,
Session, journal or permissions are changed. Resource profiles must match the NEW
task and AdmissionGate.route must witness the wrapper, not just the inner worker.
Changing a pin requires a new task approval and profile; changing a head mid-run
cannot silently reuse the original approval or cache interpretation.

Witness is host-owned, never model-supplied: verifies original context, active
session/generation, node route, base/head/runtime and current source/selection
revocation. Callback receives isolated copies; true is not self-authenticating.
Clock/freshness (120 s) and witness checked before and after worker, with time
rechecked after callback. Failure after possible dispatch suppresses measurement;
Session conservatively records UNKNOWN, retains reservation and prevents retry.
An exception or cancellation never proves the physical effect was rolled back.

record() is an integrity/provenance reference, authority=none,
dispatch_authorized=false, remote_authorized=false. This library never authorizes
execution itself. Session authority, resource admission, leases and S1 tool policy
remain independent requirements. No model loading, transport, MCP or GPU activation.
The local node ref is a trusted host input requiring genuine source binding;
equality alone does not authenticate a device. LOCAL_ONLY remains intact. User
approval of remote work requires separately reviewed native scope evolution and
actual host binding, not relabeling this task or routing via an unverified tunnel.

Tests: synthetic two-device separation, base/head/generation drift, old grant,
expiry/future, hostile object hooks, witness mutation, replay, cancellation,
UNKNOWN no retry, and native AdmissionGate with explicit TEST DOUBLE profile/lease.
NO_DATA(authenticated_host_context;physical_device_lease;remote_E2E;live_LoRA_swap).
Next: P2 deterministic routing must consume the original head/resource decisions,
then freeze these pins BEFORE asking for exact-task approval. Junie retains S1/MCP.

## Measured report budget regression

Adding a source module expands the existing CLI provenance manifest; its expanded
128-token fixture reached 16407 bytes and failed the unchanged 16384-byte ceiling
x2. Baseline e08887f passed. Scope amended in Mesa #3: cli.py throughput_contract
now carries the canonical bench-repro-01-v1 identifier without its redundant prose
caption. Every source file/hash and report field remains; byte ceiling unchanged.
Future unbounded manifest growth still needs a separately reviewed bounded
provenance representation, not budget inflation or silent source omissions.

## DV1 circuit examination and integration (same worktree / PR)

Integrated references: LAB main e08887f; APP sessions #298 b441d86d and
System Check #299 bf8ee3f; R3/R4 already integrated. Junie owns p0x S1 R34,
source reviewed local44f670361619; no review ACK is assumed.

| Stage | Classification | Existing source / exact remaining boundary |
|---|---|---|
| APP/Acho request | EXISTE_SIN_E2E | APP bin/preceptoros-pwa, hexelion_proxy; no full APP-to-remote proof |
| Frozen request/context | EXISTE_Y_PROBADO | context.py, task_binding.py; synthetic brain composition x2 |
| Node/agent identity | NO_DATA | agent_presence/sources correlate; authenticated physical source binding absent |
| Resource admission | EXISTE_Y_PROBADO | resource_admission.AdmissionGate, fixture routes/profiles/leases; physical device lease NO_DATA |
| Authorization | EXISTE_SIN_E2E | native Session exact-task grants + p0x S1; remote scoped authority not installed here |
| Node selection | EXISTE_Y_PROBADO | resource_decision filters proposals; production choice/routing P2 still FALTA |
| Execution | EXISTE_Y_PROBADO | NativeSort + Session; model/remote execution NO_DATA(remote_worker_not_bound) |
| Remote witness | FALTA | host_witness explicitly returns NO_DATA; no remote authenticated completion provider |
| Receipt | EXISTE_Y_PROBADO | native sealed task/run receipt; hash integrity is not remote authentication |
| Verification | EXISTE_Y_PROBADO | brain.verify_cycle + exact BoundWorker originals and native Session witness; synthetic only |
| Visible/audible state | EXISTE_SIN_E2E | brain.projections, APP state contracts; real visual/voice/remote roundtrip unmeasured |

Smallest correction built: brain/capability_evidence/verify_cycle now accept an
explicit bounded tuple of exact BoundWorker proofs. No automatic unwrapping,
retrospective receipt repair or fallback to unbound input. The actual native
receipt is verified against the BOUND task; only comparison with fixed benchmark
input uses the separately validated original. Each binding must match the actual
context_ref; all three prepared tasks are checked before baseline execution.
Proofs absent, duplicate, unrelated, expired or from another context reject.

Preserved RED: original brain refused a correctly granted bound baseline with
baseline_not_witnessed. Previously hashing full original task also changed the
workload input across run_id/source. Native complete task hashing still binds
those fields after correcting input semantics. New integration tests cover the
existing cycle and its independent verifier, not a second orchestrator.

### Handoff contract and first real remote dependency

Junie: review BoundWorker.original_for/task/pin + AdmissionGate.route/lease. The
host must attest the wrapper AND original worker, original context/CLAIM, exact
base/head/runtime, live session generation, grants and held resource lease.
Keep this increment LOCAL_ONLY. Next remote increment must bind exact target,
request/context digest, explicit scope, expiry, revocation epoch and result to an
existing authenticated channel (or genuinely verified host signature). A returned
hash/JSON/echo is not such a witness. No new permission issuer or lease service.

PI/Hexelion: independently repeat wrong node, changed task/context/head, revoked
session, expired evidence, timeout/network loss and forged receipt; suppress
measurement on UNKNOWN and never retry effects without reconciliation. Native
Session attestation of the BOUND task is required even if original input matches.
Callback test doubles are not real remote authentication.

Next smallest live piece: owner-bound channel/completion witness for one public
fixed operation and existing host reservation, followed by an explicit remote
scope contract reviewed with S1 owner. No real remote dispatch was attempted:
NO_DATA(remote_channel_and_host_lease_binding_not_verified). This is not a claim
that devices are offline or that the Sovereign withheld authorization.

No E2E DISTRIBUIDO is declared. No remote process, GPU, model download, host key,
service or Claude visual file was changed. Existing views are consumed headlessly.
