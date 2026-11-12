# Public local-Ollama benchmark · 2026-11-11

**Problem**: locally measured throughput receipts were accessible only through private Command comments and a local operator file; external readers could not study all 12 samples without account access.

**Source**: measured 2026-11-11 SentinelX Beelink Ollama receipt (12/12 runs), SHA-256 `317a6a163c1b88f6fff64e514e63a6cff12ef3b70dd93d33663256448e9c8950` of original private JSON.

**Adaptation**: publish one scrubbed markdown benchmark card in canonical `benchmarks/`, link from existing index, update its index assertion from 31 to 32. Public, anonymous-access reading copy at [lab issue #164](https://github.com/piskyRpapalo/lab/issues/164). No parallel benchmark catalogue, telemetry pipeline, or new model inference.

**Measured benefit**: six models, twelve individual local Ollama throughput samples and their method publicly auditable; verified HTTP 200 anonymous issue and branch card.

**Risks / limits**: CPU/GPU backend split, quality, thermals, and strict comparability with 2026-11-10 are `NO_DATA` (no supporting same-harness/sensor evidence); original raw receipt stays private, digest is not signature; adding a new card requires updating static card-count test.

**Next**: run the full Lab gates twice against exact PR head, then human review / exact-head signing before merge to `main`. No deploy or autonomous signature.

**Agent:** Codex · **Model:** GPT-6 · **Run:** SentinelX Beelink, 2026-11-11.
