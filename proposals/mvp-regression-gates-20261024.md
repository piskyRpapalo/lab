# MVP regression gates · offline evidence contract

This package adds a fixture-driven judge for five regression families. It does not launch a browser, inspect a device, contact either product, or claim the synthetic baseline is a live measurement. The versioned evidence JSON can be emitted by later browser/app runners when those proposals land.

## Required evidence and verdicts

- **Narration visibility:** all 3 themes × portrait/landscape × heights 256, 320, 375, 430, 512, 600, 720 and 800 px; each case must report visible complete narration and page scroll 0. This is a sampled viewport matrix, not every possible pixel height.
- **Zoom:** explicit 0.60 and 3.00 bounds plus 1.00 reference. Each interactive object is measured at all three map zoom values; its reported screen-size pair must remain invariant. This tests object sizing under map zoom, not browser pinch-zoom behavior.
- **Contrast drift:** fixed pairs: basic 15.80/9.91, atlantis 18.27/9.61, zombie 15.11/11.93; tolerance 0.01. A drift is red. These are regression baselines only, not WCAG or EN 301 549 certification.
- **POST-EXPORT bytes:** evidence must mark the exported frame bytes as post-export, provide base64 payload and SHA-256, and cover every state in a hashed compiler state inventory for every theme. The judge decodes UTF-8 and counts actual bytes; >1,024 B is red. The known 1,017 B frame is a historical baseline with only 7 B headroom, not a new measurement in this fixture.
- **Task parity:** each task must use the same shared-fixture hash for WEB and APP. The judge compares exact state, messages, errors, controls and contract fields. Asset hashes and visual similarity are not parity fields.

The example fixture is synthetic and deliberately carries no product heads. Its green result only checks this contract. Production evidence must name real heads, runner/browser, command, timestamp, actual exported bytes and fixture revision before it can be treated as measured.

## Red-before-green sabotage

`tests/test_mvp_regression.py` sabotages missing viewport cases, scroll/hidden narration, zoom bounds, object size drift, contrast drift, pre-export frames, oversized or altered frames, task output drift and asset-only parity. Each must produce RED while the complete synthetic baseline remains GREEN. On 2026-10-24 in the LAB Python 3.14.4 shell, the focused validator passed 12/12 tests and the baseline CLI reported GREEN for 48 viewports, 18 zoom samples, 6 contrast pairs, 6 POST-EXPORT frames and 2 shared-fixture tasks. The baseline is synthetic, not product telemetry.

## Run

```sh
python3 -m unittest tests.test_mvp_regression
python3 bin/mvp_regression.py fixtures/mvp-regression/baseline.synthetic.json
```
