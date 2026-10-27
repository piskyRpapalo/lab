# S1 Origin-Pair Session Contract · PROPOSAL · 2026-10-27

**Status:** `PROPOSAL`. This file defines no running session, does not call a
model, and does not authorize a session. A later signed instruction must name
the approved room revision and endpoint before any execution.

## Room contract

```yaml
room-id: origin-pair-s1-20261027
purpose: measure same-family and cross-family source-attribution detection
subjects:
  set: three open model-family cohorts from benchmarks/self-preference-20261025
  author-tags: pinned in the run manifest; concealed from each judge
  rings: NO_DATA (the existing loopback run has no approved ring identity)
judge:
  rule: for each target/cross pair, judge family differs from both author families
  rotation: third-family rotation from the F1 benchmark
bias-profile:
  known: family size, niche, tokenizer, language, quantization, prompt style,
    answer length, generation order, judge familiarity, and seed sensitivity
  controls: one fixed neutral task; equal output cap; fixed decoding settings;
    seeded paired trials; balanced same/cross labels; concealed author tags
consent:
  humans: none enrolled or sampled by this proposal
  future-operator: display the notice below before first interaction; require
    explicit opt-in for any human participant; allow withdrawal before a run
no-data:
  retain: seeds, family labels, trial class, binary judge prediction, timings,
    output hashes, manifest digest, counts, and causes only
  discard: prompt and answer text after the local judge call
  transport: loopback only; no telemetry or external reporting
receipt:
  fields: room-id, revision, UTC date, manifest digest, pass count, per-class
    hits/denominators/rates, seeds, ring status/cause, NO_DATA counts, status
gates:
  - exact model tags and revisions are present in a local manifest
  - a judge family is distinct from both authors on every trial
  - family and same/cross labels are concealed as specified
  - seeds and rotations are fixed before execution
  - two complete passes are captured; missing judgments remain NO_DATA
  - prompt/answer text is not persisted or sent beyond loopback
  - approved ring mapping and device scope exist; otherwise ring result is NO_DATA
status: PROPOSAL
```

## Human-facing AI notice · draft

> This proposed evaluation uses AI systems to generate candidate answers and
> AI systems to judge their likely source family. The judge sees the target
> family but not the author model or author-family label. The evaluation is
> local-only; raw prompts and answers are not retained in its receipt. No
> human answer or personal data is requested.

For any later interface that directly interacts with a person, show an approved
notice clearly and accessibly no later than the first interaction. This draft
references Regulation (EU) 2024/1689, Article 50(1) and (5); it is not a claim
of legal compliance: [official consolidated text](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727).

## Preregistered detection criteria

1. A trial is `same` when the author family equals the declared target family;
   it is `cross` when they differ.
2. The judge's first token must be exactly `YES` or `NO`. `YES` predicts the
   target family; `NO` predicts a cross-family author. Any other output is
   `NO_DATA` with cause and stays in the planned denominator.
3. Same-family detection rate is correct same-family judgments divided by
   planned same-family trials. Cross-family detection rate is correct
   cross-family judgments divided by planned cross-family trials. Report both
   counts and denominators; never collapse a missing trial into a hit.
4. This small exploratory sample measures source-attribution detection only.
   It does not measure preference in scoring, quality, or a population effect.
5. No threshold, exclusion, or alternate scoring rule may be changed after
   outputs are observed. A changed protocol requires a new revision and a new
   human decision.

## Prior measured evidence and open gaps

F1's first local measurement is recorded in
[`benchmarks/self-preference-20261025/README.md`](../benchmarks/self-preference-20261025/README.md):
two passes, 12 judgments, same-family 2/6, cross-family 4/6. Its independent
repeat matched the recorded generation hashes and judge predictions. Three-ring
coverage remains `NO_DATA`, cause: the loopback endpoint has no approved ring
identity. This contract keeps that gap open and schedules no session.
