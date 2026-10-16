# M2 — reemplazos literales con salida cerrada

Contrato: `MECANICO.md:14-17,21` y recibos archivados en `../evidence/`. Juez `mecanico_m2.py` SHA-256 `15d5b74264cd416d29cbff9e547f43a70575907747ed66df85471d1695336edc`. Fuente describe tres reemplazos literales, validación de anclas, matriz 4×4, sintaxis y parche en memoria.

| Variante 3B | Estado | latencia | causa
|---|---|---:|---|
| base | FALLA | 17.494 s | JSON de entrega inválido
| list-v2 | FALLA | 14.216 s | JSON de entrega inválido
| blocks-v2 | FALLA | 10.030 s | JSON de entrega inválido
| oneline-v3 | FALLA | 16.180 s | JSON de entrega inválido

Todas las salidas incumplieron el formato cerrado antes de poder valorar el parche; no se aplicó ninguna respuesta. Tokens, hash del modelo y hardware: NO_DATA.
