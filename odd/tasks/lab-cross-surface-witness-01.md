# LAB-CROSS-SURFACE-WITNESS-01 · Lisbon source corroboration

Status: BUILD / TEST / PR under central commission, 2026-11-18. LAB-only scope.
Authority: Mesa private #3, comment 6988111141. No production writes or admissions.

## Problem

An APP request, a public LIVE seal, a Web Service Worker revision, a phone visible to ADB, and a human authorization are independent facts. Prior descriptions conflated them. WEB owns real-browser two-crab verification, APP owns Android, and BRAIN owns signed admission.

## Reuse / separation

- LAB already has bin/federated_node_snapshot.py for **loopback model metadata**, plus surface benchmarks. Neither corroborates the two fixed **public** world-state feeds with served SW and optional ADB.
- New bin/lisbon_surface_witness.py performs GET **only** from the allowlisted public WEB/Aduana/SW routes. It never submits a request, signs, reads credentials, changes phones, or calls private rack APIs.
- The client derives visibility from seal, not historical alive. Equal public feeds corroborate a projection, **not** authentic owner signatures or human approval.
- Optional adb devices -l outputs only DEVICE_PRESENT/NO_DATA for model S110, not serial numbers. An attached phone is not an installed/approved node.
- --expected-sw is an explicit expected source version; otherwise the release gate is NO_DATA. This does not publish any change.

## Command

~~~sh
python3 bin/lisbon_surface_witness.py --live --adb --expected-sw preceptoros-2026-25-ji
python3 -m unittest -v tests.test_lisbon_surface_witness
~~~

The receipt is under 1,024 bytes, contains only counts/states and no raw world-state, identifiers, serials, tokens, payloads or secrets.

## Acceptance

- Reproducible pure-fixture negative tests x2: divergent feeds, malformed/oversized JSON, duplicate IDs/map cells, stale-alive confusion, missing data, failed SW gate, URL confinement and optional ADB.
- LAB canonical yardstick green x2.
- Read-only public observation. Pending and approval stages remain NO_DATA(owner_inbox_not_checked) and NO_DATA(owner_approval_credential_chain_unobserved) without independent private receipts.
- No APP/WEB/Aduana modifications and no direct deployment.

## Limits and next

A real Android-to-LIVE E2E verdict requires owner approval, authenticated heartbeat and independent public observation tied by a trusted request identifier. The public feeds alone cannot prove that chain; BRAIN and APP must furnish authorized scrubbed evidence. Do not add an invented E2E success flag.
