# SELF-BUILD PREFLIGHT · first slice

A deterministic offline proposal contract builds on the canonical digest helper
in meta_harness.improvement. It validates the proposal's closed shape, hashes,
exact base identifier, path allowlist, protected paths, bounded resource request,
dependency references, recovery reference and human-review reference. It does
not perform a build, compare baselines, verify a signature or authorize changes.

Three separately injected host callbacks check source identity and exact diff,
problem and plan provenance, and independent reasoning. They are trusted host
interfaces, not proof by themselves. Test callbacks are synthetic. No live
source/evidence witness, independent judge, human signature, applied rollback,
comparison or APP connection is supplied: NO_DATA. A review reference is not a
grant. Returning PROPOSE_ONLY from test fixtures is not an operational decision.

Safety paths and tests are protected even if allowlisted. The host must also
restrict the exact paths and assess the resource ceiling; syntactic budget caps
are not admission. Callbacks must check actual source state, fresh evidence,
conflicting claims, test contamination, regression coverage and recovery, all
bound to the proposal digest. No enforcement is claimed if a host supplies a
false or defective callback. The module opens no files and performs no action.
The remaining adversarial cases need real independent witness implementations.
Rollback: stop calling the adapter; it persists nothing.
