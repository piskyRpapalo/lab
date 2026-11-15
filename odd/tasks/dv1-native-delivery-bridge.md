# ROUND30: native controlled receiver execution bridge

Existing mission in private Mesa #3/#39; this is a technical contract, not a
second mission registry. Base LAB0eec7789b90912e47ff3ca93f9c9eccc65a3a6f1.
PR219 source c09da849 / PR220 source integrated in 0eec778 verified. APP300
5111baf is visibility-only; no executable delivery or agent receiver was added.

## Minimum vertical slice and missing security

The existing brain now exposes deliver_bound(BoundWorker, session, receive,
attest_ack, witness_execution, now, cancelled). It uses the ORIGINAL Session,
AdmissionGate and ExecutionJournal/DurableTokenBudget. No new dispatcher,
permission issuer, lease allocator, scheduler, registry, endpoint or database.
Only host-owned exact objects/callbacks are accepted, not model JSON commands.

1. Original request/context is frozen by task_binding; native task hash includes it.
2. Check original binding/current grant and existing journal. Prior outcomes are
   replay/history, not new delivery. UNKNOWN is never retried after restart.
3. AdmissionGate checks resources, exact wrapper routing and held lease BEFORE
   delivery. It is checked again by native Session before execution.
4. Produce metadata-only mission-delivery/0 envelope with exact task, context,
   receiver session, node, generation and frozen assignment refs. mission_ref is
   the ORIGINAL constraints_ref assignment document, not a new mission catalog.
5. receive returns mission-ack/0 (delivery_ref, agent_ref, node_ref, context_ref,
   state=RECEIVED, observed_at). Closed schema + fresh source attestation required.
6. Fresh permission/context check; existing Session handles execution, budget,
   durable atomic claim, native receipt and uncertain-outcome retention.
7. Native Session attestation AND independent execution witness required.
8. Recheck permission, binding, wrapper route, identical held lease and time before
   VERIFIED projection. It grants nothing, nor can it authorize another task.

The receiver is a CONTROLLED CALLBACK in tests, NOT any of Codex/Junie/PI/Claude
CLI. No terminal injection or claim of cross-provider delivery. Actual adapters
must impose effective I/O deadlines; bridge checks cannot interrupt an arbitrary
host callback. Calls must be bounded/read-only except the explicitly authorized
worker. ACK authenticates no identity without genuine attest_ack source binding.
Mission metadata may be delivered more than once under concurrent attempts;
ACK has no effects. Native journal guarantees tested one execution claim, not
exactly-once physical effects or exactly-once message delivery.

## Harness/Acho contract

native-delivery/0 receipt <1024 bytes, with agent/node/assignment/delivery/execution
refs, original execution observation time when present, cause and separate stages:
OBSERVED, RECEIVED, AUTHORIZED, EXECUTED, VERIFIED are distinct. Observed remains
NO_DATA: process presence is not used as proof of receiving. Native receipt refs
are retained without raw task/result data. Cached outcomes retain original time;
stale records and missing sources never become LIVE. live=false and
remote_authorized=false ALWAYS. origin=HOST_SUPPLIED_UNATTESTED, authority=none.
VERIFIED means specified local callback checks passed; it is not host authentication,
APP E2E, authority over other CLI or physical admission. Test artifacts SIMULATED.

## Security boundary still closed

LOCAL_ONLY validators are untouched. The operator SSH probe is NEVER used as this
worker or promoted into a remote grant. Existing native host_witness explicitly
lacks durable authority/fence provenance. Missing host lease, genuine node/source
binding, remote scoped permission, result witness and cross-host final fence keep
production remote dispatch closed. Hashes are integrity, not signatures.
Rechecking callbacks is not atomic cross-host revocation/CAS; no such claim made.
Cancellation/timeout cannot prove an effect was undone. UNKNOWN keeps reservation.

## Reuse / state / owner handoff

| Stage | Status and source |
|---|---|
| APP/Acho -> Harness request | EXISTE_SIN_E2E: existing APP endpoint/state; APP300 informational only |
| Original context/binding | EXISTE_Y_PROBADO: context.py/task_binding.py/brain, synthetic native chain |
| Identity / actual CLI delivery | NO_DATA(authenticated_agent_source_binding; installed_CLI_receiver) |
| Grant / resource admission | EXISTE_Y_PROBADO: native callbacks + held-lease fixtures, not live host lease |
| Selection | EXISTE_Y_PROBADO: resource_decision proposals; production router/source binding incomplete |
| Controlled receive/ACK/native execute | EXISTE_Y_PROBADO: this local callback bridge; never TTY injection |
| Remote completion | EXISTE_SIN_E2E: operator SSH public probe 4 nodes x2; native scope/lease FALTA |
| Native receipt verification | EXISTE_Y_PROBADO: original Session/journal and independent fixture witness |
| Human visible/audible consumption | EXISTE_SIN_E2E: reusable frame; Junie/Claude consumption pending ACK |

Junie owns adapters: bind receive/attest_ack to genuine receiver/session/node;
map native-delivery frame to existing Harness (no second panel) with omissions,
original freshness and independent source refs. Consult original grant/lease owner;
no implicit permissions from SentinelX/Desktop Commander visibility.
PI/Hexelion: repeat swapped node/context/agent, expired grant, revoked lease,
foreign checksum-valid receipt, missing witness, lost channel, concurrent duplicate,
changed head/generation, restart/UNKNOWN, stale replay and cancellation before and
during work. Fixtures deliberately mark all policy/profile/lease witnesses synthetic.
Claude retains UI/World/voice worktrees. No visual or APP/p0x source touched.

Next real test is blocked on genuine host scope/lease/receiver binding, not absence
of Soberano HITL. No safe native remote route is inferred from operator SSH access.
NO_DATA(native_remote_E2E;physical_resource_lease;authenticated_CLI_ACK;
independent_effect_witness;cross_host_atomic_revocation).
