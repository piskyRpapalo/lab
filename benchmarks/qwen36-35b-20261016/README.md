# Qwen 35B-A3B GGUF · local throughput · 2026-10-16
Broadcast receipt: figure=NO_DATA (multiple throughput axes) | model=Qwen 35B-A3B GGUF | machine=Ryzen 7 255 · Radeon 780M | date=2026-10-16 | sha256=0b21525e972670ed59e1812e170b27c26355381f0656ecc4e25617ece7dac58b

Direct measurement over the GGUF already present in `soberano-bench/models/`; it was not copied into the Ollama store. Model of 22,652,396,032 bytes, 35,505,251,456 parameters, SHA-256 `0b21525e972670ed59e1812e170b27c26355381f0656ecc4e25617ece7dac58b`. Raw record and full configuration in [results.json](results.json).

Tool `llama-bench`, build `01041db99dae68529db58c6fc692a9ca623b30a2`, build number 10708; executable SHA-256 `f10d18211b422432c79db4e406d7b8ac353da81b51457c3bc7bc136a23060961`. Machine: AMD Ryzen 7 255, 16 threads; Radeon 780M Graphics (RADV PHOENIX), UMA memory. Input 512 tokens, generation 128, two repetitions per backend, no warmup. `llama-bench` offers no temperature or seed options: NO_DATA / not applicable to this throughput test, which does not evaluate sampling quality.

## Yardstick A · CPU

`n_gpu_layers=0`, 16 threads. Prefill 512: 92.295 tok/s mean, SD 2.249 (samples 90.705 and 93.886). Generation 128: 2.114 tok/s mean, SD 1.747 (samples 0.878 and 3.350). The high generation spread stays visible; it is not replaced by a figure from another run.

## Yardstick B · Vulkan

`n_gpu_layers=99`, device `Vulkan0`, 16 CPU threads declared. Prefill 512: 294.271 tok/s mean, SD 14.632 (samples 283.925 and 304.617). Generation 128: 20.760 tok/s mean, SD 0.197 (samples 20.899 and 20.621). CPU and Vulkan are kept as separate yardsticks.

## Figure published by Unsloth

Unsloth declares up to 220 tokens/s generation for Qwen3.6-35B-A3B with MTP; it is a vendor figure, not measured here, and not directly comparable to this UD-Q4_K_M GGUF without MTP. Source: [Unsloth documentation, MTP Benchmarks section](https://unsloth.ai/docs/models/qwen3.6#mtp-benchmarks). Hardware/configuration comparable to this node: NO_DATA in the published figure.

This card measures synthetic throughput, not conversational utility, quality, temperature, power, consumption, or response rendering. Those fields are NO_DATA with cause: `llama-bench` only runs the throughput cases noted.
