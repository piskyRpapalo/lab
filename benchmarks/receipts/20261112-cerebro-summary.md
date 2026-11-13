# CEREBRO-CONTEXT-01 · public composition evidence

Measured on 2026-11-12, 22:49–22:50 UTC. Source runtime:
`6bc70e493a2c53509ee7ddf53879d886854880e9`, stacked on LAB #176.
Original APP libraries from main `2dd6549fcdb738914161844ac895477af11d6687`.
No APP edits, real user DB writes, conversation turns, service restarts,
downloads, LoRA training, printer actions, merge or deployment.

## What actually completed

Two independent operator-authorized public experiments:

1. Original APP `indice_rack.buscar` retrieved a public synthetic source from a
   new isolated FTS index. Original `hexelion_book` checked hashes, bounded its
   prompt, and verified a deterministic public quote and lexical relevance.
2. The consumer checked source/implementation consistency and snapshot TTL.
   It labeled the document as a snapshot, never a live device measurement.
3. Two Session-witnessed native sort baselines passed independent order,
   length and multiset checks. Original Hexelion proxy generated a real bounded
   `DELEGATE_LOCAL` choice using those receipts and the context digest.
4. Existing host exact-task grants authorized native execution. Model output
   granted no permission. The worker used zero generation tokens.
5. A canonical execution receipt was proposed to the original APP memory
   writer in a new private demonstration DB. It committed one PENDING draft.
   Another fresh connection reconciled that receipt without inserting again.
   Engram count stayed zero; no promotion API was called.
6. One cycle record fed identical text/speech summaries and a matching machine
   projection. Host-local chain verification reconstructed baseline roles,
   planner input/context binding and the delegated task before success.

This is a library composition E2E on one public sorting case. It does not claim
live APP/H3 adoption, real user memory update, an arbitrary-task autonomous
brain, semantic accuracy or heard Acho audio.

| Measured value | Trial 1 | Trial 2 |
| --- | ---: | ---: |
| Overall outcome | MEASURED | MEASURED |
| Witnessed task receipts | 4 | 4 |
| Planner generation tokens | 44 | 116 |
| Worker generation tokens | 0 | 0 |
| Approved per-trial token ceiling | 512 | 512 |
| Remaining local allowance | 468 | 396 |
| Whole-cycle client wall time, ns | 16930747454 | 3899809577 |
| Pending drafts / engrams | 1 / 0 | 1 / 0 |
| Durable reconciliation / chain / projection checks | PASS | PASS |
| Context / cycle receipt bytes, canonical | 660 / 747 | 660 / 747 |
| Artifact bytes | 12015 | 12015 |

Sequential timings are not a proven cold/warm comparison: residency, device
placement, competing work, power and temperature were not paired with these
trials. Model token counts differ; no deterministic model-generation claim.
The fixed-clock contract tests reproduce identical complete cycles; native
outputs in both real runs have the same SHA-256:
`a8eb80395b27d66237d2f8635ed35677fdbde3516027a924efefab5dafc3a2ee`.
One repeated fixture remains one case, not independent semantic accuracy data.

## Artifacts and verification

- [Trial 1](20261112-cerebro-public-1.json), file SHA-256
  `a57fb8ef416e59c0d7c19c03b7486178dc5e92ced8cd07cc68bbdf7aebce254d`.
- [Trial 2](20261112-cerebro-public-2.json), file SHA-256
  `869ee3f6d65fa3739837a89c356c9d21619d3ed6bd501baf0aea3de7f6e17a9e`.
- [Canonical test receipt](../harness-receipts/20261112-cerebro-contract-tests.json):
  679 tests twice, 678 passed, one existing skip, zero failures/errors;
  local Linux x86_64 / Python 3.14.4; receipt `35b6fc12c2e91b91`.
  Original APP-memory integration ran locally. CI without that checkout skips
  that integration explicitly; remote exact-head CI is separate evidence.
- [Mutation evidence](20261112-cerebro-sabotage.json): 14 actual in-memory code
  mutations detected in each of two runs, zero test errors. Reproduce:
  `python3 -B bin/cerebro_contract_sabotage.py --output "$RECEIPT"`.

Original source-file hashes, exact tasks, task/receipt/context references and
byte ceilings were independently recomputed locally against the source commit.
APP dependencies were rehashed; all eight execution receipts passed the existing
validator. No raw source, query, model response, private/absolute path, credential or private ID
appears in the artifacts. Hash integrity is not cryptographic authorship or
model-weights attestation. Session witness is host-local authority evidence.

The workflow companion checks also passed twice: Norte 5, Node 7, llms 2,
and indexed-tree 11996 B within 12109 B. These are local checks, not GitHub CI.
Tests invoke no real models. Synthetic chooser/storage fixtures are explicitly
marked; the two artifacts above are the real model/library measurements.

Initial red results and H5 defects remain in the feature document. The first
mutation round caught 10/11: a weak test swallowed its own assertion inside a
lost-acknowledgement callback. A caller-side attempt counter fixed the test.
Final mutation set adds H5 prompt/context/outcome regressions: 14/14 twice.

## Remaining integration work

The host must supply its existing effective authority and a durable execution
journal; Session replay alone is process-local. The draft adapter's durable
reconciliation does not attest historical execution after a whole host restart.
Cooperating memory writers share the lock; uncoordinated writers are outside
the guarantee. Source refresh is point-in-time, not a cross-service transaction.
No second state producer is installed. See the [feature/integration contract](../../odd/tasks/cerebro-context-01.md).

`NO_DATA(host_not_wired)`: live APP/H3 consumption and actual user memory.
`NO_DATA(not_measured)`: heard audio, general model selection, semantic score,
hardware placement, calibrated concurrency and energy thresholds.
`NO_DATA(not_attested)`: server network isolation; numeric client loopback alone
does not prove the service's own egress configuration.
LoRA remains NOT_AUTHORIZED; LAB176 corpus, holdout, cost and review gates apply.
