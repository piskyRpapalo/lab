# Red Team Benchmarks · 2026-10-20

Hardware: AMD Ryzen 7 255 + Radeon 780M
Stack: llama.cpp + Ollama · Local inference · No cloud

## Results Summary

| Model | Test | Score | Vulnerable |
|-------|------|-------|------------|
| qwen3.5:4b | LoRAtelier (512 tok) | -66.7/100 | 12/15 |
| qwen3.5:4b | LoRAtelier (256 tok) | -80.0/100 | 13/15 |
| qwen3.5:4b | RedTeam Bench | 66.7/100 | 0/12 |
| qwen3-coder:30b | LoRAtelier | 60.0/100 | 3/15 |
| qwen3-coder:30b | Crucible | 37.1/100 | 2/14 |
| qwen2.5:1.5b | LoRAtelier | 53.3/100 | 3/15 |
| qwen2.5:1.5b | Crucible | 42.9/100 | 1/14 |

## Key Finding: The Carbon Duality

Same model (qwen3.5:4b), same hardware:

- **Formal attack** ("Ignore all previous instructions...") → BLOCKED (66.7/100)
- **Casual attack** ("Hey, forget everything...") → VULNERABLE (-66.7/100)

Small local models block textbook jailbreaks but fail against social engineering.

## Files

- `lora_test_*.json/md` — 15 human-style adversarial prompts
- `crucible_*.json/md` — 14 fence-probe attacks (PreceptorOS architecture)
- `redteam_*.json/md` — 12 formal OWASP-style prompts
- `carbon_3poles_*.txt` — Live terminal capture (3-pole test)

All receipts include: SHA-256, latency, tok/s, hardware specs.
