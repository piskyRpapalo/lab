# B6: Dual-judge evidence integrity

The November 11 dual pilot reports 276/300 truncated candidate outputs. This
consumer checks existing local artifacts; it does not run or replace a judge.
Canonical mission B6 links B7/H2/E3. State ownership remains B1/B5/C8/A3.

Run `python3 bin/check_dual_judge_evidence.py --manifest FILE` offline. No inference,
network, writes, producer changes or raw prompts/answers in published results.
The manifest schema is `preceptoros.lab.dual-evidence/1`: records, cases_per_class
and held_out. Records contain case (string), pass (integer), response reference
and two judge references. References contain relative path and SHA-256. Each
JSON artifact contains case, pass, termination (stop/length/unknown), member
(model/family), model_sha256 and a provenance reference. Provenance binds member
and model_sha256. Judges also bind response_sha256 and verdict
(SAFE/UNSAFE/UNCERTAIN). Files must resolve inside the manifest directory.
Inputs and each artifact are bounded at 4 MiB. Hashes verify byte integrity,
not authenticity: a fabricated provenance document cannot establish lineage.

The existing family gate remains unchanged and is reused for each judge.
An admissible pair means internally consistent, complete artifacts only.
Independence and semantic accuracy remain NO_DATA without external attestation
and independent gold respectively. Disagreement is counted, never voted away.
Exit 0 means integrity checked, 1 rejected evidence, 2 unavailable evidence.
Receipts are deterministic and below 1024 UTF-8 bytes including newline.

Tests use synthetic artifacts only. The 300-row fixture excludes 276 truncated
responses and admits 24 complete pairs; it does not remeasure the pilot.
Sabotages: altered hash, duplicated judge, same family, unknown termination,
missing reference, duplicate case and path escape. Repeat the tests twice.
Run repository CI commands twice before PR; H5 reviews before publication.
Rollback: revert this three-file slice, preserving the historical pilot.
No installation or live producer changes: production E2E remains NO_DATA.

Authorization: Sovereign BUILD L, November 11; merge requires exact-head FIRMO.
Signing book reference supplied by orchestrator:
5a0432a574e4c3cd38f675ace1cda04e92a62b75.
Next mission: B1 consumption contract with B5/C8/A3, no new state bus.

Agent: Codex Astra · Model: GPT-6 · Run: NO_DATA

Local validation (2026-11-11, Linux x86_64 workspace): 529 unittest cases,
zero failures, one skip, twice; separate Norte 5, Node 7, llms 2 and tree
budget check pass twice. Independent H5 reviewer reproduced two issues:
boolean/float artifact pass identity and inadequate escape test. Both corrected;
new tests cover strict integer identity, real external file and symlink escape.
Model aliases with identical digests are rejected. Network and inference are
absent from this consumer; repository publication and CI are separate operations.
