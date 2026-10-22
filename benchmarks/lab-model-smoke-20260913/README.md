# Four-model smoke test — 2026-09-13
Broadcast receipt: figure=NO_DATA (no quality metric) | model=Four local models (labels in card) | machine=NO_DATA (source does not fix hardware) | date=2026-09-13 | sha256=5577c1274eb1814f595c8226572a62745c59a2b99d997ca6d8ea4feb3e349949
Benchcard: machine=NO_DATA (machine class absent from card) | date=2026-09-13 | runner=NO_DATA (runner absent or not singular) | quant=NO_DATA (quant absent from card) | sha256=5577c1274eb1814f595c8226572a62745c59a2b99d997ca6d8ea4feb3e349949

Source `~/p0x/soberano-bench/resultados_bench_lab.json:1-60`, SHA-256 `5577c1274eb1814f595c8226572a62745c59a2b99d997ca6d8ea4feb3e349949`; harness described by `bench_modelos_lab.py`, SHA-256 `7d7a3ea21c827fb7c773152a927c633234f5d6eb8b4e50acf8e249a1c434487a`. Hardware, build, and model hash **NO_DATA**: the JSON does not fix them. The corpus uses the same synthetic factual prompt across roles; the returned text is a fixed stimulus of the trial, not a verified news item.

| Model | tok/s | TTFT s | output tokens | prompt tokens | time s | Wh | JSON source |
|---|---:|---:|---:|---:|---:|---:|---|
| Llama 3.2 1B | 58.0 | 0.07 | 17 | 74 | 0.38 | 0.0061 | `resultados_bench_lab.json:10-14` |
| DeepSeek R1 7B | 16.8 | 0.26 | 200 | 52 | 12.18 | 0.1962 | `:15-25` |
| Granite 3 Dense 8B | 15.9 | 0.56 | 40 | 87 | 7.74 | 0.1247 | `:26-36` |
| Swift Qwen 27B | 4.4 | 2.68 | 121 | 119 | 45.54 | 0.7337 | `:37-47` |

`exito=true` measures that the call produced a response, not its truthfulness or semantic compliance. Several models' responses exceed or deform the expected format. Repetitions, confidence interval, and independent energy measurement **NO_DATA**.
