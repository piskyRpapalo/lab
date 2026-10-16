# Fluency mecánica M1–M4

Fuente de alcance y resultados: `~/p0x/estudios/bench-fluency/MECANICO.md:1-40`, SHA-256 `514886157f2328c480f555ff06b8f1f048fc2f42774d803f728ee8ad8c7053b2`. Runner `mecanico_runner.py`, SHA-256 `b9648863911c74655d7cea206d05db17c4728e99c6803ca010a2daf460f6c7de`. Jueces M1–M4: `mecanico_m1.py` `afc0b46c20586a911ef5da6cce128714def44c2604893c79e0fb1a94f1d5091a`; M2 `15d5b74264cd416d29cbff9e547f43a70575907747ed66df85471d1695336edc`; M3 `d2ce68c6220a36d65df4cf04cf85d33edb1320eec6eaefa13830a38f226d2fda`; M4 `fab34e1420c3d5b45c106a7191bd3286ccb1b9d643b4f5349e09071b0dc8348a`. Modelo Qwen2.5-Coder 1.5B/3B, llama.cpp b10068; modelo blob SHA, host hardware y fecha de cada variante: **NO_DATA** (los recibos fijan fecha 2026-10-15, no hardware/model digest). Tokens de salida: NO_DATA, CLI no expuso conteo verificable.

| Pieza | Contrato medido | Último resultado |
|---|---|---|
| M1 | modificación aislada; caso normal y sabotaje | FALLA: ambos tests fallan en prompt-v4 (1/1); variantes anteriores inválidas/timeout; ver [M1](M1/README.md) |
| M2 | reemplazos exactos, estructura y sintaxis | FALLA: entrega JSON inválida en las variantes registradas; ver [M2](M2/README.md) |
| M3 | recuperación de citas exactas de líneas | PASA 2/2 con retrieval-v3; baseline/formato y list-v2 fallaron; ver [M3](M3/README.md) |
| M4 | añadir una sola línea al límite UTF-8 16.384 | PASA: 16.370→16.378 (+8 bytes) con v3; ver [M4](M4/README.md) |

Alcance: contrato de respuesta y juez local de tarea. No mide adopción de agente ni calidad de parche aplicado; el runner declara que no aplica las respuestas al checkout. No mezclar latencia de tareas con pruebas del arnés: `MECANICO.md:27-40` recoge además suites de unidad, no inferencia. Los 19 recibos fuente se adjuntan byte a byte en `evidence/`; `SHA256SUMS` sella copias recuperadas.
