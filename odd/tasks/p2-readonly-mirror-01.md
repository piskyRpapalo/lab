# P2 host mirror · read-only contract

Reuse LAB uncertainty_views and the fail-closed HostWitness. The host constructs
an explicit closed allowlist mapping opaque source IDs to an absolute private
journal path and its exact existing task. Requests contain only an allowlisted
ID; they never supply paths, tasks, approval callbacks or credentials. This is
an in-process producer, not an HTTP endpoint, new service, grant or dispatcher.
The trusted host must supply and recheck a local-source filesystem witness;
the default is NO_DATA(local_source_not_attested). A path or allowlist entry
alone cannot prove that a mount is local. Tests use a synthetic witness only.

SQLite opens with mode=ro and query_only. WAL/SHM/rollback sidecars produce
NO_DATA until a separately reviewed snapshot mechanism exists; immutable=1 is
forbidden because it can hide committed WAL data. No source paths or raw logs
are returned. Views use the existing projection, one ref and TTL=0. UNKNOWN
remains UNKNOWN, reservation RETAINED or NO_DATA. Since real human and fence
witnesses are unavailable, a synthetic acknowledgement is not promoted.

False blocking (missing witness, busy/WAL source, unsafe source) is intentional
and measured in tests. The host still needs a safe journal source, actual human
and durable-fence adapters, authenticated APP transport, deployment review and
live E2E. Current producer uses temporary synthetic files only. Coordinate the
same record with Claude; no APP or active worker changes are part of this slice.
