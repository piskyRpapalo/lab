# SELF-BUILD-SOURCE-LINEAGE-01

Independent adapter from main, no copy or stacked dependency on #196. If the
sealed snapshot module is unavailable it returns NO_DATA. When installed, a
host creates the existing GitWitness and supplies a host-owned operation ref.
The snapshot must be captured with binding_ref(proposal_ref, candidate_sha,
operation_ref); each assessment rereads it and checks the sealed snapshot's
integrity and patch digest. Wrong operation, candidate, repository, proposal,
expired/revoked snapshot or altered bytes fail closed. There is no cache and no
authorization. Returned INTEGRITY_VERIFIED means only matching bytes in a
verified snapshot; it is not Git provenance.

The existing GitWitness can reject conflicting base, diff, paths and modes, but
its stable_source callback is not a real independently attested fence. Even if
a synthetic callback says True and all hashes match, source remains NO_DATA and
execution_authorized stays false. A HEAD flip followed by restoration and a
corrupted Git object are tested. The actual snapshot implementation #196 is not
included in this independent PR, and CI substitutes synthetic snapshot fixtures;
a separate local cross-worktree check may use the real #196 implementation but
is not a source or host authority. Future source verification needs a real
noncooperative-writer-safe stability/snapshot witness, not another dispatcher.
Rollback: stop calling this pure adapter. Failure or revocation requires reread.
