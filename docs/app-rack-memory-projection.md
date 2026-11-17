# APP-RACK-MEMORY-01 · LAB contract for the rack-private Notebook

**Status:** read-only LOCAL fixture/proposal; not deployed, not a node installer,
not human approval, and not proof of remote execution. Do not expose this
contract to the personal Companion app. There is **one** underlying journal:
the existing LAB `ExecutionJournal` (owner-private SQLite), not a new store.

## Exact source-to-consumer seam

The private-rack APP server, **after verifying rack-private authority on the
server**, may arrange a host-controlled invocation of the LAB producer:

```python
from meta_harness.readonly_mirror import ReadOnlyMirror
from meta_harness.app_memory_projection import project, verify

# All source selection, journal path, task and witness are host-owned.
# NEVER use a path, identity or authorization callback from a browser request.
mirror = ReadOnlyMirror(
    {"rack_task": {"journal": host_owned_existing_journal_path,
                   "task": host_pinned_exact_task}},
    local_source_witness=trusted_local_source_check,
)
now = host_current_utc_iso8601()
packet = project(mirror, "rack_task", observed_at=now)
if verify(packet, mirror, "rack_task", observed_at=now):
    send_only_packet_json_to_rack_notebook(packet)
else:
    send_no_data("host_recheck_failed")
```

This is **not** an executable APP route or service. APP owns the route, the
private-rack guard, the choice of the exact allowlisted source and the
optional Notebook section. Do not make any HTTP route or global environment
variable from a model-supplied file path. Do not send SQLite files, source
text, chat turns, prompts, credentials or unredacted journal receipts.

The adapter is pure read-only and creates no background worker, network
connection, journal, table, grant or retry. Its only journal access is through
existing `ReadOnlyMirror` and an additive `read_known` that uses the same
allowlist and private SQLite read-only connection. No file is published by the
producer. APP may invoke it locally on demand; a static snapshot MUST NOT be
represented as live evidence (TTL zero).

## Schema

`preceptoros.lab.rack-memory-observation/1` is one UTF-8 JSON object,
**fewer than 1,024 bytes**, with a fixed field set:

- `execution_state`: `KNOWN` / `UNKNOWN` / `NO_DATA`;
- `budget_state`: `SETTLED` / `RETAINED` / `NO_DATA`;
- `retry_policy`: `REPLAY_ONLY` for KNOWN, `NO_RETRY` otherwise;
- `acknowledgement`: `HITL_REQUIRED`, `AUTHORITY_NOT_VERIFIED`,
  `HUMAN_ACKNOWLEDGED`, `NOT_APPLICABLE` or `NO_DATA`.
  Any HUMAN_ACKNOWLEDGED status must be source-witnessed; no right to execute.
- `task_ref`, `source_ref`, `evidence_ref`, `receipt_ref`, `state_ref`:
  64-character SHA-256 references (nullable where unavailable). These
  are correlation/integrity aids, **NOT signatures or independent testimony**.
  `source_ref` is a digest of journal identity and task reference, never
  the raw journal ID or a filesystem path. A KNOWN receipt is re-read with
  the exact task reference and local budget status.
- `observed_at`, `expires_at`, `ttl_seconds=0`: same host-supplied
  observation timestamp. No future observation or cache can gain freshness
  from old `state_ref`; re-read for each consumer request.
- `cause`, `summary`, `provenance`, `authority=NOT_AUTHORIZED`,
  `independent_witness=NO_DATA`: bounded, safe, fixed vocabulary.
  `summary` is the **one source** for both visible and spoken text.

**Critical:** KNOWN means that the local journal holds a structurally
verified completed receipt for that task. It does not attest the correctness
of a model output or an effect on another physical host. When
`ReadOnlyMirror` reports `NO_DATA(claim_not_uncertain)`, the producer does
NOT convert it to KNOWN by inference: `read_known` must independently
reopen and validate the exact receipt and retained/settled budget. A missing
or inconsistent claim becomes `NO_DATA(known_receipt_not_verified)`.

A source not allowlisted, unsafe permissions, symlink, WAL sidecar, missing
local source witness, broken JSON, stale time or changed source fails
closed. An uncertain result remains `UNKNOWN`, with
`RETAINED` **only when the original reservation is actually present**.
The same state reference drives machine JSON, readable Notebook text and
Acho speech/ARIA. UI must never turn `UNKNOWN` into `VERIFIED`.

## Reproducible synthetic examples for APP integration

- `tests/fixtures/app_rack_memory_known.json`
- `tests/fixtures/app_rack_memory_unknown.json`

Both are minified, source-pinned **synthetic test examples**, not evidence
of any user's memory, live node, actual human signature or remote action.
They are generated from the real LAB journal API on a disposable SQLite
fixture and must match regenerated output exactly.

Notebook ingestion should be an **optional private section** on its
existing `/api/notebook` response. This document does not modify the
Notebook schema or endorse leaking these fields in the personal APP.
If LAB cannot be read/reverified, expose `NO_DATA(lab_source_unavailable)`
under the APP's own authenticated private-only gate, not a success badge.

**NO_DATA:** real remote journal identity, independent source/fencing witness,
remote effect, multi-node replicated memory, APP click/Android distribution,
live deploy, S1 remote grant, and production restart recovery.
