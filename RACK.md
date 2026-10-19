# RACK · propuesta REQUIERE_FIRMA

Fecha de corte del recibo: 2026-10-19 UTC. Esta ficha define la forma de un registro de sensores y endpoints. El estado observado solo vale para el comando y la fecha indicados.

## Frescura

`TTL_DAYS = 7` (entero exacto; 604800 segundos). Para una observación con `observed_at` UTC, su sello calculado es `STALE` si `now_utc - observed_at >= TTL_DAYS × 86400`; antes de ese límite conserva el sello observado. El cálculo se ejecuta al leer con `python3 bin/rack_status.py --observed-at <ISO-8601-UTC>`. Una lectura fallida o ausente queda `NO_DATA` con causa y no adquiere una fecha ficticia. El script no modifica el recibo de origen.

## Rutas medidas en esta sesión

| Vía | Ruta consultada | Resultado | Evidencia |
|---|---|---|---|
| Sensores térmicos | `/sys/class/hwmon/*/temp*_input` | LIVE · 10 canales presentes; no se publican valores en este recibo | Comando Python en [ENERGY_BUDGET.md](ENERGY_BUDGET.md), 2026-10-19 |
| Energía de paquete | `/sys/class/powercap/intel-rapl:0/energy_uj` | LIVE · contador presente; energía de inferencia NO_DATA | Comando Python en [ENERGY_BUDGET.md](ENERGY_BUDGET.md), 2026-10-19 |
| Inferencia local | `http://127.0.0.1:11434/api/tags` | LIVE · HTTP 200, 45 entradas sin nombres | Medición live de 2026-10-19T12:04:41Z abajo |
| App local | `http://127.0.0.1:8740/` | LIVE · HTTP 200 | Medición live de 2026-10-19T12:04:41Z abajo |

La lectura de sysfs se considera fresca durante siete días desde esta medición. La falta de acceso a un endpoint no se transforma en `ERROR` del servicio: describe solo esta vía de observación. No se guardan direcciones fuera de loopback, puertos privados, claves ni nombres de modelos.

## Re-medición · 2026-10-19T12:04:41Z

- `/sys/class/hwmon/*/temp*_input`: `LIVE`; 10 canales, 10 valores legibles.
- `/api/tags`: `LIVE`, HTTP 200, 45 entradas sin nombres; `/api/version`: `LIVE`, HTTP 200.
- PWA `/`: `LIVE`, HTTP 200.
- RAPL `energy_uj`: el archivo existe, pero la lectura es `NO_DATA`, causa: `PermissionError`.
- `/metrics`: HTTP 404; no expone contador de tokens. No se hizo una inferencia de prueba ni se entrenó LoRA.

Comandos exactos y tamaños de respuesta: [recibo de validación](benchmarks/ideas18oct-validation-20261019/README.md). La observación hereda `TTL_DAYS=7` y pasa a `STALE` al cumplir 604.800 segundos.
