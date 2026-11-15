# MULTIAGENT source capture · bounded host adapter P1

Technical contract under existing Mesa #39/#3, not a new mission registry.
CLAIM #39 comment6886629624. Base cf32af82d3a0726b3110d38118146f6241644dcf.
Depth2. Scope:meta_harness/agent_presence_sources.py,
tests/test_agent_presence_sources.py,this file. Sovereign resumed work after P0 closure.

## What changes

PresenceSources composes three host-configured, read-only capabilities:
CLI declarations, original execution Observation, current Mesa Claim. It calls the
existing agent_presence.project; it does not replace the native schema or sources.
The query cannot choose a path, endpoint, session or authority callback. Selection is
fixed by host configuration. No connector, publisher, daemon, registry, worker,
grant/lease, permission manager or journal schema is introduced.

A Source has opaque ref, bounded read(), and live attest(data,selection). Ref/reader
identity must be distinct. independent(sources,selection) must independently witness
actual source provenance AND stable capture/fence semantics, not just distinct IDs,
distinct functions, matching field values, file hashes or common OS ownership.
A model cannot supply these callbacks through JSON. A poorly configured always-true
host witness is NOT made authentic by this adapter. All witnesses are host-owned.

Capture detaches data immediately, bounds it, verifies each source, projects, rereads,
rechecks independence/revocation, projects at fresh host time, and performs a final
read/projection under a15s overall deadline. No retry loop. Snapshot source timestamps
remain original. A slow final provider cannot preserve earlier freshness; host clock
rollback/future data rejects. The deadline is checked after callbacks return; the
adapter cannot preempt an unbounded callback. Providers must enforce I/O bounds/timeouts.

Different source content/revision produces NO_DATA/SOURCE_CHANGED_DURING_CAPTURE;
missing/invalid source or false witness produces NO_DATA with a compact cause. The
first capture cannot be overwritten through a provider returning shared mutable objects.
Journal Observation.source_ref and Claim.source_ref must match their configured provider.
Callback exceptions do not export private error text or source bodies.

Capture record agent-presence-capture/1 (<1024B) links the P0 snapshot without source
payloads. state=CAPTURED means consistent host-attested reads ONLY, not live presence;
projection_state separately preserves P0 DECLARED/OBSERVED/STALE/NO_DATA. For an unstable
capture snapshot=None. authority=none and ownerReply=false always. A CAPTURED snapshot
may itself be NO_DATA (e.g. conflicting CLAIM owner), and consumers must inspect it.
Matching declaration+receipt+CLAIM never grants authority over another agent.

## Original lineage, not retrospective labelling

The journal source must supply the ORIGINAL session/instance/HEAD/CLAIM/task binding.
The native Session receipt does not contain those facts. A valid receipt hash or
journal.attests proves native storage/integrity, not an original Git/context binding.
Do not fill missing binding from the latest CLI declaration or today's HEAD. Refuse
attestation if the independent original context map is absent or not source-witnessed.

Current implementation has pluggable host readers, NOT installed real CLI/Mesa readers
or an authenticated original-context mapper. This is an executable capture boundary,
not closure of real cross-CLI E2E. Three agreeing fixture providers are not three
independently authenticated agents. Native read-only journal I/O is tested in private
temporary SQLite fixtures, with explicit synthetic original context; no live source used.

ReadOnlyMirror/ReadOnlyJournal, P2 source_capture/HostWitness remain the existing source
boundary. FixtureSourceCapture returns SIMULATED, never a genuine host stability proof;
it cannot be promoted by this adapter. Real WAL/SHM/sidecar races, noncooperating writers,
change-and-restore and multi-source atomicity require independently witnessed host
stability. Double/triple reads do not prove absence of ABA or an atomic global snapshot.
Providers must retain existing owner/link/sidecar restrictions and read-only contracts.
No live SQLite reader, CLI filesystem scanner or GitHub polling service is added here.

## Tests

Synthetic tests: three matching independent host capabilities; same source/reader
rejected; absent independence prevents reads; source mutation between reads; aliased
mutable input; wrong source ref; witness/independence revocation; CLAIM owner or HEAD
conflict; deadline/clock rollback; stale evidence; private omissions/errors. Existing
P0 continues to validate exact session/generation/HEAD/task/CLAIM and capability scope.

One fixture uses ExecutionJournal/Session to prepare a private synthetic receipt, then
ReadOnlyJournal.lookup/attests to read it. Journal bytes and directory entries stay
unchanged. Removing original-binding attestation refuses the same native bytes. This
proves real local read-only I/O against synthetic data, not real agent identity.

Run twice:
- python3 -B -m unittest tests.test_agent_presence_sources tests.test_agent_presence -v
- python3 -B -m unittest discover -s tests -p 'test_*.py'
- python3 -B test_llms.py
- python3 -B bin/verify_llms_tree.py

Measured locally Python3.14.4 / 15 NOV 2026:30 directed PASS twice (11 source +19
P0);1015 discovery OK twice (1014 PASS+1 inherited skip:no RED suite available).
test_llms2 PASS twice;tree5 paths11996/12109 B twice;10 guard mutations detected
twice through assertions,no runner errors. Overlapping guards are sensitivity checks,
not ten independent exploit claims. Native SQLite fixture bytes/directories unchanged.

Receipts/guard mutation checks and exact HEAD are in the external SCRUB packet.
Keep P0 and C2C inventory archives immutable; no metadata status change grants rights.

## Next integration and limits

Host must choose already-authorized independent source readers and prove original
execution context from existing evidence. If existing journals/CLI captures lack that
binding, report NO_DATA; do not invent it or retroactively write a map. Only after an
owner-reviewed source contract may a separately scoped adapter expose authorized
passive observations. Junie/Hexelion review provenance; Claude remains APP/WEB owner.
No MCP tool or renderer is wired by this increment. Consumer ACK remains required.

NO_DATA(cross_cli_live_presence_E2E),NO_DATA(authenticated_agent_source_binding),
NO_DATA(exclusive_writer_ownership),NO_DATA(real_host_stability),
NO_DATA(atomic_multi_source_snapshot). No liveness, exclusive lock, human signature,
remote access, model download/inference, runtime install, device action, merge or deploy.
