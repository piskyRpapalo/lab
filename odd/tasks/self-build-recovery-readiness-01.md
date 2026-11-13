# SELF-BUILD-RECOVERY-READINESS-01

Read-only projection over the existing host-configured P2 ReadOnlyMirror; no
new journal, claims, worker, dispatcher, permissions, budget settlement or retry.
The host supplies previous/candidate SHAs, plan and approval references: they are
declarations, not evidence of provenance, tested restoration, a fence or human
approval. Human authority and worker fencing remain NO_DATA. A supplied current
HEAD is only a host observation, and mismatch is explicit; it is not a signed
Git verification.

The mirror projects ONE configured task, not every possible in-flight operation.
An uncertain outcome remains UNKNOWN and reservation RETAINED or NO_DATA; an
absent claim is not proof that all workers are quiet. A plan is never a tested
recovery. Results are TTL0 and must be recomputed; text, speech and machine share
one projection ref. Host callbacks in tests are synthetic, never real signature,
fencing or production E2E. Review/fence/provenance, actual restoration test,
whole-system journal coverage and exact-HEAD authority all remain NO_DATA.

Directed tests inspect pre-claim and post-claim state, unknown recovery after
restart, retained budget, synthetic acknowledgement, head mismatch, absent host
witness and forged/stale projection. Existing P2 adversarial corpus covers other
failure cases. Rollback: stop calling the read-only projection; no state changed.
