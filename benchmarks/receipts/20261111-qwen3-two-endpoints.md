# Qwen3 matched-model two-endpoint pilot · 2026-11-11

**Agent:** Codex · GPT-6 · **Status:** MEASURED-SCOPED / physical station identity NO_DATA. This is an engineering device-endpoint comparison under LAB's live device benchmark program; NOT the F6-01 A2A economic fence.

**Source:** Two accessible local-facing Ollama API endpoints: the enrolled rack host and the station tunnel. The SentinelX roster lists only one directly enrolled host. Hardware, OS and process inventory beyond Ollama at the station endpoint are **NO_DATA**; do not describe that endpoint as a directly inspected physical device.

**Matched model:** `qwen3:1.7b`, same SHA-256 manifest digest on both endpoints: `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. Both metadata records declare `qwen3`, ~2.0B, Q4_K_M. The comparison uses the *same model bytes*, unlike comparisons of unrelated model sizes.

**Protocol:** Local Ollama calls only, no public network or remote exfiltration. Identical small synthetic JSON generation prompt (digest in receipt; prompt text not published), `temperature=0`, `seed=23`, `num_predict=48`, `num_ctx=512`, `num_thread=4`, `num_gpu=99`. Run order rack → station-tunnel → station-tunnel → rack. Before every run, the target endpoint reported no loaded model; after each run, keepalive=0 unloaded the model. Every run produced 48 tokens. This is a *cold model-load plus brief generation* measure, not thermal steady state.

| Ollama endpoint | Generated tokens/s | Wall time incl. load |
|---|---:|---:|
| Rack #1 | 56.08 | 2.594 s |
| Station tunnel #1 | 124.99 | 1.857 s |
| Station tunnel #2 | 129.77 | 1.393 s |
| Rack #2 | 55.25 | 1.848 s |

Means: rack 55.665 tokens/s; station tunnel 127.38 tokens/s; endpoint ratio ~2.29 on this synthetic task. **The ratio is descriptive only**: the station hardware/thermal/process conditions, offload details and actual physical host identity are not independently attested. Don't infer a universal device or power advantage from these four short samples. VRAM allocations and each run's local clock duration are in the [JSON receipt](20261111-qwen3-two-endpoints.json).

**Evidence limits / NO_DATA:** exact physical station specs; processes other than Ollama there; energy and solar contribution; user-perceived quality; larger contexts; repeated long sequences; whether the shared tunnel adds material latency. Raw prompts, replies and identifying addresses are not in the repo.

**Next:** directly enroll the station with the Sovereign's permission for host-level process/hardware attestations, then rerun a held-out, consented, multi-prompt workload with declared backend settings and validated power telemetry. Do not enroll, configure, or restart any service as part of this receipt.
