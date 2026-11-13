# Federated metadata · partial evidence, 2026-11-13

Owner: Codex CLI. Source: commissioned read-only observations, LAB main3647403.
Anonymous node mapping and actual transport binding remain in Private Mesa3.
This is a historical snapshot, not a complete inventory or a dispatch grant.
The observation lifetime is 120 seconds; after that, resource decisions must
report STALE and obtain new telemetry. Hashes prove integrity, not authenticity.

| Node / backend | Host observation | Catalog observation | State and source |
| --- | --- | --- | --- |
| node-a | NO_DATA(access_timeout), two bounded SSH attempts | NO_DATA(access_timeout), never zero models | Earlier hardware/model entries remain STALE; no current inventory |
| node-b | x86_64, 16 logical CPUs; RAM total61,845,794,816 B / available42,410,913,792 B; root available410,546,774,016 B | 29 tags /29 reported digests; resident0; backend reports0.40.3 | [Measured snapshot](20261113-federated-node-b.json), 09:25:04Z |
| node-c primary | Host telemetry deliberately omitted for tunnel observation | 17 tags /14 reported digests; resident0; backend reports0.40.3 | [Measured snapshot](20261113-federated-node-c-primary.json), 09:25:04Z |
| node-c secondary | x86_64, 32 logical CPUs; RAM total32,727,908,352 B / available28,972,474,368 B; root available185,227,816,960 B | 2 tags /1 reported digest; resident0; backend reports0.40.3 | [Measured snapshot](20261113-federated-node-c-secondary.json), 09:25:04Z |

Each manifest references ordered model parts by file hash; reconstruct the
snapshot using `header` plus the concatenated `models`, then verify
`snapshot_ref` with sorted-key compact ASCII JSON. Every part is under16,384 B.
Per-model fields include model-version digest, format, quantization, catalog
bytes, architectural and explicitly configured context, declared capabilities,
license-content digest or caused NO_DATA. Private tags are hashed. There are
26/29, 9/17 and0/2 nonempty license bodies respectively; none was legally
reviewed. Aliases stay distinct. Matching reported digests are not proof of
shared storage or identical loaded weights.

The primary and secondary backends are separate registries on the same target;
the one digest in secondary is also advertised by primary. There are14 reported
digests across those two registries, not19 independent models. Do not consolidate
files or infer storage savings. One private orchestrator tag is advertised by
primary, but no new generation was performed: availability as a specialist is
NO_DATA(current_inference_not_measured). Earlier LAB176/177 generations remain
dated evidence rather than a promise that a historical116B entry is callable now.

Metadata RTT version/tags/ps in ms: node-b1.347/13.990/0.263;
node-c primary13.066/9.958/2.894; secondary1.526/1.116/0.475.
These are request timings, never inference latency. Host load1/5/15 was
2.690/1.949/1.563 on node-b and0.187/0.245/0.153 on node-c.
PSI some avg10 CPU/memory/I/O: 0/0/2.49 and0/0/0.63 percent respectively.
One snapshot does not establish saturation thresholds or safe concurrency.
Direct device sysfs additionally reported a103,079,215,104 B VRAM carve on
node-c in a separate direct inspection during this commission (exact probe time NO_DATA); this is shared memory, not extra RAM
to add to an admission pool. Full device peaks remain NO_DATA(not_measured).

Additional weights outside these catalogs exist on node-b: a bounded filename
inspection found GGUF and safetensors in existing stores. Their provenance,
licenses, configured backend and loaded state remain NO_DATA(not_verified).
No weight was read, hashed, installed, duplicated or deleted. Two conventional
node-c store locations were absent or contained no GGUF; this is not proof of
absence elsewhere. Reuse older receipts only after source/digest verification.

## Task and node selection matrix

This matrix records eligibility evidence and abstention; it does not turn model
names, parameter counts or `completion` metadata into a quality score.

| Task | node-a | node-b | node-c | Decision supported today |
| --- | --- | --- | --- | --- |
| Programming | NO_DATA(access_timeout) | Catalog capabilities only; no code holdout | Catalog capabilities only; no code holdout | NO_DATA(task_quality_and_resource_envelope) |
| Conversation | NO_DATA(access_timeout) | Completion declared, not evaluated here | Dated isolated planner evidence in LAB177; no new liveAPP proof | NO_DATA(live_contract_and_resource_envelope) |
| Vision | NO_DATA(access_timeout) | Vision advertised by some tags, no image task measured | No vision task measured | NO_DATA(vision_evaluation_missing) |
| Embeddings | NO_DATA(access_timeout) | Embedding advertised; no new retrieval/gold evaluation | No retrieval/gold evaluation measured | NO_DATA(retrieval_evaluation_missing) |
| Independent evaluation | NO_DATA(access_timeout) | No calibrated model judge | No calibrated model judge | Use existing deterministic properties only within their tested sort task |
| Fixed public sorting | NO_DATA(access_timeout) | LAB176 retains model failures on one case; a native tool passed | LAB177 planner delegated to that native tool in an isolated cycle | Dated one-case evidence; no general model ranking or automatic dispatch |

Existing evidence: LAB176 `a8a347c73ec7`, LAB177 `631f5986f413`;
their receipts remain on their own unmerged branches. A native tool is not a
trained model. Multiple formatting trials on one case do not create new
independent cases. No LoRA proposal: NO_DATA(sufficient_independent_corpus).

## Resource admission · proposal, no scheduler installed

Admission remains refused: NO_DATA(task_resource_envelope_not_calibrated).
Reproducible proposed bounds: telemetry no older than120s, exact node/backend/
model/task/context identity, an operator-owned resource lease, no uncertain
in-flight execution, and measured peak RAM/device memory plus reserved headroom
below freshly available capacity. Reject on missing or changed context,
authorization, transport, pressure, calibration or budget. Numeric memory,
latency and concurrency ceilings are NO_DATA(no_calibrated_load_series).

Use the existing `benchmarks/station-96-first-pass-20261029/smoke.py` public
fixture runner in an idle coordinated window, one job at a time. Keep its
generation/load/wall timings separate. Add external peak-memory/pressure
sampling and exact digest/control matching before proposing limits; throughput
alone neither measures quality nor calibrates admission. No heavy benchmark
was run during the APP owner's critical E2E session.

Proposed diagnostic mapping (do not alter historical receipt enums):
MODEL_FAILURE ← independently failed output properties; CONTEXT_MISSING ←
missing/expired/mismatched source; AUTHORIZATION ← exact-grant rejection;
NODE_SATURATION ← fresh measured contention crossing a calibrated bound;
TRANSPORT_UNAVAILABLE ← bounded request failure; EVIDENCE_INSUFFICIENT ←
missing witness/calibration. Missing telemetry must never be called saturation
or model failure. Model metadata cannot approve a task or memory promotion.
