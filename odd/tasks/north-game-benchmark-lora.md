# NORTE · game benchmark to Lab and LoRA

Status: proposal only. Commission: Sovereign north, buzon#30 ·6525335471; active decree ·6525528435 lifts the LoRA freeze and requires this plan before implementation. Each implementation slice still needs exact-head FIRMA and FIRMO. This document proposes dependencies and gates; it adds no model call, game rule, data transfer, or training run.

## Objective

Measure AI-controlled movement and wave combat in the single web map, launched from the installed app on each commissioned rack node, then bring approved benchmark evidence to the Lab and use suitable, provenance-preserving examples for LoRA. The web owns the map; the app is a local client and inference surface; Lab owns the benchmark record. A heartbeat proves liveness only; it is not a benchmark result. The north makes this flow active, subject to the plan, consent, SCRUB, and exact-head gates below.

## Measured baseline

- WEB `main` at `256f1a48f2cde6a41e2fd89d6b20ad33da5708cc`: `public/game/combate_ticks.js` is a pure deterministic round resolver; `public/game/wave_duel_scene.js` renders moving wave combat; `public/face/basic.html` loads both through the `/face` battle surface. `public/openworld/estado.json` is still `preceptoros.openworld-estado/1` with `nodes: []` (blob `ebeb22c0aceb2ae4cf46cc7239959efceb86aa8b`). Source presence does not measure deployed map interaction or AI control.
- APP `main` at `3a96d50c4472761e8783086ecaab4f1f207ce3aa`: `colony/` contains a local isometric map/liveness projection; `interface/face/bubble/combate_ticks.js` contains local deterministic combat ticks; `interface/face/face_fight.js` exposes user-selected patrols and automatic seeded play. No model-to-combat action bridge was found in the inspected source. `odd/tasks/dynamic-combat.md` leaves the strategy vocabulary and outcome-affecting starting-position contract unresolved.
- LAB `main` at `03128d14dfd07eff8163ffffda9ee9c38e4c4fd8`: AI-security corpus B1 (#110) and deterministic judge B2 (#111) are merged. `benchmarks/colony-surface-20261028/` measures browser animation callback cadence and memory scope; it does not run an AI or a combat. AI-security B3 remains blocked by its separate migration and disk gates in lab#108.
- Aduana D7 sender PR #10 is now merged as `41c19c52`; the sender publishes liveness, not game actions or bench results. The Worker, D1 binding, F1 identity/cell, and first live heartbeat remain unverified in the receipts. The live map JSON above remains the measured web main state.

## Proposed sequence

### N0 · Make the map available

The map-owning web lane lands and measures the single-map state reader, v2 producer, route and combat entry together. Record the exact web head and production seal. Do not make the app a second map or infer LIVE from source presence. Until measured: map state for rack nodes is `NO_DATA` with cause.

### N1 · Sign the game-action contract

Before connecting an AI, define and sign the observation and action schemas, allowed strategies, legal initial positions, seed derivation, invalid-action handling, human stop/override, and replay identity. Current combat determinism is for the same canonical teams, seed and ordered interventions; the existing intervention is `retira`. Strategy and position semantics are not silently added by this proposal.

### N2 · Add the local app adapter

The installed app requests the approved web-map/game state, calls only the already-installed local inference runtime, validates model actions against N1, and submits only allowed game actions. The deterministic web resolver remains authoritative for combat outcome. Preserve local prompts and answers. Per node, measure app build, local model-manifest hash, runtime, request/response timing, invalid-action count, replay result and resource readings; RAM and VRAM remain separate. Unmeasured nodes are `NO_DATA` with cause.

### N3 · Capture a scrubbed benchmark receipt

Use canonical web/app/game revisions, synthetic case ID, seed hash, model-manifest digest, sample count, action-latency distribution, resolver result, replay check, and scoped resource metrics. Keep raw prompts, model answers, private identities, credentials and machine paths out of public Git and broadcasts. The current Lab has no measured game-result intake route or accepted result schema; both are `NO_DATA` until built and signed.

### N4 · Bring approved evidence to Lab

Choose an explicit, human-reviewed transfer path before any app sends data off-device. First candidate: export only scrubbed receipts for public Git; no automatic telemetry. The app contract preserves zero telemetry and the Lab contract prohibits sending prompts, outputs or node state off-device unless a separately signed contract explicitly permits it. Validate every receipt against its source hashes and schema; reject missing or mutated provenance. No live web service or external model is a test target.

### N5 · Prepare LoRA data separately from evaluation

A benchmark metric/receipt is not by itself a training example. Candidate supervision is the approved sequence of game observation, model action, deterministic resolver feedback, and outcome; its exact fields, consent, redaction, retention, access, and train/validation separation need review in the plan before implementation. Public Lab artifacts must not contain raw prompts, answers, private identities, or credentials. Private local training material needs its own access and retention controls. The existing public Lab cards provide historical training measurements, not a current game-derived dataset or an importer. Training eligibility and LoRA outcome stay `NO_DATA` until an approved dataset and its provenance are measured.

## Ownership and gates

- WEB lane: sole map state, web combat entry and live-publication measurements.
- APP/LAB lane: local model-to-action adapter after N1, benchmark recorder, scrubbed receipt contract and Lab checks.
- Sovereign: approve this plan; sign action semantics and any data-transfer/training details not covered by the north; commission device activation, live runtime calls and each consequential release. No PR signature is implied by this plan.

Before code: measure each source on fresh heads and update this task. Before a live run: verify N0–N2, exact app/web/model hashes, node identity, local runtime and consent. Before Lab ingestion: pass N3–N4 and scrub review. Before LoRA: satisfy N5. A missing gate is `NO_DATA` with its cause, never a substituted fixture or inferred result.

## Checklist

- [ ] N0: web v2 state and combat entry measured in production.
- [ ] N1: action/replay contract signed.
- [ ] N2: installed app adapter measured per commissioned node.
- [ ] N3: result schema, scrubbed capture and deterministic replay judge accepted.
- [ ] N4: approved transfer path and Lab ingestion gate measured.
- [ ] N5: private training-set consent, provenance and LoRA validation accepted.

## Log

- 2026-10-30 · fresh source inspection recorded above; no model run, game action, transfer or training occurred.

## Next step

Submit this plan for review. After plan FIRMA/FIRMO, build one signed slice at a time. N0 follows the web queue; N1 must settle action semantics before N2. Do not transfer data or start a live game run before its slice is signed and its input/output boundaries are measured.

Agent: Codex · Model: NO_DATA · Run: NO_DATA (design only)
