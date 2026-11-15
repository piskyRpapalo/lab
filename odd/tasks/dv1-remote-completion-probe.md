# DV1: operator-only authenticated-channel completion probe

Stacked after PR218, same operator worktree. This is the smallest live witness
experiment, NOT a new remote task authorization API, daemon, node registry or lease.
Invoked only by the authorized operator: python3 bin/node_completion_probe.py
--ssh-alias EXISTING_ALIAS --context-ref PUBLIC_FIXTURE_DIGEST.

Only an explicitly configured alias in the operator's existing SSH config is used.
SSH requires existing known host keys, batch auth, no key updates, no control-master
reuse, one connection attempt, no sudo. It launches one fixed Python snippet via
existing stdio channel: validate fixed public integer input/request hash/time,
compute sorted values, return exact nonce/node/context/request binding and result.
No data/model/file/service mutation is requested remotely. No secrets are read.

Input/output each <=1024 bytes; stdout is incrementally capped, stderr discarded,
8s monotonic client deadline, 30s UTC request window. Remote clock disagreement
rejects; no NTP-attack attribution or clock adjustment. Owned SSH process group
is terminated on timeout/failed protocol; no unrelated process is killed. This
cannot certify remote process termination after lost connectivity.

Verifier checks closed schema, exact node/context/nonce/request, original request
hash, fixed result including integer types, and issued<=observed<=now<=expires.
A checksum is NOT authentication. Production collection relies on SSH's strict
known-host authenticated encrypted channel; physical inventory alias binding and
portable signed receipt remain NO_DATA. Injected transports ALWAYS emit SIMULATED.
No provider callback can make a simulated run REAL through an origin argument.
No automatic retry, no release/reallocation of native UNKNOWN reservations.

Receipt authority=none, native_dispatch_authorized=false, APP_E2E=false always.
This probe bypasses no native policy: it is not registered as a model tool and is
not used to dispatch meta-task/1 remotely. The existing LOCAL_ONLY gate remains.
S1/model integration requires explicit target-scoped permission/expiry/revocation,
AdmissionGate route + existing host lease, original context, journal, independent
result checker and genuine host witness. No service is invented to fill those.

Junie consumes probe/verify_completion and exact source/request/reply digests;
review the operator-channel-to-native-host witness bridge, five-device mapping,
resource reservation, session fencing and stdout/process cleanup. PI/Hexelion
consumes synthetic transports and rejects swapped node/context/task/nonce,
checksum-valid forged/mismatched result, expired/future clocks, timeout/network
loss, duplicate JSON keys, oversize output and alias injection. Neither a probe
receipt nor an ACK confers authority. Requests for ACK stay in Mesa #3/#37/#39.

A successful real probe demonstrates only one authenticated operator-channel
public computation roundtrip. It does NOT demonstrate APP/Acho->S1->remote task
E2E, model inference, node admission, physical rights or a live LoRA swap.
