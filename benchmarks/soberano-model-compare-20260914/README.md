# Model comparison and judgment — 2026-09-14
Benchcard: machine=Ryzen 7 255 · Radeon 780M | date=2026-09-14 | runner=NO_DATA (runner absent or not singular) | quant=NO_DATA (quant absent from card) | sha256=1fcf95e4933071bffa8a9ba4d7975fbdce8071f7eba63e474838cc23084a3089

Sources: `~/p0x/soberano-bench/minicpm5_veredicto.md:1-35` (SHA-256 `1fcf95e4933071bffa8a9ba4d7975fbdce8071f7eba63e474838cc23084a3089`) and `minicpm5_resultados.json` (SHA-256 `955721a3e11e599be024b92168788222a6e87033b1262ba20bad45b1d9bd305f`); harness `minicpm5_bench.py` SHA-256 `8a261efb0d2bdc6b92d141aa28e4e521cf8e3a1bf8f9560e3c4598a2f34e615e`, prompts SHA-256 `eaafecf001f2004cee838c3951be1613e1e3debdbc9dc590bab8ceed099b614a`.

Declared hardware: Ryzen 7 255, Radeon 780M, 16 threads; 100% GPU, context 8192, 40 prompts/model (20 orchestration + 20 user), three complete batches; the card reports the last batch and that all three stayed within 3%. The exact binary/runtime hash is **NO_DATA**. Measured results (median tok/s; median TTFT; judgment over 38 classifiable responses):

| Model | tok/s | TTFT ms | judgment | orchestration | user | Source |
|---|---:|---:|---:|---:|---:|---|
| Qwen3 4B | 25.28 | 180.3 | 10/38 | 2/20 | 8/20 | `minicpm5_resultados.json:20-56` |
| MiniCPM5 2B Q4_K_M | 57.17 | 86.3 | 23/38 | 14/20 | 9/20 | `minicpm5_resultados.json:310-351` |
| Llama 3.2 3B | 35.32 | 101.8 | 13/38 | 9/20 | 4/20 | `minicpm5_resultados.json:605-651` |
| Qwen2.5-Coder 3B | 48.56 | 106.0 | 23/38 | 15/20 | 8/20 | `minicpm5_resultados.json:905-951` |

Additional numeric criteria for MiniCPM5: 66.74 turns/minute in the orchestration family; RSS 2.704 GB is an aggregate of simultaneous processes and does not attribute the memory of weights hosted on the GPU; the measured context was 8192, so RSS of model and context 16384 are **NO_DATA**. Judgment: 38 cases score, although 40/model were launched; cause of the denominator: the harness leaves two cases out of the hit count. Do not use this set as a vision benchmark or as an open-facts benchmark: it measures speed, pacing, and human criteria over fixed prompts.
