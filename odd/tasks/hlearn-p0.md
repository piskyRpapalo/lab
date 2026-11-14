# H-LEARN P0 · executable native contract composition

Technical contract, not another mission. Authority: Mesa #37 comment 6885446222;
current BUILD handed to Codex CLI, Hexelion policy/adversarial reviewer. CLAIM Mesa #3
comment 6885508908. Depth 2. Base c2afcf0b4e5da5a30683ad941ac97e9860f67402.
Scope: meta_harness/hlearn.py, tests/test_hlearn_scenarios.py,
meta_harness/wake_recovery.py, tests/test_wake_recovery.py, this file.

## What is built

Executable evaluate(task,...) composes canonical resource_decision.decide,
AdmissionGate and optional wake_recovery.plan. It never invokes the supplied worker;
that callable is only the existing gate's host route identity. No new Host, scheduler,
grant, lease, registry, actuator, journal schema or permission manager is introduced.

Typed Trace returns the original resource decision, original admission record, optional
native recovery proposal, and a compact Receipt. state/cause/decision_ref retain their
native meanings: decision_ref is the canonical resource decision's digest, not a new
permission. receipt_ref hashes the joined observation. No outcome/explain decision API.
The existing Session's native UNKNOWN field is consumed only as a witnessed receipt;
it is not repurposed into a routing API.

Resource proposal remains ABSTAIN / PRODUCTION_ADMISSION_NOT_CONNECTED for measured
profiles, even if Gate returns VERIFIED for its checks. A recovery fixture may produce
SIMULATED but never action authority. Receipt always has dispatch_authorized=false,
physical_actions=0, reservation=NOT_REQUESTED and promotion=NOT_AUTHORIZED. Native grants
are checked via existing check_grant; gate independently rechecks route/lease/grant.
Gate choice must match the resource input's task/model/profile/source/route. A future
Session still owns final permission checking, reservation, dispatch and replay.

Host owns all callbacks, grant/clock, worker identity, resource projection/profile,
ledger and prior-state lookup. They are not accepted from model JSON. Gate must be
the existing AdmissionGate type. Optional prior Session receipt must pass existing
verify AND its host's attests_prior(receipt,task), exact task/run correlation; a self-hash
or proof_of_auth label is not authenticity. UNKNOWN always abstains; completed receipts
require Session replay rather than a fresh allocation. Omitting prior is not evidence
that a host has no previous run: Session/journal remains mandatory before future effects.

Host trust-boundary inputs for recovery cannot replace task, clock, admission callback
or cancellation with their own fields. Only intent/observations/capability/ledger and
host witnesses plus after/post are allowed. Receipt <1024 bytes; resource bounds and
256 KiB input ceiling remain. Errors do not echo private exception text or task content.

## WAKE final-recheck correction

Source: Mesa #25 comment 6884857786. On the unmodified base, executable counterexamples
show empty after and contradictory after reaching SIMULATED. They were never physical
execution (dispatch=false), but their final-recheck requirements were RED. External
wake-red-before.json preserves those observations; no claim that old P0 acted on hardware.

New strict proposal semantics: after requires two distinct witness_ref values with host-witnessed source independence,
matching each other and the original diagnosis, not older than the latest diagnosis
and fresh within 120s. Missing/single/duplicate after -> FINAL_WITNESSES_MISSING;
conflict -> FINAL_OBSERVATIONS_CONFLICT; changed diagnosis -> FINAL_DIAGNOSIS_CHANGED;
older -> FINAL_OBSERVATIONS_PRECEDE_DIAGNOSIS. No next_ledger is proposed on these paths.
An ONLINE+function_ready observation cancels before simulation, even if other evidence
is incomplete; refusing an action needs less evidence than proposing one. Function-ready
with a non-ONLINE condition is self-contradictory and rejected.

Compatibility change: after=() remains a valid argument but now ABSTAINs instead of
SIMULATED. Callers must provide final host observations; fixtures explicitly provide
them. Original successful fixture expectations remain, no failure is renamed PASS.
Initial/final timestamps may tie at available clock precision in this non-executing
P0; older evidence is rejected. The future host must prove fresh causal/monotonic phase
observations rather than replaying an old snapshot as after.

Distinct witness_ref digests alone do not prove independent physical origin. The trusted
host must bind refs to independent sources and refuse shared-origin evidence; tests
exercise such refusal. NO_DATA(physical_source_lineage_not_connected) remains. Post
verification stays explicitly SIMULATED/NO_DATA; it never proves a real recovery.

## Eight required scenarios and extra adversaries

| Scenario | Executable proof |
|---|---|
| 1 fresh valid | original decision + VERIFIED gate + SIMULATED recovery; worker never called; deterministic receipt |
| 2 wrong identity | node alias invalid or observation target mismatch rejects |
| 3 stale evidence | canonical EVIDENCE_STALE rejects |
| 4 absent/revoked grant | GRANT_PERMISSION, host denial and in-gate revocation reject |
| 5 invalid/changed lease | RESOURCE_LEASE_MISSING or FINAL_HOST_RECHECK_FAILED; no worker |
| 6 duplicate/concurrent | active recovery blocks; two threads use existing journal.claim on the same run/task; exactly one claim and one durable budget reservation |
| 7 UNKNOWN resume | host-witnessed prior causes PREVIOUS_OUTCOME_UNKNOWN; reopened journal + DurableTokenBudget replays UNKNOWN without dispatch, keeps durable reservation; another run also blocked pending reconciliation |
| 8 spontaneous recovery | ONLINE/function-ready final witness CANCELLED, no next_ledger |

Extra tests: absent/conflicting/duplicate/older final observations; changed diagnosis;
self-contradictory function-ready; false source witness; forged prior; recovery input
callback injection; resource/admission crosswire; no socket/process/file I/O in the
proposal path; private errors not leaked. Test 6 and 7 alone create owner-private
temporary SQLite files; no real resource lease, device, service or tool is touched.
MEASURED profiles/grants/leases/physical identities in all fixtures are TEST DOUBLES.

## Reservation and real-host limits

H-LEARN evaluate reserves NOTHING, so repeated proposals never reserve twice. Existing
Session/ExecutionJournal supplies real local atomic run/task claims and durable token
budget reservations; the concurrent test verifies one winner and one rejection, not
an in-memory ALREADY_DONE boolean. UNKNOWN keeps its claim/reservation and requires
existing owner/fence reconciliation; no RESUME or automatic release is introduced.

This does not prove cross-device/per-device resource exclusion, cross-host fencing or
an atomic commit of WAKE next_ledger with a physical tool. NO_DATA(device_CAS_and_live_lease_binding),
NO_DATA(real_host_journal_adapter), NO_DATA(durable_physical_fence),
NO_DATA(real_actuator_authorization). Host must connect existing Session/journal to the
exact admitted worker and a witnessed per-device reservation, recheck permission/lease
and final observations immediately before any separately authorized effect. A pure
proposal or a matching digest is not that proof. No new allocator is proposed here.

## Reproduction and delivery

Run twice on the isolated branch:
- python3 -B -m unittest tests.test_hlearn_scenarios tests.test_wake_recovery -v
- python3 -B -m unittest discover -s tests -p 'test_*.py'
- python3 -B test_llms.py
- python3 -B bin/verify_llms_tree.py

Measured locally 14 NOV 2026, Python 3.14.4: 35 directed tests PASS twice
(12 H-LEARN + 23 WAKE); 985 discovery tests OK twice (984 PASS + 1 inherited skip).
Skip: test_eval_harness.test_red_suite_verdict_red, no RED suite available in this tree.
test_llms 2 PASS twice; tree verifier 5 paths,11996/12109 B twice. Ten guard mutations
detected twice through assertion failures, no runner errors; overlapping guards mean
this is sensitivity evidence, not ten independently exploitable permission bypasses.
All eight required scenario methods additionally executed twice; 17 compact per-step
receipts identical between runs. Five base WAKE recheck requirements reproduced RED
then GREEN on identical synthetic inputs twice; base source loaded read-only in memory.

External SCRUB receipt stores exact HEAD, results, per-scenario receipts, preserved RED
counterexamples, assertion-based guard mutations and checksums. Temporary journal IDs,
paths and native error text are not published. No source/branch of another preceptor
is edited. Draft publication is propose-only; integration/acceptance needs the owner.

This resolves the missing executable H-LEARN P0 BUILD by constructing directly against
current APIs. It does not assert that Hexelion's earlier fragment was applied, that
live device admission is complete, or that model-initiated MCP E2E exists. Hexelion can
review these exact files/tests; Junie/Claude consume read-only receipt fields after ACK.

Next independent work after this draft: prepare six-node C2C-R1 runtime/asset inventory
in Mesa #40, metadata only. No model download, inference, GPU load, SSH, restart,
physical wake, electricity, service changes, new server, merge or deploy.
