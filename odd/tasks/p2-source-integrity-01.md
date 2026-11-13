# P2-SOURCE-INTEGRITY-01

This fixture-only contract observes an allowlisted temporary SQLite source
without writing it. It reuses ReadOnlyJournal's ownership/mode/link checks and
P2's journal_identity, claims and resolution_events, with host-pinned device,
inode and journal ID. It reads at most 2 MiB twice, checks file metadata, path
identity and every WAL/SHM/rollback sidecar repeatedly, and runs bounded SQLite
quick_check against a private temporary copy using mode=ro. It never uses
immutable=1 on the live source. Only the copied bytes are opened by SQLite.

| Fixture or condition | Outcome/cause | Evidence boundary |
|---|---|---|
| Clean source and synthetic witnesses | SIMULATED / synthetic_fixture_only | hash identifies fixture bytes only |
| Missing, invalid, revoked local witness | NO_DATA / local_source_not_attested or local_source_revoked | no locality authority |
| Missing or revoked fixture witness | NO_DATA / fixture_witness_unavailable or fixture_witness_revoked | callbacks are synthetic |
| WAL, SHM, rollback journal, broken sidecar link | NO_DATA / source_sidecar_present | no WAL/SHM reconstruction |
| Noncooperating writer or metadata change | NO_DATA / source_changed | changes observed at checks only |
| Real WAL activated during fixture read | NO_DATA / source_sidecar_present or source_changed | ordering depends on writer timing |
| Wrong pin or inode replacement | NO_DATA / source_identity_mismatch | device/inode not a signature |
| Different stored journal ID | NO_DATA / journal_identity_mismatch | ID is not independent authority |
| Truncated/corrupt SQLite copy | NO_DATA / snapshot_corrupt | quick_check is not provenance |
| Empty or >2 MiB source | NO_DATA / source_size_invalid | intentional false rejection |
| Prior UNKNOWN and reservation | no new dispatch or release | existing P2 journal remains authoritative |

The fixture result never supplies a real source-integrity or authority verdict.
A writer could change and restore state between checks, race a witness, or alter
the source after the last check; stat metadata and matching hashes do not prove
stability. SIMULATED always accompanies NO_DATA(real_host_stability),
NO_DATA(real_host_recovery), execution_authorized=false and no_retry=true.
No real journal, APP service, permission, worker, dispatcher or grant is used.
Local callbacks in tests are synthetic; no authentication is inferred from the
journal ID, SHA-256, quick_check, allowlist or clean snapshot.

The next integration requires a separately reviewed, genuinely durable host
source/fence and provenance witness, a consistent WAL-aware capture, exact
identity and use-time freshness. Until then the existing mirror retains its
sidecar rejection. Rollback: stop calling this standalone fixture contract.
