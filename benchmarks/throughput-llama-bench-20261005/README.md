# Local models llama-bench series · 2026-10-05
Benchcard: machine=x86-Beelink · Radeon 780M | date=2026-10-05 | runner=llama-b10068 · Vulkan | quant=NO_DATA (quant absent from card) | sha256=008c0a1f50eed119739894be425da42285e422e392abe022f6cedbab350a58b4
Broadcast receipt: figure=NO_DATA (two distinct reports) | model=Multiple local models | machine=x86-Beelink · Radeon 780M | date=2026-10-05 | sha256=008c0a1f50eed119739894be425da42285e422e392abe022f6cedbab350a58b4

This card preserves two `llama-bench` reports as a separate historical series; it does not re-run or correct the 2026-09-13 Ollama series.

- Date: 2026-10-05. Machine: x86-Beelink per the signed order; the reports declare Vulkan/Radeon 780M. Exact CPU: `NO_DATA` in both sources.
- Runner/axis: `llama-b10068`, Vulkan, `-p 128 -n 32 -r 2 -ngl 99`; generation `tg32` and prefill `pp128`, tok/s. Binary hash and blob hashes: `NO_DATA` in the reports.
- Sources: `p0x/BENCH_TODOS_2026-10-05.md:1-55`, SHA-256 `008c0a1f50eed119739894be425da42285e422e392abe022f6cedbab350a58b4`; `p0x/BENCH_RIVAL_2026-10-05.md:1-25`, SHA-256 `aa287e81ff6ac9b48e234806003a504fa4714344fa2c838c8ce4f6d72c727e5b`.
- FIRMO: the Sovereign declares this series signed in the 2026-10-17 recovery order. The report digests identify files; they are not human signatures; the individual historical signature artifact is `NO_DATA` in the cited sources.

| Published model | Prefill pp128 tok/s | Generation tg32 tok/s | Source |
|---|---:|---:|---|
| Qwen3-Coder-30B-A3B | 184.24 ± 1.85 | 30.65 ± 0.37 | `BENCH_TODOS:24-25` |
| Qwen3-4B | 432.78 ± 1.46 | 26.72 ± 0.12 | `BENCH_TODOS:15-16` |
| Qwen3.6-35B-A3B | 178.06 ± 13.34 | 19.70 ± 0.02 | `BENCH_RIVAL:21-24` |
| Swift-Qwen3.8-27B | 63.86 ± 0.92 | 3.68 ± 0.00 | `BENCH_TODOS:33-34` |

The Ollama and llama-bench series have different runners, dates, and axes; they are not ranked against each other and do not replace one another. The own candidates benchmark of 2026-10-16 is in [its independent card](../qwen36-35b-20261016/README.md); its measured and declared figures remain separate.

Temperature, seed, quality, conversational response, and consumption: `NO_DATA`; these runs measure throughput. Vendor figures are not incorporated as local measurements.
