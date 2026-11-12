# CEREBRO-CONTEXT-01 · compose the existing brain contracts

Status: BUILD, stacked on LAB #176 (not merged). Constructor: Codex CLI/FORGE.
Commission: the Sovereign's 2026-11-12 CEREBRO ORQUESTADOR direction;
APP #255 deliverable B. Human exact-head FIRMO gates merge, never construction.
No APP/interface, Claude branch, user database, service, device or deployment edits.

## Problem and scope

APP #260/#261 retrieve and verify source bytes but do not enforce observation TTL.
#262 separates CLI from carbon conversation; CLI agents still share one `cli`
thread. A catalog, source quote or model proposal is not an execution grant.
The existing `memory.proponer_borrador` commits before returning, but has no
idempotency key: a lost acknowledgement can otherwise duplicate a proposal.

This slice composes existing functions in an operator-run public experiment.
It adds a consumer freshness boundary, a witnessed fixed-capability cycle, and
reconciliation around the existing draft writer. No new index, permission
service, state bus, dispatcher, training engine or permanent daemon is added.
The final outcome is a PENDING draft; only the person can promote an engram.

Depth 2, targeted coding read. Reused LAB AGENTS/STATE/README and benchmark
contracts; Study declared-depth law, governance, measurement, contracts and
collisions; Roadmap NORTE/Ley del Camino Libre and relevant HITL sections;
Atlas AGENTS; firmas current index/decisions and book blob
`c94d58841aa0434d888fc5c2728b081109a7896d` (not re-transcribed).
APP retrieval, quote, memory, CLI/action and LAB-3/LAB-4 APIs were read, not the
whole corpus or a whole-organization audit. Private source content is not exported.

Measured source bases: LAB main `364740300f8df9cabe28511188b045fe557bffd4`;
stack base LAB176 `a8a347c73ec7052fc0f85156f168fbc30e7b440d`;
APP main `2dd6549fcdb738914161844ac895477af11d6687`.
APP #260/#261/#262/#263 are ancestors of that main; its exact-head CI passed.
Installed S3 script/policy matched P0X #118 in the preceding audit. No S3 tools
are granted additional permissions by this slice. Its voice environment selects
a profile; it does not cryptographically authenticate a caller.

## Files and contracts

| File | Role | Existing dependency |
| --- | --- | --- |
| `meta_harness/context.py` | Bounded private snapshot, source/version refresh, UTC/TTL, private quote verification | APP search + `hexelion_book` injected by host |
| `meta_harness/brain.py` | One bounded cycle + same-state text/speech/JSON | LAB176 Session, witness, capability evidence |
| `meta_harness/memory_draft.py` | Reconcile one exact receipt origin with durable private DB | APP `memory.proponer_borrador`, never promotion |
| `meta_harness/brain_demo.py` | Explicit public experiment with original APP libraries | existing proxy/native worker; new private demo DB/index |
| `meta_harness/hexelion.py` | Optional closed context digest in the existing planner input | default profile remains byte-identical |
| `tests/test_meta_context.py`, `test_brain.py`, `test_memory_draft.py` | Portable deterministic/negative contract tests | doubles are labeled synthetic, not real model evidence |

Input is host-owned: query, source policy, pinned source implementation digest,
exact prepared tasks, current UTC, Session authority/budget/cancellation callback,
and optional draft writer. Sources are private data, never tool names or grants.
`source_version` covers the loaded APP dependencies in the demo, not authenticity
of their authors or the model's weights. The host trusts the selected checkout.

The proposed `preceptoros.context-consumption/1` record (<1024 B) exports hashes,
counts, capture time and freshness basis. `document` is `snapshot_only`, even if
the quote says “live”; source last-modified time is not a device measurement.
Unknown document dates are retained as `source_time_unknown`; observations with
unknown, future or expired source timestamps are refused. Snapshot lifetime and
source observation age both have a host-chosen bounded TTL. Sources and pinned
implementation bytes are rechecked before each action. This is point-in-time
validation, not a transaction spanning retrieval, inference and the filesystem.

The proposed `preceptoros.brain-cycle/1` receipt (<1024 B) references the context,
two baseline receipts, planner receipt, delegated receipt and draft status.
Closed causes name the exact failed stage. A valid projection hash proves
integrity, not authenticity; `verify_cycle` additionally needs the live Session
witness and exact tasks. Serialized receipts alone cannot grant permission.

Planner choice is recovered from its witnessed closed-output digest, including
Session replay. A refreshed adapter object need not have executed. Every actual
dispatch still passes the existing exact-task host authority and shared budget.
The optional `context_ref` enters that planner's prompt and exact input hash;
it conveys the verified snapshot reference, never raw source text or the query.
Only one operator-prepared public sorting capability is demonstrated: no claim
of arbitrary task understanding, general intelligent selection or calibrated
semantic accuracy. Failed or uncertain attempts do not silently fall back.

The memory adapter exports the existing row state with a cause; no private row
ID, text, path or prompt is exported. Only a fixed receipt-hash summary reaches
the APP writer. It uses a permanent private flock inode and exact
`meta-receipt:<sha256>` origin. It finds at most two rows for that origin,
refuses duplicates/mismatches, and reconciles a commit whose acknowledgement was
lost. Discarded/promoted rows are reported, never resurrected or promoted.
No migration or table is added. Cooperating writers must use this adapter;
uncoordinated writers and hostile same-UID filesystem replacement are outside
the guarantee. Lock/SQLite operations have bounded waits; trusted synchronous
Python callbacks must return promptly. Cancellation after a possible commit
returns NO_DATA; an authorized retry reconciles instead of blindly inserting.

## Reproduction and acceptance

Portable tests, no model calls or external traffic:

```sh
python3 -B -m unittest tests.test_meta_context tests.test_brain tests.test_memory_draft
python3 -B -m unittest discover -s tests
```

Run both commands twice. Repository workflow companions and negative mutations
are required before publishing; exact-head remote CI is separate evidence.

An operator with an existing APP checkout and installed local Hexelion can run:

```sh
python3 -B -m meta_harness.brain_demo --execute-public \
  --app-root "$APP_CHECKOUT" --state-dir "$NEW_PRIVATE_DEMO_DIRECTORY" \
  --approval-ref "$HOST_APPROVAL_REFERENCE_SHA256"
```

The directory must not already exist. The demo fails rather than overwrite it.
It creates only a public synthetic FTS index and a new owner-private APP-schema
database there; it never selects the real user DB. Two separate runs need two
new directories. Without `--execute-public`, there is no inference or DB write.
`--stop-file` cancels new work; an already-issued local generation may finish.
No endpoint is accepted on the CLI: the demo uses the existing numeric-loopback
Hexelion proxy. Server network isolation is NO_DATA, not implied by loopback.
The fixed public prompt carries no private source or conversation text.

Acceptance: original APP retrieval/quote checks pass; two current native
baselines pass independently checked sort properties; actual Hexelion proposes
delegation; host authority approves exact task; native execution passes; a
receipt exists; the original memory writer commits one pending draft; another
fresh DB connection reconciles it without inserting; engram count stays zero;
one closed cycle record feeds text/speech/JSON. If Hexelion abstains or any step
fails, keep the NO_DATA result and locate its stage instead of forcing a PASS.

## Verification log

- Initial 16 consumer tests: two replay failures, caused by reading a newly
  created planner object's unset `decision` on Session cache hits. Fixed using
  the witnessed receipt digest; original tests now pass. Red retained here.
- Original APP lookup and quote/relevance pipeline smoke: MEASURED, one public
  source, six pinned source files; no model or private corpus used.
- Portable targeted tests at initial checkpoint: context/brain 17 + memory 26
  PASS. Final canonical tests, mutations, H5, model runs and CI: pending.
- Real code mutations: initial 10/11 detected in both runs. The dedup mutation
  survived because a test assertion inside the proposer was caught as a lost
  acknowledgement. Added a caller-side attempt counter; now 11/11 detected
  twice, zero test errors. The adapter itself already avoided the second call.

## Integration, limits and rollback

EXISTE EN CÓDIGO: this LAB consumer and the merged APP source APIs.
INTEGRADO: prototype library composition only; APP/H3 runtime wiring pending.
OPERATIVO / MEDIDO E2E: only claims backed by the final public-demo artifacts.
NO_DATA(host_not_wired): live APP consumption and actual user memory update.
NO_DATA(not_measured): Acho/screen-reader/physical audio, general semantic
accuracy, cross-model optimization, calibrated latency/concurrency/energy limits.
One fixture cannot justify a LoRA; LAB176 measurement gates remain unchanged.

For Claude: inject existing APP/H3 effective authority and a durable execution
journal (Session replay alone is process-local). Pin source policy/version;
reuse the existing retrieval/quote path and original memory writer. Consume
`record`/`views`, keeping private snapshots and drafts out of public endpoints.
Do not add a parallel producer. Show PENDING as awaiting review, never learned
or LIVE. The demo gate is not human authentication or a production authority.
The user decides when to wire the real database and when to promote a draft.

Rollback: remove this optional consumer/entry point or reviewed revert of this
slice. Existing APP/S3/Claude services remain untouched. Demo state stays private
for operator review; no automatic deletions, promotions, timers or deployments.
Next selected authorized mission: source-attributed read-only resource evidence
for admission/concurrency bounds, composed with the existing router/Session;
no load experiment or service restart until idle/coordinated conditions exist.
