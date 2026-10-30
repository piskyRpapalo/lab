# Unified-memory station · tanda 1 · 2026-10-30

Broadcast receipt: figure=33.72 generated units/s median (gpt-oss:120b MXFP4, 65,536 context, three hot runs) | model=gpt-oss:120b MXFP4 · Kimi-Linear 48B-A3B Q4_K_M · Nemotron 30B-A3B Q4_0 | machine=unified-memory station, Strix Halo · Ryzen AI Max+ 395 · Radeon 8060S, 64 GiB carve era | date=2026-10-30 | sha256=NO_DATA (raw session JSON lives in the private fleet sensor record; this card carries runtime digests)

Benchcard: machine=unified-memory station, Strix Halo · Radeon 8060S, 64 GiB carve era | date=2026-10-30 | runner=Ollama 0.40.3, `ollama run --verbose --keepalive=10m --think=false`, three hot runs per model, one fixed Spanish probe | quant=MXFP4 / Q4_K_M / Q4_0 | sha256=NO_DATA (raw session JSON not hashed for this card; runtime digests below)

## Method

Three hot runs per model with the same fixed Spanish probe on local loopback. Rate is the
median of the runtime-reported `eval rate` of three runs; all three samples are shown.
TTFT is time from CLI process start to the first non-white output byte, so it includes the
CLI's own cost. Cold load is the runtime `load duration` of the first inference after
both instances were emptied. Loaded context confirmed through the runtime process list:
65,536 for the three main models. The anchored tag means the model carries the head's
system message; it is not inferred from the model family.

**Launcher incident (registered, not hidden):** the first attempt returned rc=1 on seven
calls before any model load, and the process list was left empty. The first logger did not
capture stderr, so the CLI error is `NO_DATA` for lack of capture. Those attempts were
not counted as measurements. stderr capture was fixed, the run repeated, and every run in
this table finished rc=0.

## Results (64 GiB carve configuration)

| Model | Arch / params | Quant | Disk | Resident / total | Context | Cold load | TTFT hot (cold) | Samples (u/s) | Median | Sensor peaks |
|---|---|---|---:|---:|---:|---:|---|---|---:|---|
| anchored gpt-oss:120b | MoE harmony · 116.8B | MXFP4 | 65.37 GB | 61.65 / 64 GiB | 65,536 | 11.776 s | 208.23 ms (12.752 s) | 33.72, 34.11, 32.44 | **33.72** | CPU 54.1 °C · GPU 54.0 °C · 91.57 W · 2,536 MHz · busy 99% |
| Kimi-Linear 48B-A3B | MoE + MLA + KDA · 49.1B | Q4_K_M | 30.06 GB | 29.47 / 64 GiB | 65,536 | 5.702 s | 118.93 ms (5.847 s) | 61.88, 58.66, 60.20 | **60.20** | CPU 64.1 °C · GPU 60.0 °C · 91.07 W · 2,605 MHz · busy 98% |
| Nemotron 30B-A3B | MoE + Mamba2 + MTP · 32.9B | Q4_0 | 19.06 GB | 18.23 / 64 GiB | 65,536 | 3.903 s | 67.00 ms (4.030 s) | 69.19, 67.22, 67.95 | **67.95** | CPU 58.0 °C · GPU 55.0 °C · 90.47 W · 2,644 MHz · busy 97% |

Temperature/power/frequency peaks are the maximum of 1 s samples across each model's full
sequence — not an average and not a laboratory maximum. `gpu_busy_percent` (99/98/97)
is the runtime's busy sampling; it is kept distinct from the "100% GPU" placement report.

Typed verdicts on the honesty probe: Kimi and Nemotron **PASS** (exact `NO_DATA` answers);
the anchored 120B **PARTIAL** — it passed the sensor honesty probes but exposed internal
reasoning text before its answer, so output containment is not met. The probe asked for a
summary and a three-step instruction; no response text is published.

## Sensor honesty and limits

- lm-sensors absent. Sampled `/sys/class/hwmon/*` every second: `k10temp` (CPU) and
  `amdgpu` (GPU temperature, power, frequency). CPU power: `NO_DATA` — no hwmon sensor
  exposes it.
- `gpu_metrics` blob was read (264 B per read) but not decoded: `NO_DATA` for its
  exclusive fields, cause: no validated parser in this session. Every temperature/power/
  frequency figure above comes from hwmon, never from an interpreted blob.
- VRAM, GTT and OS RAM are kept separate and never summed. GTT peaks: 0.023 GiB on all
  three loads; DRM-reported GTT capacity in this era: 30.72 GiB. Basal DRM before/after:
  VRAM 154,939,392 B, GTT 18,661,376 B, process list empty both times.
- Wall power and net joules/token: `NO_DATA`; the RAPL package counter requires root and
  was denied in this session. The ENERGY_BUDGET contract (control window, token count)
  was not met, so no energy figure is published.

## Exotic-family smokes (compatibility only)

| Candidate | Measured | Verdict |
|---|---|---|
| IBM Granite 4.0 H-Micro Q4_K_M | 3.19B, 1,942,572,096 B on disk; brief load OK, short non-empty answer, 100% GPU, context 65,536, resident 2.9 GB | **PASS_LOAD_SMOKE** |
| RWKV-7 G1j 1.5B Q6_K (community package) | load and short answer OK, 100% GPU, context 16,384, resident 1.4 GB | **PASS_LOAD_SMOKE** |

Both verify engine compatibility only — no quality or competitive-speed claim.

## Unresolved candidates (typed, with causes)

- **Qwen3-Next 80B-A3B Q4_K_M** (48.73 GB artifact): battery incomplete — the probe was
  requested on an instance where the blob was absent; a control generation on the instance
  that held the blob returned empty. Ambiguous, not proven incompatible:
  `NO_DATA` throughput and compatibility, cause: instance separation and empty control run.
- **Qwen3-235B-A22B**: manifest measured at 88,014,818,560 B, within the download ceiling,
  but the runtime pull failed rc=1 before any byte downloaded — multishard GGUF manifest
  unsupported by the runtime registry. `NO_DATA` throughput, cause: registry pull failure.
- **Context 131,072 trial** (separate commission, after the firmware UMA change to a
  96 GiB carve + 15.2 GiB GTT, system left with 30 GB): the anchored 120B loaded at
  131,072 context, 100% GPU, but generation measured 18.68 u/s (vs 33.72 at 65,536) and the
  semantic probe returned an empty completion at the end of a 65,538-token probe.
  Verdict **NO_PROMOVER_131K**; the station reverted to 65,536 and was re-verified.
  Raw trial log: `NO_DATA` here, cause: retained in the private fleet sensor record.

## Model identity (runtime digests, not weight hashes)

| Tag | Runtime digest |
|---|---|
| anchored head tag (gpt-oss:120b) | `c78bcad557e6c1acb6a58f56bf850801fd6bb8e8a175b4bd97c850006eaf4c8d` |
| gpt-oss:120b base | `714d86958b6e870a9320e78126ac1ce3477727a1cd9bf7194b8ace0d84c62fd8` |
| Kimi-Linear 48B-A3B | `6566e16282eeaed8d65ff9ab923d2bb7c931dcc5f251cd9478e3e65e976c30bf` |
| Nemotron 30B-A3B | `5708872d680b139d6b4d3c5e68bef3a4eaa85c3ff31f23cab0b4f24af40304d1` |

## Scope

A sample bench, not an authorization to declare an ideal model. No model was deleted; no
service preference changed; no firmware touched; no port opened; nothing published beyond
loopback. Semantic quality beyond the honesty probes, energy, and cross-device behavior
remain `NO_DATA` with their causes.
