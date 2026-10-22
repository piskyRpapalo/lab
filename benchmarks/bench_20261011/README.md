# bench 2026-10-11 · embedding and reading benchmarks (measured)
Benchcard: machine=ecosystem node (rack) | date=2026-10-11 | runner=prompt-pair 512 | quant=NO_DATA (quant absent from card) | sha256=26e61fb7f56d9da3d6820ea71b39cf43c1b7454ee75d79f08e314004a74c707b

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

## Record provenance

The figures and causes summarized above correspond to the local JSON `bench_20261011_resultados.json` (SHA-256 declared above). Date/hardware, llama.cpp build, model/sha, method, and command are recorded there in `bench_20261011_resultados.json:1-66`; the command is at `:34`, the embedding figures at `:21-29`, and the NO_DATA causes at `:43-61`. The table above is the published summary; no test was re-run.
