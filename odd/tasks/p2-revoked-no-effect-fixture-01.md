# P2 revoked means no effect · synthetic fixture only

## RED before GREEN

The first test-only destination incremented a counter despite a revocation after
Session's last grant read. The directed assertion `sink.effects == 0` failed:
1 != 0. A retained negative control still shows that an unprotected synthetic
destination performs one effect even after that earlier revocation. No real
endpoint, host grant, credential, signer, worker, dispatcher or service is used.

The GREEN fixture gives the *test-only effect owner* a separately mutable
synthetic state and checks active status, host, target, operation, task hash,
generation and expiry inside the same in-process lock that orders its counter
increment and revocation. Duplicate operations are rejected in that fixture.
This is an illustrative linearization inside a disposable process, **not** a
durable fence or a host authority. A Boolean or dictionary in this test is not
a signature. Session and ExecutionJournal production code are not changed.

## Bounded measured matrix

Nine fixture requests: two valid and seven invalid (revoked, stale generation,
wrong operation, host, target, task, and expired). Expected/observed per run:
`authorized_effects=2`, `unauthorized_effects=0`, `revoked_effects=0`,
`false_blocks=0/2 valid`, `unknown_retained=7/7 rejected`. On sink rejection,
Session has already handed over to an adapter and conservatively records UNKNOWN
and retains the reservation; this is an availability cost, not a false success.
The fixture repeats both the no-admission and synthetic-admission revocation
windows. It tests known replay, duplicate claimants, interruption after one
effect, an UNKNOWN after journal reopen, no retry and no budget release.

These zeroes cover only the named fixture matrix. A valid synthetic operation
passes once, but new processes or real sinks do not share the fixture's lock or
in-memory replay set. If an effect was accepted before revocation, later
revocation cannot undo it. Neither process termination nor this test establishes
that an old real worker cannot execute. NO_DATA(real_host_attestation),
NO_DATA(durable_worker_fence), NO_DATA(live_dispatch_binding),
NO_DATA(real_host_recovery), NOT_AUTHORIZED remain. Host issuer/revoker,
protected operation and effect-owning enforcement point require separate
sovereign decision before any real integration. Rollback: stop running tests.
