# G0: comparación CPU/Vulkan, harnesses y motor local

## Yardstick A — llama-bench (2026-07-18)

Fuente: `~/p0x/deploy/soberano/BENCH_G0.md:1-31`; SHA-256 `f53ad0aef08cb17a6f30b696124531737744ee7c0eb6fd2a6f124a0d781c6836`. Modelo Qwen3-Coder 30B A3B Q4_K_M, llama.cpp prebuilt b10068. CPU 16 hilos frente a Vulkan con iGPU Radeon 780M; 3 corridas por configuración. Datos crudos: `~/p0x/mente/telemetria/soberano_bench_g0.json:1-220`, SHA-256 `0716204d001dca11ea2f5ce9b11801e3f026efb8909f65736a5ac3b339d927e3`.

| Prueba | CPU | Vulkan | Razón medida |
|---|---:|---:|---:|
| pp512 tok/s | 99.93 ± 11.24 | 357.70 ± 2.52 | 3.58× |
| tg128 tok/s | 9.90 ± 0.30 | 32.49 ± 0.03 | 3.28× |

Archivos binarios b10068 CPU/Vulkan: `~/p0x/soberano-bench/bin/llama-b10068-bin-ubuntu-x64.tar.gz` SHA-256 `6bf3d20de562e4df230f1a7c54fb7a06a80c7ff40f5311c953e8255744be4eb2`; variante Vulkan SHA-256 `713641920dce6c8efb953ebc9ffa309977e200cec5e182e6ad0e8b086203cdc3`. Fuente no registra hash del ejecutable extraído ni flags completos de cada llamada: **NO_DATA**.

## Yardstick B — smoke de harnesses

Fuente `~/p0x/deploy/soberano/HARNESS_G0.md:1-56`, SHA-256 `fee8670f8c6f78cc549e69662692314f5d63c34b5cb8108c156a40b3c512ee5d`. Fecha 2026-07-18. Tres CLIs contra el motor local respondieron `OK`: Aider (~600 tokens de prompt), OpenCode (~7.100), Qwen Code (~15.000); CPU. Primer intento de Qwen Code expiró a 120 s. Es una prueba de instalación/lectura trivial, no de calidad de edición ni de tareas; comandos exactos, compilaciones y hashes por harness **NO_DATA**.

## Yardstick C — smoke del motor local

Fuente `~/p0x/deploy/soberano/MOTOR_LOCAL.md:1-40`, SHA-256 `4ced934ef4cdcafe8de20e35ac3fa08b12b97a25032ba3531959eca852260ac8`. Fecha 2026-07-18, Qwen3-Coder 30B Q4_K_M vía API local, CPU, contexto solicitado 16.384. Una llamada: 30 tokens de prompt en 0,30 s; 78 tokens de salida en 3,13 s = 24,9 tok/s; total frío 19,45 s. Memoria reportada: 20 GB por Ollama, cgroup 36,7 GiB, sistema 57 GiB y ~33 GiB disponibles. No mezclar esta llamada única con G0; captura/hash de solicitud y repetición **NO_DATA**.
