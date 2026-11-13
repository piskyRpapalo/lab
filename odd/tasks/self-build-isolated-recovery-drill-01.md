# SELF-BUILD-ISOLATED-RECOVERY-DRILL-01

A test-only fixture constructs two deterministic Git commits in a disposable
repository. The old tree contains a small function that passes a fixed test;
the candidate changes it to subtraction and fails that same test. The fixture
captures the actual Git binary diff through sealed_patch_snapshot, binds it to
the proposal, candidate and operation through self_build_lineage, and uses the
existing GitWitness with a SYNTHETIC stability callback. It clones the candidate
into a separate disposable Git directory, checks out the previous commit only
there, verifies previous tree ID, clean index/worktree/untracked state and actual
file bytes, and reruns the behavior test. No existing repository is restored or
mutated and no new runtime executor or journal exists.

The receipt records two measured local fixture runs, deterministic base/tree,
candidate, patch and operation hashes and monotonic durations. The new fixture
state DEMONSTRATED_IN_SANDBOX applies only to this temporary experiment; it is
not a readiness contract, real host recovery, source attestation or permission.
Both NO_DATA(real_host_recovery), NO_DATA(real_host_stability) and NOT_AUTHORIZED
remain. Timings are observations of the anonymous local runner, not a service
latency or rack resource estimate. The cross-run hashes do not confer authority.

Negative tests include bad/missing base, patch tampering, changed and restored
HEAD, expiration/revocation, missing restored file, continuing regression, wrong
operation, corruption of a temporary Git object, and UNKNOWN P2 with retained
budget. The last uses the existing journal, mirror and readiness projection;
the temporary drill does not retry an uncertain real operation. False rejection:
GitWitness accepts only supported docs fixture paths; other real tasks untested.
A Git tree hash alone does not validate unrelated files or host stability. This
does not establish concurrent host fencing, real signer, APP E2E or disaster
recovery. Rollback of the fixture change is removal through normal review.
