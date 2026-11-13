# Durable Session claims · P2

The existing Session keeps run IDs only in memory. The existing memory_draft
already reconciles durable drafts; it is not a dispatch journal. This optional
host-owned SQLite journal extends Session, without another dispatcher/service.

A new private journal must be explicitly created in a private host-owned
directory; existing files are never overwritten. Read-only lookup happens before
authorization; the atomic run_id/task digest claim happens only after permission,
budget, cancellation and admission checks, immediately before dispatch. A completed witnessed receipt can
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

Independent review found that the earlier head inserted claims before checking
permission. Denial, inadequate budget or interruption during those checks could
leave false uncertainty and block other work. New tests verify no persistent
claim in those cases, including100 denied runs and restart. An interruption after
the final atomic claim remains uncertain, even if it occurred just before the
adapter call: the journal cannot prove that an external side effect did not begin.
