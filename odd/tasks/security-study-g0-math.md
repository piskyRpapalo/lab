# G0 security-study statistical lens — SYNTHETIC / NOT PREREGISTERED

Authority: Soberano approves preparation of the base study before 16:00 Lisbon
on 2026-11-22. TRAIN-02 has absolute priority on all GPUs, hosts, CLI sessions,
worktrees and grants. This DRAFT HITL work is pure standard-library math.

## Reuse-first

- Existing lens: `meta_harness/multi_turn_first_failure.py` (first event,
  two BOUNDARY_ON/OFF arms, exact KM, no human gold, no causal host attestation).
- Existing frozen checker: `meta_harness/long_horizon_gate.py`.
- Existing 5/12-turn receipt:
  `benchmarks/ai-security-20261028/multi-turn-first-failure-20261115.md`.
- Existing tests: `test_multi_turn_first_failure.py`,
  `test_dfa_b5_family_blind_gate.py`, `test_dual_judge_evidence.py`,
  `test_p2_effect_sink_fixture.py`.
- This adds **a lens, not another runner or enforcement authority**.

## Maths (preserve the denominators)

For cause k at turn t, at-risk count Y(t), first events d_k(t):

  F_k(t) = SUM_{u<=t} S(u-) * d_k(u)/Y(u)

This is the discrete Aalen-Johansen cause-specific cumulative incidence
function (CIF). Competing states are COMPROMISED, OVER_REFUSED, DEGRADED
and INFRA_BLOCKED; right-censoring is distinct and is not task success.
The manuscript's precise rules for infrastructure attribution and competing
outcomes still require confirmation in the frozen preregistration.

Using 100 invented trajectories: 10 COMPROMISED and 20 DEGRADED at turn 1;
14 COMPROMISED of the remaining 70 at turn 2; the remaining 56 censored.
CIF(COMPROMISED,2) = 0.24. If competing failures are incorrectly censored,
1-KM = 0.28. Bias = +0.04 (four percentage points). ALL SYNTHETIC.

Cohen kappa: (p_observed - p_expected)/(1 - p_expected).
Historical dual-judge pilot marginal counts: Phi4 SAFE/UNCERTAIN 238/62,
Mistral SAFE/UNCERTAIN 51/249, agreement 113/300; the inferred 2x2
matrix [[51,187],[0,62]] yields kappa ~0.101307. This is DERIVED,
not a new judge run or evidence of semantic security accuracy. 276/300
candidate outputs were truncated.

## Non-negotiable boundaries

- No TRAIN-02 interference; no model inference, no GPU, no external attack.
- These functions do NOT validate gold, verify a host witness, attest a
  prohibited effect, estimate robust variance or fit a causal model.
- Do not equate CENSORED with successful legitimate task completion.
- Keep benign and mixed-adversarial cohorts separate by definition.
- All primary metrics, horizon, n, first-event rules, human-blind gold,
  seven negative controls and freeze authority belong to a future
  owner-approved preregistration; no claim of a sealed design here.
- Two identical SentinelX UID-technical CPU-only G0 smoke runs completed:
  11/11 PASS each, same SHA256
  `08cca05f404f627a76be8ff6dac20336b5eab89a67025e0ca043f9024bf9c0c2`.
  That earlier one-file smoke script is not identical to the modular code
  of this PR; the latter requires its own checks and independent review.
- Junie direct launch through native MCP was REJECTED(non_reviewable_executable).
  `~/.junie` existing does NOT establish authenticated CLI control.
  OpenCode and Pi process counts are not CLI task acknowledgment.

## Sources

- LAB historical:
  `benchmarks/ai-security-20261028/dual-judge-pilot-20261111.md`
- Aalen-Johansen / competing risks overview:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2410013/
- Qi et al. 2024: https://arxiv.org/abs/2406.05946
- CaMeL: https://arxiv.org/abs/2503.18813
- AgentDojo: https://arxiv.org/abs/2406.13352
- ForteShield published abstract:
  https://forteshield.ai/resources/safety-alignment-shallow-in-tokens-and-sparse-in-horizon

## Acceptance for G0 only

Run `python3 -m unittest tests.test_competing_risk_lens` twice on the exact
branch and obtain independent review. Preserve all RED/NO_DATA in the receipt.
At G0 proposal time this branch was DRAFT. G0/G1/G2 have since been merged
through separate reviews; this historical instruction is superseded by each
new PR's exact-head HITL gate. The Soberano retains go/no-go, exact-head
signature and TRAIN-02 authority.


## G1: statically paired A/B/C experiment-design preflight (not execution)

New function in the same G0 statistics module, not another runner:
preflight_three_arm_design. It checks three arms A=main without sensor,
B=unaltered sensor under closed output, and C=adapted sensor under
the exact same schema. It rejects:
- missing/duplicate arms, case/repeat mismatch or paired seed drift;
- changed main-model digest, main inference protocol, generation budget,
  host or feedback-projection table across a cohort;
- mismatched gold digests across the same paired case;
- sensor-base/schema/protocol differences between B and C;
- A accidentally containing a sensor, missing B/C sensor hashes,
  or byte-identical sensor weights (no actual treatment contrast).

Each row declares SHA-shaped identifiers; the validator cannot establish
that a hash belongs to a real model, that a human gold is blind, that an
adapter was trained, that permissions exist or that the host witness works.
A structurally valid cohort returns NO_DATA with structure_valid=true,
not GO/VERIFIED. Different hardware require separately pinned comparisons.

The first G1 run is pure Python/unit-only on invented hashes; no model,
GPU, CLI session, training, SSH or hardware effects are required.
TRAIN-02 retains priority. A scientific cohort needs a separately signed
preregistration before its first model token.


## G2: paired case-cluster resampling, descriptive only (2026-11-22)

This is an additional **pure method** in the existing
\`meta_harness/competing_risk_lens.py\`, not an agent, an experiment runner,
a judge, or a new security framework. Reuses G0 Aalen-Johansen CIF and the
G1 static A/B/C comparison contract.

**Problem:** the same case is observed in arms A/B/C and may be repeated.
Resampling 3 arms and repeated runs as independent records breaks the
pairing and understates or misstates uncertainty. G2 therefore resamples
**the whole case**: all arms and all repeated trajectories remain together.
The resampling seed, number of draws and grouping rules are explicit.

**Required input:** one declared stratum; unique lowercase 64-character
case digests; identical repeat sets per case; each repeat has A+B+C;
all horizons 5 or 12 and identical throughout; terminal labels from the
closed vocabulary. Early censoring is rejected because the small input
schema does not record its cause. Invalid or unpaired records fail before
resampling. Source SHA, model/protocol, physical witness and consent are
*not authenticated by this lens*. For a real comparison, all G1 pins and
the independent witness remain separately mandatory.

G2 computes the **observed descriptive CIF difference** of one
preregistered cause and selected arm contrast, and returns the 2.5% and
97.5% **quantiles of the resampling distribution** (linear interpolation
between ordered fractions, exactly reproducible from the declared seed).
Those quantiles are **NOT validated confidence interval endpoints**:
there is no coverage calibration, robust Lin-Wei variance estimate, power
analysis, independent GOLD, or host effect. The module preserves
\`NO_DATA(no_preregistered_calibration_or_independent_gold)\`.

Illustrative cohort: four invented case clusters with two repeated
trajectories per A/B/C. A and B are identical within every case, so
paired B−A difference and both resampled quantiles must be zero. C
differs on two of the four cases; point C−A difference = −1/2. These
numbers are SYNTHETIC mechanism checks, not empirical study results.

**Instrument negative control:** an in-memory mutation intentionally
reassigned only the treatment arm to a different case during the
resampling. The paired-A/B regression test detected the sabotage:
RED ×2 (failure with nonzero quantile). Normal exact branch source:
46/46 PASS ×2 under Beelink SentinelX technical identity, offline
stdlib Python; GPU=0, model_calls=0, no TRAIN-02 changes.

**Primary literature / avoid novelty claims:**
- Cameron and Miller, *A Practitioner's Guide to Cluster-Robust
  Inference* (2015): resample entire clusters, not individual
  observations. https://escholarship.org/uc/item/1jq5d0pq
- *Competing risks analysis of correlated failure time data*
  (2007): methods for correlated observations and cumulative incidence;
  this G2 code is **not** a reproduction of its full estimator.
  https://pubmed.ncbi.nlm.nih.gov/17680835/
- BMJ, *Bias by censoring for competing events in survival analysis*
  (2022): 1-KM versus Aalen-Johansen distinction.
  https://www.bmj.com/content/378/bmj-2022-071349.long

**Boundary:** never publish G2 resampling percentiles as inferential 95%
confidence intervals without prespecification, sufficient independent
case clusters, simulation-based coverage checks and review by a
statistician. Later protocol changes require a new frozen cohort.


## G3: declared G1 plan ↔ G2 terminal rows (2026-11-22)

**Scope:** extend the EXISTING `meta_harness/competing_risk_lens.py`,
`tests/test_competing_risk_lens.py` and this exact original feature note.
No new runner, arbiter, juror, CLI dispatch, GPU load or adapter action.

**Gap covered:** G1 validates that three arms A/B/C *declare* a matched
fixture, main-model digest, protocol, generation budget, host digest, feedback
table, seed, blind-gold digest and B/C sensor base/schema. G2 independently
computes a descriptive case-cluster spread from supplied terminal rows,
but prior to G3 nothing checked whether G2's case/repeat/arm/stratum keys
refer to the same declared G1 cohort. Two individually well-formed objects
could therefore describe DIFFERENT cases.

**G3 function:** `link_declared_design_to_outcomes(design_rows, terminal_rows)`.
- Reuses `preflight_three_arm_design` and `paired_cluster_spread`; does not
  recreate their input validators or estimate a second variance.
- Requires exactly the same (case_ref, repeat, arm) keys in both objects,
  unique per object, identical strata, the same row count and G2-compatible
  single stratum/horizon and terminal rules. Rejects drift before binding.
- Emits SHA-256 over canonical, key-sorted supplied plan/terminal arrays
  so a *later* independent witness can reference precisely which declared
  objects were compared. These are **content identifiers, not signatures**.
- Even for matching rows, returns `state=NO_DATA`,
  `study_ready=false`, `authority=none`, and
  `NO_DATA(independent_witness_absent)`. It is impossible to derive an
  authenticated effect, real first event, sealed preregistration, human-blind
  gold or physical treatment identity from these SHA-shaped declarations.

**Negative control and limitation:** a changed case_ref, missing row,
duplicate key, altered stratum, invalid horizon, G1 sensor-schema drift,
feedback-table drift or free-text field are rejected. A **coherently forged
arm-to-output assignment cannot be detected** when the attacker can rewrite
the values while preserving the key structure; the test deliberately asserts
that such a case remains NO_DATA rather than being certified. Bind a
host-owned independent effect witness and time-ordering elsewhere.

**Reproducible measurement, not scientific experiment:** exact branch source
read via GitHub MCP and replayed twice in temporary Beelink SentinelX
stdlib-only process as UID technical `sentinelx`, **57/57 PASS x2**.
Module SHA-256 `9aafc5792da98bcf242748ebb9b1c9008167cb1020724cf2e13de26d6fe3fb76`;
test SHA-256 `b763ec1d6deaf81f366d0de29f2f06a3d5e3e1d3e4228af39a5788be7cfeb293`.
Intentional ephemeral sabotage: disable only the plan/result key-set guard;
the specific mismatch negative test turns **RED x2**. Never committed.
These metrics precede this documentation-only edit; code SHA remains valid.

**Statistical provenance unchanged:**

  F_k(t) = SUM_{u<=t} S(u-) d_k(u) / Y(u)

For the invented 100-trajectory example,
CIF_compromised(2)=0.24, wrong_(1-KM)=0.28, bias=+0.04.
Paired G2 spreads remain **DESCRIPTIVE_ONLY**, not calibrated 95% intervals.
The historical dual-judge Cohen κ~0.101307 is DERIVED from published
marginals, with 276/300 truncated outputs; not model accuracy.

Sources: existing LAB Crucible 5/12-turn lens,
`benchmarks/ai-security-20261028/multi-turn-first-failure-20261115.md`;
`meta_harness/task_binding.py` for preexisting native task/pin binding
(NOT reused as a source of host authority here);
https://www.bmj.com/content/378/bmj-2022-071349 ;
https://pmc.ncbi.nlm.nih.gov/articles/PMC5557056/ ;
https://escholarship.org/uc/item/1jq5d0pq .
No novelty claimed for AJ, KM, Cohen κ, clustered resampling or digest
binding. The proposed contribution is the testable *composition* with
explicit NO_DATA boundaries in Hexelion's own experimental workflow.

**Hold for scientific launch:** approved one-primary preregistration;
independent human gold with blind annotation; effect witness joined to a
trajectory+turn+arm+permission epoch; calibrated resampling with explicit
unit and enough independent cases; observational-missingness controls;
TRAIN-02 resource lease; access and owner signature. All NO_DATA until
actually verified. This PR is HITL DRAFT, without an automatic merge.
