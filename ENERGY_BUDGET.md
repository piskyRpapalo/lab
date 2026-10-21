# ENERGY_BUDGET · proposal REQUIRES_FIRMA

Receipt date: 2026-10-19 UTC. This file separates sensor capability, traffic, and energy per generated token. Missing evidence remains `NO_DATA` with a cause. Private identifiers and inference text are not published.

## Measurement contract

`J_net/token = (ΔE_paquete_J − P_idle_W × Δt_s) / tokens_generados`

The measurement must cover the same generation; `ΔE_paquete_J` is `energy_uj` divided by 1,000,000. Measure `P_idle_W` in an immediately preceding control window of equal duration using the same sensor and configuration. If the counter resets or overflows, the control window is missing, or the runner provides no generated-token count, the entire result is `NO_DATA`. Package energy does not represent wall consumption and cannot attribute energy to other devices.

## Local sensor-capability receipt

- Date: 2026-10-19 10:28 UTC.
- Exact command:
  `python3 -c 'import pathlib; h=pathlib.Path("/sys/class/hwmon"); print("hwmon_temp_channels="+str(sum(len(list(p.glob("temp*_input"))) for p in h.glob("hwmon*")))); print("rapl_package_counter="+str(pathlib.Path("/sys/class/powercap/intel-rapl:0/energy_uj").exists()))'`
- Result: 10 thermal channels visible in sysfs; the RAPL package-energy counter is present.
- Generated-token count and net joules/token: `NO_DATA`; cause: the local inference endpoint could not be queried from this sandbox because loopback socket access was denied by policy. No inference traffic was generated and no before/after energy value was read.
- Endpoint availability command:
  `python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/api/tags",timeout=2)'`
  Result: `NO_DATA` because local socket access is unavailable in this environment.
- Wall-power meter: `NO_DATA`; cause: no measured path to a wall-power meter was available in this session.

The presence of the RAPL counter confirms only that a read path exists; it is not an inference-energy measurement. Before publishing any J/token value, attach the exact capture command, duration, initial and final counter values, idle control, and generated-token count from the same process.

## Local model input

The measurement remains in the lab as a record for the local small model. The runner consumes receipts and does not send raw inputs, outputs, or sensor readings outside the machine. Without an accessible counter, the state remains `NO_DATA`.
