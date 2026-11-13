# Durable Session claims · P2

The existing Session keeps run IDs only in memory. The existing memory_draft
already reconciles durable drafts; it is not a dispatch journal. This optional
host-owned SQLite journal extends Session, without another dispatcher/service.

A new private journal must be explicitly created in a private host-owned
directory; existing files are never overwritten. The journal atomically records
run_id and exact task digest before dispatch. A completed witnessed receipt can
be replayed after restart; changed input with the same run_id is rejected.
Unknown/in-flight work blocks new claims until the host resolves it. No cleanup,
automatic retry, reconciliation override or memory promotion is provided.

SQLite FULL synchronous commits and an immediate transaction protect competing
claims. The journal stores hashes and existing sanitized receipts, never inputs
or model outputs. Host must preserve the journal and own authentication, budget,
lease, backups and recovery. In particular this slice does not reconstruct a
spent token budget after restart, authenticate a tampered host database, or
provide multi-host locking. No APP/service deployment or production E2E claimed.
An unresolved claim requires a separately authorized reconciliation procedure;
it must never be deleted merely to make progress. External authority checks
remain in Session; the journal cannot mint permissions.
