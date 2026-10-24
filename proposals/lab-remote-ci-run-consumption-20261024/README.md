# LAB remote CI run consumption recorder

## Purpose and evidence boundary

`bin/record_lab_ci_run.py` consumes pasted text only. It does not call GitHub,
read a repository, launch a workflow, dispatch CI, or transmit logs. The first
real remote result is still `NO_DATA`, cause: no run id/log for this recorder
has been supplied. Existing local test passes do not count as remote CI.

The measured LAB workflow at base `c74fd867e7e933060d3eadffe9fd65902b25dc1a`
uses Python 3.10/3.11/3.12 and repeats three gates twice per matrix job:
`unittest discover`, `test_llms.py`, and `verify_llms_tree.py`. The recorder
records each observed invocation independently; it does not assume a matrix
size or manufacture missing repetitions.

## Feed one completed run

Capture metadata and the run log with the operator's already authorized `gh`
installation. This proposal does not dispatch, rerun, or fetch a live service.

```sh
: "${LAB_REPOSITORY:?set the owner/repo measured for the LAB checkout}"
gh run view RUN_ID -R "$LAB_REPOSITORY" \
  --json databaseId,headSha,status,conclusion > run.json
gh run view RUN_ID -R "$LAB_REPOSITORY" --log > run.log
cat run.json run.log > pasted-run.txt
python3 bin/record_lab_ci_run.py --input pasted-run.txt --run-id RUN_ID
```

For a `gh run view RUN_ID --log` capture without the JSON header, supply all
four metadata values measured separately from `gh run view --json`:

```sh
python3 bin/record_lab_ci_run.py --input run.log --run-id RUN_ID \
  --head-sha HEAD_SHA --status completed --conclusion success
```

For a short human summary, prepend this single line and include the full gate
summaries below it:

```text
RUN id=RUN_ID head_sha=FULL_COMMIT_SHA status=completed conclusion=success
```

The parser accepts GitHub's tab-separated job/step/timestamp/log form, the
compact `RUN` line, and `gh run view --json` object text. It expects a completed
run and at least one complete result for each required gate. JSON output records
run id, head SHA, status/conclusion, per-invocation test counts/outcomes,
verbatim failure blocks, and an input SHA-256. `failure_details_state` explicitly
says when the run is known RED but the pasted log contains no failure text.

- GREEN / exit 0: run completed successfully and all three gate families have
  complete observed results.
- RED / exit 1: a completed run or gate reports failure; captured failure text
  is copied verbatim into the local receipt.
- NO_DATA / exit 2: absent or invalid input, run mismatch, invalid head SHA,
  in-flight/cancelled run, incomplete summaries, or missing gate family.

The input cap is 4 MiB of strict UTF-8. Preserve raw logs in a restricted local
evidence location; do not paste unreviewed failure text into a public report.
The tool hashes the exact submitted text and always returns `network_used=false`.

## Red-before-green sabotage

`tests/test_lab_remote_ci_run.py` first failed to import the absent module
(RED), then passed 9/9 after implementation (GREEN). Sabotage cases cover an
empty/incomplete log, wrong run id, missing gate, in-flight run, cancelled run,
two-pass tab-separated job logs, and verbatim failure text. Synthetic IDs and
failure strings are test-only.

## Receipt

- Piece: `bin/record_lab_ci_run.py`, its focused test, and this proposal on
  `mistral/lab-remote-ci-run-consumption-20261024`, based on LAB
  `c74fd867e7e933060d3eadffe9fd65902b25dc1a`.
- Cost/yardstick: local standard-library parser; focused sabotage suite 9/9.
  Two full LAB passes: 177 unittest tests each (1 skip, 0 failures),
  `test_llms.py` 2/2, tree verifier 5 indexed paths at 11,695 B <= 12,109 B.
- Remote CI consumption remains `NO_DATA`, cause: no real run log was supplied.
- No commit, push, PR, merge, signing, CI dispatch, or deploy.
