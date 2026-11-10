# DFA-06 · Generate Verifiable Evidence Packages (offline fixture)

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **Status:** PROPOSED; no authority, signing or external transport.

**Source:** Public Mesa DFA-06 (missions/DFA-20261110-proposal.md), Study #109, LAB F-08 offline latency utility. One implementation slice, not a new mission registry.

**Existing before this piece:** LAB receipt formatter and hash-bearing measurement tools, F-08 computes from *declared* event times but does not verify evidence delivery. No DFA-06 bounded envelope producer at the inspected LAB main.

**New instrument:** `bin/dfa06_evidence_bundle.py` accepts a *scrubbed, synthetic metadata manifest*, enforces a closed schema, a 16,384-byte **package** ceiling, SHA-256 integrity over canonical bytes and receiver-side verification. It deliberately does **not** read private artifacts or copy their content.

**Fail-closed:** duplicate IDs, unbounded lists, unknown fields, private path-like IDs, invalid timestamps, missing NO_DATA causes and tampered payloads fail. No signing key, network or model inference. The result `VERIFIED_BYTES` must **not** be printed as `VERIFIED_SOURCE` or `VERIFIED_SIGNATURE`.

**Command:**
```sh
python3 -m unittest discover -s tests -p 'test_dfa06_evidence_bundle.py'
python3 -m unittest discover -s tests -p 'test_*.py'
# Two independent runs, on fresh origin/main branch.
```

**Observed limits:** source digests are supplied, **not verified against source files**; the envelope is **unsigned**; no live request/receiver transport or delivery latency. E2E=NO_DATA (cause: synthetic metadata-only fixture). The proposed 5-second DFA-B4 target cannot be inferred from this run.

**Next:** connect a separate offline receiver fixture (DFA-B4) and only later an explicitly authorized real consumer; keep HITL exact-head and public SCRUB.
