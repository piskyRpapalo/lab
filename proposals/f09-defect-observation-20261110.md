# F-09 · Offline PR defect and sabotage observation

**State:** PROPOSAL; input claims are **not** verified against GitHub CI. Source: F-09 in `ideas9nov.txt`, [private audit](https://github.com/piskyRpapalo/buzon/issues/61), [public reconciliation](https://github.com/piskyRpapalo/preceptoros-public-mesa/issues/4). A separate slice from Lab F-08.

Standard-library-only, no network. The script accepts locally scrubbed `{"observations":[...]}` where each item contains opaque `id`, state `GREEN|RED|NO_DATA`, a closed `sabotage` declaration, and a typed `cause` for `NO_DATA`. It rejects duplicates, extra properties, missing causes, and invented sabotage outcomes. The output is aggregate counts and rational pairs `[numerator,denominator]`, not floating claims; unknown PRs are excluded from measured denominator but explicitly counted. Absent CI or sabotage observation remains NO_DATA, not a false green.

```sh
python3 bin/f09_defect_observation.py /local/scrubbed-obs.json
python3 -m unittest discover -s tests -p test_f09_defect_observation.py
```

The `preceptoros.lab.f09-observation/1` marker is a **provisional research envelope** pending Babel admission. **NO_DATA:** real CI joins, actual defect density in production, whether red preceded green on real PRs. Next implementation gate: verified immutable head and CI run IDs; no automatic remediation or merge.
