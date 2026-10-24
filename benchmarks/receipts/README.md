# Yardstick receipts · VC1 · 2026-10-19
Broadcast receipt: figure=NO_DATA (multiple suite receipts) | model=NO_DATA (test suites) | machine=NO_DATA (hostnames scrubbed) | date=2026-10-19 | sha256=NO_DATA (multiple receipt digests)
Benchcard: machine=NO_DATA (machine class absent from card) | date=2026-10-19 | runner=NO_DATA (runner absent or not singular) | quant=NO_DATA (quant absent from card) | sha256=NO_DATA (single complete source SHA-256 absent)

The measured runner emits only test counts and outcomes; it does not retain
names, stdout, stderr, prompts, answers, or hostnames.

## 2026-10-19

- Exact command: `python3 bin/measure_yardstick.py --output benchmarks/receipts/20261019-vc1.json`
- Result: `GREEN`; 34/34 passed, 0 skipped, 0 failures, in each of two runs.
- Runtime: Linux x86_64, Python 3.14.4.
- Source commit: `0839bb37deaed9635ee996503f3a2bbf1abb86aa`; tracked tree clean.
- Remote CI: `NO_DATA`, cause: this repository has no remote CI configured.
- Full machine-readable receipt: [`20261019-vc1.json`](20261019-vc1.json).

## 2026-10-24 · first remote CI run

- Run `40125508923`; head `4851f69dd0d41b51ca4068dd718bd8bb469f052d`; conclusion `success`.
- Parsed pasted GitHub Actions log offline. Three Python matrix jobs (3.10, 3.11, 3.12), two passes per job; unittest 221 tests / 1 skip / 0 failures per pass, `test_llms` 2/2, tree verifier 5 indexed paths.
- Parsed-log SHA-256: `e9ee6ae5f7e9c4b7b89207c3014f8cb38dc78219cae592f71206cdfac75f796a`.
- Physical audio and runner hardware class: `NO_DATA`, cause: the workflow log does not measure speaker output or identify a physical host class.
- Full structured receipt: [`remote-ci-runs/40125508923.json`](remote-ci-runs/40125508923.json).
