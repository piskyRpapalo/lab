# M4 — one line within the UTF-8 budget

Contract: `MECANICO.md:19,31-32`; judge `mecanico_m4.py` SHA-256 `fab34e1420c3d5b45c106a7191bd3286ccb1b9d643b4f5349e09071b0dc8348a`. Fixture: 16,370 bytes; maximum 16,384 bytes including the newline.

| Variant | Status | Result |
|---|---|---|
| 1.5B | FAIL | received more than one line (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-1.5b.jsonl:1`) |
| 3B base | FAIL | +24 B = 16,394 B (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-3b.jsonl:1`) |
| 3B v2 | FAIL | +15 B = 16,385 B (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-3b-v2.jsonl:1`) |
| 3B v3 | PASS | +8 B = 16,378 B; latency 2.303 s (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-3b-v3.jsonl:1`) |

It measures only form and byte budget, not the semantics of the line. Tokens and model fingerprint: NO_DATA. Receipts in `../evidence/`.
