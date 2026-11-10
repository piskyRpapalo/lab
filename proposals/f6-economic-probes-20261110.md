# F6 · Economic red-team consistency fixtures

**State:** research-only; not a real market, financial operation, agent gate, or cryptographic verifier. Source: `ideas9nov.txt` addendum F6; [buzon#61](https://github.com/piskyRpapalo/buzon/issues/61). Extend Lab's existing Crucible **test vocabulary**, not its runtime or services.

Three synthetic probes:
- `reach_inflation`: claim cannot exceed distinct supplied receipt digests; matching digests are still unverified and return NO_DATA.
- `budget_overpromise`: claim exceeding declared available integer joules is denied; otherwise sensor evidence remains NO_DATA.
- `arbitration_spoof`: arbitrary agent attempting Sovereign arbitration is denied; merely claiming `sovereign` never grants authority.

```sh
python3 bin/f6_economic_probes.py /local/scrubbed-fixture.json
python3 -m unittest discover -s tests -p test_f6_economic_probes.py
```

**Acceptance:** three impossible-claim cases denied; plausible but unverified cases remain NO_DATA; test twice, output has no payload identities, no permissions or network. **NO_DATA:** live market, real A2A signed receipts, energy sensors, legal/economic model. A separate human-approved policy and E2E proof would be required before exposing any decision surface. Provisional schema only, not Babel-coined.
