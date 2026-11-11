# Synthetic Model Matrix · Beelink / OneXStation · 2026-11-11

**Agent:** Codex · GPT-6 (LAB). **Status:** MEASURED-SYNTHETIC / UNCALIBRATED. **Scope:** candidate model-protocol assessment relevant to DFA-B1 (dark-pattern judgments) and DFA-B5 (manipulation / false NO_DATA), **not** execution of the full DFA-B1 Guardian gauntlet or the Study #112 B5 requirements.

**Primary evidence:** [machine-readable, scrubbed JSON receipt](20261111-mini-large-model-synthetic-matrix.json), built from **48 local run receipts** and 24 unique authored synthetic fixture cases. All raw prompts and raw model outputs remain off GitHub. The 24 fixture texts are not published; their SHA-256 is in the JSON. This supports identifying a *specific* fixture set but means external prompt-level replay is **NO_DATA: private_fixture_text_not_committed**. Synthetic gold labels were not independently validated by humans.

## Protocol and resource fences

- **Four equally sized classes:** SAFE; MANIPULATION (assistant-induced emotional dependence); DARK_PATTERN (deceptive UI choices); FALSE_NO_DATA (a model says no source despite supplied excerpt). Six **distinct** cases per class. Previous Gemma2 8-case results are historical and not directly comparable to this new fixture.
- The same exact 24 cases were run twice, under fresh processes; one endpoint/model/protocol was run at a time, in 4 batches of six, with model unloaded and `ollama ps` confirming zero resident models after **every batch**. Never treat 48 attempts as 48 distinct cases.
- `POST /api/generate`, `stream=false`, `format=json`, `temperature=0`, `seed=23`, `num_predict=64`, `num_ctx=2048`, `num_gpu=99`. One additional source-qualified protocol for Qwen3 1.7B explicitly sets `think=false` and keeps all other declared options unchanged.
- Rack Ollama and station tunnel both reported Ollama **0.40.3**. Model digests are in the JSON, including the identical `qwen3:1.7b` digest between endpoints. Rack hardware observed: Ryzen 7 255 / Radeon 780M. Station hardware inspected via BatchMode SSH: AMD Strix Halo / Radeon 8060S. A direct SSH OS probe does **not** cryptographically attest that the forwarded inference API is served by that physical host.
- Before each batch, check no other models loaded and resource headroom. Other Claude processes were not killed. No new models downloaded. GPU/CPU power and stable temperature were not measured. The Jetson's configured SSH alias timed out; **NO_DATA: connection_timeout**.

## Results (each row represents 24 UNIQUE cases, repeated twice)

| Model | Endpoint | Protocol | Correct pass 1 | Correct pass 2 | Invalid / pass | Median output tokens/s |
|---|---|---|---:|---:|---:|---:|
| Qwen3-Coder 30B | Station tunnel | Default JSON | **23/24** | **23/24** | 0 | 76.34 / 76.94 |
| Mistral Nemo 12B | Rack | Default JSON | **22/24** | **22/24** | 0 | 12.19 / 12.31 |
| Qwen3 1.7B | Rack | JSON + think=false | **21/24** | **21/24** | 0 | 62.50 / 62.49 |
| Qwen3 1.7B | Station tunnel | JSON + think=false | **20/24** | **20/24** | 0 | 139.11 / 140.69 |
| Gemma2 2B | Rack | Default JSON | **19/24** | **19/24** | 0 | 39.99 / 40.23 |
| Qwen3 1.7B | Rack | Default JSON | **0/24 usable** | **0/24 usable** | **24** | 55.94 / 55.91 |

**Key negative finding:** Under the original contract, Qwen3 1.7B produced invalid JSON/labels for all 48 attempts. In an explicit *different* protocol with `think=false`, it produced 24/24 parseable labels per pass and scored 21/24 on rack, 20/24 on station. This establishes that a protocol adjustment strongly changes usefulness under the same fixture, not *why* every original output was malformed. Do not hide either result or rename malformed output to an incorrect logical judgment.

**Key reproducibility finding:** Every model/protocol/endpoint repeated the exact same predicted labels on all 24 cases in its two passes. With the **same exact Qwen3 1.7B model digest** and `think=false` protocol, **23/24 labels matched across the two endpoints**; one differed. This is measured endpoint disagreement, **not** sufficient evidence that GPU architecture alone caused it. API versions match, but execution kernels, service configuration, offload and numeric differences were not controlled.

## Interpretation and next gates

- This is a *small, straightforward synthetic classification pilot* with authored gold and no human independent reference or held-out challenge calibration. Do not call it 90% detection, certified family-blind judging, general model intelligence or regulatory conformity. The **DFA-B1 ten Guardian probes** are still pending. **DFA-B5** still needs at least 60 independently adjudicated cases *per class*, held-out family-blind evaluation and consent/provenance. Qwen-family candidates cannot be judges of a Qwen-family manipulator within that protocol.
- Throughput means **generated tokens divided by Ollama's reported generation duration**, not first-token latency, complete UX latency or energy efficiency. Each six-case batch reloaded the model; cold-start overhead is separately recorded as local run wall time. A speedier model may hallucinate more.
- `gpt-oss:120b` (~65 GB artifact) and `llama3.3:70b` (~42.5 GB) are installed at the station inference endpoint, but **were not loaded**: the station read-only preflight showed ~27 GB available RAM; this study deliberately did not risk a 42–65 GB load without a validated offload/memory budget.
- To improve: (1) rerun a genuinely harder, separately adjudicated holdout across models; (2) add the existing WEB Guardian's ten red/green DFA-B1 probes without implementing another Guardian; (3) verify station-to-tunnel attestation and Jetson accessibility; (4) add measured thermals/power only after validating the electrical sensor; (5) test real APP/WEB chat with source-citation failures and accessible UI. The JETSON and physical-screen-reader paths remain NO_DATA.

## Rebuild and independent checks

LAB `bin/aggregate_synthetic_model_matrix.py` is an offline standard-library aggregator. It validates exact batch ranges, two passes, 24 unique class-balanced IDs, source hashes and the 0-resident-model condition; it rejects invented `correct` counters, raw response fields and mixed fixture/model digests; and it emits **only aggregate counters plus receipt hashes**. The JSON output is **11,879 bytes**, within the 16,384-byte piece ceiling; no filenames, model answers, prompts, private IPs, private user identifiers or personal data are included.

```bash
python3 bin/aggregate_synthetic_model_matrix.py --input-dir <private_local_run_directory> --output <new_scrubbed_receipt.json>
python3 -m unittest discover -s tests -p 'test_synthetic_model_matrix.py'
python3 -m unittest discover -s tests -p 'test_*.py'  # twice in distinct processes
python3 test_llms.py
python3 bin/verify_llms_tree.py
```

The input directory must be the *private, authenticated local run files*, not generated examples. The public artifact alone cannot regenerate those raw run files. No model promotion, autonomous merge, user-affecting deployment, or signature results from this receipt. **HITL: Sovereign retains exact-head approval.**
