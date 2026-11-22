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
This branch must stay DRAFT, no merge or production integration. The
Soberano retains go/no-go, exact-head signature and TRAIN-02 authority.
