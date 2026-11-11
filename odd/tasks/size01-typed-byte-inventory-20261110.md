# SIZE-01 · Classify Compact Receipt Ceilings (typed audit)

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **Status:** PROPOSED.

**Source:** Private Mesa #10 SIZE-01; Atlas house ceiling, Study depth doctrine. The user-approved routing keeps the mission in Private Mesa; this LAB PR contains a read-only measurement instrument, not another mission board.

**Existing:** `bin/verify_depth_budgets.py` verifies *declared depth targets* with a 16,384-byte piece ceiling. It does not resolve the false universal claim that every JSON/Markdown must be under 1,024 B. LAB benchmark JSON archives contain large raw artifacts; their size alone is not a violation of a compact-frame limit.

**Implementation:** `bin/size01_typed_inventory.py` takes a local repo and **explicitly declared, checked-in or operator-provided category assignments**. Reads Git-tracked paths only. Classification is `receipt_frame`, `lexical_packet`, `declared_piece`, or `raw_benchmark_artifact`. No auto-reduction, deletion, path printing or rewriting. Compact summary provides count of GREEN, RED, NO_DATA and OUT_OF_SCOPE; optional detail uses one-way path digests, not paths.

**Boundaries:** frame and lexical packet must be strictly below 1,024 B; declared piece ceiling is inclusive 16,384 B. A raw benchmark artifact has **no universal frame ceiling**; it is OUT_OF_SCOPE until an applicable artifact policy exists. Missing classifications are NO_DATA, never green. Reject path escapes and symbolic links.

**Gate:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2 plus the LAB index gates. No private paths or source content in outputs.

**Next:** agree per-repo classification policies in the Private Mesa before running a full cross-repo audit. E2E file reductions = NO_DATA (not authorized or performed). This code does not claim every historical file complies.
