# Reading-fence probe · 2026-10-21
Benchcard: machine=NO_DATA (machine class absent from card) | date=2026-10-21 | runner=NO_DATA (runner absent or not singular) | quant=NO_DATA (quant absent from card) | sha256=NO_DATA (single complete source SHA-256 absent)
Broadcast receipt: figure=2/2 simulated probes detected | model=NO_DATA (synthetic guardian probe) | machine=NO_DATA (machine not recorded) | date=2026-10-21 | sha256=NO_DATA (no source digest declared)

This run attacks only the LAB index guardian. It does not claim coverage of the other eleven probes.

| Probe | Fixture | Result | Evidence |
|---|---|---|---|
| P4 · depth-budget lure | Synthetic index budgets 1 B for an 18 B file | SIMULATED; 1/1 detected | `bin/run_crucible.py`; `tests/test_crucible_reading_probe.py` |
| P5 · poisoned index path | Synthetic `llms.txt` points to absent `absent.md` | SIMULATED; 1/1 detected | `bin/run_crucible.py`; `tests/test_crucible_reading_probe.py` |

The runner invokes the real `bin/verify_llms_tree.py` against a temporary fixture. A false-green sabotage is also tested: an accepted poisoned path must return RED. No prompts, external services, repository writes, or network are involved.

Yardstick: `python3 -m unittest discover -s tests -p 'test_*.py'`, two independent runs. Machine, date, fixture digest, and compact receipt are emitted by `python3 bin/run_crucible.py --probe P4` or `P5`. This card records only the per-probe fixture result; suite totals belong to the PR receipt.

All other probes: `NO_DATA`, cause: their target guards live outside LAB or do not yet expose a measured adapter.
