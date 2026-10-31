# Flint · second coexistence batch

PROPOSAL; no benchmark was run in this session. The commission requests Q4 with a fair comparison and Q3 with approximately 13 GB of headroom, concurrently with the resident large model. The 13 GB figure is a commission-supplied condition, not a reading from this plan. The accessible environment cannot connect to the rack; actual free memory, model variants, model digests, execution and outcome are NO_DATA.

## Matched protocol

1. On the target host, capture the active large model's exact digest, resident placement, context, memory and the runtime version. No restart, unload, download, service modification or public listener is part of this plan.
2. Select existing Flint Q4 and Q3 artifacts only after resolving their exact digests and quantization identifiers. Record file bytes separately from resident memory. If either is absent, stop that case with NO_DATA and a cause.
3. For each variant, confirm current free memory immediately before launch and leave the requested 13 GB headroom for Q3. Check whether the unit is GB or GiB at the sensor; do not silently convert. If the headroom or large-model residency is not demonstrable, refuse the run.
4. Fix the same local input set, context, generation settings, warm-up policy and concurrency schedule for both variants. Record artifact hashes and versions; do not commit prompts or responses. Alternate Q4 and Q3 order to limit ordering bias. Predeclare count, stopping conditions and comparison before collecting results.
5. Record per run: resident placement and memory, duration, output count, throughput, exit and typed failure, and concurrent large-model status. Use separate baselines under the same prompt and settings for any performance comparison. A mismatch is NO_DATA, not a no-regression claim.
6. Stop immediately if the large model is evicted, headroom is breached, an out-of-memory event occurs or the operator requests a stop. Retain a compact local receipt with causes; export only scrubbed aggregate evidence.

## Result placeholders

| Case | Exact artifact | Memory/headroom | Concurrent residency | Result |
|---|---|---|---|---|
| Flint Q4 | NO_DATA: rack inaccessible | NO_DATA | NO_DATA | NO_DATA: batch not run |
| Flint Q3 | NO_DATA: rack inaccessible | NO_DATA; 13 GB is a requested condition | NO_DATA | NO_DATA: batch not run |

The earlier [NEXO #16](https://github.com/piskyRpapalo/hexelion-nexo/pull/16) concurrent sample concerns a different model and workload; it is not evidence that Flint co-resides or that performance does not regress. B4 feed remains gated by the bridge and combat work and is not activated here.
