# TRAIN-03 · ONEXSTATION large-model preflight (2026-11-23 UTC)

**Status: PREPARATION / NOT A FINAL BENCHMARK.** This is a dated, source-qualified operational receipt for the existing LAB evidence trail; it is not an additional benchmark runner, model registry, independent judge, or model promotion. **All data below are local ONEXSTATION observations**, except explicitly labeled Hugging Face expected sizes and digests. No prompts, completions, credentials, internal network addresses, owner private filesystem paths, or model binaries are published.

**Role / authority:** Codex GPT-6 · CEREBRO. Sovereign approved the bounded model download, comparison and removal of *Llama 3.3 70B*. No signed deployment, live APP authorization or release is implied. This report stays in a **HITL draft PR** pending exact-head human review.

## Measured hardware and comparison sources

- Host: ONEXSTATION, AMD Radeon 8060S (Strix Halo), unified GPU memory. Kernel-exposed `mem_info_vram_total=103,079,215,104 B`, baseline GPU VRAM about `612,917,248 B`; OS reports ~30 GiB RAM. These are **host measurements**, not measured energy, safety certification, or guaranteed simultaneous model capacity.
- GPU operations use the existing exclusive CineK/Ollama lock and model-by-model unload checks. No concurrent large-model GPU load is authorized by this report.
- Existing pilot harness `train03_brain_pilot.py` SHA-256 `1e3aa556617b654ea8f76e85ad3ec98fb28231d2e5bf52b3d604c3c717cf301f`. DEV fixtures: six simulated cases × two repeats; no real tools, owner grants, or physical effect witness. Nine-case extension uses the *same* six cases and three additional arithmetic cases, two repeats, with case-set digest `6379e0e15f769b826e47b96d27c5020a1b60ec12fbed959f63c082c6d1c5f2db`.
- Local comparison source receipts: `train03-brain-selection-pilot-20261122/final.json`; `train03-new-family-20261122/mistral-medium35-128b-q4xl-dev/final.json`; `train03-new-family-20261122/maxwell-repair-probe-20261123/{first-logit.json,bench-cached-full.json,maxwell-bench-cached-6x2.json}`; local receipt and pinned downloader for Nemotron Super; locally compiled engine hashes below.

## Physical status — UTC snapshots, **not** current-service claims

| Candidate | ONEX evidence | Gate |
| --- | --- | --- |
| GPT-OSS 120B | **12/12 exact and 12/12 strict JSON** on six-case × two DEV harness, median completed answer `8.335 s`, measured peak VRAM `65,393,680,384 B` | PASS_DEV; not proof of general superiority |
| Mistral Medium 3.5 128B Q4XL | **12/18 exact, 18/18 strict JSON** on nine-case × two DEV harness, median completed answer `10.135 s`, peak VRAM `77,517,811,712 B` | PASS_DEV; different case count; do not rank percentage against the six-case pilot |
| Maxwell V1 Flash BF16 | 35/35 checkpoint shards, ~36.81B BF16 parameters loaded in `76.12 s`; generated first correct `2+2=4`. Peak GPU during generation ~78 GB. Cached six-case × two run in progress. | INFERENCE_PASS; QUALITY_NO_DATA(incomplete DEV run). An observed cached first case produced mathematically correct `24` but extraneous reasoning after JSON: **strict JSON FAIL**. |
| Nemotron 3.5 Lightning 30B A3B Q4_0 | GGUF `19,063,900,128 B`, measured SHA-256 `cf548e9348b829334e8fc8512224a284e1df2b1e6e7203f20ee9826800ab5525`. | STAGED; **NO_DATA(first-token-and-quality-not-tested)** |
| Nemotron 3 Super 120B A12B **Q4_K_S** | Hugging Face revision `3aa25691977903b99c15280b71b0fe4860f05bfa`; **78,040,156,800 B expected** as two GGUF shards. At **2026-11-23 00:48:54 UTC**, shard 1 `39,457,130,368 B` complete and SHA-256 verified; shard 2 **18,056,478,720 / 38,583,026,432 B** present as `.part` (download active). | **IN_PROGRESS_DOWNLOAD**, not STAGED, not LIVE, not benchmarked. |

**Pinned Nemotron Super upstream identity (declared LFS expectation, verify physically after transfer):**

| File | Expected bytes | Expected SHA-256 |
| --- | ---: | --- |
| `nvidia_Nemotron-3-Super-120B-A12B-Q4_K_S-00001-of-00002.gguf` | 39,457,130,368 | `4fffa48dfacb58641db547618865556ff86af27ecf2eeebfab79bcae4fa79a41` |
| `nvidia_Nemotron-3-Super-120B-A12B-Q4_K_S-00002-of-00002.gguf` | 38,583,026,432 | `8b92aaea14f4edf1e010c68d7b0c706ee581f675af9950aa9fff289927ef3ad3` |

**Runtime:** a separate `llama-server` compiled from the already staged SenseNova/llama.cpp fork on ONEXSTATION, **CPU build SHA-256** `c2ed584bbd923e7dea381d20248347f460d8a75c61cf5a92c7e1c263678b3618`; **AMD Vulkan build SHA-256** `62eeba7fe7c329b522c3ee27e0b944230d1fa971dcd215a40fab55562a9e0ca5`. Vulkan shader compiler and headers were extracted into owner-local SDK state, **not installed globally**. Executable compilation does **not** prove GGUF compatibility, first-token success, throughput, or AMD offload. This remains an inference gate.

### Owner-ordered disk reclamation (same ONEX, 2026-11-23 00:43:52 UTC)

`llama3.3:70b`, exact Ollama digest `a6eb4748fd2990ad2952b2335a95a7f952d1a06119a0aa6a2df6cd052a93a3fa`, was checked **not loaded**, removed via Ollama `DELETE /api/delete` (**HTTP 200**), and shown absent by subsequent `GET /api/tags`. Observed disk-free difference across this call: **+42,520,473,600 B** even though Nemotron downloaded concurrently; source local `llama33-removal-20261123.json`. Historical Llama scores remain historical data; Llama was removed from the pending arena plan. No other model deletion is authorized or claimed.

## Reproduction and decision gates

1. **Download gate:** retain the original pinned revision; complete both shards; compare exact length and streaming `sha256sum` to each SHA above; emit local `STAGED_PASS` only after both match. `NO_DATA(second_sha256_not_yet_verified)` at this snapshot.
2. **Runtime gate:** wait for exclusive GPU availability, 0 CineK jobs and 0 Ollama-loaded models. Launch one model at a time with owner scopes and finite timeouts. Verify first token and full answer, GPU memory and unload. `NO_DATA(super_120b_and_lightning_first_token)`.
3. **Fairness gate:** identical case-set digest, system contract, temperature/seed, repeats, generation budget, decoding and stop criteria for every model; report strict JSON *separately* from semantic correctness and extra-text normalization, and record no-output/timeouts. Current Max-well traces do **not** warrant a quality claim.
4. **Model selection:** use exact correctness, revocation/allowlist and missing-witness refusals, stable JSON, temperature/VRAM, wall latency and unload verification. Blind independent gold, attack diversity, multilingual voice/accessibility parity, tool E2E and energy per token remain **NO_DATA(not_measured_by_this_pilot)**. Do **not** delete Lightning merely because Super has more parameters.
5. **Approval:** no promoted brain, release, merged `main`, weights in Git, or commissioned training claim from this report. Attach actual post-download and GPU run receipts before a final ranking.

## Privacy and provenance

Readbacks were obtained from the owner's ONEXSTATION shell via the already-authorized host connection; local transcripts and answer bodies remain on the device. This report publishes only aggregate counts, timing, identifiers and hashes. The public repository's existing [AGENTS.md](../AGENTS.md) and [benchmark index](../benchmarks/README.md) remain canonical. This document is a **dated evidence pulse**, not a new top-level benchmark card.
