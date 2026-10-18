# Vulkan throughput series · 2026-09-07

This card preserves the seven ordered rows of the local throughput record; it does not re-run or recalculate the measurement.

- Date and axis: 2026-09-07; prefill/prompt and generation, in tok/s; one sample per row; context 32,768.
- Machine/backend: Radeon 780M via Vulkan. Exact CPU and memory: `NO_DATA` in the visible metadata of this card.
- Runner: Ollama series, per the signed order. Runner version and hash: `NO_DATA` in the source record.
- Judge: Qwen2.5:7b, a different family, with `MAX_LOADED_MODELS=1`, per the signed order; it does not evaluate its own floor.
- Local source: `p0x/no-publicar/mudanza-20261011/cae/cerebros.json:1`, SHA-256 `a7450c9c387d43305035419a8632f1b091e36c0e82a96bdf773680906a51133d`. Each row corresponds to the indicated index under `/cerebros/` in that one-line JSON. Local identifiers are omitted for privacy; the JSON is not copied.
- FIRMO: the Sovereign declares this series signed in the 2026-10-17 recovery order. Individual historical signature artifact: `NO_DATA` in the cited source; no independent cryptographic verification is claimed.

| Source row | Prompt tok/s | Generation tok/s |
|---:|---:|---:|
| 0 | 1,017.39 | 55.15 |
| 1 | 228.75 | 16.79 |
| 2 | 248.99 | 16.36 |
| 3 | 355.67 | 33.29 |
| 4 | 72.27 | 31.78 |
| 5 | 110.65 | 16.75 |
| 6 | 440.39 | 28.53 |

These figures are one session's throughput, not quality, conversation latency, or a yardstick interchangeable with `llama-bench`. The original file contains local identities and stays out of the public repo.
