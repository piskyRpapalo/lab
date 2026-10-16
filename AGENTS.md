# Agent contract · lab

This is the single canonical instruction set for agents working in the lab. Tool-specific files point here and do not create parallel policy.

- The agent proposes and measures; a human signs PR by PR. Never sign, merge, choose the Mesa's seal letter, push to `main`, or push to Jetson.
- Start branches from current `origin/main`. Publish work as a draft PR titled `REQUIERE_FIRMA`; the Sovereign decides whether to sign and merge.
- This repository is the measured record. Each number carries source, machine, date, harness/command, and scope. Vendor figures are labeled as declared, never as local measurements. `NO_DATA` always has its cause; do not invent or silently omit fields.
- Do not commit raw prompts, raw answers, credentials, private identifiers, or personal data. Receipts and artifacts may contain counts and paths, never private values.
- Preserve human review and zero telemetry. Do not send model inputs, outputs, or node state to an external service as part of a benchmark.
- Yardstick: `python3 -m unittest discover -s tests -p "test_*.py"`. The local contract requires two runs for a piece. Remote CI is not configured in this repository; report that explicitly and never describe local checks as remote CI.
- Read `STATE.md` for the measured record and `README.md` for repository scope. If either is stale or does not contain a value, report `NO_DATA` with cause rather than copying an old number as live.

## Claude Code and Codex

`CLAUDE.md` points back to this file. Keep one source of policy; update this file first when the lab contract changes.
