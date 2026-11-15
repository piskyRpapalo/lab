# MULTIAGENT-P0 · sovereign agent presence projection

Technical contract/receipt; missions and assignment remain in Mesa. Authority:
Mesa #39:6885860648 and current Sovereign BUILD. CLAIM #3:6885956406. Depth 2.
Base LAB c2afcf0b4e5da5a30683ad941ac97e9860f67402; #210 remains a separate draft,
review closed for exact-head human signature without merge or source modification.
C2C-R1 inventory is preserved; no models, inference or GPU activity in this increment.
Scope: meta_harness/agent_presence.py, tests/test_agent_presence.py, this file.

## Source audit and reuse

Gentle Shell at c5313157b798a9c31ff122204f6b8c7dde1c3d75:
https://github.com/Gentleman-Programming/gentle-shell/tree/c5313157b798a9c31ff122204f6b8c7dde1c3d75
lib/orchestrator-presence.ts, lib/orchestrator-scope.ts, lib/orchestrator-consultation.ts;
MIT source license, copyright Mario Zechner. Independent Python implementation of
metadata-only identity/expiry/binding concepts, not a port of its publisher or storage.
No free-text activity/tool-output transport: source explicitly warns that a field
whitelist does not redact secrets. No timers, cursors, directories, daemons or server.

Existing ExecutionJournal/Session own task identity, execution claims and native receipts.
HostWitness, P2 source-integrity, M1a and ReadOnlyMirror already provide host-pinned
source/capture/uncertainty boundaries. They do not provide an agent/session/instance
plus Mesa CLAIM plus Git HEAD presence projection. The new projection composes those
source references without creating a registry, journal schema or execution channel.
Reuse: delegation.sha/encode/validate_task/verify; canonical resource age_seconds;
self_build_git_witness.HEX40. GitWitness's host-pinned repo identity remains the future
Git capture boundary; this pure module does not construct or invoke it or run Git.
MH-01 device/capability evidence is not agent identity or permission. MCP S-3/M1
read-only client is not called or replaced. APP/WEB/visual owners are unaffected.

## Typed input and pure contract

Selection: exact opaque session_ref, instance_ref, generation, repo_ref, clone_ref,
worktree_ref and immutable HEAD. Host generates privacy-approved opaque references;
a short name, path hash or digest alone does not authenticate an agent. Two clones
may share a repository origin while having different host/common-dir identities.
Same display names never select or merge sessions. Restart/instance/generation changes
require explicit new selection; no automatic fallback to another activation.

Declaration: that selection plus approved public label/repository/branch/mission slug,
claim_ref, scope_ref, original declared_at, heartbeat_at and explicit field omissions.
It is an agent declaration, not proof of execution or assignment. Public labels and
branch spellings have closed size/character rules; no filesystem path is accepted.

Claim: current host-witnessed Mesa source, owner session/instance, repository/worktree,
mission/scope, claim generation, source observation and review-pending flag. claim_ref
is a digest of this capture, not a new mission or a signature. Owner/generation changes
invalidate the previous binding; no automatic takeover or task allocation. Its timestamp
means when the host witnessed the current Mesa projection, not when the issue was born.

Observation: exact selection/claim/source plus existing task and ORIGINAL native Session
receipt. Neither raw task nor receipt is published. Integrity verification is necessary
but insufficient: host verify_observation must prove journal ownership/source stability
AND the original session/instance/HEAD/CLAIM/task binding. Session.attests alone proves
the receipt is stored; it does not add missing Git/session/claim lineage. An attacker can
relabel a self-consistent wrapper; the independent host context witness must refuse it.
The tests simulate that host map and demonstrate refusal; no live adapter is claimed.

Capability: approved name, exact receipt/task/scope references plus independent host
qualification. A recent PASS can demonstrate only that named, scoped task, not general
competence or permission. Output includes native evidence_basis (e.g. synthetic), so
fixture evidence cannot masquerade as a measured runtime capability. UNKNOWN, stale,
unwitnessed, duplicate or unrelated evidence is never promoted into demonstrated ability.

project(...) returns agent-presence-snapshot/1, detached from inputs, at most16KiB.
receipt(snapshot) returns a compact <1024B consultation receipt referencing the SAME
snapshot/evidence. authority='none' and ownerReply=false are invariant in both.
No grant/lease, control handle, scheduler, mission assignment, write lock or tool exists.

## States and time

| State | Meaning | What it does not mean |
|---|---|---|
| DECLARED | Fresh publication; current assignment or execution evidence absent/unwitnessed | Accepted mission, observed work, authenticated process |
| OBSERVED | Host witnessed recent KNOWN native execution evidence on exact pinned context | Process still alive, completed mission, permission or exclusive ownership |
| STALE | Declaration or last witnessed execution evidence exceeded15s | Agent died/offline, mission revoked, resource released |
| NO_DATA | Missing/ambiguous/invalid/conflicting binding or proof, with explicit cause | A failed physical device or a denied human decision |

metadata_kind=DECLARED_PUBLICATION distinguishes public label/branch metadata from the
independently observed execution. liveness always remains NO_DATA(process_liveness_not_proven).
has_recent_execution_evidence is true only for OBSERVED; it is never named active=true.
Native failed KNOWN execution may still be observed; only completed PASS plus independent
capability witness qualifies a capability. OBSERVED of a synthetic receipt remains
explicitly synthetic. A hash, same OS user, model name or voice echo is not authentication.

Source declared_at and native receipt observed_at drive expiry; query projected_at and
new heartbeat never refresh old evidence. TTL15s follows the source presence contract,
not a mutation of LAB's120s resource policy. Mesa capture has its separate120s ceiling.
Future timestamps reject. Missing records yield NO_DATA, retained old records STALE;
no deletion, probing or resurrection occurs. This is a selected bounded capture, not
an atomic fleet snapshot or current process-health guarantee.

A fresh peer publication claiming the same opaque worktree causes advisory NO_DATA /
WORKTREE_CLAIM_CONFLICT. It neither decides who owns the tree nor changes a claim/lock.
The host/Mesa resolves conflict. Stale peer metadata cannot hold a writer lease forever;
this projection has no leases in the first place. Exclusive writer ownership stays unknown.

## Privacy and human review

Host allow_publication approves the exact metadata capture, identifiers and omissions
BEFORE any selected publication is released. Context/outputs/prompts are not fields.
Source can omit label/repository/branch/HEAD/mission/scope/capabilities/review explicitly;
omitted values are null/empty and never silently replaced by another source. Opaque
references may still be correlatable: the owner decides whether publishing them is safe.
Unknown fields/unsafe labels/oversized/malformed payloads fail closed, not free-text redaction.

human_review comes from the independently witnessed current Mesa capture. WAITING means
that source reports review pending for its scope; false means NO_PENDING_REVIEW_REPORTED_NOT_APPROVAL.
Neither is a signature or permission. Omitting review yields NO_DATA. Existing Mesa/source
refs resolve exact file scope; no parallel list of missions or signature book is stored.

Limits:32 bounded declarations,8 capabilities,256KiB encoded input,16KiB snapshot,
<1024B receipt. All callbacks are bounded read-only host injections, never model-authored
JSON. Returned structures contain no journal bodies, private exception text, prompts,
raw tool output, endpoints, absolute paths or credentials. SHA is integrity only.

## Required tests and evidence

1. Two agents claiming one worktree -> NO_DATA conflict; authority none.
2. Disappearance -> STALE after expiry or NO_DATA if capture absent, not invented death.
3. Restart/new instance -> no old activation reuse; evidence selection mismatch rejects.
4. Same names -> distinct session/instance identity; no label-based join.
5. New mission owner/claim generation -> NO_DATA, no implicit reassignment.
6. Receipt at other HEAD/clone/generation -> NO_DATA; relabelled wrapper refused by host.
7. Private omissions -> no private value transported; unknown raw context fields rejected.
8. Old evidence/new heartbeat -> STALE, old observed_at preserved, no active claim.

Extras: DECLARED vs OBSERVED, UNKNOWN, absent/false host witnesses, exact capability
scope and evidence_basis, future/bad time privacy, duplicate/size limits, deterministic
capture, I/O tripwires, no review-as-approval and receipt schema/authority tampering.
Fixtures use existing Session and TEST DOUBLE witnesses, not real cross-CLI processes.

Run twice:
- python3 -B -m unittest tests.test_agent_presence -v
- python3 -B -m unittest discover -s tests -p 'test_*.py'
- python3 -B test_llms.py
- python3 -B bin/verify_llms_tree.py

Measured locally 14 NOV 2026, Python 3.14.4:19 directed tests PASS twice;990 discovery
tests OK twice (989 PASS+1 inherited skip, test_eval_harness.test_red_suite_verdict_red,
no RED suite available in this tree). test_llms2 PASS twice;tree5 paths within
11996/12109 B twice. Ten guard mutations detected twice by assertions, no runner
errors; overlapping guards are not ten independently exploitable bypasses. Required
eight scenario methods run twice with15 compact step receipts byte-identical.
C2C-R1 inventory/receipt hashes checked unchanged; no inventory collection repeated.

External SCRUB receipt records exact HEAD, commands/results, eight scenario receipts,
mutation sensitivity and C2C inventory preservation hashes; no source publications
or private activity are copied. #210 checks were re-read, not rerun or rewritten.

## Integration proposal and remaining NO_DATA

1. Review/sign #210 separately; this PR starts at current main and does not import it.
2. Review the independent presence schema, omission policy and host-source binding.
3. A separately reviewed read-only host adapter can join existing Mesa/Git/journal
   captures with exact generation/instance pins, revocation and actual source stability.
   No new store or daemon; source books/journal remain authoritative.
4. Junie/Hexelion review input lineage and adversaries; Claude consumes only after ACK
   for one semantic view across visual/voice/accessibility/machine. No UI built here.

NO_DATA(cross_cli_live_presence_E2E),NO_DATA(authenticated_agent_source_binding),
NO_DATA(real_Mesa_Git_journal_capture_adapter),NO_DATA(atomic_multi_source_snapshot),
NO_DATA(process_liveness),NO_DATA(exclusive_writer_ownership). No new keys, remote
access, permissions, daemons, models, inference, APP/WEB edits, merge or deploy.
