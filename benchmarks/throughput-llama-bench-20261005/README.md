# Serie llama-bench de modelos locales · 2026-10-05

Esta ficha conserva dos informes de `llama-bench` como una serie histórica separada; no reejecuta ni corrige la serie Ollama de 2026-09-13.

- Fecha: 2026-10-05. Máquina: x86-Beelink según el encargo firmado; los informes declaran Vulkan/Radeon 780M. CPU exacta: `NO_DATA` en las dos fuentes.
- Runner/eje: `llama-b10068`, Vulkan, `-p 128 -n 32 -r 2 -ngl 99`; generación `tg32` y prefill `pp128`, tok/s. Hash del binario y hashes de blobs: `NO_DATA` en los informes.
- Fuentes: `p0x/BENCH_TODOS_2026-10-05.md:1-55`, SHA-256 `008c0a1f50eed119739894be425da42285e422e392abe022f6cedbab350a58b4`; `p0x/BENCH_RIVAL_2026-10-05.md:1-25`, SHA-256 `aa287e81ff6ac9b48e234806003a504fa4714344fa2c838c8ce4f6d72c727e5b`.
- FIRMO: el Soberano declara esta serie firmada en el encargo de recuperación de 2026-10-17. Las huellas de los informes identifican archivos, no son firmas humanas; el artefacto histórico individual de firma queda `NO_DATA` en las fuentes citadas.

| Modelo publicado | Prefill pp128 tok/s | Generación tg32 tok/s | Fuente |
|---|---:|---:|---|
| Qwen3-Coder-30B-A3B | 184,24 ± 1,85 | 30,65 ± 0,37 | `BENCH_TODOS:24-25` |
| Qwen3-4B | 432,78 ± 1,46 | 26,72 ± 0,12 | `BENCH_TODOS:15-16` |
| Qwen3.6-35B-A3B | 178,06 ± 13,34 | 19,70 ± 0,02 | `BENCH_RIVAL:21-24` |
| Swift-Qwen3.8-27B | 63,86 ± 0,92 | 3,68 ± 0,00 | `BENCH_TODOS:33-34` |

Las series Ollama y llama-bench tienen runners, fechas y ejes distintos; no se ordenan ni se sustituyen entre sí. El benchmark propio de candidatos del 2026-10-16 está en [su ficha independiente](../qwen36-35b-20261016/README.md); sus cifras medidas y declaradas permanecen separadas.

Temperatura, semilla, calidad, respuesta conversacional y consumo: `NO_DATA`; estas corridas miden throughput. Las cifras de proveedores no se incorporan como mediciones locales.
