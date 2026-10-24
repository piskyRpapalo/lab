# Proposal: post-deploy WEB freshness receipt

**State:** staged proposal; no deploy or live request performed.
**Branch:** `mistral/web-faro-freshness-receipt-20261024`.
**Base:** LAB `origin/main` at `108e2412caeebf079ebbe2fc11d20fa6561aa58a`.

## Procedure

After the authorized operator completes the existing manual deploy, run the
existing `atlas/faro.py` from a clean WEB checkout whose `HEAD` equals its
fetched `refs/remotes/origin/main`. Preserve FARO's stdout and exit code as a
local input. Then run:

```sh
python3 bin/record_web_faro_receipt.py \
  --web-repo /path/to/preceptoros-web \
  --faro-output /path/to/faro-output.txt \
  --faro-exit-code 0 \
  --deployment measured-deployment-label \
  --output /path/to/freshness-receipt.json
```

The label is an operator-provided public identifier. The recorder itself
makes no network request and does not deploy. It refuses to
produce a green result if the checkout is dirty, `HEAD` differs from the fetched
main ref, FARO's five summary fields are absent, any expected public artifact is
not counted equal, or FARO reports drift/errors. Exit `0` is green, `1` is a
measured drift/red result, and `2` is `NO_DATA` with a named input or network
measurement cause.

The receipt binds source commit, deterministic public-tree SHA-256, public file
count, `atlas/faro.py` SHA-256, exit code, all FARO counters, deployment label,
observation time, and transcript SHA-256. These values let the pending FARO
rerun consume the same format without copying raw terminal output into a
public report.

## Yardstick

The exact live byte comparison remains FARO's yardstick. The recorder verifies
that its recorded equality count matches the number of files in `public/` at
the named main commit. Local tests use temporary repositories and synthetic
FARO transcripts only; they validate parsing and receipt state, not a real
deployment. A remote FARO run and post-deploy freshness are `NO_DATA` here,
cause: no deployment or live site was contacted in this proposal.

## Receipt

- Local judge: `python3 -m unittest tests.test_web_faro_receipt` — 6 tests
  passed after implementation; initial import failure was the red baseline.
- LAB full gate: two passes. Each pass ran discovery (153 tests, 152 pass,
  1 skip), `test_llms.py` (2/2), and `verify_llms_tree.py` (5 indexed paths
  resolve; 11,695 B <= 12,109 B).
- Diff whitespace: `git diff --check` passed.
- Remote CI: `NO_DATA`, cause: no PR has been opened.
