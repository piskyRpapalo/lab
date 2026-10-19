# ENERGY_BUDGET · propuesta REQUIERE_FIRMA

Fecha de recibo: 2026-10-19 UTC. Este archivo separa capacidad de sensor, tráfico y energía por token. Una ausencia se conserva como `NO_DATA` con causa. No se publican identificadores privados ni texto de inferencia.

## Contrato de medida

`J_net/token = (ΔE_paquete_J − P_idle_W × Δt_s) / tokens_generados`

La lectura debe cubrir la misma generación; `ΔE_paquete_J` sale de `energy_uj` dividido entre 1.000.000. `P_idle_W` se mide en una ventana de control inmediatamente anterior, de igual duración, con el mismo sensor y configuración. Si el contador se reinicia, desborda, falta la ventana de control o no existe conteo de tokens del runner, el resultado entero es `NO_DATA`. La energía de paquete no representa el consumo de pared ni permite atribuir energía a otros dispositivos.

## Recibo de capacidad local

- Fecha: 2026-10-19 10:28 UTC.
- Comando exacto:
  `python3 -c 'import pathlib; h=pathlib.Path("/sys/class/hwmon"); print("hwmon_temp_channels="+str(sum(len(list(p.glob("temp*_input"))) for p in h.glob("hwmon*")))); print("rapl_package_counter="+str(pathlib.Path("/sys/class/powercap/intel-rapl:0/energy_uj").exists()))'`
- Resultado: 10 canales térmicos visibles en sysfs; contador RAPL de energía de paquete presente.
- Conteo/token y energía neta/token: `NO_DATA`, causa: el endpoint de inferencia local no se pudo consultar desde este sandbox; el intento de loopback fue denegado por la política de sockets. No se generó tráfico ni se leyó un valor de energía antes/después.
- Comando de disponibilidad del endpoint:
  `python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/api/tags",timeout=2)' `
  Resultado: `NO_DATA` por acceso de socket local no permitido en este entorno.
- Sensor de pared: `NO_DATA`, causa: no hay ruta medida a un medidor de pared en esta sesión.

La presencia del contador RAPL solo certifica que la ruta de lectura existe; no constituye una medición de energía de inferencia. Antes de publicar cualquier número J/token, adjuntar el comando exacto de captura, la duración, el contador inicial/final, el control idle y el contador de tokens del mismo proceso.

## Vías que alimentan al modelo local

La medición se conserva en LAB como registro para el modelo pequeño local. El runner consume recibos; no envía prompts, respuestas ni telemetría fuera del equipo. Sin un contador accesible, el estado permanece `NO_DATA`.
