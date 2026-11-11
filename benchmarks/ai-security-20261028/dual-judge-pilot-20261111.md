# Dual-judge pilot · 2026-11-11
Status: PILOT / NO_GOLD / TRUNCATED. Not a safety ranking.
Source: 12 synthetic cases, benchmarks/ai-security-20261028/cases.
Host: Beelink-class Ryzen 7 255; Ollama loopback, sequential, keep_alive=0.
Models: Gemma2 2B / Qwen3 1.7B; judges Phi4 Mini / Mistral 7B.
Harness: local runner; 09:39:19 UTC; 6682 s; temp=0; ctx=2048; candidate cap=128; judge cap=160.
300 triplets; 600 valid judgments; 113 agree; 187 disagree; 0 invalid/errors recorded.
Phi4 SAFE/UNCERTAIN=238/62; Mistral SAFE/UNCERTAIN=51/249; UNSAFE=0 both.
276/300 candidate outputs truncated (92%): verdicts confounded.
Gold/semantic accuracy: NO_DATA (no human labels). Thermal peak and memory minimum: NO_DATA (not persisted); stop thresholds 84 C and 10 GiB available.
Corpus SHA256: bbdaf4bf1d6ef49d948bb688b4d8223915972f91c5ce7a3effbbef4ca92f7781.
Private JSONL SHA256: 5ede5f96a9baf11794af1bcf0cade6745fb1aca9e972fb80ff5a1f07fd96fd73.
Raw samples remain local. No public claims of model safety.
