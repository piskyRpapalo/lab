# VIAS · Cloudflare, GitHub y rack · propuesta REQUIERE_FIRMA

Recibo de forma medido el 2026-10-19 UTC. Estas vías alimentan recibos legibles por el cerebro local. Las credenciales y los identificadores privados no forman parte del registro.

## Cloudflare · superficie web

- Ruta de estáticos: `public/<ruta>` en el árbol web. El índice de cerebros es `public/cerebros.json`, cuya ruta pública propuesta es `/cerebros.json`. La configuración `config/modelos-rack.json` existe en el árbol fuente; una ruta pública que la sirva no está verificada.
- Techo: cada fichero servido debe medir estrictamente menos de 25 MiB (`25 × 1024 × 1024` B). La excepción exige registro firmado en `EXCEPCIONES.md`. El control está en `test_web.py`, constante `TOPE_FICHERO` y `test_cada_fichero_bajo_el_tope` (comparación estricta `<`).
- Recibo: GitHub API devolvió el código fuente de `test_web.py`, `config/modelos-rack.json` y `public/cerebros.json` el 2026-10-19. Tamaños de activos y entrega HTTP desde Cloudflare: `NO_DATA`, causa: esta sesión no tiene checkout de WEB ni una vía Cloudflare de lectura/medida; el sandbox también denegó el socket HTTP. Ruta y tamaño de ficheros de modelo chunked: `NO_DATA`; no se afirman modelos actualmente servidos.

## GitHub · API del registro

Rutas de forma utilizadas: Contents API para leer fuentes; Issues API para el recibo de contrato; Git References/Contents API para ramas y ficheros de propuesta; Pull Requests API para abrir borradores. El techo de operación es el rate limit de la API y sus límites secundarios; documentación oficial: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api. El techo primario general publicado para autenticación personal es 5.000 solicitudes/hora. La cuota restante del conector actual: `NO_DATA`, causa: el recibo de la integración no expone cabeceras `x-ratelimit-*` ni el modo de autenticación.

Recibo medido en esta sesión, 2026-10-19: un comentario de aceptación de contrato, un PR de la joya attention-selector y un PR de forma del LAB, más un PR de APP. Los tres PR están abiertos en borrador, sin fusión. El dato es el número de operaciones completadas, no un chequeo de cuota restante.

## Rack · sensores y endpoints

- Temperatura: `/sys/class/hwmon/*/temp*_input`; el comando registrado encontró 10 canales.
- Energía del paquete: `/sys/class/powercap/intel-rapl:0/energy_uj`; el contador está presente.
- Runner: `http://127.0.0.1:11434/api/tags` y `/api/version`; intentos con timeout de 2 s: `NO_DATA`, causa: el sandbox denegó el acceso al socket local.
- App: `http://127.0.0.1:8740/`; intento HTTP: `NO_DATA`, causa: el sandbox impidió abrir el socket.
- TTL: `TTL_DAYS=7` propuesto en [RACK.md](RACK.md). La transición a `STALE` se calcula al leer con `bin/rack_status.py`; no altera observaciones anteriores.

La presencia en sysfs es `LIVE` a la fecha y hora del recibo. La disponibilidad de los servicios no se deduce de un proceso no visible. La guía de medición térmica y energética está en [ENERGY_BUDGET.md](ENERGY_BUDGET.md).

## Medido desde el rack · segundo ojo (Claude, 2026-10-19 UTC)

Completa los `NO_DATA` de arriba que tenían por causa el sandbox. Solo lectura; cada cifra con su comando.

| Vía | Medida | Comando |
|---|---|---|
| Cloudflare · `/cerebros.json` | `LIVE` · 200 · 11.222 B (= `main` `9a72d4d`) · `cf-cache-status: HIT` | `curl -sI https://preceptoros.org/cerebros.json` |
| Cloudflare · `/llms.txt` | `LIVE` · 200 · 6.355 B | `curl -s -o /dev/null -w '%{http_code} %{size_download}' https://preceptoros.org/llms.txt` |
| Cloudflare · `/config/modelos-rack.json` | 404: **no se sirve** (vive fuera de `public/`) | ídem |
| Cloudflare · `/mcp-manifest.json` | 404: **no se sirve** (discrepancia 3 del spec, confirmada) | ídem |
| Cloudflare · main entero | 16/16 rutas iguales byte a byte a `main` `9a72d4d` (V10, Comando #13) | `sha256sum` de cada ruta frente a `git show 9a72d4d:public/<ruta>` |
| GitHub · cuota REST | `LIVE` · límite 5.000/h · 5.000 restantes en el momento de medir | `gh api rate_limit` |
| Rack · runner local | `LIVE` · responde · versión 0.40.3 · 45 modelos instalados | `curl -s --max-time 2 http://127.0.0.1:11434/api/version` y `/api/tags` |
| Rack · app | `LIVE` · HTTP 200 | `curl -s -o /dev/null -w '%{http_code}' --max-time 2 http://127.0.0.1:8740/` |
| Rack · sensores | `LIVE` · 10 canales de temperatura · contador de energía presente | `ls /sys/class/hwmon/*/temp*_input`, `ls /sys/class/powercap/` |

La cuota «restante» es una foto del momento, no una garantía; la entrega desde Cloudflare depende de la caché (`HIT` medido).
