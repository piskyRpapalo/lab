# Federated receipt consumption · LAB to APP

Commission13-Nov-2026. Five rack nodes, one APP. Phones remain APP clients;
neither a browser model candidate nor an Android installation becomes a sixth
rack node. APP/runtime/Acho integration belongs to Claude. This optional LAB
reader adds no UI, daemon, dispatcher, permission service or inference call.

## Preserved evidence and states

The five source manifests/parts, dated summary and original12-test verifier at
head8eb0a1a were checked byte-for-byte before this work. No receipt, source date,
collector hash or model count is rewritten. The old feature document remains in
that immutable commit; new implementation notes are appended to its log.
New observations use NEW dated/revision filenames and new seals. The reader
accepts a dated name with optional `-r1` etc; it never writes source files.

`bin/federated_projection.py` reconstructs the existing
`preceptoros.lab.node-metadata/1` snapshots from their existing parts manifests.
The caller supplies each expected full snapshot SHA256 from its trusted,
reviewed source. Part hashes, counts, node binding and the reconstructed seal
are checked. A file that merely provides its own hash is not a trust anchor.
Input roots are operator-owned; same-UID replacement of a parent directory is
outside the guarantee. Symlink/FIFO files, duplicate JSON keys, nonfinite JSON,
path traversal, wrong node/pin, altered parts and oversized packets are refused.

The output reuses `node-metadata/1` with additive `kind=projection`, consumption
fields and its own `projection_ref`. It is not a new inventory schema. Original
`snapshot_ref` becomes the projection's `source_ref`; it is never represented as
the seal of changed bytes. `collector_sha256` retains source implementation
identity. Input observations are not modified or upgraded by this reader.

| Concept | Representation | Exact meaning |
| --- | --- | --- |
| DECLARED | `topology_state`, backend version, capability basis, optional cited prior failure | Supplied by topology/config/manifest/host; not a successful inference |
| OBSERVED | Fresh consumption `state`; model tags and host facts | Metadata was queried in the retained snapshot; no continued liveness promise |
| VERIFIED | `verification.state=VERIFIED`, `scope=receipt_integrity` | The specific integrity check passed; not model quality, authorization or server authenticity |
| STALE | Consumption/freshness/resource/model state | Original observation is older than the consumer's120s ceiling; retain history and counts |
| NO_DATA(cause) | Missing observation, current response, inference, admission or sensor | Evidence is insufficient; an unknown count is null, never an invented zero |

Legacy input `catalog_state=VERIFIED` described a successful metadata query.
The consumer interprets that as OBSERVED with an independent integrity scope.
It also accepts future source receipts explicitly labeling metadata OBSERVED.
It never changes the legacy source bytes. A failed catalog does not erase valid
host memory facts, and does not announce zero models. Freshness remains visible
even when the catalog request failed. Missing PSI is not zero pressure.

Use node + host-supplied backend binding + full model-version digest for an
identity. Keep node-c primary and secondary separate; do not collapse aliases
into capabilities or shared weights. Backend names are host-owned source
bindings, not remotely authenticated transport identities. The retained data
already demonstrates equal alias hashes with different weights on two nodes.

## Minimal APP contract and deterministic example

The existing LAB177 `preceptoros.brain-cycle/1` remains the task-result contract.
A census snapshot is context, not a task execution. Do not mint a fake cycle,
task receipt, permission or memory draft from metadata. After176 integration,
reconcile177 and use its actual witness/`verify_cycle` checks for task outcomes.

The optional reader returns the same existing `record`/`views` pattern as LAB177:

- `record`: sanitized census consumption state, source seal, date, explicit
  causes, model refs/digests, historical resources, missing measurements and
  `admission.allowed=false`.
- `views.text` and `views.speech`: the SAME `summary` and `state_ref`.
  Visual text and semantic screen-reader announcements both consume text;
  audible narration consumes speech. Claude controls rendering and consent.
- `views.machine.record`: the SAME complete record and reference.

Every emitted JSONL packet is under16,384 B, or consumption is refused. A packet
is a projection, not a sub1KiB execution receipt. No raw tag, prompt, answer,
path, endpoint, host identifier, serial or credential is projected. Stable
inputs + an explicit read time produce identical bytes. Changing read time
creates a new projection revision, not a new source observation.

Run from the LAB checkout (read-only, no backend or private APP needed):

```sh
python3 -B bin/federated_projection.py --receipts-root benchmarks/receipts \
  --source 20261113-federated-node-e.json=cf9d926a3eb70ac87e8ab33da7d18a942e8b365113912bbbe4e6e9b28635c199 \
  --at 2026-11-13T09:42:00Z
```

This is HISTORICAL REPLAY: node-e is OBSERVED at that selected time; the other
four nodes are NO_DATA because their sources were not supplied. The checked-in
`benchmarks/receipts/20261113-federated-projection-example.json` labels this
replay explicitly. Omit `--at` to use current UTC; the retained observation will
then be STALE. The reader does not refresh it. Add other pinned `--source`
arguments for the remaining observed backends. All five source refs are in the
existing manifests; obtain trust from the selected reviewed Git ref, not from
a model, mutable frontend state or an untrusted manifest alone.

For the complete retained bundle (five backend observations, four reached
physical nodes, node-a declared with no supplied snapshot), replay with:

```sh
python3 -B bin/federated_projection.py --receipts-root benchmarks/receipts \
  --source 20261113-federated-node-b.json=9a1adac53532e6a558c53498de72d67b52656044cd7ff9358e73d0d5af1f3d4e \
  --source 20261113-federated-node-c-primary.json=073f6cd0e4f188a94aae87fe867d7510460ca775ad68d1897ca27f6c1866d422 \
  --source 20261113-federated-node-c-secondary.json=64613d5a810da8fd89084866308f934064a420c1f4f24e18a6aa7cc03a4c3dd4 \
  --source 20261113-federated-node-d.json=a16605fd146a8b9e1241aa874e0c3de5a79027e6ba00ae30b266142275b47f29 \
  --source 20261113-federated-node-e.json=cf9d926a3eb70ac87e8ab33da7d18a942e8b365113912bbbe4e6e9b28635c199 \
  --at 2026-11-13T09:42:00Z
```

The earlier node-b/c observations are STALE at this replay time; node-d/e are
OBSERVED. Omitting `--at` expires every old observation using the current clock.

For an imported reader, use `load_receipt(root, name, trusted_ref)`, then
`project(source, host_read_time, trusted_ref, backend)` and `views(record)`.
Validate a received packet using `verify_packet(packet, source, host_read_time,
trusted_ref, backend)`: it recomputes the result from pinned source and a
HOST-chosen request time. It does not take its clock/pin from the packet. A
jointly modified/resealed record and views therefore cannot pass that check.
Reproject on a later read; neither the read time nor its hash attests a clock.
APP should deduplicate spoken/reader announcements by node/backend/state/cause/
source, rather than announce every changed read-time hash. Keep the exact
packet reference in the structured state. LAB installs no polling loop.
Canonical bytes use Python sorted-key compact ASCII JSON with nonfinite numbers
refused. Preserve original source bytes: a client must not parse/reserialize a
source file and call it the same evidence. In particular, floating spellings
such as0.0 can differ in JavaScript. Use the trusted Python verifier for source/
packet validation and carry its opaque refs through mobile/Acho consumers;
cross-language canonicalization is not claimed by this slice.

Missing nodes remain in the DECLARED five-node topology. For node-a, APP may
attach its existing cited prior timeout using `missing(..., last_failure={
"cause":"access_timeout", "source_ref": <trusted receipt hash>})`. The result
marks that claim DECLARED/host_cited_prior_failure with no new observation time.
The dated summary SHA256 is
`4f42a5814af1b7fe493dc5db71c53aa108bab5c42fee4d998941a25456775d6b`.
The historical inventory and access-failure receipts remain separate sources;
not supplying them does not mean the node or its models have disappeared.

## User-facing acceptance, without invented progress

| APP state | Required evidence and wording |
| --- | --- |
| Metadata observed, inference untested | Fresh OBSERVED record; use its exact summary |
| Observation expired | STALE record; preserve original date and historical model count |
| Last route/request failed | A cited failure or failed metadata receipt; unknown physical power state |
| Model announced, not evaluated | Catalog reference + inference NO_DATA; no skill/availability badge |
| Selection refused, evidence insufficient | Admission NO_DATA + `missing_measurements`; do not call missing calibration insufficient RAM |
| Resource shortfall measured | Requires future task-bound calibrated envelope + fresh telemetry; not emitted by this reader |
| Specific result validated, receipt available | Existing176/177 exact task receipt and independent witness; show its scope/ref |

An identity/ref/state/cause must agree in Notebook, Lab and all four readings.
No second Notebook/Lab producer is installed here. Claude injects its existing
read-only authority, trusted source root/pins, clock and durable task journal.
Catalog hashes never grant actions, trigger fallback or promote PENDING memory.
Acceptance of APP wiring and physical audio remain NO_DATA(runtime_owner_pending).
"No task evaluation supplied" means absent from this census input, not "this
model has never been tested". The preserved176/177 historical task evidence is
queried through its own existing contract and exact model/task scope. Keep those
sources visible; do not relabel their dated results as current admission proof.

## Minimum proposed measurements · execute later, one owned job at a time

1. Establish an idle resource lease with the runtime owner and verify the exact
   node/backend/digest, scoped task grant, budget, timeout/cancel and durable
   uncertain-outcome reconciliation. Do not unload someone else's resident.
2. Reuse `benchmarks/station-96-first-pass-20261029/smoke.py` and its public
   fixture. Three separately started two-sample repetitions give6 observations
   per exact context/profile. Report all failures, min/max/median, load and wall
   apart from generation; no claimed p95 or cold-start control from6 samples.
   A cold-start experiment needs a separately owned idle setup, never a silent
   unload/restart during another session.
3. Record configured context/input/output limits and task-bound peak process/
   host/device RAM with sensor scope/resolution. Sampled peaks are lower bounds;
   shared UMA is not additive independent RAM+VRAM. Record PSI or NO_DATA and
   memory reservation headroom; metadata RTT and weight bytes are not envelopes.
4. For useful task quality, reuse independent baseline/holdout/regression/
   negative-control rules from176/DFA/B5. Pin corpus/license/provenance/splits,
   scorer and acceptance thresholds BEFORE running. One public sort case or a
   throughput test does not qualify programming, vision, retrieval or a judge.
5. Only after isolated task measurements, propose an owner-approved concurrency
   probe with a critical-session E-STOP and fresh resource accounting. Energy
   requires an appropriate meter; otherwise NO_DATA. No numerical scheduler
   limit, model selection or training is activated by this proposal.

## Existing browser mini-guide · candidate only

Reuse [WEB source](https://github.com/piskyRpapalo/preceptoros-web/blob/main/public/game/web_node_brain.js)
and its [existing manifest](https://github.com/piskyRpapalo/preceptoros-web/blob/main/public/models/web-node/manifest.json).
Source blobs verified in GitHub: d802e899ca82bf5e24e69576f09b3152fb136eed and
94c33954263e2abaca9e43dfcce9726c25c1d442. Manifest SHA256
`1afc8206d3f9796ef17b01268c59f6bda54e85bf88e61dcdacc7967bf37bb87b`.
SmolLM2-135M-Instruct adapted guide, Q4_K_M, five chunks105,453,984 B,
wllama3.8.1 JS/WASM. Model/runtime licenses Apache-2.0/MIT are DECLARED by that
source, not a new corpus-license review. Manifest declares19/32 versus base2/32;
this LAB did not rerun or independently validate that score. Runtime code has
consent, pinned bytes/cache and offline paths. Its deterministic page-controls/
missions overrides must be attributed separately from model answers in any
future evaluation. Do not credit wrapper answers as model accuracy.

Candidate bounded tasks: sourced read-only help snippets and short summaries,
subject to separate holdout, hallucination/abstention and physical-device latency/
memory tests. Authorization/routing/resource admission stay deterministic and
host-owned. Do not train another mini-orchestrator, download weights, load the
browser engine or count this candidate as connected to Hexelion. A LoRA needs
matching base/runtime. APK1.0.1 is TWA per the commission; current phone inference
and APP integration remain NO_DATA. Claude owns installation and identity.
