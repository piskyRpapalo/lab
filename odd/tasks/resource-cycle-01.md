# Resource checks in the existing brain/Session path

Owner Codex CLI, LAB. User13-Nov: measure and unify missing logic. Base actual
main0d3d58a includes179/180. No APP/mobile/TANK3 work. CLAIM Mesa6851380408.

The existing offline instrument stays byte-identical: historical source hashes
and all census measurements survive. A host AdmissionGate reuses its exact
task/digest/source/time/resource checks, the176 grant validator, and178 source
verification callbacks. It additionally requires MEASURED independently
witnessed profiles, exact worker→node/backend binding and an already-held live
exact-task resource lease. Synthetic profiles cannot pass. The gate is injected
into the existing Session, used by the existing brain cycle. It is not another
dispatcher or resource allocator. Session rechecks grant expiry and cancellation
after the gate; rejection refunds a pre-dispatch token reservation. Unknown
execution retains tokens; host retains the lease until reconciliation. No auto
retry/release, backend switch, memory promotion or new brain-cycle schema.

Legacy Session without admission remains available for existing local tests and
operator-authorized local tools. A federated host MUST inject this gate and its
own durable lease/authority/worker binding. A serialized VERIFIED record or an
ABSTAIN cause alone never authorizes execution. Gate records mean scoped checks,
not task success, independent quality certification or live APP integration.

The previous offline instrument's PRODUCTION_ADMISSION_NOT_CONNECTED is used
only as its internal all-envelope-checks-passed signal. It is never relabeled as
a grant. This host composition then checks permission, actual route, live lease
and freshness again before the original Session dispatch. Existing receipts
remain authoritative for actual outcomes; side records bind exact task refs.

## Bounded node-d measurement

Reuse the existing throughput runner and existing independent grade_public CSV
scorer, not a new model evaluator. Two sequential public16-integer fixture
attempts, already-installed1GB-class digest selected before running; no model
downloads. Fixed runner settings include normal keep_alive=0 for this newly
loaded owned model only; no explicit unload request or displacement of resident
models. Metadata preflight found zero residents, low load, >6GB available and
temperatures54–57C. Kernel PSI files are unavailable: preserve NO_DATA, do not
derive production saturation bounds from this experiment.

Operator experiment ceilings: at least4GiB available before start, load1≤1,
temperature<70C, two generations at most, request timeout25s, total65s. During
sampling stop further attempts on temperature≥70C, available RAM<1GiB, unknown
completion or lost window. These are conservative bounds for this experiment,
not benchmark-derived resource admission thresholds. No heavy concurrent run.
Only the locally owned tegrastats observer is terminated; no global --stop.

Observe idle versus execution RAM/temperature/GR3D/VDD_IN at200ms where present.
Keep vendor MB literal rather than choosing SI/MiB. Global GPU activity and
service counters are separate channels, not proof of process GPU execution.
Nonstreaming runner cannot measure TTFT. A single public case repeated twice
cannot calibrate general quality, concurrency, task peak memory or energy.
Any missing field has a cause; no runtime/service/power change is authorized.

Positive host-wiring tests use explicit test doubles, not measured node profiles.
Real measurement/results and final exact-head CI will be appended separately.

## Observed result · 13 November11:32:50Z

Two generations completed with stable service-reported digest65ec0654 and
identical answer hashes. Existing scorer returned OUTPUT_SCHEMA twice (64-token
CSV profile). Generation37.755684/38.569877 tokens/s; end-to-end6.007932206/
5.841060936s; load4.156353210/3.867681426s. These timings do not qualify this
model for the task. No retry or alternate profile/model was run for a green score.

Idle5 sensor samples: GR3D0%; VDD_IN mean4922mW. Execution58 samples:
GR3D0–99%; VDD_IN mean9367.207mW/max20496mW; vendor RAM max2709MB.
Available RAM before6622068736B; sampled minimum4798836736B; sampled maximum
temperature60937mC. Scope is host shared memory/global GPU/rail, not process
peak or demonstrated NVIDIA model attribution. TTFT, process peak, concurrency
and integrated joules remain NO_DATA. There is one distinct public case, no
independent holdout or calibrated admission envelope. No profile is promoted.

Experiment ref59bf06a6d75cf68b210cc73dd70e205c39016cd7ab88cd3ac9306d1288e5c7a2;
source commitf46fddc3 preserves the exact probe/runner/scorer hashes. No source
or historical measurement was rewritten. The original experiment source code
was delivered over known-host SSH/stdin, not installed on the node.

Final local gate:754 tests x2 (753 pass, one existing skip); all canonical
companions x2 PASS;14 real-code mutations in two rounds per gate,56 detections.
19 directed tests including immutable measurement seals PASS. An initial gate
correctly caught that a historical replay pinned old delegation bytes: preserved
the original artifact byte-for-byte and published replay-r2 with current source
hashes rather than rewriting the past. Postflight snapshot11:35:08Z confirms
zero resident models and PSI NO_DATA; it is a separate new metadata revision.

APP/runtime consumption remains NO_DATA(host_not_wired); route/lease callbacks
in positive integration tests are explicit test doubles, not node capability
measurements. Current real two-attempt quality failure cannot create a lease
or profile. New governance audit LOGIC-SOVEREIGNTY-01 is separate, proposed in
Mesa6851704388. No governance document or APP file changed by this slice.
