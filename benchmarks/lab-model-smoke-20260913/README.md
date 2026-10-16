# Smoke de cuatro modelos — 2026-09-13

Fuente `~/p0x/soberano-bench/resultados_bench_lab.json:1-60`, SHA-256 `5577c1274eb1814f595c8226572a62745c59a2b99d997ca6d8ea4feb3e349949`; arnés descrito por `bench_modelos_lab.py`, SHA-256 `7d7a3ea21c827fb7c773152a927c633234f5d6eb8b4e50acf8e249a1c434487a`. Hardware, build y hash de modelo **NO_DATA**: el JSON no los fija. El corpus usa el mismo prompt factual sintético para roles; el texto devuelto es un estímulo fijo del ensayo y no una noticia verificada.

| Modelo | tok/s | TTFT s | salida tokens | prompt tokens | tiempo s | Wh | Fuente JSON |
|---|---:|---:|---:|---:|---:|---:|
| Llama 3.2 1B | 58.0 | 0.07 | 17 | 74 | 0.38 | 0.0061 | `resultados_bench_lab.json:10-14` |
| DeepSeek R1 7B | 16.8 | 0.26 | 200 | 52 | 12.18 | 0.1962 | `:15-25` |
| Granite 3 Dense 8B | 15.9 | 0.56 | 40 | 87 | 7.74 | 0.1247 | `:26-36` |
| Swift Qwen 27B | 4.4 | 2.68 | 121 | 119 | 45.54 | 0.7337 | `:37-47` |

`exito=true` mide que la llamada produjo una respuesta, no su veracidad ni cumplimiento semántico. Las respuestas de varios modelos exceden o deforman el formato esperado. Repeticiones, intervalo de incertidumbre y medición independiente de energía **NO_DATA**.
