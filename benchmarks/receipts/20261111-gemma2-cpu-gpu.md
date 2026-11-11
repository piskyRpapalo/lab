# Local Gemma2 CPU/GPU device pilot · 2026-11-11

**Agent:** Codex · GPT-6 · **scope:** physical Beelink device, local Ollama, two repeats per backend. The canonical LAB F6 is live device benchmarks; this is a new, smaller and clearly bounded observation, not F6-01 A2A economic fencing.

**Hardware class:** AMD Ryzen 7 255 / Radeon 780M · x86_64. **Model:** gemma2:2b-instruct-q4_K_M (Ollama metadata family `gemma2`, 2.6B, Q4_K_M). Only the enrolled rack host was measured; other devices were not instrumented.

**Protocol:** identical synthetic JSON-generation task on every run (digest preserved, prompt text excluded), 48 generated tokens, `temperature=0`, `seed=23`, `num_ctx=512`, `num_thread=4`. CPU forces `num_gpu=0`; GPU requests `num_gpu=99`; observed Ollama `ps` confirmed actual CPU / GPU route. Test order GPU → CPU → CPU → GPU. Each run started with no model loaded; each run used `keep_alive=40s` and explicitly unloaded the model afterward (0 resident models).

**Results:**

| Backend | Generation tokens/s | Total wall time (incl. load) |
|---|---:|---:|
| GPU #1 | 40.11 | 2.504 s |
| CPU #1 | 27.47 | 3.780 s |
| CPU #2 | 27.68 | 4.014 s |
| GPU #2 | 40.26 | 2.495 s |

Average generation rate GPU=40.185 tokens/s, CPU=27.575 tokens/s; this is approximately 1.46x as many tokens/s for the GPU under these **small-sample** conditions. Cold-load wall time is a different metric from steady generation throughput; do not equate them. The JSON receipt includes observed VRAM allocation (GPU ~1.81 GB, CPU zero) and the timestamp scope.

**Evidence:** [machine-readable aggregate receipt](20261111-gemma2-cpu-gpu.json). No raw prompts, model answers, user data, internal addresses or personal identities are included.

**NO_DATA:** multiple prompt types, long-context quality, sustained thermals, power/solar fraction, CPU/GPU energy efficiency, other nodes, external independent replication, and normal human-perceived response quality. This benchmark does not authorize a model promotion, a legal-compliance claim or an idle-process kill.

**Next:** version an approved multi-prompt offline harness and measure temperature/power only once the metering adapter is validated; compare with dated historical Vulkan/llama-bench results only when workload and denominator are commensurate.
