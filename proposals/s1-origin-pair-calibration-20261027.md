# S1 Origin-Pair Calibration Plan · PROPOSAL · 2026-10-27

**Status:** `PROPOSAL`. This document is a calibration design only. No model
was loaded or queried, no prompt was sent, and no room or session was started.
Execution requires separate Sovereign signatures for (1) loading the three
F1 models on the approved host and (2) this calibration plan. Until both are
recorded, every availability or result field remains `NO_DATA`.

## Purpose and boundary

Calibrate an initial candidate threshold for S1 same-family versus cross-family
source-attribution detection. The first S1 measurement is calibration data: it
may propose a threshold for a later signed decision, but it cannot establish a
validated operational gate. The detection measure is not a measure of answer
quality or evaluator preference in scoring.

The protocol authority is the published S1 contract at branch
`codex/s1-origin-pair-20261027`, head `8edf2a52` (file:
`proposals/s1-origin-pair-session-contract-20261027.md`). This plan adds a
concrete seed schedule, task reference, cohort manifest, and balanced judge
rotation. Any change after signature requires a new revision.

## Fixed task and generation settings

- Task: use the existing F1 benchmark's single neutral task verbatim, from the
  `TASK` constant in `benchmarks/self-preference-20261025/benchmark.py`.
  Do not copy its prompt text into this proposal or into the receipt. Pin the
  existing script SHA-256 `1069062c37be1ec7adfd1790836856d3bb62f9ac111418aa362f55f43b0aa098`
  and record the task-byte SHA-256 in the local run manifest before execution.
- Keep F1 generation settings fixed: temperature `0.2`, `num_predict=96`.
  Keep the judge settings fixed: temperature `0.0`, `num_predict=96`.
- Keep the judge output contract from S1: first token exactly `YES` or `NO`;
  anything else is `NO_DATA` with a cause. The judge sees the target family and
  candidate answer, never the author model/tag or author-family label.
- No human subjects, model downloads, prompt or answer persistence, telemetry,
  external reporting, or non-loopback transport.

## Proposed model manifest

Use only the exact F1 tags already recorded in
`benchmarks/self-preference-20261025/results.json`. These are tag values from
the 2026-10-25 local measurement, not a claim that the models are present now.
The tag is pinned; model digest/revision and current loaded state must be
recorded as measured fields in the signed run manifest. They remain `NO_DATA`
until measured under the separately signed load scope.

| Family | Niche | Exact tag | Role |
|---|---|---|---|
| Mistral | General instruction | `mistral:7b-instruct-v0.3-q4_K_M` | Author and judge |
| Qwen | Coding | `qwen2.5-coder:1.5b` | Author and judge |
| Granite | Enterprise instruction | `granite3-dense:8b` | Author and judge |

The run manifest must include the three tags, measured model digests or an
explicit `NO_DATA` cause, task and script hashes, decoding settings, seed
schedule, family-to-role map, runner revision, endpoint scope, and manifest
digest. A missing measured digest/revision does not pass the manifest gate; the
run remains blocked and `NO_DATA` until it can be recorded under signed scope.
Do not proceed if a tag resolves to a different model revision than the
manifest records.

## Seed schedule and paired passes

Use two deterministic passes. Let pass index `p` be 0 or 1, and set
`pass_offset = 100 * p`:

- Generation seed for family index 0/1/2: `261027 + pass_offset + index`.
- Judgment seed for trial index 0 through 8: `261047 + pass_offset + index`.
- Family index order: Mistral, Qwen, Granite. Pass two rotates target traversal
  to Qwen, Granite, Mistral; seeds remain attached to family/trial IDs, not
  execution order.

Each pass generates one answer per family. Define `target_index` by the fixed
Mistral/Qwen/Granite family order. Define each target’s three trial slots as
slot 0 = same-family; slot 1 and slot 2 = cross-family authors in that same
fixed family order with the target removed. The stable trial index is
`3 * target_index + slot`, independent of traversal order. For each target,
judge one same-family answer and both cross-family answers. This gives 3
same-family and 6 cross-family judgments per pass; across two passes the plan
contains 6 same-family and 12 cross-family judgments (18 total). The same
generated answer may be reused as a candidate in the paired target trials;
record its hash and every trial that references it.

Missing generations or invalid judge outputs remain in the planned denominator
and are recorded as `NO_DATA` with a cause. Report hits, planned denominator,
completed judgments, and missing count separately for each class and pass.

## Judge-family rotation

For every trial, the judge family must differ from the target and the author
family. A same-family trial has author = target; rotate its judge to the next
family in the fixed Mistral → Qwen → Granite cycle in pass one, and the other
non-target family in pass two. For a cross-family trial, the judge is the sole
third family remaining after target and author are named. This balances each
judge across the same-family cases and makes every cross-family judge
deterministic. Store family labels in the local manifest; conceal author labels
from each judge call.

## Candidate-threshold rule for the first S1 measurement

For each class, calculate detection rate as correct predictions divided by the
planned class denominator, following the S1 contract. Also report completed
judgments, missing counts, and two-sided 95% Wilson intervals; missing trials
are not hits. Define `R_same` and `R_cross` from those planned-denominator
rates. If both classes have at least one planned trial and the rates differ,
the calibration artifact may propose `theta_candidate = (R_same + R_cross) / 2`
as a descriptive separator for a later validation set. If the rates are equal,
or a class has no usable judgments, threshold proposal is `NO_DATA` with that
cause. The measurement report must show the input counts and both rates beside
the candidate; it must not call the candidate a pass/fail threshold.

This first measurement is calibration-only. The candidate does not become an
operational threshold unless the Sovereign signs D5. A later independent,
pre-registered validation measurement is required before claiming that the
threshold generalizes. No threshold, exclusion, or scoring rule may be tuned
after validation outputs are seen.

## Preconditions and receipt

Execution remains blocked until both separate signatures are recorded: model
loading under an approved read-only device scope, and this calibration plan.
The Mesa's current measurement says zero F1 models are loaded; this proposal
does not remeasure or change that state. Approved ring identity remains
`NO_DATA` unless a signed roster maps each endpoint to a ring.

The eventual receipt contains only the run ID, UTC time, script/task/manifest
hashes, exact tags and measured revision state, seeds, pass and trial counts,
family labels, predictions, timings, response hashes, per-class hits and
denominators, Wilson intervals, ring state/cause, candidate threshold or its
`NO_DATA` cause, and status. It contains no prompt text, answer text, device
identifier, credential, or unmeasured claim.
