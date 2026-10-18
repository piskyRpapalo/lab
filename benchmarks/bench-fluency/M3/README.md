# M3 — quotation retrieval

Contract: `MECANICO.md:18,23,30-31`; judge `mecanico_m3.py` SHA-256 `d2ce68c6220a36d65df4cf04cf85d33edb1320eec6eaefa13830a38f226d2fda`. Path, line, and exact text are compared; retrieval-v3 measures quote completeness given a set of candidates, not free search over the repo.

| 3B variant | Status | latency | result |
|---|---|---:|---|
| base | FAIL | 50.207 s | invalid delivery JSON (`evidence/medicion_mecanico_M3_20261015_qwen2.5-coder-3b.jsonl:1`) |
| list-v2 | FAIL | 6.978 s | 0/2 quotes; line text does not match (`evidence/medicion_mecanico_M3_20261015_qwen2.5-coder-3b-list-v2.jsonl:1`) |
| retrieval-v3 | PASS | 4.856 s | 2/2 exact quotes (`evidence/medicion_mecanico_M3_20261015_qwen2.5-coder-3b-retrieval-v3.jsonl:1`) |

It does not measure the initial selection of the full document. Tokens and model fingerprint: NO_DATA. Receipts in `../evidence/`.
