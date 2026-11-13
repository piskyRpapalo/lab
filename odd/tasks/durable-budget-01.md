# Durable token budget · proposed host integration

Optional extension of the existing Session and ExecutionJournal. Host explicitly
initializes a new empty private journal with a fixed budget; no existing journal
or database is migrated, reset or deleted. The human/host supplies the limit;
this code does not authorize an action or increase a provider quota.

Pre-permission checks and budget preflight perform no persistent reservation.
Immediately before possible dispatch, a SQLite transaction records the exact
task claim AND debits its maximum token reservation. Concurrent callers are
serialized. A known receipt and settlement commit together; a successful replay
does not debit again. An unknown result or crash retains the full reservation
and blocks new claims. Interrupted authorization/denial creates neither a claim
nor a debit. Host retains lease and authority; no automatic retries or reset.

SQLite storage must remain private, host-owned and intact. This is a local token
ceiling, not a provider billing meter, a multi-host quota or a durable resource
lease. Human-authorized resolution and handling a damaged journal are separate
proposals; no uncertain reservation is released automatically. Tests use only
temporary synthetic SQLite journals; no APP or service is activated.

Local validation: 781 tests twice (one pre-existing skip), canonical companion
checks twice and 11 directed budget tests twice. Real child process exit after
atomic claim retains the reservation after restart. CI exact-head follows.
