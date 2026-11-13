# P2 host witness · fail-closed boundary

LAB main dc00c0b. Existing signing book requires `HITL: <sha40> <slug> <date>`
in Sovereign's buzon#30; installed preceptoros-firmar explicitly belongs to the
Sovereign and acts on PR heads. Neither proves an uncertainty proposal's SHA256,
expiry, revocation or journal/task binding. No signing service is added or run.

Existing run_worker terminates and joins its own child, but this is process-local;
no durable cross-restart worker fence was demonstrated. A missing PID or reused
PID is not a fence. Existing resource lease is a host callback, not evidence of
durable fencing. Therefore human_authorize, quiescence and resolution_witness
all return literal False. Diagnosis reports NO_DATA with a bounded cause and
rejects stale, forged and misbound records; it cannot activate a real decision.

This conservative boundary can falsely block recovery: false-blocking is
expected until actual signed-decision and durable-fence producers exist. No
untrusted metadata, claimed approval or fabricated PID evidence changes that.
Future integration requires independent evidence of exact human authority,
revocation/expiry and an active durable fence over the original worker/lease.
Local-only; no APP, service, hardware, permission, journal or signer changes.
