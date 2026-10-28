# AI security corpus · 2026-10-28
Broadcast receipt: figure=NO_DATA (corpus only; no evaluated run) | model=NO_DATA (no model evaluated) | machine=NO_DATA (corpus has no device measurement) | date=2026-10-28 | sha256=NO_DATA (run has not occurred)
Benchcard: machine=NO_DATA (corpus only) | date=2026-10-28 | runner=NO_DATA (judge is a later slice) | quant=NO_DATA (no model evaluated) | sha256=NO_DATA (run has not occurred)

Twelve original synthetic scenarios for lab issue [#108](https://github.com/piskyRpapalo/lab/issues/108), covering seven requested categories. They are author-written fixtures, not an evaluation result, a representative security dataset, or a complete standard assessment. Fields are scenario, required and forbidden literal phrases, and the expected safe or NO_DATA outcome. The phrase lists are proposed criteria; a future deterministic literal judge can miss synonyms and cannot establish semantic correctness. Case review and adversarial validation are needed before interpreting any score.

The issue names an external interview-question repository as inspiration. Its GitHub API returned HTTP 404 on 2026-10-28; its contents and license are NO_DATA. No external text was copied. No private prompts, answers, or identifiers are included. A local model run is NO_DATA: no model was run for this corpus; migration and the issue's measurement gate remain to be established. Disk space reported by `df -h` on the rack on 2026-10-28 was 381 GiB available, subject to change; this observation does not prove the migration gate.

Agent: Codex · Model: GPT-6.1 Terra · Run: NO_DATA (corpus only)

## Proposed literal judge

`judge.py` reads the SHA-256 manifest and refuses missing, added, or altered case files and empty criteria. The manifest detects changes relative to these bytes; it is not a signature or a trust anchor. It normalizes Unicode NFKC, case and whitespace, then checks required and forbidden substrings plus a caller-supplied verdict. The output contains indices and causes, not the answer. A PASS means only these literal conditions passed: synonyms, negation, context and semantic safety remain NO_DATA without independent review. No seed is used because the procedure has no randomness. No model output is included.

`python3 -m unittest tests.test_ai_security_judge` exercises synthetic criteria and sabotages a changed file, removed file, removed criterion even after recalculating its digest, prohibited phrase and wrong verdict. An empty answer is rejected. These checks measure the judge, not a model.

Agent: Codex · Model: GPT-6.1 Terra · Run: NO_DATA (no model evaluated)
