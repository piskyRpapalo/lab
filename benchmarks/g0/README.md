# G0: CPU/Vulkan comparison, harnesses, and local engine · 2026-07-18
Broadcast receipt: figure=NO_DATA (CPU/Vulkan multiple rows) | model=Qwen3-Coder 30B A3B Q4_K_M | machine=Radeon 780M · 16 CPU threads | date=2026-07-18 | sha256=f53ad0aef08cb17a6f30b696124531737744ee7c0eb6fd2a6f124a0d781c6836

## Yardstick A — llama-bench (2026-07-18)

Source: `~/p0x/deploy/soberano/BENCH_G0.md:1-31`; SHA-256 `f53ad0aef08cb17a6f30b696124531737744ee7c0eb6fd2a6f124a0d781c6836`. Model Qwen3-Coder 30B A3B Q4_K_M, llama.cpp prebuilt b10068. CPU 16 threads versus Vulkan with iGPU Radeon 780M; 3 runs per configuration. Raw data: `~/p0x/mente/telemetria/soberano_bench_g0.json:1-220`, SHA-256 `0716204d001dca11ea2f5ce9b11801e3f026efb8909f65736a5ac3b339d927e3`.

| Test | CPU | Vulkan | Measured ratio |
|---|---:|---:|---:|
| pp512 tok/s | 99.93 ± 11.24 | 357.70 ± 2.52 | 3.58× |
| tg128 tok/s | 9.90 ± 0.30 | 32.49 ± 0.03 | 3.28× |

b10068 CPU/Vulkan binaries: `~/p0x/soberano-bench/bin/llama-b10068-bin-ubuntu-x64.tar.gz` SHA-256 `6bf3d20de562e4df230f1a7c54fb7a06a80c7ff40f5311c953e8255744be4eb2`; Vulkan variant SHA-256 `713641920dce6c8efb953ebc9ffa309977e200cec5e182e6ad0e8b086203cdc3`. The source records no hash of the extracted executable nor the full flags of each call: **NO_DATA**.

## Yardstick B — harness smoke tests

Source `~/p0x/deploy/soberano/HARNESS_G0.md:1-56`, SHA-256 `fee8670f8c6f78cc549e69662692314f5d63c34b5cb8108c156a40b3c512ee5d`. Date 2026-07-18. Three CLIs against the local engine answered `OK`: Aider (~600 prompt tokens), OpenCode (~7,100), Qwen Code (~15,000); CPU. The first Qwen Code attempt expired at 120 s. This is an installation/trivial-read test, not one of editing quality or tasks; exact commands, builds, and hashes per harness **NO_DATA**.

## Yardstick C — local engine smoke test

Source `~/p0x/deploy/soberano/MOTOR_LOCAL.md:1-40`, SHA-256 `4ced934ef4cdcafe8de20e35ac3fa08b12b97a25032ba3531959eca852260ac8`. Date 2026-07-18, Qwen3-Coder 30B Q4_K_M via local API, CPU, requested context 16,384. One call: 30 prompt tokens in 0.30 s; 78 output tokens in 3.13 s = 24.9 tok/s; 19.45 s cold total. Reported memory: 20 GB by Ollama, cgroup 36.7 GiB, system 57 GiB with ~33 GiB available. Do not mix this single call with G0; request capture/hash and repetition **NO_DATA**.
