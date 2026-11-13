# NVIDIA benchmark proposals · node-d · not executed

Owner LAB; runtime coordination with Claude. Source snapshot remains13-Nov09:41:40Z:
6 advertised model tags, backend declares0.33.2, no resident;8GB-class shared
memory. These dated facts do not establish present availability or GPU use.
Installed JetPack/L4T/CUDA/TensorRT versions, current power mode and compatible
TensorRT engine inventory are NO_DATA(not_measured). No packages, weights,
containers or engines are installed, converted, rebuilt or run by this proposal.

## Preflight for a future owned measurement window

Agree an idle lease/E-STOP with the APP owner. Preserve an uncertain in-flight
result instead of retrying. First inspect exact software/binary versions, model
digest, configured context, process ownership and current mode. Existing
`nvpmodel -q` / `jetson_clocks --show` queries may be considered when available
and already permitted; absence or access denial is NO_DATA. No clock/power/fan
change, restart or forced unload is part of this plan. NVIDIA documents
`jetson_clocks --show` separately from settings changes in its
[power/performance guide](https://docs.nvidia.com/jetson/archives/r36.4/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html).
Select version-matched documentation after the installed stack is observed.

## N1 · Existing Ollama model, GPU participation and public throughput

Reuse `benchmarks/station-96-first-pass-20261029/smoke.py --public-fixture`
and its current loopback/identity/byte guards; do not fork another runner.
The operator selects one already installed digest and exact controls. Run three
separate two-sample repetitions, sequentially, only in the owned window. Keep
every failed/mismatched receipt. Report median/min/max of6 observations, model
load and end-to-end wall separately; this is not p95 or task-quality evidence.

If already installed, a bounded foreground `tegrastats --interval 1000` observer
can record RAM, GPU activity, EMC, temperature and exposed power fields. NVIDIA
documents these metrics and interval-based stdout in its
[tegrastats guide](https://docs.nvidia.com/jetson/archives/r36.4.4/DeveloperGuide/AT/JetsonLinuxDevelopmentTools/TegrastatsUtility.html).
Record exact sensor fields/version/unit and start/end times. Scope termination
to the observer owned by the experiment; do not use the global `--stop` option
against other observers. Do not infer GPU execution merely from model metadata,
or attribute GPU activity while another process is using it. Resource readings
and runtime-reported offload claims remain separate evidence channels.

Acceptance to proceed: exact digest/controls stable, no unowned worker, complete
bounded receipts and sensor coverage. Missing GPU attribution means
NO_DATA(gpu_execution_not_attributed), not a CPU/GPU performance ratio.

## N2 · Task/context memory envelope and short thermal stability

After N1, preregister a task/context matrix within the existing runner's controls
and a separate independently scored quality set. Any altered context/profile
gets a distinct comparison key; preserve the baseline. No silent increase of
token limits. Use the smallest approved task first and an operator-selected
duration ceiling; a10-minute soak is PROPOSED only after short runs succeed
and the APP owner confirms the resource window. No automatic stress ladder.

Measure memory with process/device/host scope and sampling resolution, available
RAM, swap changes and temperatures. Exposed rail power requires recorded scope,
units, idle baseline and time integration before reporting net task energy;
missing or unvalidated rails remain NO_DATA(energy_not_validated). Sample maxima
are lower bounds; shared memory is not independent VRAM plus RAM. Large-free-
block statistics are not an admission budget. Preserve drift/throttling and
failures; they are measurements rather than grounds to change power settings.

Stop on owner E-STOP, lost resource lease, missing telemetry needed for the next
step, transport/identity change, timeout or unknown completion. Thermal/memory
stop values must be preregistered from the observed platform and owner policy;
none is invented here. Repeated quality failures remain separate from transport,
context, authorization and measured resource shortfalls. No concurrency limit is
derived from a single idle snapshot or a six-sample speed test.

## N3 · Optional pre-existing TensorRT engine baseline

This lane is NO_DATA(no_approved_compatible_engine_inventory). It becomes a
proposal for execution only if an existing trusted engine, model/base/license,
input shapes, precision, task dataset/scorer and matching local runtime are
identified. Do not deserialize unknown engines or convert/install one to make
the benchmark possible. NVIDIA describes `trtexec` benchmarking and controlled
measurement environments in its [TensorRT guidance](https://docs.nvidia.com/deeplearning/tensorrt/latest/performance/best-practices.html).
Latest upstream guidance is not proof that its runtime/flags are present here.

With an already approved compatible engine, preregister shape/batch1/precision,
bounded warmup/repetition, wall/host/GPU timing definitions and memory. Use fixed
real test inputs and an independent correctness check; generated inputs cannot
prove task accuracy. Keep CUDA-event timings distinct from end-to-end latency.
No FP16/INT8/Tensor Core/DLA throughput claim follows from the board name.
Any missing engine, scorer or compatible runtime closes this lane with a cause.

## Output and future consumers

All lanes produce dated source-bound evidence for existing LAB contracts,
not a scheduler, automatic specialist selection or training. `bench-repro-01-v1`
retains throughput semantics; independent task results retain176/177 witnesses;
scoped resource observations retain units, time and sensor provenance. Reuse
the existing comparison/gate code before adding fields. Publish aggregates and
hashes only. Raw host identifiers, prompts, answers and logs remain private.

Mobile clients can later consume the SAME offline census/task projections.
The browser mini-guide is a candidate to evaluate separately on consented
devices, with base/runtime/manifest pins and physical resource tests. Neither
an Android TWA/PWA installation nor a mobile label joins the five-node rack.
Enrollment, scoped grants and independent inference evidence are separate gates.

Current result for N1/N2/N3: PROPOSED / NO_DATA(execution_not_requested_in_this_slice).
No benchmark, model operation, power change or service change was performed.
