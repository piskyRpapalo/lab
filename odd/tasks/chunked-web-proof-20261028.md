# Chunked web decision proof

## Objective
Deliver a runnable, locally served proof that a user-triggered, deterministic browser choice model can fetch, verify, cache, and use a 25,000,000-byte synthetic weight payload in chunks, then answer through the PR #363 `AtlasRadioChat.dice` message contract. No live Worker, deployment, external telemetry, or model-quality claim.

## Why
NORTE 7 commissions measured evidence for a chunked web model. The source corpus defines the web model as a local intent router to pre-measured shortcuts or cause-bearing `NO_DATA`; it must not generate prose or authorize actions.

## Scope
- Add reproducible synthetic weight generator, 4 chunk assets, manifest, browser loader/classifier, chat-contract demo, local run guide, receipts, inventory and contract update.
- Run proportionate unit/integration checks twice against the same branch snapshot; measure local HTTP bytes and deterministic output.
- Commit reviewable work units with Conventional Commit messages; feature-branch-chain is selected because the session is unattended.

## Constraints
- Start: `origin/main` at `3f49cf870213464a2dc2d8a3b26a9c99b92b6a90`.
- No writes to `preceptoros-web`, active branches, #363/#365, live Workers, deployments, credentials, signatures, or external model APIs.
- One 25,000,000-byte synthetic model split into four explicitly bounded files; each individual file <=25 MiB. Never claim model quality or production model selection.
- UI gives origin and exact size before the explicit download gesture. Verify every chunk SHA-256 before cache use. Missing/corrupt bytes fail closed as `NO_DATA` with cause.
- Screen answers are fixed canon chunks under 150 UTF-8 bytes; channel body under 1,024 bytes; no signature or action fields.
- English public names; no private identifiers or prohibited vocabulary in code/UI.
- Exact 07-Oct manifesto locator remains `NO_DATA` until found; do not infer it.

## Delivery
- Strategy: `feature-branch-chain` (unattended session).
- Forecast: ~500 authored lines plus generated binary fixtures (excluded from authored line count); split by coherent transport/model/demo and docs/receipt work units.
- Engram mirror: pending/unavailable; no Engram tool is exposed in this session.

## Tasks and acceptance
- [x] T1: Add deterministic synthetic weight generator and pinned manifest with declared chunk boundaries and hashes; generator reproduces bytes exactly.
- [ ] T2: Implement consent-gated browser fetch/cache verification, corrupt/missing-cache NO_DATA, deterministic fixed-point classifier, and chat adapter.
- [ ] T3: Add local demo/server guide and update inventory/contract with source anchors, boundaries, Workers `ORIGEN_MISMATCH`, and NO_DATA gaps.
- [ ] T4: Run checks twice, measure HTTP served bytes and same-input output hashes with UTC/machine/commands, retain concise receipts.
- [ ] T5: Commit coherent work units, push feature branch, open draft PR `REQUIERE_FIRMA`; no merge/deploy.

## Verification evidence
- T1: generator ran twice on 2026-10-28 UTC; all four payload hashes and manifest hash reproduced byte-exactly. Generator: `python3 proposals/chunked-web-proof-20261028/generate_model.py`.

## Log
- 2026-10-28: Read ODD reference, Lab AGENTS, README, STATE, prior chunk prototype, ideas 18/20, and PR #363 contract. Chose unattended `feature-branch-chain`.
- Engram task mirror pending because no Engram tool is available to this session.
