# WAKE-01: pure recovery proposal (P0)

Technical contract and review receipt; mission authority remains in Mesa #25/#3.
Depth 2, directed source reading. Base: d9807a96982b03ae5acea7ea289e4f32bd571a5f.
Scope: meta_harness/wake_recovery.py, tests/test_wake_recovery.py, this file.
CLAIM: private Mesa #3 comment 6884577387. LAB #207 stays independent.

## Sources and reuse

- Mesa #25 comment 6884491995: WAKE commission, six nodes, clock/physical-map limits.
- Mesa #3 comment 6884412316 and #38 comment 6883835103: coordination/H-LEARN.
- bin/resource_decision.py: canonical age_seconds (120s), encode and resource identities.
- meta_harness/resource_admission.py: canonical AdmissionGate; no new Host/grant/lease.
- meta_harness/delegation.py: existing task identity, validation, hashing and permission boundary.
- meta_harness/recovery_readiness.py is build rollback readiness, not fleet power control.
- meta_harness/readonly_mirror.py already serves journal/Notebook/Acho projection.
- p0x/hexelion/laboratorio/MH-01-DISCOVERY-CONTRACT.md and
  test_device_discovery_admission.py: synthetic/historical admission is not live authority.
- p0x/hexelion/laboratorio/mcp_cliente_hexelion.py: S-3 read-only tools
  ping/capabilities/state/audit_last; voice matching is not authentication.
- hexelion-nexo/heartbeat_d7/observe.py: public coverage observation, not power diagnosis.
- APP notebook_read.py/notebook_write.py: dated, sanitized observation projections;
  last_seen does not prove a running process. WAKE receipts are not wired to these schemas.
- MH-01 projections are evidence, not permission. MCP S-3 read-only capabilities do not
  authorize recovery. Nexo/heartbeat reachability does not prove a service or power state.

## Typed inputs, trust and output

Frozen Intent binds opaque node_ref, unique attempt_ref, generation and method into
existing task.input_sha256. Observation binds node, independent host witness, timestamp,
condition and function_ready; post proofs additionally bind attempt_ref. Capability binds
method, node, freshness, evidence digest, critical flag and optional physical mapping.
Ledger is a trusted per-device snapshot with version, attempts, bounded seen-attempt
history, cooldown, active reservation and unknown-outcome flag. No addresses, credentials,
MACs, plug IDs, raw errors or device inventory are transported in receipts.

Host owns verify_observation/verify_capability and admission(task) callbacks. They must
witness identity, physical independence of sources, capability/critical-infrastructure
policy and the current AdmissionGate.record for the exact recovery actor/task. A model
cannot supply these callbacks or a serialized record as authority. Digest checks are
integrity checks, not authentication. The recovery actor may be Beelink; the unreachable
target cannot itself satisfy the actor's resource/route/lease checks. This module reads
an existing gate record, never evaluates a new grant or activates a resource.

Typed RecoveryProposal returns {RecoveryReceipt receipt, Optional[Ledger] next_ledger}. Receipt <1024 encoded bytes contains state/cause,
task digest, stages, method, generation/CAS version and next-ledger digest. Receipt hash
is reproducible integrity only. dispatch_authorized=false, physical_actions=0 and
promotion=NOT_AUTHORIZED are invariant. SIMULATED is never MEASURED, admitted, recovered
or permission to execute. Missing proof has verification=NO_DATA with explicit cause.
No real successful recovery is claimed, including when two synthetic post proofs agree.

OBSERVE -> DIAGNOSE -> SELECT_METHOD -> ADMIT -> EXECUTE_SIMULATED -> VERIFY -> RECEIPT.
ABSTAIN, CANCELLED and owner-only PROPOSED can finish early. Network loss/unknown power
never becomes a power diagnosis. Two distinct host-witnessed sources must agree.
RECONNECT requires service failure; WAKE_LAN requires suspend/off and witnessed capability;
WAKE_WLAN requires suspend and witnessed capability. POWER_REQUEST requires physical
mapping and always stops for owner authorization; critical power always needs owner.
MANUAL_RECOVERY also permits owner-only guidance for unknown network/power; it
only proposes intervention and grants nothing. P0 implements no effect.

Limits: maximum 8 observations per phase, TTL 120s, maximum 3 attempts per host-authorized
recovery episode, cooldown 300s. Resetting the budget is an external owner decision,
not a model operation. Missing history/unknown outcome blocks retries. Repeated attempts
and old generation reject. Host cancellation or a responding function cancels recovery.
Post proofs must match attempt, node, function and two independent witnesses, be fresh,
and not precede the latest diagnosis evidence. All callbacks are bounded, read-only,
host-trusted injections. Exceptions fail closed without their private error text.

Concurrency: next_ledger is ONLY a proposal, never a committed lock or new lease. Two
simultaneous pure calls can produce identical proposals. A future host must atomically
CAS expected_version and reserve the attempt before an allowlisted effect; a losing CAS
must reobserve. A version counter from a model is not a witnessed ledger. The host must
retain unknown outcomes/reservations until reconciliation, not reset them to retry.

## Six-node fixtures and current evidence limits

Tests use six synthetic opaque identities corresponding in scope to Beelink,
Onexstation, Orange Pi, Raspberry Pi, Jetson and Fedora C302C, not their identifiers.
Canonical observation says network recovered; this is not firmware/WoL/GPU verification.
Fedora: NO_DATA(ssh_wol_wowlan_not_verified). Orange Pi:
NO_DATA(physical_identity_and_ssh_socket_vs_unit_not_verified). Jetson:
NO_DATA(clock_or_timezone_skew_and_supported_power_state_not_verified).
Fleet: NO_DATA(physical_plug_mapping_missing), NO_DATA(firmware_wake_capability_unverified).
Beelink/router/critical infrastructure may never be power-cut by a model decision.
No operational reads/probes, SSH, Tailscale, network scan or power manipulation occur.

## Verification and adversarial matrix

Synthetic tests cover all six nodes; exact AdmissionGate record accepted without worker
execution; another task's record rejected; revoked lease rejected; arbitrary model OK
rejected; stale/future evidence; identity mismatch; missing/duplicate/conflicting witnesses;
unknown network/power; capabilities missing; service/WLAN methods; plug mapping/critical
owner; retry budget; cooldown; replay/history; active concurrent attempt; old generation;
reappearance/cancellation; attempt-mismatched/older post proof; incomplete function proof;
host cancellation, tampered intent/record digest, bounded malformed input and
private callback errors. I/O tripwires cover sockets,
processes and file opening. No physical recovery latency/success benchmark exists:
NO_DATA(no_authorized_real_executor). External Hexelion-specific unpublished scenarios:
NO_DATA(no_additional_fixture_received); no claim of running unseen cases.

Commands, each twice:
- python3 -B -m unittest tests.test_wake_recovery -v
- python3 -B -m unittest discover -s tests -p 'test_*.py'
- python3 -B test_llms.py
- python3 -B bin/verify_llms_tree.py

Measured locally on 2026-11-14, Python 3.14.4: 21 directed tests PASS twice;
931 discovery tests OK twice, one inherited skip each (test_eval_harness.py,
no RED suite available in this tree). test_llms: 2 PASS twice; tree: 5 paths within
11996/12109-byte budget twice. Ten in-memory sabotages detected twice, with assertion
failures (not runner errors). The independent #207 source at
9ae5b5b41c00e54cb8c962f01291ece09ce319fc passes its 17 tests twice in this host
and shares the same canonical resource module; no source/branch coupling is introduced.
These are software fixture measurements, not hardware recovery benchmarks.

Exact HEAD, logs, mutation results and checksums belong in the external SCRUB receipt
and PR/Mesa delivery, avoiding a self-referential commit digest.

## Activation order and consumers

1. Review this pure P0; H-LEARN consumes ABSTAIN/PROPOSED/SIMULATED plus explicit cause.
2. Notebook/Acho consume the compact semantic receipt via the existing journal/mirror;
   no new writer or visual UI is built. Mapping this receipt into their existing schemas
   remains NO_DATA(consumer_adapter_not_built); no drop-in ingestion is claimed. Unknown observations stay NO_DATA.
3. Separately authorize a host adapter with atomic reservation, final permission/lease
   recheck, critical-infrastructure policy and explicit tool allowlist. No MCP executor
   is introduced here. LAB #207 needs no import, dependency, rebase or change.
4. Prove identities, source independence, clock freshness and physical mapping before
   enabling each method. Start read-only reconciliation, then separately authorized
   service reconnect, wired wake, supported WLAN, and human-only power request.
5. Measure recovery latency, success rate, false positives and unauthorized operations
   only under an approved live experiment; current numbers are NO_DATA(synthetic_only).

Risks: forged host callbacks, dishonest witness independence, stale records after read,
ledger rollback and post-proof causality require trusted host enforcement. A P0 receipt
cannot eliminate these operational risks and is never an action token. No merge/deploy
or physical activation is included; the Sovereign retains exact-head integration/activation.
