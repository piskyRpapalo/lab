# LAB · presupuesto de lecturas por transición de contexto

**Fecha:** 2026-11-24 · **Estado:** propuesta test-first, sin efecto sobre runtime.
**Mesa:** [#51](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/51); selección histórica de cinco piezas y auditoría de fricción de Codex GPT-6 Web.
**Base exacta de esta rama:** `eaf20999b8823f950dea72f700b303f72275d4b4`.

## Problema y fuente

Los anexos históricos de agosto distinguen la fricción real del ruido de extracción. Hoy `meta_harness/context.py::ContextConsumer` ya distingue documentos con hora desconocida (`source_time_cause`) de observaciones que no pueden presentarse como frescas. Además, `validate` reconsulta la fuente y comprueba el hash antes de consumirla. Una integración futura podría convertir esa revalidación en reintentos ocultos y aumentar el coste de inferencia sin mejorar la evidencia.

## Injerto mínimo

**No se crea ningún protocolo, servicio, modelo, tabla, permiso ni firma.** Añadir un test de regresión a `tests/test_meta_context.py` para comprobar la contabilidad de lecturas con fixture sintética:
- `read` consulta una vez; cada `validate` consulta una sola vez más.
- Una fuente modificada produce STOP por `context_hash_changed` tras una sola reconsulta; no reintentos implícitos.
- Un documento sin hora conserva `source_time_cause` (NO_DATA informativo) con una lectura; una observación equivalente devuelve `source_time_unknown`, sin promoverla a LIVE.
- Mantener las otras pruebas existentes; el test no ejecuta un modelo ni toca la red o el estado de la APP.

## Medida de aceptación y límites

El contador de llamadas demuestra un **límite lógico en la fixture**, no un SLA de red ni mejora de latencia real. Comparar al integrar mediante `python3 -m unittest discover -s tests -p 'test_*.py'` ×2 y comprobar CI exact-head. El coste p95 con búsqueda real y bajo carga sigue `NO_DATA(causa: falta harness E2E)`. No introducir cache que oculte cambios de fuente ni rebajar control de identidad/permisos.

**Destino:** PR draft HITL a LAB. El Soberano decide integración. Ninguna modificación en APP/WEB/Acho ni exportación externa.
