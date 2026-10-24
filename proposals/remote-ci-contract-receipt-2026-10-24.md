# Receipt · LAB remote CI contract alignment

- **What:** corrected the agent contract to match the checked-in PR/main-push
  workflow and strengthened its existing regression test.
- **Measured source:** `origin/main` `068052eb53df6cf09c2a660724ba27cd89f43b47`;
  `.github/workflows/pruebas.yml` runs on `pull_request` and pushes to `main`,
  with Python 3.10–3.12 and two full passes per job.
- **Red → green:** the new focused contract test failed before the AGENTS update;
  `python3 -m unittest tests.test_agent_contract` then passed 2/2.
- **Yardstick:** `python3 bin/measure_yardstick.py --timeout-seconds 300` ran the
  full local suite twice: 147 tests each pass, 146 passed, 1 skipped, 0 failures
  and 0 errors; both GREEN. Runtime was 3.118 s and 3.040 s, Python 3.14.4,
  Linux x86_64. These are local results, not remote workflow results.
- **Cost:** two tracked-file edits plus this receipt; measured test time was
  6.158 s total, excluding setup and receipt formatting.
- **Limit:** workflow configuration is verified in source; current remote CI
  execution status is NO_DATA because no CI run was inspected in this task.
- **Status:** proposal staged on `mistral/lab-gate-truth-20261024`; no commit,
  push, PR, merge, or signing.
