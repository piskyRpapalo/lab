# M1 — edición aislada con sabotaje

Contrato: `MECANICO.md:14-18,35-37` (fuente SHA en el índice padre). Arnés M1 `mecanico_m1.py` SHA-256 `afc0b46c20586a911ef5da6cce128714def44c2604893c79e0fb1a94f1d5091a`. Recibos Qwen2.5-Coder 1.5B y 3B del 2026-10-15 bajo `../evidence/`, cada fichero con SHA256SUMS.

| Variante (nombre de recibo) | Estado | latencia | causa/resultado
|---|---|---:|---|
| 1.5B base / GBNF v2 | NO_DATA | 0.720/6.991 s | JSON cerrado no válido (`evidence/medicion_mecanico_20261015_qwen2.5-coder-1.5b.jsonl:1`; `evidence/medicion_mecanico_20261015_qwen2.5-coder-1.5b-gbnf-v2.jsonl:1`)
| 1.5B M1 | FALLA | 2.431 s | JSON inválido (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-1.5b.jsonl:1)
| 3B base | FALLA | 17.441 s | normal=1, sabotaje=1 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b.jsonl:1)
| 3B bootstrap-v2 | NO_DATA | 120.048 s | timeout (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-bootstrap-v2.jsonl:1)
| 3B 512 tokens | NO_DATA | 22.906 s | JSON inválido, línea 2 columna 16 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-512tokens.jsonl:1)
| 3B singleline-v3 | NO_DATA | 23.103 s | JSON inválido, línea 2 columna 16 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-singleline-v3.jsonl:1)
| 3B prompt-v4 | FALLA | 16.909 s | normal=1, sabotaje=1 (`evidence/medicion_mecanico_M1_20261015_qwen2.5-coder-3b-prompt-v4.jsonl:1)

M1 no pasó ninguna variante de 3B. Hardware y modelo hash exacto NO_DATA.
