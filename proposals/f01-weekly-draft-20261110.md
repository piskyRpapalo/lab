# F-01 · Weekly draft from F-08 / F-09 aggregates (offline)

**Status: PROPOSAL, not a scheduled service.** Source: `ideas9nov.txt` F-01, [Mesa audit #61](https://github.com/piskyRpapalo/buzon/issues/61), [public Mesa #4](https://github.com/piskyRpapalo/preceptoros-public-mesa/issues/4). Does not supersede the single mission catalogue.

Compose `{"week":"2026-W46","f08":{"signed":2,"pending":1,"verification":"NO_DATA: unverified_ref"},"f09":{"green":3,"red":1,"unknown":2,"verification":"NO_DATA: unverified_CI"}}` in a **local, scrubbed** file. This prototype consumes only aggregates, not source events. Explicit `{"cause":"..."}` can stand in for either absent source. The output is below 1,024 UTF-8 bytes, deterministic with source-input SHA-256. No network, runtime dependency, mail, scheduled cron or live signatures.

```sh
python3 bin/f01_weekly_draft.py /local/scrubbed-aggregates.json
python3 -m unittest discover -s tests -p test_f01_weekly_draft.py
```

**Caveat:** these are declared observations; the tool does not verify the original F-08/F-09 source receipts or FIRMO. Its provisional envelope is not a new Babel term. **NO_DATA:** WBR operational state, real scheduled cycle, energy data, live CI provenance. Next: source-verified ledger connectors only after the corpus owner and reconciliation matrix have been approved.
