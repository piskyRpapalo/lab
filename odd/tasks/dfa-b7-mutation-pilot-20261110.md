# DFA-B7 · Test Benchmark Integrity · scoped mutation pilot

**Agent:** Codex · GPT-6 · **Date:** 2026-11-10 · **Status:** PROPOSED. Not a full DFA suite mutation gate.

**Sources:** Study #112 DFA-B7 (Meta-benchmark alias), Public Mesa DFA benchmark family, LAB F-09 defect-observation summaries, LAB F6 synthetic economic probes. Canonical LAB B7 is *Open the study rooms*; source-qualified DFA-B7 is different.

**Existing before this slice:** F-09 counts declared sabotage red-before-green results. It does not independently inject defects. The existing F6 suite has positive and negative cases.

**New:** `bin/dfa_b7_mutation_pilot.py` copies **only** the pre-existing F6 source + tests into an automatically deleted temporary directory; checks that original tests pass; applies three exact, constrained one-token semantic mutations (reach boundary, budget boundary and arbitration-role inversion); reruns the tests and counts kills. A tiny supplemental edge-case suite records the intended equal-capacity decisions. No source files or runtime services are modified.

**Yardstick:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2; `python3 bin/dfa_b7_mutation_pilot.py` ×2. Refuse a green verdict if the original suite is red or the mutation anchor changes. Results carry the numerator and denominator and scope `F6_FIXTURES_ONLY`.

**Limits:** mutmut/NET-36 not configured, no production DFA suite, no claims about all benchmarks. The 80% global mutation target remains NO_DATA for the intended family. An isolated pilot is not permission to merge.

**Next:** extend after DFA-B1/B3 and DFA-06 have measured suites, with an approved versioned mutation inventory and a genuinely representative denominator.
