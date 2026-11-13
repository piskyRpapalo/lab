# SELF-BUILD-GIT-WITNESS-01

Read-only host-configured witness for a *committed* candidate, relative to an
existing exact SHA-1 base. The model supplies no repository path or command.
The host binds an opaque repository ref to the physical directory inode and
candidate HEAD. Git diff output is limited, uses no shell/external diff, and
includes both sides of renames via --no-renames. Exact changed paths and the
SHA-256 of the full binary patch must match the proposal. Git metadata, protected
paths, symlinks, submodules, dirty/index-divergent files, untracked/ignored files,
index flags and unsupported paths fail closed. This first slice accepts ordinary
Markdown under docs only; legitimate changes elsewhere are false rejections.

A host stability guard is REQUIRED across the complete inspection. Two HEAD and
status samples alone cannot rule out an intervening change followed by a revert.
There is no real host guard here; tests use a synthetic callback. A defective or
model-controlled callback is not proof. Repository objects are real in temporary
test repositories; no live operational host or signature is claimed. The witness
only supports source identity and makes no claim about evidence quality, human
approval, task execution, or safety of an authorized change. Unsupported SHA-256
Git repositories return NO_DATA. Inspect causes contain no raw paths or logs.

No service or dispatcher is added. Preflight can call the witness directly as
source_witness; missing stability causes NO_DATA. Sovereign path policy from #193
is separately required. Rollback: stop constructing the witness; it writes no
repository state and uses GIT_OPTIONAL_LOCKS=0 and a disabled fsmonitor.
