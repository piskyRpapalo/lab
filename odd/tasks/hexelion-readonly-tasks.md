# Hexelion · three solo read-only task candidates

- Commission: buzon#30 ·6523629460. Law: task-contract/1 and ground-truth/1, decree ·6523629544.
- Source revision measured from GitHub: hexelion-nexo `3e5d9d934ecb941fc27968f1803fb80c0d5ae844`; every source blob is pinned in `contracts/hexelion-readonly-tasks.v1.json`.
- Scope: (1) read `/api/rack-map` over numeric loopback; (2) resolve IDs only from the two pinned source-index documents; (3) run the pure wake judge offline. All three have empty writes and deterministic judges. Task 3 validates bytes; it does not send a wake request or establish a status-chat protocol.
- Authority boundary: solo work is limited to the exact read-only actions above. Any write, broader network call, push, PR, deployment or node-state change requires prior approval. Signing, merging, credential reading and invented facts are forbidden.
- Ground truth: emit source head/blob, observation time for measurements, and a cause for every NO_DATA. A missing or changed source hash fails closed.
- Implementation status: candidates only. Hexelion main has the sensor, source index and pure judge, but this contract adds no dispatcher or live credential.
- Check: parse contract; assert three unique tasks, all `writes` empty, source hashes pinned, network scopes exact, and `NO_DATA` failures caused. Sabotage by replacing a GET with POST must be rejected.
- Log: 2026-10-30 · source heads and blobs read from GitHub; no task executed and no app or rack changed.
