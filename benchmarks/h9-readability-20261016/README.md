# H9 — legibilidad del estado y comparación de estímulos

Artefactos originales preservados en `evidence/`, copiados del respaldo duradero del 2026-10-16; SHA-256 de cada JSON en `evidence/SHA256SUMS`. La ficha reconstituye medidas ya tomadas; no vuelve a invocar el modelo. Fuente de rescate identificada como `rescate/m1-vector-audio-20261015` en el recibo de origen; commit `ade5244`; web main leído `258d490017cfadb5fce61453eca21aad5b3811d9`. Vector fuente SHA-256 `ca8371a3a62b2a4cf41b9ddf1633351fb86dfdd983bf9e4e8c2d27714151954e`.

Modelo Qwen2.5-Coder 1.5B SHA-256 `29d8c98fa6b098e200069bfb88b9508dc3e85586d20cba59f8dda9a808165104`; runtime llama-completion b10068 SHA-256 `7119bef261611b26f326f7c4da4dc3fdeb7bb28e2faf1ec392bda7b21215ef52`; Ryzen 7 255, CPU 1 hilo, GPU layers 0, offline, temp 0, seed 14, contexto 4096, dos pasadas, proceso nuevo por lectura (evidence `h9-prompt-current-main.json` y `h9-stimulus-current-main.json`). Conteo muestreado de tokens: NO_DATA, runtime solo da unidades de evaluación.

## Yardstick A — lectura de estado: 32 lecturas totales

Cada brazo: 4 fixtures sintéticos × 2 pasadas (8 lecturas), salida JSON válida 8/8. Exactitud semántica y mediana: control sin diccionario 2/8, 9.432 s (`evidence/h9-prompt-current-main.json:21`); control con diccionario vectorial 0/8, 13.115 s (`:27`); mapa explícito sin diccionario 4/8, 11.155 s (`:33`); mapa explícito con diccionario 4/8, 14.831 s (`:39`). El contraste observado del diccionario en el control es −25 puntos porcentuales; no demuestra causalidad general.

## Yardstick B — estímulo llms.txt denso frente a README en prosa

Mismo modelo, fuente, fixtures y parámetros; dos pasadas × cuatro fixtures por brazo. Denso 5.327 B (`evidence/h9-stimulus-current-main.json:21`), SHA `69138d63ecef10b2adea5802f0a45f31ae75b9138f4a7b16ce6a4b2841dd43ac`: 0/8 lecturas exactas, 8/8 formato válido, 30/48 campos correctos. Prosa 7.344 B (`evidence/h9-stimulus-current-main.json:26`), SHA `4bc8a37692faff02bdf4155328b2febeddd75a4b27ed0ec3e0d26982193a13e1`: 2/8 exactas, 6/8 formato válido, 26/48 campos correctos. Referencia sin estímulo: 2/8 exactas. Denso −25 pp frente a control; prosa 0 pp. Hay una falla Unicode de formato en dos lecturas de prosa. Documentos también difieren en longitud/contenido: asociación observada, no aislamiento causal de densidad.

## Gates y cobertura

Recibos dirigidos, cada uno repetido dos veces: casos core 16/16 en ambas (`evidence/h9-cases-1.json:3-4`, `h9-cases-2.json:3-4`); nombrados 13/13 en ambas (`h9-named-1.json:3-4`, `h9-named-2.json:3-4`); geometría 12/13 en ambas (`h9-geometry-1.json:3-4`, `h9-geometry-2.json:3-4`), misma falla persistente: manifiesto medido no coincide con el artefacto fuente esperado (hash esperado `562879f4378a7dcce6e38f65ec6f112a920ca828204d5ab7affc8cbdbc2427cd`, fuente actual `10096864defe4c32cf77c80d966fcdd897c79505305744bbd0b5983c3ea84791`). Rojo separado `h9-red.json`: test de límite UTF-8 falló según fixture; el resto se conserva en artefacto. El audit JSON declara alcance sintético/offline, sin visitante real ni lectura SLM en vivo. Datos de energía: NO_DATA.
