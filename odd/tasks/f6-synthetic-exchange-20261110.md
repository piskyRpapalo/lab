# F6-01 · Exercise Economic Fences in a Synthetic A2A Exchange

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **State:** PROPOSED/MEASURED_SOURCE_ONLY.

**Source:** Private Mesa #10, ideas10nov §4 F6-01; canonical F6 is *live device benchmarks* (distinct). Crucible fence F6 is **not** a signed A2A market or authorization service.

**Existing:** LAB `bin/f6_economic_probes.py` and `tests/test_f6_economic_probes.py` merged via lab#148. Three offline consistency rules already exist and are **not rewritten** by this piece.

**New slice:** `bin/f6_synthetic_exchange.py` represents a closed synthetic A2A message, executes the pre-existing F6 assessor, issues a SHA-256-bound, scrubbed decision receipt. No real node identifiers; no sender keys, actual transport, market transaction, or privilege.

**Acceptance:** deliberate inflated reach, impossible energy promise and unauthorized arbitration yield DENY; plausible but unattested reports yield NO_DATA. Two independent test runs with full LAB gate; output contains only pseudonymous ID, classification, digest, cause and explicit missing attestations.

**Gate:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2.

**Risk:** supplied hashes do not prove receiver signatures. `sender="sovereign"` is just a string; NO_DATA must not become authorization. This is a safe preparatory **fixture** for ACHO-01, not proof that ACHO-01 or a live A2A testnet is running.

**Next:** after an approved Acho frame schema and signing policy, adapt a separate transport fixture. End-to-end live A2A=NO_DATA (cause: no network, no trust signatures and no live receiving node).
