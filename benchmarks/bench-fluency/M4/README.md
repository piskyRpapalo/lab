# M4 — línea dentro del presupuesto UTF-8

Contrato: `MECANICO.md:19,31-32`; juez `mecanico_m4.py` SHA-256 `fab34e1420c3d5b45c106a7191bd3286ccb1b9d643b4f5349e09071b0dc8348a`. Fixture: 16.370 bytes; máximo 16.384 bytes incluyendo newline.

| Variante | Estado | Resultado |
|---|---|---|
| 1.5B | FALLA | recibió más de una línea (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-1.5b.jsonl:1`)
| 3B base | FALLA | +24 B = 16.394 B (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-3b.jsonl:1`)
| 3B v2 | FALLA | +15 B = 16.385 B (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-3b-v2.jsonl:1`)
| 3B v3 | PASA | +8 B = 16.378 B; latencia 2.303 s (`evidence/medicion_mecanico_M4_20261015_qwen2.5-coder-3b-v3.jsonl:1`)

Mide solo forma y presupuesto de bytes, no semántica de la línea. Tokens y huella del modelo: NO_DATA. Recibos en `../evidence/`.
