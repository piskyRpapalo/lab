# Contribute a reproducible local AI benchmark · 2026-11-12

**Status:** contributor guide. This document explains the contribution process; it does not certify any model, reproduce an unpublished fixture, or supersede [LAB's agent contract](../AGENTS.md).

LAB accepts bounded, measurable contributions from people running open models on their own hardware. Start with the [benchmark index](../benchmarks/README.md), the existing [harness receipts](../benchmarks/harness-receipts/README.md), and the repository's `AGENTS.md`. Use the receipt schema matching the measurement: [`preceptoros.lab.harness-receipt/1`](../benchmarks/harness-receipts/README.md) is used for harness **test** receipts; [BENCH-REPRO-01 public throughput](../benchmarks/receipts/20261112-public-throughput-qwen3.json) uses `bench-repro-01-v1` inside each `executions[].receipt`. Do not cast one into the other or invent a competing schema.

## Before running

1. **Define one claim.** State whether you measure generation throughput, latency, field extraction, instruction following, accessibility, or adversarial behavior. A speed score is not a quality or compliance score.
2. **Find an existing benchmark.** Link the closest card, harness, and tests. If none fits, write `NO_DATA: matching harness not identified` and explain the gap.
3. **Declare the apparatus.** Record UTC date, OS, CPU/GPU class, memory class, engine/version, model name and immutable digest (when available), quantization, context, decoding settings, and offline/online boundary. For every unavailable field, use `NO_DATA` with a cause.
4. **Declare the reference.** Record dataset origin, case and field denominators, synthetic versus real inputs, who produced labels, whether they were independently checked, and exclusion criteria. Do not imply that author-generated labels are independent ground truth.
5. **Respect privacy.** Prefer public synthetic fixtures. For sensitive or privately held inputs, publish aggregate metrics, source hashes, and methodology only; do not commit raw images, prompts, model answers, personal identifiers, machine paths, credentials, or private infrastructure details. A digest identifies bytes; it is not a human signature.

## Run and report

6. Record exact commands and at least two runs when feasible. Include errors, timeouts, malformed outputs, and negative tests rather than silently dropping failures. Declare which hardware, software, fixture, and parameter variables remained fixed between runs.
7. Preserve provenance separately: fixture SHA-256, measured artifact SHA-256, source repository commit, PR head SHA, test results, and human sign-off are different things. Use the existing receipt format where applicable; explain incompatibilities rather than forcing unlike experiments into one metric.
8. Open one narrow **draft PR** titled `REQUIERE_FIRMA` according to `AGENTS.md`. Run the relevant tests twice and include negative/sabotage checks where appropriate. Report baseline failures separately from changes introduced by your patch. CI passing does not authorize a merge; the Soberano signs the exact PR head.

## Minimum reviewer checklist

- [ ] Claim, unit, numerator and denominator are explicit.
- [ ] Existing benchmark and receipt conventions are reused or incompatibility is explained.
- [ ] Dataset origin and independence of labels are declared.
- [ ] Hardware, engine, model version, settings, dates and offline boundary are documented.
- [ ] Private inputs and identifiers are excluded from public artifacts.
- [ ] Repetitions, failures, exclusions and negative checks are reported.
- [ ] Artifact digest, source commit, PR head and human signature are distinguished.
- [ ] Results are limited to the measured scope; no implied fairness, safety or legal certification.
- [ ] OS-specific baseline failures are distinguished from patch regressions.
- [ ] External reproduction is possible without private infrastructure, **or** marked `NO_DATA` with a cause.

## Example of a bounded claim

For a **hypothetical, not measured by this guide** receipt-reading experiment, a contributor could report **139/142 fields matched**, **23/26 receipts fully matched**, and **approximately 6.5 minutes per receipt at p50**, only if each number is supported by an available source receipt and labeled *contributor-reported*. Such numbers do **not** establish independent ground truth, broad representativeness, or general model accuracy. If its source commit has not been published, record `NO_DATA: awaiting contributor source commit`.

## Reproducing an existing result

The [2026-11-11 Beelink Ollama card](../benchmarks/ollama-beelink-20261111/README.md) reports six local models and twelve generation-throughput samples. Its original input bytes were not published. **Do not call a new run byte-identical reproduction of those samples.** A new public synthetic fixture with a documented SHA-256 constitutes a *new experiment*, even if settings and models resemble the historical run.

**Scope:** documentation only. No inference was run to create this guide, and no new measurements are claimed.
