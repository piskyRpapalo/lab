# Lore por edificio: índice de procedencia

- Commission: buzon#30 ·6523629460. Canon: decree ·6523629544.
- Explore: `ideas13oct v2.0.1` is authority (2026-10-13, SHA-256 `dd3ed9ec…`); it names four of nine objects. `ideas6oct` is older rationale (2026-10-06, SHA-256 `80f61917…`), section heading `2.5 El edificio`.
- Measured source collision: `ideas6oct` repeats section number 2.5; an earlier heading is `Atlas / schemas públicos`. The index selects the later, exact heading named by the decree and records the collision.
- Implement: add `lore/building-index.json`; four canonical names and claims cite authority, rationale and decree. Five slots remain `NO_DATA`; generated `unknown-*` keys are index placeholders, never canon IDs.
- Ground truth: source dates and hashes are pinned; no public repository path or private identifier is embedded. Newer authority wins; older context explains only. Conflicts are explicit.
- Check: parse JSON; assert nine rows, four named `HECHO`, five `NO_DATA` with causes, and valid citations. Adversarially remove a cause or source and require rejection.
- Log: 2026-10-30 · source extracts and hashes read; duplicate §2.5 identified; no lore added for the five unknown objects.
