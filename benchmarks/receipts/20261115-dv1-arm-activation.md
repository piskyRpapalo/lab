# DV1 · operator-channel ARM activation · 2026-11-15

**Scope:** operator-only public computation, not distributed model dispatch. Source: LAB `main` `f01bfd5` (`bin/node_completion_probe.py`); context is a synthetic SHA-256 digest. No model, remote file, service, or privileged operation was changed.

| Existing SSH alias | Trial 1 | Trial 2 |
| --- | --- | --- |
| `fragua` | REAL `PROBE_COMPLETED` | REAL `PROBE_COMPLETED` |
| `el-vigia` | REAL `PROBE_COMPLETED` | REAL `PROBE_COMPLETED` |
| `jetson` | REAL `PROBE_COMPLETED` | REAL `PROBE_COMPLETED` |

All six returned `attempts=1`, `cause=correlation_and_result_checked`, `native_dispatch_authorized=false`, `APP_E2E=false`, `physical_alias_binding=NO_DATA`, `authority=none`. Exact private SSH configuration, nonces and host fingerprints are intentionally omitted. These observations prove a bounded authenticated-channel computation roundtrip, not portable host identity or permission to run models.

**Current-main regression:** isolated archive of `origin/main` plus canonical instruments, Python 3.14, `python3 -B -m unittest tests.test_node_completion_probe tests.test_native_delivery_bridge tests.test_fleet_projection tests.test_task_binding tests.test_c2c_cache_scope -q` **69/69 PASS twice**. Includes controlled receiver simulation; does not prove a live CLI receiver. Prior local ARM meta-harness tests used an older LAB checkout and are not substituted for this current-main check.

**Do not duplicate:** #216 fleet projection; #218/#220 task binding; #219 operator SSH probe; #221 native delivery bridge; #222 C2C scope; Sovereign S1 R34 is an isolated p0x branch. `LOCAL_ONLY` remains enforced.

**Blocked:** `NO_DATA(real_host_lease; authenticated_receiver_and_agent_binding; cross_host_revocation_fence; independent_remote_effect_witness; APP_to_S1_to_remote_model_E2E)`. Next work is source-bound ACK/lease verification under host authorization, not a new SSH transport, scheduler or registry. No merge/deploy authorization is implied by this receipt.
