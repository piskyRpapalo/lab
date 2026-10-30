# NORTE B4 · offline intake preflight

Status: propose-only, dependent on Lab PR #126 (B3 record contract). Plan
authority: merged Lab #125 / NORTE plan. This slice adds no data transfer,
repository write, filesystem read, network call, game, model or training.

## Contract

`benchmarks/norte_intake.py` wraps one validated B3 record in
`preceptoros.norte-intake/1`. It checks the web commit's full-hash syntax and
recomputes SHA-256 over canonical B3 record and Bubble frame bytes. The device
field still must be `NO_DATA` or match an explicit canonical census allowlist.
The closed envelope is below 16 KiB.

These hashes prove byte consistency only. The function does not verify that a
web commit exists or contains the claimed frame, authenticate a signer, or
approve a transfer. A human must verify source provenance and authorize the
transfer path before any receipt is accepted into Lab. There is no importer or
storage route in this slice.

## Measured gates

- Current Lab source for this proposal is B3 PR #126 at head `5be0c219`; it
  supplies the record judge. This PR targets that branch and is stacked until
  #126 is merged by the Mesa.
- Aduana D7 production `/health` returned HTTP 200 while `/api/v1/latidos`
  returned 404 on 2026-10-30. No game-result feed is measured here.
- No duel result or source frame was supplied. Fixtures are synthetic and keep
  result/date/device/seal as caused `NO_DATA`.
- The approved N4 public-export path and N5 training eligibility remain
  `NO_DATA`; this preflight cannot satisfy either gate.

## Checks

`tests/test_norte_intake.py` covers deterministic bytes, mutation detection,
malformed provenance, closed fields, and the census allowlist. All test values
are synthetic; hashes are not cryptographic signatures or source attestations.

## Log

- 2026-10-30 · created after a read-only measurement of the intake dependencies;
  no B4 record was transferred or stored.
