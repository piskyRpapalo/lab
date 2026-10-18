# M1 — isolated edit with sabotage

Contract: `MECANICO.md:14-18,35-37` (source SHA in the parent index). M1 harness `mecanico_m1.py` SHA-256 `afc0b46c20586a911ef5da6cce128714def44c2604893c79e0fb1a94f1d5091a`. Qwen2.5-Coder 1.5B and 3B receipts from 2026-10-15 under `../evidence/`, each file with SHA256SUMS.

| Variant (receipt name) | Status | latency | cause/result |
|---|---|---:|---|
| 1.5B base / GBNF v2 | NO_DATA | 0.720/6.991 s | invalid closed JSON (`evidence/medicion_mecanico_20261015_qwen2.5-coder-1.5b.jsonl:1`; `evidence/medicion_mecanico_20261015_qwen2.5-coder-1.5b-gbnf-v2.jsonl:1`) |
| 1.5B M1 | FAIL | 2.431 s | invalid JSON (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-1.5b.jsonl:1`) |
| 3B base | FAIL | 17.441 s | normal=1, sabotage=1 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b.jsonl:1`) |
| 3B bootstrap-v2 | NO_DATA | 120.048 s | timeout (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-bootstrap-v2.jsonl:1`) |
| 3B 512 tokens | NO_DATA | 22.906 s | invalid JSON, line 2 column 16 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-512tokens.jsonl:1`) |
| 3B singleline-v3 | NO_DATA | 23.103 s | invalid JSON, line 2 column 16 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-singleline-v3.jsonl:1`) |
| 3B prompt-v4 | FAIL | 16.909 s | normal=1, sabotage=1 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-prompt-v4.jsonl:1`) |

M1 passed no 3B variant. Hardware and exact model hash: NO_DATA.
