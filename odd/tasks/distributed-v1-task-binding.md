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
complete task reference and all pins. BoundWorker.task() returns that new task;
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
