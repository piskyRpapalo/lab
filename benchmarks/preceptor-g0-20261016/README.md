# G0 · local reading of the Preceptor's authority · 2026-10-16
Broadcast receipt: figure=NO_DATA (no aggregate outcome) | model=qwen3-coder:30b | machine=Ryzen 7 255 · Radeon 780M | date=2026-10-16 | sha256=NO_DATA (card has model digest, not a result-source digest)

Preceptor role test with `qwen3-coder:30b`, executed by the local Ollama endpoint. Model digest `5e8c8157b1b50f092e9c488360bcb63ffa53726cf732d71fc9c9401c43bc78d7`; size 18,556,689,759 bytes; requested and observed context 16,384. Machine AMD Ryzen 7 255, 16 logical CPUs, Radeon 780M. During the call `ollama ps` reported `100% GPU`, context 16,384, runner `llamacpp`.

The fixed task measures a voice navigation order, the human choice and signing, and the model's role as proposer. The lab keeps the hash of the prompt and of the responses, the schema, the options, and the timings; the raw texts are not archived. Temperature 0, seed 20261016, `num_ctx=16384`, two sequential calls in a persistent server process.

## Red before green

Red: a call to `127.0.0.1:9/api/generate` with no engine available, `curl` exit 7, connection refused. This verifies that the harness does not invent a response when the engine is absent.

Green: two calls to the local model returned the same JSON, 75 prompt-evaluation tokens and 33 output tokens in each. The first took 14.698 s total, including 13.209 s of load; the second took 1.037 s, with 0.002 s of load. Identical response hash in both. This case measures one narrow authority-boundary decision, not general coding capability, speech recognition, or model quality.

## Limit

The model identifier is measured by digest. Physical temperatures, energy, and quality over a battery of tasks were not measured: NO_DATA with those causes. The earlier July G0 results remain separate in [g0](../g0/README.md); they are not combined with this resumption.
