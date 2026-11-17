# Persistent memory: process-boundary measurement and distributed limits

This is a **measurement note**, not a new mission, protocol, memory engine,
service, authority issuer or deployment. The source of missions remains the
existing Mesa/canonical index. The tests use disposable localhost-only fixtures.

## Existing memory producers and consumers

| Existing source | Durable state | Freshness / retention boundary | Safe consumer | Remaining evidence |
|---|---|---|---|---|
| APP `memory.py` | SQLite engrams, links, profile, drafts, conversations and outgoing records; WAL; SQLite API backup and restore that refuse overwriting a live destination | No global expiry for all records established here: `NO_DATA(global_APP_memory_TTL)`; backups verify selected row counts, not complete semantic equivalence | APP local memory/retrieval; LAB `memory_draft.py` may propose an exact receipt-bound draft with host consent, not promote | Live APP backup→restore→full functional replay: `NO_DATA` |
| LAB `meta_harness/execution_journal.py` | Private SQLite run claims, receipts, durable token reservations, separate witnessed resolution events | Unknown/pending claims remain until host-authorized reconciliation; no automatic expiry or retry. Owner-private directory and file required | Existing `Session`, `DurableTokenBudget` and `ReadOnlyMirror` | Authentication of a physical remote worker: `NO_DATA` |
| LAB `meta_harness/uncertainty_views.py` and `readonly_mirror.py` | **No new store**; re-read existing host-owned journal | Projected TTL **0 seconds**; always recheck source and witness; WAL-sidecars require a separately approved snapshot | Text, speech and machine consume one current `state_ref`; no permission gained | Genuine human authorization and remote independent witness: `NO_DATA` |
| LAB `meta_harness/context.py` | Ephemeral, source-version-bound retrieval snapshot, not durable memory | Validated consumer max age 1..86400 seconds, default 120; observation sources also checked for age | Local host-injected retrieval; quote validation | Stale or unversioned sources cannot become live evidence |
| Private internal training/feedback loop | Existing local SQLite state and candidate-dataset files, not a distributed memory consensus mechanism | Dataset/model freshness and cross-device promotion: `NO_DATA` | Human-reviewed local training pipeline | `NO_DATA(training_E2E,remote_provenance)` |

Source paths are illustrative contract anchors, not install paths. No private
hostnames, IP addresses, model identities or credentials are included.

## What the new test actually measures

`tests/test_memory_process_recovery.py` uses the existing
`ExecutionJournal`, `Session`, `DurableTokenBudget`, and
`ReadOnlyMirror`. It launches a **new Python interpreter for each phase**
and an owner-private temporary database:

1. Write a deterministic **synthetic** known result, terminate the
   producer process, reopen in a new process, and require exact replay
   without another worker call or another token charge.
2. Write a deterministic **synthetic** uncertain result, terminate,
   reopen, preserve its reservation, forbid replay effects and fresh work,
   and project the same current UNKNOWN state through text, speech and
   machine with one `state_ref`.
3. A projected view has TTL0. Verifying a previously observed packet
   against a later timestamp must fail.
4. All worker side-effect markers exist **only in the temporary fixture**.
   No model, remote node, public service or human grant is invoked.

These scenarios complement, rather than replace, the existing tests for
real child exit after an atomic claim, human-witnessed synthetic restart,
lost acknowledgement and corruption.

## Distributed memory is a separate gate

A process restart on one host **does not** establish durable replication or
authenticated memory across devices. Do not send an APP database, free-form
prompts, private context or complete journals to a peer by default.

Before any node-to-node persistence claim, measure an exact
host-owned source identity, expiry/revocation, transport observation,
fencing/lease, snapshot or journal handoff boundary, and one independent
witness. A SHA-256 digest does not authenticate a remote host.
The recipient's projection is evidence to check, not authority to execute.

Acceptance for a later, separately approved test: a synthetic node journal
is restarted, its read-only minimal projection is correlated to a
particular source and context via an authenticated channel, an UNKNOWN
operation never retries, and the result remains NO_DATA where remote source
binding or host authority is missing.

**Current status:** LOCAL_PROCESS_RESTART=TESTED_IN_FIXTURE;
REMOTE_PERSISTENT_MEMORY_E2E=NO_DATA(not_tested);
INDEPENDENT_REMOTE_WITNESS=NO_DATA(not_implemented).
