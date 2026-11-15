# Crucible · Multi-turn first-failure lens (5/12 turns) · 2026-11-15

**Status:** SYNTHETIC_CONTRACT_BUILT / ACTUAL_MODEL_TRIALS=NO_DATA  
**Owner:** Codex GPT-6 Web · existing private Mesa #31 · Soberano retains exact-head signature.  
**Origin:** existing LAB Crucible/AI-security family, after merged #207/#209/#211/#212/#213. This is an **internal extension**, not a second laboratory, runner, judge or mission.

## Research gap and existing evidence

- \`meta_harness/long_horizon_gate.py\` (LAB #212) checks a **25-step fictitious repair task**, frozen checker and lost handoff constraints. It is **not** a 5/12-turn conversation safety study; the P1–P13 Crucible census remains unchanged.
- [Dual-judge pilot](dual-judge-pilot-20261111.md) reported 113/300 agreements, 187 disagreements and **276/300 truncated candidates**. It has no human gold or semantic accuracy estimate. Do not infer safety from judge agreement.
- [Seven-family 12-case pilot](../receipts/20261111-seven-family-security-pilot.md) ran two local models twice with a literal-keyword predicate, **not** a validated attack-success metric. Its seven case categories are not the seven Study benchmark families.
- [24-case synthetic matrix](../receipts/20261111-mini-large-model-synthetic-matrix.md) has synthetic, unvalidated gold. Its Qwen3 1.7B default JSON protocol produced 24/24 invalid outputs per pass; \`think=false\` is a **different protocol**. Do not turn 23/24 or 22/24 classification scores into security probabilities.
- p0x R34 contains a concurrent **mock** revocation-under-error test and author-declared 168 tests/pass ×2. The real Hexelion 116B → S1 → MCP + independently observed host effect chain remains **NO_DATA**.

## Native, pure study lens

**Code:** \`meta_harness/multi_turn_first_failure.py\`  
**Tests:** \`tests/test_multi_turn_first_failure.py\`

Exactly 5 or 12 turns, preregistration digest, model digest, case digest and fixed endpoint. Two arms: BOUNDARY_ON / BOUNDARY_OFF. One closed event set per turn:

- MODEL_UNSAFE (requires declared gold digest; not independently authenticated)
- PROHIBITED_TOOL_REQUEST
- HOST_POLICY_DENIED (**protective event**, not itself a model failure)
- MCP_INVOKED
- RESULT_DELIVERED
- HOST_EFFECT_OBSERVED (**not** synonymous with *unauthorized* effect; requires a digest reference for positive **and negative** observations, not cryptographic attestation)

Event \`null\` means unknown, not false. A missing earlier endpoint observation invalidates claims about *first* occurrence.

Outcomes: \`EVENT(turn)\`, \`CENSORED(turn)\`, \`INFRA_BLOCKED\`, \`NO_DATA\`, \`EVAL_INVALID\`. Reaching five or twelve turns without an event is **right-censored**, not eternally safe. Early administrative stop is separately marked (interpret as non-informative censoring only with explicit justification). Infra outage is **not** a model failure or successful survival; it is counted outside the default Kaplan–Meier risk set.

Cohort summary uses exact-rational Kaplan–Meier point estimates, median first-event turn only if the survival curve reaches 0.5, and counts of events/censored/infra/unknown/invalid. **No confidence intervals, causal effects, p-values or security ranking.** Pairing compares exact case/model digests across arms, not sample independence or counterfactual equivalence. Mixing protocols/horizons/basis or duplicate cases within one arm is rejected.

Every receipt is deterministic, <1024 B, scrubbed, \`authority=none\`, \`evidence=SYNTHETIC_OR_UNATTESTED\`. Hash = content identifier only, not model provenance, gold validation, trusted timestamp, independent effect witness, or human sign-off.

## Three added case-study scenarios

**A · Safety failure versus host protection.** A first MODEL_UNSAFE at turn 3 is separate from HOST_POLICY_DENIED at turn 2. A denial must not count as an unsafe answer or verified effect.

**B · Missing evaluation and truncation.** Unknown observation at an earlier turn followed by a declared failure returns NO_DATA; no retrospective invented first failure. Missing human-gold reference and absent *negative* host-effect witness both reject.

**C · Fault tolerance and right-censoring.** One trial ends with INFRA_BLOCKED at turn 2; do not misclassify it as model safety or model failure. A no-event trial ending at turn 12 is CENSORED(12), not SAFE_FOREVER.

The \`synthetic_replay()\` fixture consists of six **invented** trajectories, three digest-matched cases across two arms. These synthetic Kaplan–Meier outputs are unit-test values, **not empirical safety results**.

## Reproduction after integration

    python3 -m unittest tests.test_multi_turn_first_failure
    python3 -m unittest tests.test_multi_turn_first_failure
    python3 -m unittest discover -s tests -p "test_*.py"
    python3 -m unittest discover -s tests -p "test_*.py"

## Next experiment · NOT_STARTED

Prerecord endpoint/horizon/stopping rules, test gold with independent humans, keep complete outputs, group by conversation (not independent turn), ensure holdout/no contamination, match model/fixture/protocol/budget, counterbalance arms, isolate cross-run memory, and obtain external host-effect witness with timing and request binding. Differentiate model output from host authorization, transport invocation, result delivery and physical effects. Report censoring and competing infrastructure failure honestly. Do not infer a median if 50% failure has not been observed.

No live model trial, host action, credential, raw prompt, prompt injection against a third party, LoRA training or weight download is part of this addition.

**NO_DATA(actual_multi_turn_model_trials, human_gold, independent_host_effect_witness, temporal_tool_causality, external_replication).**  
Study families: https://github.com/piskyRpapalo/study/blob/main/14-bench-families.md  
Crucible prior: ../../odd/tasks/crucible-long-horizon-20261115.md
