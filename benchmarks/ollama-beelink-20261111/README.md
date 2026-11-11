# LAB · Ollama throughput · 2026-11-11 · Beelink

**Status: MEASURED (local generation speed only)**. This is a public, scrubbed readout of 12 completed samples from six installed models. No raw prompts, responses, credentials, private file paths or hardware identifiers are published.

## Summary (tokens generated per second)

| Installed model | Run 1 | Run 2 | Arithmetic mean |
|---|---:|---:|---:|
| Gemma2 2B (`gemma2:2b`) | 40.685 | 40.611 | **40.648** |
| Qwen3 1.7B (`qwen3:1.7b`) | 55.795 | 55.791 | **55.793** |
| Mistral 7B Q4_K_M (`mistral:7b-instruct-v0.3-q4_K_M`) | 17.496 | 17.490 | **17.493** |
| Qwen3.5 9B (`qwen3.5:9b`) | 13.809 | 13.836 | **13.8225** |
| Mistral Nemo 12B Q4_K_M (`mistral-nemo:12b-instruct-2407-q4_K_M`) | 10.884 | 10.915 | **10.8995** |
| Qwen2.5 14B (`qwen2.5:14b`) | 9.082 | 9.021 | **9.0515** |

## Machine and exact method
- Source: direct SentinelX script execution on the **Beelink class** device; AMD Ryzen 7 255, Radeon 780M integrated graphics, 57 GiB RAM. Date: 2026-11-11, 08:38–08:40 UTC. Ollama v0.40.3, local loopback API `/api/generate`; no downloaded models.
- Fixed **synthetic** prompt (not published), identical string across every sample, Spanish question on an elementary astronomy fact. Prompt raw bytes and model replies are not stored.
- Request settings: `stream=false`, `think=false`, `temperature=0`, `seed=42`, `num_predict=64`, `num_ctx=2048`, `keep_alive="0"`. Each model was run twice sequentially, not in parallel.
- Metric: `eval_count * 1e9 / eval_duration` (nanoseconds) as reported by Ollama, rounded to three decimals. Every sample generated exactly 64 tokens and finished with `done_reason=length`. This is **not** end-to-end responsiveness, model quality, or sustained-load stability.
- Memory: 57 GiB physical; available memory before the run ~43 GiB. Exact CPU/GPU split, power, thermals: **NO_DATA** (no backend/sensor receipt). GPU support being present does not demonstrate GPU execution.
- Comparison with 2026-11-10: **NO_DATA** (exact prompt/harness equality not established), even when speed values resemble one another. OneXStation and Jetson **NO_DATA** (not attached as SentinelX hosts for this run).
- DFA-B5 family-blind pilot was **not rerun**; prior reported state 4/8, one invalid, remains **RED**. This report does not claim quality, DFA certification, or any benchmark of security.

## Each measured sample

| Model | Trial | Gen tokens | Gen time (s) | Wall time (s) | Load time (s) | Prompt tokens |
|---|---:|---:|---:|---:|---:|---:|
| Gemma2 2B | 1 | 64 | 1.573049 | 3.846 | 2.147604 | 22 |
| Gemma2 2B | 2 | 64 | 1.575927 | 2.862 | 1.167422 | 22 |
| Qwen3 1.7B | 1 | 64 | 1.147058 | 2.171 | 0.917592 | 33 |
| Qwen3 1.7B | 2 | 64 | 1.147134 | 2.172 | 0.919710 | 33 |
| Mistral 7B | 1 | 64 | 3.658007 | 7.788 | 3.903749 | 23 |
| Mistral 7B | 2 | 64 | 3.659329 | 5.040 | 1.155750 | 23 |
| Qwen3.5 9B | 1 | 64 | 4.634812 | 11.602 | 6.427650 | 27 |
| Qwen3.5 9B | 2 | 64 | 4.625657 | 7.648 | 2.487923 | 27 |
| Mistral Nemo 12B | 1 | 64 | 5.880034 | 8.425 | 2.227342 | 17 |
| Mistral Nemo 12B | 2 | 64 | 5.863646 | 8.387 | 2.207178 | 17 |
| Qwen2.5 14B | 1 | 64 | 7.046904 | 15.492 | 7.969161 | 46 |
| Qwen2.5 14B | 2 | 64 | 7.094697 | 15.290 | 7.718682 | 46 |

## Provenance and integrity

- Private local source receipt: `hexelion.ollama.throughput.v1` (original retained on operator's device, not uploaded).
- SHA-256 of **private, unredacted local receipt**: `317a6a163c1b88f6fff64e514e63a6cff12ef3b70dd93d33663256448e9c8950`. A digest establishes byte identity, **not** a signature or independent validation. It is not the digest of this published text.
- Original measured receipt had 12 samples, six models, and no raw model answers or prompts.
- Two corresponding preliminary Command receipts: [run A](https://github.com/piskyRpapalo/buzon/issues/53#issuecomment-6791242497) and [run B](https://github.com/piskyRpapalo/buzon/issues/53#issuecomment-6791250934) (Command links may require permission).
- Publish method: public read-only report. No promotion to `main` without the signing process.

**Agent:** Codex · **Model:** GPT-6 · **Run:** SentinelX local Beelink, 2026-11-11.

Public discussion: https://github.com/piskyRpapalo/lab/issues/164
