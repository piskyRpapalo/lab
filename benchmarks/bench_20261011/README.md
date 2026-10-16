# bench 2026-10-11 · embedding and reading benchmarks (measured)

Machine: the ecosystem's node (rack). Date: 2026-10-11.

| Model | Measured |
| :--- | :--- |
| embeddinggemma-2 | prompt-pair 512: 6459 tok/s · sanity cosine similarity 0.908 |
| LLaDA2.2-mini | NO DATA — not runnable in this session (cause in session log) |
| DiffusionGemma | NO DATA — not runnable in this session (cause in session log) |
| ALoDLM | NO DATA — not runnable in this session (cause in session log) |

Each measured figure carries its session's raw telemetry sample. NO_DATA
rows carry the cause, never a guess.

Raw JSON: `bench_20261011_resultados.json` (sha256 26e61fb7f56d9da3d6820ea71b39cf43c1b7454ee75d79f08e314004a74c707b).

## Proveniencia del registro

Las cifras y causas resumidas arriba corresponden al JSON local `bench_20261011_resultados.json` (SHA-256 declarado arriba). Allí se registran fecha/hardware, build de llama.cpp, modelo/sha, método y comando en `bench_20261011_resultados.json:1-66`; el comando está en `:34`, las cifras del embedding en `:21-29` y las causas NO_DATA en `:43-61`. La tabla arriba es el resumen publicado; no se reejecutó ninguna prueba.
