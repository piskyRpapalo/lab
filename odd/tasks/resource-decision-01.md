# Resource decision · independent offline prototype

Commission FORGE-CEREBRO13-Nov-2026. Owner Codex CLI, LAB only. Start from
current main3647403. This is a new decision-control slice, not a replacement for
LAB178's inventory/projection or LAB176/177's dispatcher/evaluator/memory.

## Historical pre-integration checkpoint and isolated177 reconciliation

176 remains READY at7d893178d27579ee21a2074c446ed89807991256, literal-head
CI43402087203 SUCCESS. Canonical firmas tree/index and176 comments were checked:
NO_DATA(exact_head_merge_signature_not_located). Prior chat HITL was recorded
for publication in Mesa6850290690. Question recorded for the Sovereign/Mesa;
no signature is invented and building continues independently.

The original177 worktree/head631f5986f41323e87afa92da55bdb0fef215d8a1 is
unchanged. An additional isolated detached worktree starts at main3647403 and
locally simulates non-squash integration of176 then unchanged177. This is not a
remote/main merge. Preview commit3a449d4e57f40e1bb8009835faf3f63852d66c5f,
treefbe87855da4d00393cf5c7ea06994afdc1091014; versus177 only6 workflow lines
differ, preserving delegation/context/memory source contracts and original
commits. Directed49 tests x2, canonical679 x2 (one existing skip), companions x2
PASS;14 real-code mutations x2 detected. Local suite8.805/9.074s.
Final177 HEAD/CI/signature still require actual176 integration and reconciliation.
NO_DATA(final_PR177_CI); local preview is not that final result. No public177
rewrite, force push, worktree cleanup or future signature transfer.

178baccd5f remains published/READY and unchanged. Its compatibility with a
future main will be rechecked after any integration; both share the same explicit
checkout/assertion workflow fix.175 belongs to its contributor; fork untouched.

## Contract and trust boundary

`bin/resource_decision.py` is a bounded pure function. Input task is the existing
`preceptoros.meta-task/1`; node inputs are existing node-metadata/1 projections.
Host callbacks must reuse176 task/grant validation,178 original-source/pin/time
verification and independent evaluation/resource ledgers. JSON cannot supply
callbacks. No callback means abstention. Source self-hashes, alias names,
`quality_pass` or `MEASURED` labels alone never replace a witness.

The host-owned policy contains current token/depth limits, active-job count,
required independent-case minimum and any exact human-approval reference.
Human-required operations need a host signature-verification callback, not just
a hash-shaped reference. Task input may not override policy or grants. The task
profile excludes run_id but includes all other exact task fields. Profiles bind
that key, node/backend/full model digest, catalog source ref, observation time,
quality/case count, latency, headroom and calibrated concurrency/pressure bounds.
No live numerical bound is invented; every example number is SYNTHETIC.

Host adapter outline: wrap176 `validate_task` to return strictly True on success;
obtain its existing exact-task grant, call176 `check_grant` with the host clock,
then return only its approval_ref. Do not pass an unchecked grant dictionary.
Wrap178 `verify_packet` using original source, trusted pin and the host's chosen
read time. The independent ledger callback must validate the full quality and
resource profile; it cannot merely compare its self-hash. Source pins and host
policy never come from user/model text. Actual callbacks remain host-owned.

Local bridge exercised the REAL176 validator/grant checker from the isolated
preview, with a clearly synthetic grant/profile. Canonical task hashes matched;
the positive control stayed SIMULATED_ELIGIBLE and an extra approved field was
rejected. Artifact20261113-resource-contract-bridge.json records source code
hashes and the preview tree. This is not production permission or an APP E2E.

The prototype checks witness identity,120s source/profile age, matching digest,
token/depth budget, host approval, measured-envelope arithmetic, pressure and
concurrency. It repeats host checks before returning a proposal. It does not
reserve resources: a future executing host must recheck live resources and use
the existing Session authority/journal/cancellation before any action.

Output kind=resource-decision-proposal is advice, not a new execution receipt.
Its seal binds that advice only. `dispatch_authorized=false` and
`memory_promotion_authorized=false` ALWAYS. Positive synthetic controls say
SIMULATED_ELIGIBLE. Even witnessed MEASURED profiles currently return
ABSTAIN(PRODUCTION_ADMISSION_NOT_CONNECTED): production integration waits for
final176/177/178 contracts and actual calibration. No fallback or backend change.
Do not mint a fake brain-cycle/1 from these controls; actual task results still
use177's existing independently witnessed cycle. LoRA remains unproposed.

## Reproducible controls

```sh
python3 -B bin/resource_decision_probe.py
python3 -B -m unittest tests.test_resource_decision tests.test_nvidia_readonly_compat
```

Eight mandatory cases: compatible model/witnessed fixture envelope; announced
but untested; failed node metadata; stale evidence; equal aliases/different
digests; insufficient budget; human signature required; malicious override.
The alias control selects only the exact digest. Multiple eligible nodes
abstain for host choice; no arbitrary ranking. Additional tests cover memory
shortfall, latency budget, calibrated contention, absent telemetry, stale/future
profiles, source/context mismatch, forged signatures, cancellation, revocation,
unwitnessed profiles and scrubbed callback failures.

The report labels SYNTHETIC_CONTROLS_NOT_NODE_MEASUREMENTS. Artificial sample
counts and byte/millisecond values exercise logic, not corpus size or hardware.
Repeat inputs produce identical bytes; inputs are not mutated. Decisions stay
under1024 B; source/code/artifact pieces stay under16KiB. Actual test-suite
counts use the existing unittest/workflow; the control report is not relabeled
as a canonical execution or model-quality receipt.

## NVIDIA compatibility observation · new revision, no new benchmark

`bin/nvidia_readonly_compat.py` reads the existing release/version metadata,
targeted package database and presence of standard tools/module. Its only
commands are dpkg-query and an installed `ollama --version`; the latter's child
environment pins loopback and removes proxy variables. No generator, engine
deserialization, sensor load, clock/power command or service action is used.
No models are recensused. New source hash/date/ref is preserved separately from
178's original09:41:40Z node-d snapshot; old observations are not rewritten.

At10:48:09Z: release file reports L4T36.4.7; CUDA version file12.6.11, cudart
package12.6.77; TensorRT packages10.7.0.23+cuda12.6; Ollama CLI0.33.2.
JetPack metapackage NO_DATA(metapackage_not_reported): do not infer a specific
JetPack version from L4T. nvgpu module present; tegrastats inPATH; trtexec present
at its standard location but notPATH; nvcc notPATH. Package/tool presence is
not a CUDA execution or model/backend compatibility test.

Next experiment reuses178 `docs/nvidia-benchmark-proposals.md`, source ref
baccd5f. First obtain an idle resource lease coordinated with Claude. Use an
already installed digest, unchanged runtime/power settings, owned cancellation,
independent task scorer and source-bound output. First-token latency needs a
separate approved streaming probe; a nonstreaming total wall time is not TTFT.
Report tokens/s, process/host/device peak scopes and sampler resolution, GPU
activity attributed to that owned run, temperatures and available power rails
with units. Compare idle against execution before proposing task energy;
unavailable sensors are NO_DATA. No active benchmark has been run in this slice.

## APP handoff and boundaries

Claude consumes178's existing offline projection, original source seal, host
pins/time and same record/views; this slice only adds proposal tests. APP268
was reported as a side-port consumer by Claude, not merged/live proof. No APP
code/worktree touched. TANK3, all mobiles/Acurast and deferred iPhone excluded.
No installed model, driver, service or frequency changed. Rollback: optional
offline files/reviewed revert; there is no deployed component to restore.

## Cutover revalidation

GitHub changed during construction: Sovereign merged176→033737f,
175→5358f38 and178→ef8c756. This branch fast-forwards its base to actual
mainef8c756 before publication, inheriting the exact-head workflow unchanged.
177 was closed by merge26f7f248 into the old176 branch, not main; its
brain/context/memory files are absent from main. Codex is preparing its original
owner branch against currentmain for a successor integration PR. The historical
preview/bridge records above retain their original scope and are not final CI.

`python3 -B bin/resource_contract_probe.py` now uses the actual merged176 task
and grant validators and178 pinned source loader/verifier. A historical node-d
catalog replay abstains without independent profiles; a changed memory value
is rejected against its original source; expired evidence abstains; an extra
permission field fails the actual task validator. Permission/clock controls
are explicitly synthetic, never a Sovereign signature. No model calls or APP
runtime wiring. Missing observations with no timestamp report NODE_UNAVAILABLE
rather than blaming the clock. The control report is regenerated for this code;
the real infrastructure compatibility observation is byte-for-byte unchanged.

Local final gate on mainef8c756:690 tests x2 (689 pass, one existing skip),
canonical companions x2 PASS;22 directed tests PASS,8 mandatory controls PASS.
Cerebro integration successor is LAB179, head116c3d7. Literal-head remote CI
and private Mesa receipt follow publication; no future signature inferred.
