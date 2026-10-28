# Colony surface benchmark · 2026-10-28
Broadcast receipt: figure=Android browser rAF p05 57.47–57.80 Hz; p50 57.80–58.48 Hz; Chrome package PSS 309029–318545 KiB | model=NO_DATA (not applicable) | machine=Android 13 arm64 handset | date=2026-10-28 | sha256=00d93979f9334c68d905ebe54a7aef567524d5b0b2b7ee549d3f6e209bee36e7
Benchcard: machine=Android 13 arm64 8-core, 12.37 GB; workstation sustained FPS NO_DATA (tab lost focus) | date=2026-10-28 | runner=Node 22.22.1 + Chrome 155 DevTools Protocol | quant=Nearest-rank rAF p50/p05; 2 × 60 s per condition | sha256=3494fa617d434d22d78fcaf79049de3c0688990444665eb5d1f938f5afedcdc9

## Scope and result

The Android browser completed all four surface/preference conditions with two 60-second runs per condition and 8 seconds of warm-up. The live target was `https://preceptoros.org/openworld/`. The app target was `colony/walking_render.html` extracted from app commit [`6dc204e`](https://github.com/piskyRpapalo/PreceptorOS/commit/6dc204ea1982598a45eb78813aeb0f2483a7df3e), served from a temporary local HTTP server. No app or web repository was modified.

| Measured endpoint | Surface | Reduced motion | rAF p50 (Hz) | rAF p05 (Hz) | Intervals | Chrome package PSS median (KiB) |
|---|---|---:|---:|---:|---:|---:|
| Android handset | Live OpenWorld | Off | 57.803 | 57.471 | 7,141 | 312,344 |
| Android handset | Live OpenWorld | On | 58.480 | 57.803 | 7,092 | 309,814 |
| Android handset | App walker fixture | Off | 57.803 | 57.471 | 6,883 | 309,971 |
| Android handset | App walker fixture | On | 58.140 | 57.471 | 7,313 | 309,543 |

The table reports browser `requestAnimationFrame` callback cadence, calculated as the reciprocal of each timestamp delta. It does not measure compositor-presented frames or physical display scanout. Each row pools the raw intervals from both repetitions using nearest-rank quantiles. The source 26-session benchmark index has no shared FPS protocol, so comparison with older FPS values is `NO_DATA` (cause: protocols differ).

## Reduced-motion check

The Chrome DevTools emulation was toggled for each condition and `matchMedia('(prefers-reduced-motion: reduce)')` was checked in every run. The app fixture received 240 deterministic “Next cycle” clicks per run. It emitted 2,151 CSS `transitionrun` events with motion enabled and zero with reduced motion enabled. OpenWorld was observed passively; it emitted zero CSS transition events in both conditions. This confirms the preference reached the browser and the fixture's transition rule; it does not claim that the live page exercised an animated state during this sample.

## Memory scope

Android Chrome package PSS was sampled before, during, and after each 60-second run. The values include the browser package and cannot be attributed to one page or tab. Page JS heap is `NO_DATA`: Chrome returned the identical rounded `performance.memory` value (10,000,000 B) for every observation, which does not resolve actual heap use. The workstation process memory also remains `NO_DATA` because its sustained visible-tab sample was rejected after the tab lost visibility or focus.

## Device census and weakest endpoint

The Android handset profile was recorded without serial or product name: Android 13, arm64, 8 online CPU cores, 12,365,721,600 B total memory, 1080 × 2408 physical pixels, and 480 dpi. `dumpsys display` reported available refresh rates of 60, 90, and 120 Hz; active physical scanout rate is `NO_DATA` (cause: available modes do not identify the active mode; no independent scanout measurement was made). Chrome was version 155.0.8059.84.

The lowest p05 among the sustained, instrumented endpoints is 57.471 Hz on the sole measured endpoint, the Android handset. This is a measured floor for the tested subset, not a fleet-wide ranking. Fleet-wide weakest device remains `NO_DATA`: one Android endpoint was ADB-online; three additional mobile devices appeared on USB without an ADB browser target; seven Tailscale network peers were online without a browser/CDP frame sampler. The workstation's 60-second run lost visibility/focus and was rejected. Peer names, USB IDs, serials, and addresses are omitted.

## Source and visual evidence

The live page returned HTTP 200 during the browser runs. A follow-up GET at 2026-10-28T22:01:12Z returned HTTP 200, 11,823 B, SHA-256 `5aa53bbd5aca5f513660fdd6364c4e6030162eb1b474e419f8c2ea0f468d0f7c`. That follow-up digest does not identify the exact sampled response body; the live source commit is `NO_DATA` because the public surface does not expose it. The app fixture archive SHA-256 is `c65b8561fbf23766631a0b15c60ba4d06df739afedd5c410b750430363500174`; file hashes and commit time are in `evidence/app-source.json`.

Android captures are from the loaded page viewport, without browser chrome. They identify the pages used by the measurement; they are not display-scanout evidence.

| Surface / preference | Capture |
|---|---|
| OpenWorld · reduced motion off | [PNG](evidence/android-openworld-reduce-off.png) |
| OpenWorld · reduced motion on | [PNG](evidence/android-openworld-reduce-on.png) |
| App walker · reduced motion off | [PNG](evidence/android-app-reduce-off.png) |
| App walker · reduced motion on | [PNG](evidence/android-app-reduce-on.png) |

The summary receipt is [`evidence/receipt.json`](evidence/receipt.json); raw frame intervals and memory samples are [`evidence/android-samples.json`](evidence/android-samples.json). Environment and source hashes are [`evidence/environment.json`](evidence/environment.json), [`evidence/live-surface.json`](evidence/live-surface.json), and [`evidence/app-source.json`](evidence/app-source.json). The rejected workstation condition is [`evidence/rack-no-data.json`](evidence/rack-no-data.json). The Android run source snapshot and its reconstructed digest are recorded in the summary; a direct source digest at process start is `NO_DATA` (cause: it was not captured before the run).

## Reproduction

Node 22's built-in WebSocket client, Chrome DevTools Protocol, and ADB were used; no third-party package or user telemetry was involved. The app archive was served over loopback and forwarded to the phone with ADB reverse.

```sh
node benchmarks/colony-surface-20261028/measure.mjs \
  --device=android --duration-ms=60000 --repeat=2 \
  --output=benchmarks/colony-surface-20261028/evidence
python3 benchmarks/colony-surface-20261028/environment.py
python3 benchmarks/colony-surface-20261028/live_surface.py
python3 benchmarks/colony-surface-20261028/summarize.py
```

For the Phase 2 walker regression, the same runner accepts `--web-url=` and `--app-url=` overrides. The default app URL is the local walker fixture; it remains unconnected to production.
