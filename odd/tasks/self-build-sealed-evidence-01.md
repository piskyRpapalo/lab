# SELF-BUILD sealed patch evidence

The memory_draft lock coordinates only cooperating writers; an unrelated Git
process can change and restore HEAD, the index, worktree, ignored/untracked files,
Git objects or directories without taking it. Double sampling cannot prove those
intermediate changes absent. No actual whole-host stability or durable fencing is
available here: NO_DATA(real_host_stability). Do not connect a synthetic callback
as a real GitWitness stability provider.

This independent Linux alternative captures bounded, caller-supplied patch bytes
in an anonymous memfd, applies kernel write/grow/shrink/seal seals, checks digest,
size, file identity, proposal reference and deadline on reads. Its integrity
verdict refers only to those captured bytes. Even a correct checksum and a
verified kernel seal do not prove those bytes came from the declared Git repo,
base, candidate, diff or a stable capture. Every result keeps source stability
NO_DATA and execution_authorized false. The host clock and Python process are
trusted; this is not a hostile-Python sandbox or a durable artifact. Restart,
unsupported platforms, process failure or missing handle require recapture;
no persistence, permissions or services are changed.

Expiry/revocation limits subsequent reads through the handle, not copies already
returned or duplicated descriptors. Consumers must not use a cached read as a
grant; action-time freshness, human approval, source provenance and recovery
remain separate NO_DATA dependencies. Seal verification only supports immutable
bytes, not exclusive access to the original repository or a production E2E.
Fixtures test kernel seals, HEAD flip/revert, noncooperative flock writer, source
replacement, Git object/index/untracked changes, digest mismatch, expiry,
revocation and unsupported execution. They do not establish host provenance.

Next independent component: independently verify the canonical Git source and
patch provenance against a host-controlled, stable or cryptographically attested
snapshot, then bind reviews to the exact snapshot; do not create a new evaluator.
Rollback: stop using this optional snapshot handle; no persistent state is kept.
