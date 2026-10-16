# Qwen 35B-A3B GGUF · throughput local · 2026-10-16

Medición directa sobre el GGUF ya presente en `soberano-bench/models/`; no se copió al almacén de Ollama. Modelo de 22,652,396,032 bytes, 35,505,251,456 parámetros, SHA-256 `0b21525e972670ed59e1812e170b27c26355381f0656ecc4e25617ece7dac58b`. Registro crudo y configuración completa en [results.json](results.json).

Herramienta `llama-bench`, build `01041db99dae68529db58c6fc692a9ca623b30a2`, build number 10708; ejecutable SHA-256 `f10d18211b422432c79db4e406d7b8ac353da81b51457c3bc7bc136a23060961`. Máquina: AMD Ryzen 7 255, 16 hilos; Radeon 780M Graphics (RADV PHOENIX), memoria UMA. Entrada 512 tokens, generación 128, dos repeticiones por backend, sin warmup. `llama-bench` no ofrece opciones de temperatura ni semilla: NO_DATA/no aplican a esta prueba de throughput, que no evalúa calidad de muestreo.

## Yardstick A · CPU

`n_gpu_layers=0`, 16 hilos. Prefill 512: 92.295 tok/s media, SD 2.249 (muestras 90.705 y 93.886). Generación 128: 2.114 tok/s media, SD 1.747 (muestras 0.878 y 3.350). La alta dispersión de generación queda visible; no se sustituye por una cifra de otra corrida.

## Yardstick B · Vulkan

`n_gpu_layers=99`, dispositivo `Vulkan0`, 16 hilos CPU declarados. Prefill 512: 294.271 tok/s media, SD 14.632 (muestras 283.925 y 304.617). Generación 128: 20.760 tok/s media, SD 0.197 (muestras 20.899 y 20.621). CPU y Vulkan se conservan como yardsticks separados.

## Cifra publicada por Unsloth

Unsloth declara hasta 220 tokens/s de generación para Qwen3.6-35B-A3B con MTP; es una cifra del proveedor, no medida aquí y no comparable directamente con este GGUF UD-Q4_K_M sin MTP. Fuente: [documentación Unsloth, sección MTP Benchmarks](https://unsloth.ai/docs/models/qwen3.6#mtp-benchmarks). Hardware/configuración comparable a este nodo: NO_DATA en la cifra publicada.

La ficha mide throughput sintético, no utilidad conversacional, calidad, temperatura, potencia, consumo, ni render de respuesta. Esos campos son NO_DATA con causa: `llama-bench` solo ejecuta los casos de throughput señalados.
