# ACHO-LOCAL-EVIDENCE-01 · LAB bench adapter

Problem: APP motor/configuration, catalog, model generation, and witnessed execution
are separate. A common read-only measurement consumer is missing for heterogeneous
local engines. Source: Mesa #62 CLAIM 7206034823, B Pulso #63 7191668246; LAB
transports.py and canonical throughput instrument; APP hexelion_proxy.py and
turnos_hexelion.py; Acho canon WEB docs/acho-language.md.

Adaptation: normalize existing Ollama /api/generate and llama.cpp native completion
response counters; reuse the Ollama sample instrument. No new HTTP transport,
registry, persistence, authorization, APP or MCP endpoint. Caller owns model pin,
before/after artifact observations and request/session binding. No raw prompts or
answers in results. REPORTED is not independently attested. Fixture is SIMULATED.
reader_fields is an input for H's existing emitter, not a new frame protocol.
Memory is supplied by an independent measurement, never derived from disk size.
llama.cpp wire compatibility is fixture-only, not yet measured on hardware.

Measurement 2026-11-26: rack 21434 Ollama version/tags/ps roundtrips returned,
no loaded models; APP arnes failed exit 1; user journal inaccessible. No
model generation attempted because no large model was resident. APP end-to-end,
TTFT, throughput, attributable memory and station principal: NO_DATA. Never
infer successful generation from service/catalog status.

Benefit target: identical counters for equivalent fixtures, zero false LIVE or
COMPLETED_VERIFIED, no response text in metadata. Run targeted unittest twice
and LAB gates twice; independent D review exact HEAD. Physical next: explicit
small-model budget, isolated public case, bind existing APP turn and LAB receipt,
validate llama.cpp endpoint contract against pinned running binary. No weights,
service changes, automatic fallback or new grants. HITL before integration.
