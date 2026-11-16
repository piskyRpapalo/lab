# Execution Grant Reservation R1

**Status:** BUILT + TESTED (fail-closed, synthetic contract fixtures only)

## Contract

`ExecutionJournal.claim_authorized()` accepts exactly `grant_id`, `run_id`, `task_sha256`, `agent_id`, and `host_conditions_sha256`. A host-composed `GrantVerificationSource` must validate the existing human-grant signature, issuer trust, bindings, current revocation generation, expiry, and trusted host conditions while the journal holds `BEGIN IMMEDIATE`. The verifier's binding and evidence references are checked before a single SQLite transaction inserts both the unique grant reservation and the run claim. A grant and run can each be consumed at most once. Any write failure rolls back both records.

The existing `claim()` remains a raw journal deduplication primitive; it does not mean authorization and is not connected to dispatch. This increment does not transform plans into tasks or launch a CLI.

## Fail-closed boundary

No production grant issuer, trusted signature verifier, or revocation source was found in the reviewed LAB/APP contracts. Missing verifier returns `NO_DATA(authorization_source_unavailable)` without writes. Even a verifier adapter that labels evidence `REAL` returns `NO_DATA(real_authority_verifier_not_integrated)` until the concrete existing human-signature authority is wired and reviewed. Synthetic fixtures can only return `SIMULATED_RESERVED`; they never produce `AUTHORIZED`.

## Reproduction

- Targeted: `python3 -B -m unittest -q tests.test_execution_grant_reservation` — 9 tests PASS twice.
- Regressions: `python3 -B -m unittest -q tests.test_execution_journal tests.test_durable_budget tests.test_human_uncertainty` — 33 tests PASS twice.
- Sabotage: temporarily removed the `REAL` fail-closed check; `test_real_label_without_integrated_trust_boundary_is_no_data` failed as expected (the adapter would otherwise reserve). Source restored; clean targeted suite PASS.
- `git diff --check` PASS.

## Covered limits

Synthetic fixtures exercise missing source, verifier result corruption, task/run/agent/host binding, grant replay after restart, expiry, revocation, simultaneous claim attempts, and rollback after an injected mid-transaction failure. These tests verify the SQLite contract and fail-closed behavior; they do not prove cryptographic authority, a live grant, dispatch, revocation at dispatch time, CLI execution, or real effects.

## NO_DATA

- `NO_DATA(human_grant_issuer_not_found_in_reviewed_contracts)`
- `NO_DATA(trusted_grant_signature_verifier_not_integrated)`
- `NO_DATA(revocation_source_not_integrated)`
- `NO_DATA(real_cli_dispatch_not_authorized_or_connected)`

## Next minimum step

The APP/LAB owner must wire the existing human signature verifier and revocation state into a concrete host-owned `GrantVerificationSource`, preserve the same transaction/consumption semantics, then add a separately authorized dispatch transition that revalidates expiry/revocation and emits evidence. No task may move to `DISPATCHED` based only on this reservation contract.
