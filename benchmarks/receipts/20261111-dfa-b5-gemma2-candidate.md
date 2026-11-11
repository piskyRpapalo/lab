# DFA-B5 · Gemma2 candidate local pilot · 2026-11-11

**Agent:** Codex · GPT-6. **Status:** RED / synthetic device pilot. No legal conformity claim. Study #112 and LAB #157 family-blind preflight remain the sources of mission purpose.

**Machine class:** x86_64 · AMD Ryzen 7 255 / Radeon 780M. **Model:** gemma2:2b-instruct-q4_K_M · Ollama metadata family `gemma2`, 2.6B parameters, quantization Q4_K_M. A separate loaded smoke reported `100% GPU` and 2.2 GB resident, with **zero models resident after unloading**. This smoke is not the eight-case scoring run.

**Yardstick:** Local Ollama API; one model at a time; `temperature=0`, `seed=23`, `num_predict=64`, `num_ctx=2048`, response format `json`. Eight synthetic cases: relational guilt pressure (3), safe choice and honest uncertainty (3), false NO_DATA despite an excerpt (2). Identical fixture hash used twice. Fixture text and full model answers are not published; the digest supports comparison but **cannot itself reproduce the test**.

**Result (same eight cases repeated; NOT sixteen independent examples):**

| Axis | Pass 1 | Pass 2 |
|---|---:|---:|
| Overall correct | 4/8 | 4/8 |
| Manipulation | 3/3 | 3/3 |
| Safe | 1/3 | 1/3 |
| False NO_DATA | 0/2 | 0/2 |
| Malformed output | 1 | 1 |
| Elapsed wall time incl. initial model load | 6.250 s | 5.064 s |
| Median generation throughput | 40.92 tokens/s | 39.84 tokens/s |

The pass-to-pass predictions were identical. **RED:** the candidate is not yet a calibrated judge; it confuses safe opt-outs and true abstention, and fails the false-NO_DATA examples. No overfitted "green" revision is authorized.

**Source integrity:** structured aggregate receipt [JSON](20261111-dfa-b5-gemma2-candidate.json) records the SHA-256 of each local run report and the shared synthetic fixture digest. Local reports remain on the rack, not GitHub. Digest of a report is not an attestation of a human reference label or model suitability.

**NO_DATA with cause:** independent human judgments absent; n>=60/class not collected; no held-out calibration; paired Qwen manipulator not run; exact reader/auditor usability not tested; raw fixture replay not available publicly. These are deliberate limits.

**Next:** prepare consented human-reference and held-out protocols; verify the Gemma judge independently after calibration and compare at least one *unseen* fixture set. No default judge promotion or model activation from this receipt. Human selection and merge remain separate.
