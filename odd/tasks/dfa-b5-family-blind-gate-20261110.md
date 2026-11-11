# DFA-B5 · Detect Synthetic Companion Manipulation (judge preflight)

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **Status:** PROPOSED, NOT A DETECTION BENCHMARK.

**Source:** Study #112 DFA-B5, Private Mesa classification and LAB Fisher lesson (n >= 60 per class). Source-qualified DFA-B5 must not collide with canonical LAB B5 agent telemetry.

**Existing:** historical red-team artifacts and Crucible offline probes; no verified 60-per-class labeled dataset or family-independent judge was selected. The proposed qwen3-coder:30b judge is not installed in the inspected rack; a Qwen-family judge would also violate the family-blind principle when paired with a Qwen manipulator.

**New:** `bin/dfa_b5_family_blind_gate.py` is a closed-schema, offline *declared-candidate preflight*: denies same-family candidates, fewer than 60 declared cases per class and missing held-out set. Different-family candidates return NO_DATA until provenance, installation, availability, human selection, dataset calibration and consent are verified. It never connects to Ollama, starts an evaluation, installs a model or grants authority.

**Gate:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2. Report denied/NO_DATA, never promote declared family strings into verified provenance.

**Risk:** A field claiming `family=gemma` is self-reported; it is NOT a trustworthy family attestation. A real Gemma-family candidate can be *considered* after hardware memory assessment, explicit Sovereign choice and verification of installed model identity.

**Next:** Sovereign selects the judge model and authorizes a consented synthetic calibration set; LAB then measures family-blind detection with independent labels. Detection >=90%, false NO_DATA catch >=80%, held-out >=85% remain NO_DATA.
