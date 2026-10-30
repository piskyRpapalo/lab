# NORTE B3 · local benchmark record contract

Status: implementation proposal · commission `preceptoros-web#427` plan and
Lab `#125` merged at `907341c`; one slice only. No game, model, transfer or
training run is performed here.

## Contract

`contracts/preceptoros.norte-record-1.schema.json` and
`benchmarks/norte_record.py` accept a round envelope plus a summary. The round
contains a Bubble/1 frame with one phrase per visible atom and a required
doctrine seal, a primary color from that frame, axial integer coordinates, and
a simulation tick. Tick is supplied data, never a wall clock. The Bubble frame
and the full round envelope are each strictly below 1,024 UTF-8 bytes.

Summary fields are seed, rules version, device pseudonym, date, result, and
seal. Every field is either `MEASURED` with source and observation time or
`NO_DATA` with its own cause, source and attempt time. A measured device must
match the explicit canonical pseudonym list supplied from `flota.json`; the
current versioned census has identity `NO_DATA`, so no live record can claim a
device. The seal is opaque supplied evidence: this slice does not generate a
signature or infer seal semantics.

No user identity, walker position, raw prompt/answer, hardware name, path,
network access, or file write is accepted. Canonical serialization is stable
JSON only; it is not a signature. B4 feed, app transfer and LoRA ingestion
remain out of scope and `NO_DATA` until their separate gates are met.

## Measured gaps

- Fleet device pseudonym: `NO_DATA`, cause: `flota.json` keeps the canonical
  identity field empty pending a measured private census.
- Result/seal in the fixture: `NO_DATA`, cause: no game run or upstream
  action/replay seal was supplied.
- Live frame and colors: `NO_DATA`, cause: no benchmark session was executed.

## Verification

`tests/test_norte_record.py`: deterministic canonical bytes; exact field sets;
caused gaps; device-census allowlist; SCRUB rejection; Bubble seal/phrase; and
1 KiB sabotage. The round writer, transfer route and semantic outcome judge
are not implemented in this slice.
