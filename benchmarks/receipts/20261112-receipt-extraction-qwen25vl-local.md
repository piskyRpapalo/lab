# Local receipt extraction · qwen2.5vl on CPU · 2026-11-12

Broadcast receipt: figure=97.9% field accuracy (139/142 fields; 23/26 receipts fully correct); p50 391.2 s per receipt | model=qwen2.5vl:7b Q4_K_M, num_ctx 16384 (Ollama 0.40.14) | machine=AMD Ryzen 7 5700G, 32 GB RAM, Windows 10 x86_64, CPU only | date=2026-11-12 | sha256=dacc2c3e0e971b643e307f60fcb5059455f0c518052509d3f48ec716db804e07 (file digest of backend/eval/models.json at source commit 0f8b378)
Benchcard: machine=AMD Ryzen 7 5700G 8C/16T, 32 GB RAM, Windows 10 x86_64 | date=2026-11-12 | runner=Receipt-Ghostbuster eval_models.py at c3820c2, loopback Ollama 0.40.14 | quant=Q4_K_M | sha256=dacc2c3e0e971b643e307f60fcb5059455f0c518052509d3f48ec716db804e07

**Scope:** contributor-reported. One open vision model, run fully on-device, reading 26 photographed shop receipts, scored field by field. **Claim:** field extraction accuracy and per-receipt latency on this set only; no quality, safety, fairness, compliance or general-accuracy certification.

**Closest existing:** [vision candidates, 2026-09-27](../artemis-candidates-20260927/README.md) measures JSON output, not vision. Matching harness: `NO_DATA: matching harness not identified`. No existing receipt schema fits field extraction (`preceptoros.lab.harness-receipt/1` is for test receipts, `bench-repro-01-v1` for throughput), so the JSON documents its own fields.

**Reference:** real photographed shop receipts from one shopper, not synthetic. Denominators: 26 receipts, 142 fields (a field is scored only where the label gives a value). Labels were written by the contributor from the paper receipts and were **not independently checked**; they are not independent ground truth. Exclusions: none.

**Source:** [Receipt-Ghostbuster](https://github.com/Aimilios94/Receipt-Ghostbuster), code commit `c3820c2`, result commit `0f8b378` (`backend/eval/models.json`). A commit SHA identifies the repository state; a file SHA-256 identifies the exact bytes of one file. The scorer, prompt, Modelfile and the six scored fields are public there (`backend/scripts/eval_models.py`, `backend/scripts/eval_extraction.py`, `backend/ollama/Modelfile`). The receipt photos and labels are private and stay private.

**Command:** `python backend/scripts/eval_models.py --models ollama:qwen2.5vl-receipt --refresh` (fresh reads, nothing from cache). Window 2026-11-11 23:40:51Z to 2026-11-12 04:02:11Z, exit code 0.

**Offline conditions:** the only model endpoint was loopback Ollama. LangSmith tracing off, Sentry DSN empty, cloud provider keys replaced with dummies. The local provider path has no cloud fallback.

**Model and engine:** `qwen2.5vl-receipt` = `qwen2.5vl:7b` (8.3B, Q4_K_M) plus `num_ctx 16384`, because the default 4,096-token context truncates receipt images. Ollama digest `55b7b427…c645`. Ollama 0.40.14, llamacpp runner, `ollama ps` showed **100% CPU**; the integrated GPU was not used. Decoding: temperature 0.0001 (the base model's default, not set in the request), `max_tokens` 4096, seed `NO_DATA: not set`.

## Result

| Field | Correct / scored |
|---|---:|
| Vendor | 25/25 |
| Date | 23/25 |
| Total | 26/26 |
| VAT amount | 21/21 |
| VAT rate | 21/21 |
| Category | 23/24 |
| **All fields** | **139/142 (97.9%)** |

Receipts with every field right: 23/26. Errors: 0. Latency per receipt (including the pipeline's date re-read when triggered): p50 391.2 s, p95 1295.2 s, mean 595.4 s. Cost: $0. The app's review gate let 1 of the 3 wrong reads post automatically and sent 30.4% of correct reads to review.

## Repeatability on one version

The same 26 were last read on 2026-11-07 with the same model digest, the same Ollama 0.40.14 and the same prompt: 138/142 (97.2%), 22/26 fully correct. This run: 139/142. 23 of 26 receipts came back identical on every scored field; one receipt went from wrong to right and none from right to wrong. Fixed between runs: machine, Ollama version, model digest, prompt, the Ollama read path, and the scorer (both read sets scored at `c3820c2`). Changed: the code commit (the previous run was at `dedb262` with uncommitted changes), whose changes add other providers and don't touch the Ollama read path or the prompt.

Earlier runs on the same 26: 89.4% (run 2026-10-22), 90.1% (reads 2026-11-03 to 05, 25 of 26 on Ollama 0.40.11), 97.2% (2026-11-07). The rise from 90.1% came with a version change; two runs on one version can't prove the version caused it, so the source repository publishes the local model as a range, 89.4–97.9%. A companion note in `preceptoros-companion` (2026-11-03) reported 86.6% on n=25 from an older run with one crashed read; it is not comparable with this card.

## Evidence

[Machine-readable aggregate receipt](20261112-receipt-extraction-qwen25vl-local.json). The result commit, the SHA-256 of the result file as committed, and the SHA-256 of the scorer, extractor and Modelfile as committed at `c3820c2` are in it. The labels and the run log are private; only their digests are given. No receipt images, field values, prompts, model answers or file names are included.

## NO_DATA

- Held-out set: the 9-receipt locked test set was not re-read in this run.
- Power and thermals: no meter, not instrumented.
- GPU: not measured; this is a CPU-only figure.
- Independent replication: one machine, one operator.
- External reproduction: the receipt photos and labels are private; the method, code and model are public.
- Independent labels: the labels are the contributor's own.
- PR head SHA and human sign-off: not yet; the Soberano signs the exact PR head.

Agent: Claude Code · Model: Claude Opus 5.5 · Run: on the operator's own desktop, 2026-11-11 to 2026-11-12.
