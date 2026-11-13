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
