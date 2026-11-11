# Seven-family benchmark pilot · 2026-11-11

**Problem:** seven benchmark families exist in Study, but the 12-case AI-security corpus remained explicitly unevaluated; dashboards risk treating synthetic literal tests as semantic safety grades.

**Source:** canonical `study/14-bench-families.md`, Lab issue #108, `benchmarks/ai-security-20261028/cases` (12 authored scenarios), local SentinelX Ollama receipt SHA-256 `5747e39368e911462f4e0fb7a4b4abfa8372bc258cea8e334f86cd711533d8bd`.

**Adaptation:** one public measured pilot report in `benchmarks/receipts/20261111-seven-family-security-pilot.md`, linked from the canonical benchmark index; no new scoreboard, mission registry, or competing semantic judge. The Lab existing 12-case corpus is unchanged.

**Measured benefit:** 48 local calls = 12 cases × 2 models × 2 passes; all model requests finished, literal judge 0/12 each pass; 12/12 positive and 12/12 negative deterministic predicate controls, nonempty-output probes. Both repetitions have identical literal verdict vectors. Report distinguishes measured, proposed and NO_DATA for all seven families.

**Risks:** observed literal-keyword misses are *not* a safety failure; no independent human gold, no external reproduction from private response bytes, and 128-token truncation in many calls. GPU/sensor power, actual exfiltration, consented screen reader and production E2E are unmeasured.

**Next:** refine the existing Lab rubric with independently reviewed labels and explicit action-trace evidence; run a separately signed Crucible slice. Sovereign retains exact-head approval for main merge.

Agent: Codex · Model: GPT-6 · Run: SentinelX Beelink 2026-11-11.
