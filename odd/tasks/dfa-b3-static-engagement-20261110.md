# DFA-B3 · Audit Engagement Restraint (static candidate detector)

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **State:** PROPOSED.

**Source:** Study #109; public Mesa DFA-03 / DFA-B3; APP's four Spanish policy prohibitions. Canonical LAB B3 means link harness and app — it is a different source-qualified mission.

**Existing before this piece:** frontend Guardian fixtures and APP policy describe some prohibited patterns; these are not a demonstrated runtime enforcement of all engagement behaviors. No LAB DFA-B3 score was measured.

**New offline slice:** `bin/dfa_b3_engagement_scan.py` detects media-autoplay HTML attributes, JavaScript Notification permission/constructor calls and specifically named passive-reward hooks. Reports rule IDs, line numbers and counts **without emitting source text, URLs or local paths**. No network, no model or browser. Tests include deliberately defective and clean controls; no source changes outside LAB.

**Yardstick:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2 on a fresh main-based branch.

**Non-claims:** A static signal is not necessarily a dark pattern: permission requests might follow consent, video autoplay may be muted and disclosed, and a missing signal does not prove restraint. Therefore detections yield REVIEW_REQUIRED, non-detections yield NO_DATA with cause, and `engagement_restraint_score` remains null because purpose, denominator and live behavior are not measured. The manifesto's proposed score <0.1 is **not validated**. No legal conformity claim.

**Next:** connect the scanner to a source-qualified, scrubbed source manifest with a declared purpose and independent human review of flagged cases. This requires coordination with WEB/APP owners; do not edit their active branches. End-to-end=NO_DATA (cause: no browser behavior or consent observation).
