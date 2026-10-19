# VIAS · Cloudflare, GitHub y rack · propuesta REQUIERE_FIRMA

Recibo de forma medido el 2026-10-19 UTC. Estas vías alimentan recibos legibles por el cerebro local. Las credenciales y los identificadores privados no forman parte del registro.

## Cloudflare · superficie web

- Ruta de contenido: `public/<ruta>` en el árbol web, servida como `https://preceptoros.org/<ruta>`. El manifiesto público de modelos vive en `public/cerebros.json`; los ficheros de modelo se sirven desde `public/assets/` según el propio manifiesto.
- Techo: cada fichero servido debe medir estrictamente menos de 25 MiB (`25 × 1024 × 1024` B). La excepción exige registro firmado en `EXCEPCIONES.md`. El control está en `test_web.py`, constante `TOPE_FICHERO` y `test_cada_fichero_bajo_el_tope`.
- Recibo: GitHub API devolvió el código fuente de `test_web.py` y `config/modelos-rack.json` el 2026-10-19. Tamaños de los activos servidos y entrega HTTP desde Cloudflare: `NO_DATA`, causa: esta sesión no tiene checkout de WEB ni una vía Cloudflare de lectura/medida. La consulta live HTTP tampoco se permite en el sandbox. Por tanto no se afirma que un modelo concreto esté actualmente servido.

## GitHub · API del registro

Rutas de forma utilizadas: Contents API para leer `test_web.py`, `config/modelos-rack.json` y `RACK.md`; Issues API para el recibo de contrato; Git references/Contents API para escribir una rama de propuesta; Pull Requests API para abrir borradores. El techo de operación es el rate limit de la API y sus límites secundarios; documentación oficial: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api. Para autenticación personal, el techo primario general publicado es 5.000 solicitudes/hora. La cuota restante del conector actual: `NO_DATA`, causa: el recibo de la integración no expone cabeceras `x-ratelimit-*` ni el modo de autenticación.

Recibo medido en esta sesión, 2026-10-19: issue de contrato actualizado (comentario creado); un PR de la joya attention-selector y un PR de forma del LAB abiertos; el PR de APP se prepara en una rama separada. Estados: abiertos, sin fusión. El dato es el número de operaciones completadas, no un chequeo de cuota restante.

## Rack · sensores y endpoints

- Temperatura: `/sys/class/hwmon/*/temp*_input`; el comando registrado encontró 10 canales.
- Energía del paquete: `/sys/class/powercap/intel-rapl:0/energy_uj`; el contador está presente.
- Runner: `http://127.0.0.1:11434/api/tags` y `/api/version`; intentos con timeout de 2 s: `NO_DATA`, causa: el sandbox denegó el acceso al socket local.
- App: `http://127.0.0.1:8740/`; intento HTTP: `NO_DATA`, causa: el sandbox impidió abrir el socket.
- TTL: `TTL_DAYS=7` propuesto en [RACK.md](RACK.md). La transición a `STALE` se calcula al leer con `bin/rack_status.py`; no altera observaciones anteriores.

La presencia en sysfs es `LIVE` a la fecha y hora del recibo. La disponibilidad de los servicios no se deduce de un proceso no visible. La guía de medición térmica y energética está en [ENERGY_BUDGET.md](ENERGY_BUDGET.md).
