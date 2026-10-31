# Canonical map-node identity and local brain binding

Status: PLAN · propose-only · no fleet or credential mutation in this task-plan commit.

Authority: [buzon#30 ·6547058047](https://github.com/piskyRpapalo/buzon/issues/30#issuecomment-6547058047), following the ODD single-source plan in [preceptoros-web#510](https://github.com/piskyRpapalo/preceptoros-web/pull/510).

## Objective

Record the two measured D7 map identities in the fleet evidence without publishing device identifiers, inventing a sender-to-device join, or turning the fleet inventory into a second world-state publisher. Define the private local-app sender binding needed before a local brain can be shown as belonging to either map node.

## Measured baseline · 2026-10-31

- Aduana `GET https://api.preceptoros.org/api/v1/latidos` returned HTTP 200 and `preceptoros.openworld-estado/2`, `cobertura=MEDIDO:2`. An earlier read in this work showed `primer-ancla` at `{q:0,r:0}` and `onexstation` at `{q:1,r:0}`, both `LIVE`. Latest read at `2026-10-31T18:26:48Z` retained both aliases/cells but showed `primer-ancla=LIVE` and `onexstation=STALE`; coverage 2 counts registered heartbeat rows, not two currently live senders. This is a freshness transition, not a missing identity or evidence of sustained liveness. Corroborating acta ·6547058047.
- Aduana's receiver contract says `PRECEPTOROS_HEARTBEAT_NODES` is receiver-side alias-to-cell configuration and `PRECEPTOROS_HEARTBEAT_KEY_HASHES` is separate, secret digest-window configuration. Successful authenticated publication proves the receiver currently accepts these two aliases; it does not disclose credentials or prove which physical app/model process owns either key.
- Lab `main` `f2c7e21c6209ebd1c734cae64afb13d5353b566b` still has `flota.json` schema `preceptoros.flota/1`, one private station row, and `fleet_coverage=NO_DATA`. The strict v1 node schema describes physical/runtime census, not a list of public map identities; it cannot represent these two aliases without a versioned schema change.
- The rack's local PWA on port 8740 now serves signed PreceptorOS main `44cf577f452a48bce49fe3dfd07e7a2e8ea04dac`. The process has no `PRECEPTOROS_HEARTBEAT_NODES`; the PWA source does not consume that receiver-side variable. Adding it to this process would not bind a brain to a node.
- The active local model reported by `/api/estado` is not sufficient evidence to join that process to either public alias. Physical sender ownership, sender key custody, and local model-to-node binding remain `NO_DATA`.

## Contract ownership

- Aduana remains the only D7 receiver and `preceptoros.openworld-estado/2` publisher. Its existing request is `preceptoros.latido/1`.
- Lab `flota.json` remains the physical/runtime inventory. A schema evolution may add a measured reference or snapshot of canonical public aliases and cells, but must retain `NO_DATA` for the physical-device join until separately evidenced; do not change the v1 document in place.
- The PWA sender, if later approved, uses a per-node alias plus a distinct credential delivered through a private service credential mechanism. It never receives the receiver's full node map, never publishes world-state v2, and sends no prompt, model output, user identity, device serial, or corpus to Aduana.
- The web consumes the one published v2 state. No consumer infers node life or identity from a model label, hostname, IP, or an app process being healthy.

## Build sequence

1. Preserve the two API-measured aliases/cells as immutable source evidence with timestamp and response digest; do not copy secret or physical identity data into GitHub.
2. Propose a versioned `flota.json` schema and fixture that can hold public map bindings separately from physical machine census. Require unique aliases and unique integer cells; preserve NO_DATA when the physical sender-to-machine relation is unknown.
3. Propose a PWA sender adapter only after each physical emitter has an explicitly assigned alias and its own credential. Use `preceptoros.latido/1`, one monotone sequence per node, bounded retry, and no payload beyond the D7 contract. Keep model prompts and outputs local.
4. Add offline tests for the schema, alias/cell uniqueness, absent-config fail-closed behavior, credential redaction, sequence monotonicity, and zero network activity without explicit sender configuration. Do not add real secrets or contact production from tests.
5. On the rack, the Soberano provisions distinct credentials and verifies a real authenticated heartbeat from each assigned device; compare the resulting v2 rows with the assigned local brain before claiming the chat-to-node binding. Rotate keys within the declared 24-hour window.

## Acceptance evidence

- One versioned fleet schema with compatibility/migration tests and exact measured public aliases/cells.
- The fleet file contains no device serial, hostname, private address, raw credential, key hash, model prompt, or corpus.
- Aduana remains the only publisher; the public D7 output stays v2 and sequence monotonicity remains enforced per alias.
- No chatbot-to-node claim until the physical sender, credential, alias, cell, and local model process are joined by an authorized rack measurement.

## Next step

Review this plan, then submit the schema/data change as a separate exact-head proposal. The app sender integration remains a separate implementation piece because it crosses the private rack service and the Aduana credential boundary.
