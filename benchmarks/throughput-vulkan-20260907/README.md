# Serie Vulkan de throughput · 2026-09-07

Esta ficha conserva las siete filas ordenadas del registro local de throughput; no vuelve a ejecutar ni recalcula la medida.

- Fecha y eje: 2026-09-07; prefill/prompt y generación, en tok/s; una muestra por fila; contexto 32.768.
- Máquina/backend: Radeon 780M por Vulkan. CPU y memoria exactas: `NO_DATA` en los metadatos visibles de esta ficha.
- Runner: serie Ollama, según el encargo firmado. Versión y hash del runner: `NO_DATA` en el registro fuente.
- Juez: Qwen2.5:7b, familia distinta, con `MAX_LOADED_MODELS=1`, según el encargo firmado; no evalúa su propio piso.
- Fuente local: `p0x/no-publicar/mudanza-20261011/cae/cerebros.json:1`, SHA-256 `a7450c9c387d43305035419a8632f1b091e36c0e82a96bdf773680906a51133d`. Cada fila corresponde al índice indicado bajo `/cerebros/` en ese JSON de una línea. Los identificadores locales se omiten por privacidad; no se copia el JSON.
- FIRMO: el Soberano declara esta serie firmada en el encargo de recuperación de 2026-10-17. Artefacto histórico individual de firma: `NO_DATA` en la fuente citada; no se afirma verificación criptográfica independiente.

| Fila fuente | Prompt tok/s | Generación tok/s |
|---:|---:|---:|
| 0 | 1.017,39 | 55,15 |
| 1 | 228,75 | 16,79 |
| 2 | 248,99 | 16,36 |
| 3 | 355,67 | 33,29 |
| 4 | 72,27 | 31,78 |
| 5 | 110,65 | 16,75 |
| 6 | 440,39 | 28,53 |

Estas cifras son throughput de una sesión, no calidad, latencia de conversación ni un yardstick intercambiable con `llama-bench`. El archivo original contiene identidades locales y queda fuera del repo público.
