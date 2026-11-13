# Human acknowledgement of an uncertain execution

The existing Session/journal retains UNKNOWN after a lost outcome and blocks
new claims. No self-hash, model text or automatic timeout resolves it. This
optional LAB adapter creates a read-only, exact proposal before any decision:
fixed journal identity, run_id, exact task hash, prior outcome hash, evidence
reference, authority reference, timestamp and the only supported decision:
ACK_UNKNOWN_RETAIN_RESERVATION. The original outcome remains UNKNOWN; the
original run ID never executes again; its full token reservation stays charged.

The authority reference is a host-assigned identifier for a human decision,
not itself a signature. A host callback must verify the Sovereign's actual
approval of the exact proposal ref. An independent host callback must verify
and fence the old worker so it cannot resume. Before every later new claim, a
host-owned resolution_witness must again validate approval and the active fence;
missing, changed, revoked or unavailable witnesses fail closed. The journal
identity is random and recorded only when explicitly creating a new journal;
older journals lacking it return NO_DATA and are never migrated automatically.

On valid approval, an append-only acknowledgement event is recorded; repeating
the exact decision is idempotent. It permits other separately authorized tasks
only while their independent budgets/leases/permissions pass. It does not claim
the uncertain action succeeded or failed, free its reservation, mint authority,
promote memory, trigger a retry or run a service. This is not an APP integration.

Procedure: stop/fence the worker; collect independently verifiable evidence;
prepare the exact proposal; show its ref and consequences to the Sovereign; only
the host's real authority adapter can attest the resulting decision; commit the
acknowledgement and maintain the fence/witness. If evidence, approval or fence is
unavailable, leave the journal blocked. The old run remains UNKNOWN. Actual
signature verification, worker fencing, APP projection and budget settlement
of an unknown outcome are host responsibilities and remain NO_DATA here.
All tests use synthetic human/fence witnesses; no real signature is claimed.
