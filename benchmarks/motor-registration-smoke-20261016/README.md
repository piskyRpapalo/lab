# Engine registration check · 2026-10-16

This card separates the registration and the single-call smoke test from the G0 benchmark; it is not used as a yardstick or as an estimate of sustained performance.

- State inherited from the Sovereign's signed order: local registry created; full digest and size are recorded in [G0](../preceptor-g0-20261016/README.md#red-before-green). Context 16,384 and temperature 0.2 are recorded in `deploy/soberano/Modelfile:13,16` of the local system.
- Date: 2026-10-16. Axis: one cold load + one response; 16.97 s declared. Permission cause recorded by the Sovereign: `chown` by the service user.
- Exact machine, runner version, and raw receipt of that call: `NO_DATA` in the source artifact consulted. `deploy/soberano/MOTOR_LOCAL.md:41-44` records another cold test of 19.45 s with 24.9 tok/s output on CPU; that is a distinct reading and does not replace the 16.97 s declared here.
- FIRMO: the signed recovery order of 2026-10-17 declares the registration resolved. Ollama was neither revalidated nor re-run in this recovery.

The G0 result, with its two measured responses and its missing-engine red, remains in its own card; this unit smoke test adds no evidence of quality or stability.
