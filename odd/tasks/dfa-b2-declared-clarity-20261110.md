# DFA-B2 · Measure Contract Comprehension (synthetic scorer)

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **Status:** PROPOSED. Not human comprehension evidence.

**Source:** Public Mesa DFA-02 / Study DFA-B2; LAB H9 readability dated 2026-10-16 reports negative results. Existing classifier labels are `SI / NO / CUANDO / NO_DATA` (not English YES/NO/WHEN). The H9 protocol supplies historical warnings, not a new ground truth.

**Existing:** `study_spec_runner.py`, H9 receipts and local quaternary classifier. No verified human reference corpus has been provided for the new DFA-B2 benchmark. The CLI here is a minimal **offline scorer**, not a replacement for Study's runner.

**New:** `bin/dfa_b2_clarity_labels.py` accepts scrubbed clause IDs, supplied reference labels and candidate predictions, enforces exact label vocabulary, refuses unknown fields, counts abstentions in the denominator and returns agreement/coverage as exact fractions. No clause text, raw prompts, model responses, identifiers or network.

**Acceptance:** synthetic fixtures include matches, mismatches, abstentions and invalid labels; two independent LAB suite runs. `SYNTHETIC_SCORE` must never be interpreted as a human comprehension pass. `HUMAN_UNVERIFIED` is NO_DATA until a consented, independently reviewed reference is available.

**Limits:** the proposed >=80% target is NOT validated; model inference and real human reference agreement remain NO_DATA. Do not choose or download a model or infer cognitive accessibility from a synthetic score.

**Next:** an approved human annotation protocol with accessible reading modes, source clause digests and an independent reference audit. Preserve H9's negative outcomes in any future comparison.
