# P2 host attestation and use-time revocation · synthetic boundary

## Source audit

The existing HostWitness is explicitly fail-closed: `human_authorize`,
`quiescence` and `resolution_witness` return false; no real issuer or durable
worker fence is integrated. ExecutionJournal and uncertainty_ack retain UNKNOWN
and budget and require fresh independent witnesses for acknowledgement. The
ReadOnlyMirror rereads the configured projection; FixtureSourceCapture only
returns SIMULATED on synthetic sources. No PID, inode, journal ID, hash,
projection hash, syntactic signature ref or SQLite consistency proves authority.

## New cross-boundary adversarial fixtures

- A coherent fixture snapshot and syntactically valid acknowledgement still
  yield NO_DATA(real_host_attestation); existing HostWitness declines all grants.
- A copied journal retains its journal ID; replacing the source inode is
  rejected against the original pin. The ID is not independent host proof.
- A change to an unrelated table changes DB bytes while mirror.verify() remains
  true for an unchanged task projection at the same timestamp. This is expected
  projection equality, **not** an authenticated source-generation check. No
  caller may promote that result to host/source authority.
- Revoking the synthetic local witness between observation and verification
  invalidates the old projection and returns NO_DATA on a new read.
- A forged/expired record and a newly instantiated HostWitness never establish
  human approval or a fence. An actually active durable fence cannot be shown.
- Revoking the synthetic fence on the second acknowledgement check rolls back
  its transaction and retains budget; no new execution occurs.
- An actual child process reopening an UNKNOWN journal is blocked and observes
  the same retained reservation; no automatic retry or fabricated success.

The tests use disposable SQLite files, synthetic witnesses and the existing P2
contracts. No host authority, source generation protocol, signer, service,
dispatcher, live journal, APP or recovery mechanism is added. `verify=True`
means only that the same projection was recomputed, not that the source as a
whole stayed unchanged. Tests cannot establish behavior for changes reverted
between observations or noncooperating raw-file writers.

## Missing contract and next human decision

A genuine issuer, source identity/generation bound to the intended operation,
revocation and a durable fence enforced at every side-effect boundary remain
NO_DATA(real_host_attestation,durable_worker_fence,real_host_stability).
Before any real journal/credential/runtime integration, the sovereign must
separately define and authorize the host, attestor, source, resource window,
operation scope and enforcement boundary. A possible next fixture is a fully
specified host-owned verifier contract with explicit use-time reattestation,
but no synthetic signer or test callback should be promoted into authority.
Rollback: stop running these tests; no runtime state changes.
