# META-HARNESS-01 · measured evidence · 2026-11-12

Controlled experiments; no training or automatic activation. Native delegation was
measured twice; production integration and the memory-to-APP circuit remain pending.

## Measured outcomes

| Stage and source | Observed result across two executions | Records |
| --- | --- | --- |
| Initial planner, `50fb481` | Planner unavailable as evidence; no specialist dispatch; native MCP ping succeeded | [1](20261112-meta-50fb-1.json), [2](20261112-meta-50fb-2.json) |
| Native planner parameters, `8377260` | Real Hexelion replied NO_DATA twice; 57/78 tokens; no unsupported delegation | [1](20261112-meta-8377-1.json), [2](20261112-meta-8377-2.json) |
| CSV baseline, `74415db` | Qwen3 1.7B: four OUTPUT_SCHEMA observations; planner abstained | [1](20261112-meta-7441-1.json), [2](20261112-meta-7441-2.json) |
| JSON64, `a7bee32` | Four OUTPUT_SCHEMA observations; planner abstained | [1](20261112-meta-a7be-1.json), [2](20261112-meta-a7be-2.json) |
| JSON128, `c973a6f` | Qwen3: four TASK_SKILL observations; valid JSON, wrong result | [1](20261112-meta-expanded-1.json), [2](20261112-meta-expanded-2.json) |
| Same JSON128, `c973a6f` | Gemma2 2B: four TASK_SKILL observations; planner abstained | [1](20261112-meta-gemma-1.json), [2](20261112-meta-gemma-2.json) |
| Native control, `25534b3` | Eight PASS observations (four baseline, four delegated); Hexelion DELEGATE_LOCAL twice; exact host grants required | [1](20261112-meta-native-1.json), [2](20261112-meta-native-2.json) |

All rows reuse **one** public16-integer case; repeated runs and output-profile
variants are not independent cases. Nothing here estimates model-wide accuracy.
CSV64, JSON64 and JSON128 are distinct explicit contracts, not byte-identical
reproductions of one another or historical LAB #164. No result was overwritten.
The native control is a real Python tool, not an AI, LoRA or fake model response.

Native source: `25534b32f85229fed47070328bdc8d0b3356428b` (includes fresh LAB main
after #174). Existing APP proxy SHA256:
`def230bbecd97cce16768835a9ba2844f7803ec28b9f413f26181e6d1f42fc4b`.
Each report binds public source-file hashes to its actual Git commit, exact tasks,
host approval reference, result hashes and projections. Every task receipt is
<1024 B; complete reports are <=15718 B. Hashes identify bytes, not authorship.

### Bounded real circuit

Operator opts into a fixed public capability profile -> two current baseline
executions -> source-bound context for private Hexelion -> DELEGATE_LOCAL proposal
-> trusted host grant for the exact task -> native execution -> independent
monotonic/multiset properties -> attributed receipt -> identical text/speech/machine
summary. The operator selects the candidate profile; autonomous multi-capability
selection, memory update and APP rendering are not proven by this slice.

Native worker tokens: **0**. Planner: **91/85**, within the512-token ceilings;
remaining shared allowance **421/427**. [Whole-probe timings](20261112-meta-native-timings.json):
**3.563 s / 3.157 s**, including catalog, protocol, process and local checks; these
are not isolated model latency or energy readings. The native output hash is
`a8eb80395b27d66237d2f8635ed35677fdbde3516027a924efefab5dafc3a2ee`.

The measured improvement is the use of a deterministic tool for this mathematical
job: the observed native results pass the public properties with zero worker model
tokens. Both small-model baselines remain RED for this case. No claim about other
tasks or general model ranking follows. The LoRA gate asks for independent held-out
evidence: **one unique case is insufficient**, and `lora_authorized` stays false.

### Failure diagnosis and physical limits

A separate bounded JSON64 diagnostic observed `done=true`, `done_reason=length`,
`eval_count=64`, response79 B, JSON error at byte79, thinking0 B, stable model digest.
Output hash `34010433a717fcaffd92bbac0a2ea928dc8f5c5d1fd358d617c0586d74ed8c33`
matches the preserved JSON64 failures. Increasing the explicit output budget removed
the parsing failure and exposed the distinct skill failure. Earlier private-planner
failure root cause was not isolated; its native parameters were restored.

Read-only local sample on2026-11-12: physical RAM61845794816 B, available40880824320 B,
swap8589930496 B unused; thermal readings20/52 C with sensor attribution NO_DATA.
Machine class is DECLARED Beelink; precise sensor timestamp, VRAM placement, remote
memory, watts, joules/token and temperature attribution are NO_DATA. RAM and VRAM
are not summed. No service was restarted/reconfigured, model downloaded, weight
trained or adapter activated. Only public synthetic inputs were used.

MCP proof is target-scoped: selected native stdio initialize/list/ping was measured;
selected private MCP manifest was read without dispatching its data/write tools.
This is not proof that every declared tool or the newer APP S-3 route is operative.
Loopback does not attest hidden server egress or rehash model weights.

### Reproduce and qualify

See [contract and commands](../../odd/tasks/meta-harness-01.md); for the successful
profile select `--worker-profile native-sort --bootstrap-baseline` with the existing
APP proxy. Runtime references are operator configuration, never embedded credentials.
All earlier negative profiles remain available for regression.

Final local checks: **630 tests x2, one existing skip**, canonical companions x2;
[81 targeted tests x2](../harness-receipts/20261112-meta-harness-tests.json), and
ten deliberate code sabotages x2 detected. H5 code and delta reviews fixed identity,
cancellation, budget, completion, witness and reporting defects. Artifact review and
CI exact-head are reported in the PR; local counts do not substitute for CI.

Status: EXISTS IN CODE and measured operator-run delegation. INTEGRATED in main,
autonomous daemon operation, memory promotion, full carbon-to-APP/Acho E2E, physical
device accessibility and production deployment: **NO_DATA(not_measured_in_this_slice)**.

## Dated verification log


Local canonical checks: discovery **616 tests twice, one existing skip, zero failures**;
norte5, llms2, Node chunk responder and tree11996/12109B all twice GREEN. New targeted
suite: **67 tests twice**, also measured with existing `eval_harness.py` (deterministic
counts). No real inference in tests: only pure injections, synthetic local HTTP and
synthetic stdio processes. Seven deliberate code mutations were caught twice in
disposable copies: permission bypass, shared-budget overrun, cancellation after
reservation, re-sealed false success, MCP identity replacement, incomplete planner,
and duplicate reviewer identity. No source worktree was mutated for sabotage.

H5 independent review found four initial blocker groups and one snapshot compatibility
regression. All fixed and rechecked: executable byte binding before launch;
cancellation/deadline recheck/refund; strict planner completion; semantic receipt
validation; registered Python main namespace. Independent67 tests twice and additional
synthetic exploits found no remaining blocker. This is code evidence, not a live
model, network-isolation or human-signature attestation. Live result appended separately.

The first real planner probe at `50fb481` failed twice; MCP health passed, and no
specialist call escaped the failed planner. Retain these failed source-bound receipts.
The adapter had changed the native planner's512-token/think-low contract to64/false.
The corrected adapter preserves its working parameters with an explicit512-token
planner grant and shared640-token ceiling (512+64+64), while the public throughput
specialist remains fixed64. Specific root cause of those two failures is not isolated.
Fixed proxy error codes now survive into a closed optional failure_cause field;
identity rejection is not mislabeled as a broken transport. H5 delta recheck passes,
including68 targeted tests twice. Latest complete suite:617 tests twice (one skip),
all canonical companion gates GREEN. No training or model activation occurred.

Bootstrap context is immutable and rehashed against the authorized input. Baselines
must match the expected tasks/public input, be fresh (<=120 s), and be witnessed by
their actual host Session; self-hashed or old planner receipts are insufficient.
Independent H5 bootstrap recheck:74 targeted tests twice, no remaining blockers.

CSV baseline at74415db:4/4 OUTPUT_SCHEMA, planner abstained twice. This supports
contract repair, not LoRA. Explicit `--worker-profile json-array` adds a closed
16-integer grammar and public prompt suffix; task/input hashes differ from CSV.
The fixture case hash stays the same, so profile variants do not add independent
cases. Original CSV/#173 remain unchanged. Final code checks:624 tests twice
(one skip),75 targeted twice; H5 format-repair recheck PASS. Live outcomes below
are in the source-bound receipt summary linked from the benchmark index.
