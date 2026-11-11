# DFA-B4 · Measure Evidence Delivery Time (local receiver fixture)

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **Status:** PROPOSED. Stacked on the DFA-06 implementation branch (LAB #150), not on main.

**Sources:** Public Mesa DFA-B4 / DFA-06; Study #109; LAB F-08 already measures duration from **declared** timestamps. This instrument is different: it observes in-process serialization and receiver verification with a monotonic clock.

**Implementation:** `bin/dfa_b4_offline_receiver.py` consumes a scrubbed synthetic manifest, builds the DFA-06 package, round-trips its canonical JSON bytes in local memory, verifies payload digest at the receiver boundary, and records monotonic latency and byte count. Results contain only aggregate numbers, not source text.

**Gate:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2 (fresh process); `python3 test_llms.py` and `python3 bin/verify_llms_tree.py` ×2. It must also reject tampering, invalid source metadata and clock reversal.

**Limit:** local serialization and in-memory receiver are **not** a network path or a real auditing companion. The proposed <5-second delivery target is NOT measured or scored. Source truth, Ed25519 signatures and live transport = NO_DATA with cause. No promises of regulatory compliance.

**Next:** after DFA-06 review, add a separate sender/receiver process fixture over an approved local boundary; an actual remote audited E2E run requires consent and a signed deployment scope. One code slice per PR.
