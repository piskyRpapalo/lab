# M2 — literal replacements with closed output

Contract: `MECANICO.md:14-17,21` and receipts archived in `../evidence/`. Judge `mecanico_m2.py` SHA-256 `15d5b74264cd416d29cbff9e547f43a70575907747ed66df85471d1695336edc`. The source describes three literal replacements, anchor validation, a 4×4 matrix, syntax, and an in-memory patch.

| 3B variant | Status | latency | cause |
|---|---|---:|---|
| base | FAIL | 17.494 s | invalid delivery JSON |
| list-v2 | FAIL | 14.216 s | invalid delivery JSON |
| blocks-v2 | FAIL | 10.030 s | invalid delivery JSON |
| oneline-v3 | FAIL | 16.180 s | invalid delivery JSON |

All outputs violated the closed format before the patch could be assessed; no answer was applied. Tokens, model hash, and hardware: NO_DATA.
