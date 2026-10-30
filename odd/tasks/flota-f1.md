# Flota F1 · esquema v1 y primer NodeCard

- Commission: buzon#30 ·6523629460. Schema accepted by decree ·6523629544: `preceptoros.flota/1`.
- Sources pinned: lab main `3a7b739`; first-pass PR #121 and receipt buzon#30 comment ·6511028607 (2026-10-29). The station is the first sovereign row by decree ·6523194194.
- Implement: `contracts/preceptoros.flota-1.schema.json` and root `flota.json`. Every measured value has `valor/fuente/hora`; every gap has `causa/fuente/intento`. RAM, swap and VRAM are separate; no combined-capacity field exists.
- Station facts: exact RAM total/available, VRAM total, root free bytes, runtime version, two model labels, 70B size, per-call resident VRAM and runtime-reported GPU layer placement. Small-model exact bytes, queue, swap, load, listeners, gateway, sensors, heartbeat and full-fleet rows are `NO_DATA` with cause.
- Private census is acknowledged by PR #121 but its rows are absent from the versioned record. Do not reconstruct peer identities or values. Public file uses a functional placement label and no physical names.
- Check: schema/data shape, field-union requirements, required gap causes, first-row placement, RAM/VRAM separation, no private addresses/names; sabotage by deleting a cause must fail.
- Log: 2026-10-30 · source inspection complete; one measured station row; fleet remainder stays `NO_DATA` until a shareable source is commissioned.
