# Proposal: offline WEB artifact audit

**State:** staged proposal; no remote run or deployment performed.
**Branch:** `mistral/web-artifact-offline-audit-20261024`.
**Base:** LAB `origin/main` at `108e2412caeebf079ebbe2fc11d20fa6561aa58a`.

## Contract

`bin/audit_web_artifacts.py` compares a local build directory with every file in
`public/` at the fetched WEB `refs/remotes/origin/main`. It reads that revision
with `git archive`; it opens no socket and never checks out or changes WEB.
The manifest schema is `preceptoros.lab.web-build-manifest/1` and pins the full
source commit plus each relative path, byte count, SHA-256, and kind
(`asset` or `bubble_frame`). The compared file set must be exact. A Bubble frame
is capped at 1,024 bytes; the caller supplies and records the per-file and
whole-build ceilings because the build budget is a measured input, not an
unstated constant.

The static scan rejects literal external URL references and reports recognized
network calls whose target is not a statically readable local path as
`NO_DATA`. It does not prove runtime network silence: receipt field
`runtime_network` is always `NO_DATA: static scan only`. Dynamic code, browser
behavior, and unrecognized request APIs remain outside this judge.

Run from the LAB checkout with a fetched WEB checkout, artifact directory, and
manifest:

```sh
python3 bin/audit_web_artifacts.py \
  --web-repo /path/to/preceptoros-web \
  --artifact-root /path/to/offline-build \
  --manifest /path/to/web-build-manifest.json \
  --max-file-bytes 16384 --max-total-bytes 26214400
```

Exit `0` means the measured file set, bytes, manifest pins, and supplied
ceilings match. Exit `1` means a measured mismatch or detected external URL.
Exit `2` means a required input/ref or a static network target could not be
measured. A green result is limited to the named source commit and the supplied
artifact directory; it is not a browser-runtime or deployment claim.

## Local judge

Yardstick: `python3 -m unittest tests.test_web_artifact_audit` in this branch.
The tests build isolated temporary Git fixtures and make no network requests.
They cover exact bytes, missing/extra files, wrong pins, external URLs, dynamic
targets, the 1,024-byte frame ceiling, the total-byte ceiling, and a stale
source commit. The test does not establish the size or request behavior of a
particular WEB release; run it with that release's measured artifact directory
and explicit limits.

## Receipt

- Source yardstick: fetched WEB `origin/main` object, read through `git archive`.
- Local judge: 9 tests; all passed after the implementation (RED before the
  validator existed: import error, then GREEN after implementation).
- LAB full gate: two passes. Each pass ran discovery (156 tests, 155 pass,
  1 skip), `test_llms.py` (2/2), and `verify_llms_tree.py` (5 indexed paths
  resolve; 11,695 B <= 12,109 B).
- Remote CI: `NO_DATA`, cause: proposal has not been pushed and no PR run exists.
- Runtime zero-network: `NO_DATA`, cause: static scan cannot observe runtime.
