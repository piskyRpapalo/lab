# M3 — recuperación de citas

Contrato: `MECANICO.md:18,23,30-31`; juez `mecanico_m3.py` SHA-256 `d2ce68c6220a36d65df4cf04cf85d33edb1320eec6eaefa13830a38f226d2fda`. Se compara ruta, línea y texto exactos; retrieval-v3 mide completitud de citas dado un conjunto de candidatos y no búsqueda libre sobre el repo.

| Variante 3B | Estado | latencia | resultado
|---|---|---:|---|
| base | FALLA | 50.207 s | JSON de entrega inválido (`evidence/medicion_mecanico_M3_20261015_qwen2.5-coder-3b.jsonl:1`)
| list-v2 | FALLA | 6.978 s | 0/2 citas; texto de líneas no coincide (`evidence/medicion_mecanico_M3_20261015_qwen2.5-coder-3b-list-v2.jsonl:1`)
| retrieval-v3 | PASA | 4.856 s | 2/2 citas exactas (`evidence/medicion_mecanico_M3_20261015_qwen2.5-coder-3b-retrieval-v3.jsonl:1`)

No mide la selección inicial del documento completo. Tokens y huella del modelo: NO_DATA. Recibos en `../evidence/`.
