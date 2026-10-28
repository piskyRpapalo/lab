# Chunked web choice model · proof contract

State: `EMULATED` demonstration and measured local transport. No release, live Worker, legal-compliance claim or language-model quality claim.

## Doctrine and boundaries

The located 20-Oct ideas corpus defines this feature as a local intent router: it does not chat or invent prose; it selects a pre-existing shortcut below 1,024 B or returns cause-bearing `NO_DATA`. The exact 07-Oct manifesto locator is `NO_DATA`; see `INVENTORY.md`. This proof narrows that intent to a four-class synthetic demonstration and fixed response text.

- Browser holds the eyes surface only. It never signs, calls tools, mutates state, or authorizes an action.
- The user sees the exact total size, same-origin source, per-file size, offsets and SHA-256 before any weight request. Only the explicit **Download and verify weights** action starts those requests.
- Four 6,250,000 B files form a contiguous 25,000,000 B decimal payload (23.84 MiB). Each file is below the 25 MiB deployed-chunk ceiling; this does not assert a whole-site limit. Source files are each below 16,384 B. The sample chat message is below 1,024 UTF-8 B.
- Every downloaded chunk is size-checked and SHA-256-checked before it enters IndexedDB. Cache reads re-check size and digest. Missing, corrupt or unavailable bytes return `NO_DATA` with a stable cause; cache misses do not trigger a download. Download is a separate explicit user action.
- The local synthetic classifier uses signed int8 weights and fixed-point sums. Only a small declared vocabulary has nonzero weights; unknown or tied results return `NO_DATA`. The output is one fixed, prewritten category message below 150 UTF-8 B. No visitor text is logged, sent to a Worker, or stored.
- Chat output calls `AtlasRadioChat.dice({quien, fuente, sello, texto})`, matching the open PR #363 API shape. The page includes a clearly labeled local fixture, not the production radio module. Nothing in #363 is edited or assumed merged.

## Data and chat contract

`model/manifest.json` declares schema, total bytes, same-origin location, class order, chunk length, byte offset and expected SHA-256. Hashes prove fetched bytes match this manifest; they do not authenticate who published the manifest. Publisher signature/immutable release policy is not included.

`decide(text, verifiedWeights)` emits either:

- `{ status: "SIMULATED", category, text }`, where `text` is fixed canon under 150 UTF-8 B; the demo maps it to the #363 `sello: SIMULATED` message; or
- `{ status: "NO_DATA", cause }`, with no category or fallback model.

The adapter sends only `quien`, `fuente`, `sello`, and fixed `texto` to the in-page chat API. The proof checks that this serialized shape is under 1,024 B. There is no worker request envelope in the runtime path.

## Worker and optional AI proposal

No Cloudflare Worker was made, deployed, invoked or changed. A future Worker binding would first need an explicit zone/origin resolution; the current mismatch is recorded `ORIGEN_MISMATCH`. Any later static worker may receive only a public category signal after a local moderator passes it. Attacks abort locally; unknown inputs fail closed. Worker AI is optional and not selected. Its cost and latency are `NO_DATA · no invocation`; this proof has zero Worker calls.

## Unresolved design rules

1. Production weight provenance, trained-model selection, license, publisher authenticity and rollback policy.
2. Moderator threat coverage, reviewer-approved policies, intent labels, mixed-intent resolution and adversarial validation.
3. The real pre-measured shortcut catalogue, response source receipts, localization and #363 live integration acceptance.
4. IndexedDB quota, eviction behavior, model replacement/version invalidation and offline service-worker cache integration.
5. Cloudflare zone/origin, routing, data boundary, and whether a Worker is needed at all (`ORIGEN_MISMATCH` is unresolved).
6. If AI is later selected, the allowed model/binding, input limits, cost ceiling and latency yardstick require a separate proposal and measurement.

## Run locally

Requirements observed in the proof environment: Python 3.14.4, Node.js 22.22.1, Google Chrome 155.0.8059.39, and Python `websockets` 15.0.1. The demo server binds only `127.0.0.1` and makes no external requests.

```sh
python3 proposals/chunked-web-proof-20261028/generate_model.py
python3 proposals/chunked-web-proof-20261028/run_browser_proof.py
node --test proposals/chunked-web-proof-20261028/tests/chunk-model.test.mjs
```

For manual use, serve the proposal directory locally with `python3 -m http.server --directory proposals/chunked-web-proof-20261028 8765 --bind 127.0.0.1`, open `http://127.0.0.1:8765/demo.html`, inspect origin/size/hashes, choose **Download and verify weights**, then ask a bounded keyword. **Load verified cache** never downloads. Delete the browser's local IndexedDB database to reproduce the missing-cache result.

`run_browser_proof.py` opens Chrome through its local DevTools interface, checks no weight request before the explicit button action, observes missing-cache `NO_DATA`, clicks download, verifies all chunk requests and hashes, then checks repeated chat output equality. It terminates the browser and local server; no deployment occurs.
