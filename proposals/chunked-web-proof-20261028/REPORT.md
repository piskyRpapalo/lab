# NORTE 7 · local proof report

## Result

`EMULATED · locally measured`. A deterministic synthetic 4-class choice model was served from a loopback web origin in four contiguous files. Chrome displayed the origin, exact total and all per-chunk byte ranges and hashes before any weight request. There were zero weight requests before the user-action control was triggered; the explicit download control then fetched exactly four files. Chrome reported and the client verified 25,000,000 response-body bytes. Each chunk passed its declared length and SHA-256 check before IndexedDB storage. A fresh empty cache returned `NO_DATA · cache_chunk_missing`. Unit sabotage also verified corrupt-cache and missing-network causes.

Repeated bounded input produced the same category and fixed chat text in both browser runs. SHA-256 of the exact chat text: `605e71b9dc8e0cbdcee1150f61d00bc2659c9ba9f9a217e6ce030788c04b2dde`. The response is fixed demonstration text, not generated prose. The chat panel is a local fixture implementing the exact `AtlasRadioChat.dice({quien, fuente, sello, texto})` shape from open PR #363. This demonstrates the contract call and a visible answer, not integration into a merged world surface.

## Measurements and receipts

- Scope digest: `7fd692ca24b79eb4e8acc6ad37e290d47a0431c4b068be1c9203f77b11003dc0`.
- Pinned source-list digest: `3a9d31cc6d35a99cd57c078c5dbc20a1ec933f197a7d8c5ef505905da0047b8c`.
- Manifest SHA-256: `5687756df72aa28e7619bc61981ac56a0db683570b01da0315a2710d93ebfd51`. Individual chunk hashes and boundaries are in `model/manifest.json`; combined chunk-hash digest: `b3abdbe8e4ab1092c2a47b1d69999f6cdb4e6f559d1e4b6600285d3893a89eb2`.
- Browser runs: 2026-10-28 00:13:25 UTC and 00:13:26 UTC; Linux x86_64, Google Chrome 155.0.8059.39. Command: `python3 proposals/chunked-web-proof-20261028/run_browser_proof.py`.
- Browser result in each run: source visible before fetch; 0 pre-action weight requests; 4 chunks × 6,250,000 B = 25,000,000 B; cache miss cause `cache_chunk_missing`; repeated chat output equal; 0 Worker calls.
- Node checks: `node --test proposals/chunked-web-proof-20261028/tests/chunk-model.test.mjs`, run twice on the same source tree on 2026-10-28; 4/4 passed each run. Runtime: Node.js 22.22.1.
- Lab yardstick: `python3 -m unittest discover -s tests -p 'test_*.py'`, two runs on Linux x86_64, 2026-10-28; 236 tests each, 1 skipped, both passed. The earlier `STATE.md` snapshot is stale; this is a fresh run at this feature ref.
- Generator ran twice and reproduced the four binary digests and manifest byte-for-byte. Commands and model details: `generate_model.py` and `model/manifest.json`.
- `RECEIPT.json`: 979 bytes, including both run dates, scope/source digests, chunk-set digest, manifest/output hashes and explicit gaps.

All source pieces in this feature are below 16,384 B. The four model files are each below 25 MiB; 25 MiB applies per deployed chunk/file, not to the total site. The proof used only loopback HTTP; it did not contact external services.

## Limits and causes

This is a synthetic sparse weight table whose tiny declared vocabulary is useful only to test deterministic transport and integrity. It proves no broad intent coverage, model quality, accessibility acceptance, or production fitness. The moderator is a narrow local demonstration, not an EU AI Act/GDPR certification. The manifest hashes provide byte integrity relative to the displayed manifest, not publisher authentication.

The 07-Oct manifesto could not be located at a pinned source revision: `NO_DATA · exact source/revision missing`. Production weights, license, publisher authenticity, moderator coverage, measured rack shortcuts and their evidence are `NO_DATA · no accepted source/model supplied`. The actual #363 world integration is `NO_DATA · PR remains open and this branch did not edit WEB`. Offline service-worker installation/persistence and quota/eviction are `NO_DATA · not exercised`. The active `juez.py` and `calibra_juez.py` source revisions are `NO_DATA · only archived snapshots were found`.

No Worker was authored, queried, deployed or invoked. A future Worker would require a resolved Cloudflare origin/zone; record `ORIGEN_MISMATCH` until that is resolved. Workers AI remains optional and unselected: cost and latency are `NO_DATA · no invocation`. There is no external call, model-provider request, signing operation, or state-changing action in this proof.

## Review path

The inventory and contract are in `INVENTORY.md` and `CONTRACT.md`. Local run instructions are in `CONTRACT.md`. The demo is not served publicly. This branch is a draft review candidate only; no merge or deployment is requested by the proof.
