# Chunk responder · demonstration contract

Status: proposal and offline prototype. No deployment, model download, legal certification, or live request was performed.

## Read-only source inventory

- The current web tree at commit `183f2ddd` records the active upper view in `body[data-view]` (`docs/rebuild/examples/face_panel.js:60,77`); its `heads` map names `map`, `battle`, `profile`, and `info` (`:4-8`). The permanent chat stays below the view. The browser sends only public identifiers, never DOM text or visitor utterance.
- Lab `proposals/voice-pipeline-mvp-20261024-v2/CONTRACT.md` (source app main `7885afe88ad8a456d6af91aa08a62998818b5c9c`) defines complete visible-title inventory and the deterministic priority/order plan. This contract reuses `reading_plan: plan-del-guion` and the screen's ordered title IDs; it does not create a second reader.
- Study `13-rosetta.md:102` calls `chunked-web-decisor` proposed and points to app `decisor.py`. This web prototype is separate from the semantic chunker `p0x/mente/pipeline/chunk.py`, whose own file calls its Chonkie thresholds stubs. The exact sealed 07-Oct source document was not located in the read-only inventory: `NO_DATA · source path unavailable`; the doctrine below is taken from the commission text and must be re-anchored to that document before a production acceptance.

## Decision-model architecture anchor

The Sovereign's sealed SPEC-1 addendum defines the roles: **Web = eyes, App = body, Lab = brain**. The addendum's exact corpus path and commit were not supplied in this checkout: `NO_DATA · citation locator unavailable`; its text is treated as the governing input, not reconstructed. This package implements only the Web eyes contract, and is reusable as a typed interface by App and Lab. It does not implement the App decision models or claim a binding decision.

The cascade order is `stdlib rules -> choice model -> mini orchestrator -> large model`; spend the expensive token last. Tier 1 sealed rules stay in front of any model. A Tier 2 choice model is a preceptor, not an oracle: its proposals use typed `choice`, `score`, `noul`, and auditable probabilities, and confidence is treated as a suspect signal; determinism is preferred before any MoE. Sealed rules plus golden cases validate proposals. A deterministic/binding choice is never delegated to a model, and an irreversible choice is never made by an agent without the carbon. This responder deliberately emits no `score` or probability because it has no Tier 2 model proposal; inventing confidence would be misleading.

For this prototype, the local exact-phrase allowlist is a **Tier 1 demonstration rule**, not the requested production moderator model. It runs before category selection. A future choice-model adapter must return a typed proposal to Lab/App for sealed-rule and golden-case validation; it cannot change canon or authorize action. The Worker sees only the already-approved public category/screen signal and returns a deterministic eyes-level chunk. Nothing in this flow signs, calls, adopts, transfers, mutates, or binds.

## Two-stage dataflow

1. The browser-local moderator receives the visitor text and returns `ALLOW + category`, `ABORT`, or cause-bearing `NO_DATA`. The included implementation is a finite exact-phrase demo allowlist plus a small injection tripwire. It is not a general moderator model and does not claim to detect every attack, satisfy EU AI Act/GDPR, or replace risk review. Unknown input fails closed. The actual model/runtime/policy hash remains `NO_DATA · model not selected`.
2. Only after local `ALLOW`, the client may send the public signal below to a stateless Worker. Visitor text, user IDs, personal context, screen prose, audio, and private state are forbidden fields. An attack aborts locally and makes zero Worker calls. The Worker is a blind switch over a bundled public canon map; it has no AI binding, storage, signing key, tools, action route, or outbound fetch.
3. The same resolver and embedded canon power `routeOffline`; loss of Worker/network does not disable the sample categories. `demo.html` is a local-only harness for this fallback. Production wiring must pin this fallback in the page's offline asset set and prove the no-network behavior before release; the current live page is not wired by this lab-only proposal.

## Request/response

Request schema is `preceptoros.chunk-request/1`, JSON UTF-8 no larger than 1,024 bytes. Exact allowed top-level keys: `schema`, `gate`, `policy`, `screen`, `category`.

```json
{"schema":"preceptoros.chunk-request/1","gate":"ALLOW","policy":"demo-allowlist/1","screen":{"id":"guide-v1","active_view":"map","reading_plan":"plan-del-guion","title_order":["map-title","chat-title"]},"category":"screen_help"}
```

`screen.id` is a public screen/canon identifier; `active_view` is one of `map|battle|profile|info`; `reading_plan` must identify the already-existing voice plan; `title_order` carries 1–16 existing title IDs, not text. `category` is selected by the local moderator from `greeting|screen_help|controls|privacy`. The `gate` field is a flow marker, not a cryptographic attestation; the Worker is not a security boundary. Unknown keys (especially `visitor_text`) are rejected. An invalid/oversize request returns HTTP error with `NO_DATA` cause.

Response schema is `preceptoros.chunk-response/1`. A hit returns status `CHUNK`, the same public screen/view and title order, `reading_plan`, category, stable `chunk_id`, source `embedded-canon/1`, and the exact canon string. The UTF-8 byte length of each `chunk` is strictly below 150. A miss returns `NO_DATA` with a stable cause such as `canon_chunk_absent`, `screen_context_invalid`, or `moderator_gate_missing_or_invalid`. No timestamp, randomness, conversation history, model-generated prose, signature, or action field exists. JSON response size is not the 150-byte chunk limit.

```json
{"schema":"preceptoros.chunk-response/1","status":"CHUNK","screen":{"id":"guide-v1","active_view":"map"},"reading_plan":"plan-del-guion","title_order":["map-title","chat-title"],"category":"screen_help","chunk_id":"guide.screen-help/1","chunk":"La vista activa se lee en el orden de títulos indicado.","source":"embedded-canon/1"}
```

`NO_DATA` body is exactly `{ "schema": "preceptoros.chunk-response/1", "status": "NO_DATA", "cause": "<stable-cause>" }`. Worker transport statuses are 200 for `CHUNK`, 400 for invalid/absent signals, 405 for a non-POST method, 413 above 1,024 request bytes, and 415 for non-JSON content. All responses carry `Cache-Control: no-store`.

## Offline model and weight policy

The current demo accepts only exact, listed phrases. The local moderator receives the utterance; `makeRequest` emits no payload on `ABORT`/`NO_DATA`. If a later moderator needs weights, download starts only after a separate explicit user gesture and before download shows origin, exact byte size, and expected SHA-256. The client verifies the hash before enabling the model; absent origin/size/hash or mismatch is `NO_DATA`, never silent fallback to a remote provider. No weights or download mechanism are included here.

## Runtime choice and boundaries

Workers AI is not selected. There is no model invocation, token billing, or model latency in this prototype; those figures are `NOT APPLICABLE` to the deterministic Worker and must not be reported as measured performance. Worker request latency and Cloudflare cost are `NO_DATA · no deployed measurement`. Keeping the Worker static avoids shipping private input and preserves deterministic output; it also means open-ended answers are unavailable.

The web model is demonstrative and may only classify to the listed pure categories and return existing canon chunks. It never signs, calls tools, decides canon, adopts, transfers, mutates, or authorizes. Cloudflare receives only a public category and public screen IDs; it is not a relay for private input. This is a data-minimization design, not a legal-compliance claim. There is no logging code or persistence in the handler.

## Cache/deploy note

No deployed file changed. If a future release changes HTML or its imported client module, purge the relevant edge cache after the manual deploy, then measure the FARO byte comparison. A successful deploy alone is not evidence that edge HTML is fresh.

## Verification

`node --test tests/chunk_responder.test.mjs` verifies the offline twin, Worker handler, limits, stable output, allowed fields, and no outbound fetch/clock/randomness. The sabotage cases are unknown canon, attack input, unexpected/private payload field, denied gate, oversized request, invalid method, and stale/missing transport. The CI workflow runs this test in each of its two full passes. This proves code-level behavior only; model quality, legal conformity, installed-page offline behavior, Cloudflare timing/cost, and real user comprehension remain `NO_DATA` with the causes above.
