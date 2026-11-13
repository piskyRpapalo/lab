# P2 WAL consistency fixture · 2026-11-13

## Source audit and scope

LAB #201's FixtureSourceCapture and ReadOnlyMirror reject -wal/-shm/-journal,
source change, identity mismatch and missing or revoked witnesses. ExecutionJournal
retains UNKNOWN and token reservations. HostWitness rejects all real-authority
callbacks; a PID, journal ID, cloned DB, checksum or synthetic callback is not an
independent host identity or fence. No existing genuine source generation/fence
is established. Existing math coordination remains #6865619018; no model workload
is invoked by this fixture.

## Experiment

Tests use only temporary HumanUncertainty SQLite journals. A SQLite WAL writer
commits a fixture table; a separate read-only SQLite connection backs it up to
an in-memory DB with the SQLite Online Backup API, never immutable=1. The WAL
snapshot includes the committed table and excludes a still-open write transaction;
its UNKNOWN claim and reserved budget remain UNKNOWN and retained. A concurrent
commit during incremental backup yields either complete generation, never a
mixed pair in the tested fixtures. The backup may internally restart under a
concurrent SQLite commit; that is SQLite copy behavior, not a task retry.

An old snapshot becomes stale after a new WAL commit. Neither generation values
nor SQLite consistency prove host stability, source provenance, authorization,
or a durable use-time fence. Existing source_capture continues rejecting WAL/SHM.
A clone retains the journal ID but a mismatched host inode is refused; pinning
the clone's own inode still yields no authenticated source. HostWitness refuses
forged/revoked authority. An actual child process reopens an unresolved journal,
is blocked without dispatch and reports the reservation remains 64. A separate
empty journal denies a revoked permission without creating a claim or reservation.
Test sources and witnesses are synthetic; no live journal, APP, credentials,
models, worker, service, scheduler, journal implementation or dispatcher is introduced.

## Limits and next step

SQLite's transaction guarantees do not cover processes that bypass SQLite file
locking, repository/directory replacement, stale use after the last observation,
filesystem/VFS compromise, or operational source attestation. Backup is coherent
only in the tested setup; failure to reproduce is NO_DATA, not verified host
stability. Backups may touch the WAL/SHM of their *temporary* source, so no live
source should use this fixture. Falsely blocking WAL remains intentional in the
existing mirror. NO_DATA(real_host_stability), NO_DATA(real_host_recovery),
NO_DATA(durable_worker_fence), NOT_AUTHORIZED remain. Existing P2 corpus covers
additional forged/stale/inode/corruption/revocation cases; no retry or refund is
permitted for UNKNOWN. Next: design a separately attested source + durable fence
and use-time revocation contract, test independently before seeking an explicit
human decision on any live host access. Rollback: stop running fixture tests.
