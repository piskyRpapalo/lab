# C2C-R0 · pure same-host preflight

Technical contract/receipt, not a new mission. Mesa #40 CLAIM 6885051484.
Depth 2. Base LAB 5538ce6abd644f5179c0d8005514a3b235748bf0.
Scope: meta_harness/c2c_preflight.py, tests/test_c2c_preflight.py, this file.
LAB #207/#208 are merged; integration review closed without repeating its tests.
H-LEARN remains BLOCKED(missing_complete_patch); this piece does not implement it.

## Pinned public sources, not installed capabilities

Selected receiver Qwen/Qwen3-1.7B; sharer Qwen/Qwen2.5-1.5B-Instruct;
fuser nics-efc/C2C_Fuser/qwen3_1.7b+qwen2.5_1.5b_Fuser.
Metadata inspected 14 NOV 2026 without downloading weights:

| Artifact | Candidate repository revision |
|---|---|
| Receiver | 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e |
| Sharer | 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 |
| Fuser | f01fc3258b305e280e04c7238f4f2cf31b7dc70d |
| C2C runtime source | 5eac72b90faf7b3dc2638e874fe7cba1e74c8bcf |

These are candidate metadata pins, NOT demonstrated training-time model revisions.
The fuser config names models but does not pin those revisions. Its 28 projector .pt
files have LFS SHA256 values in upstream metadata; final/projector_config.json maps
28 aligned layers and projector_0.json specifies source 2 -> target 8 KV heads,
head_dim 128, BF16. Receiver config has 28 layers/8 KV heads/128 head_dim;
sharer has 28 layers/2 KV heads, derived 1536/12=128 head_dim.
BHSD tensor layout and actual cache access still require runtime/host witnessing.
No cache tensor was loaded here and no metadata match proves execution compatibility.

Primary sources:
- https://github.com/thu-nics/C2C/tree/5eac72b90faf7b3dc2638e874fe7cba1e74c8bcf
- https://huggingface.co/Qwen/Qwen3-1.7B/tree/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e
- https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
- https://huggingface.co/nics-efc/C2C_Fuser/tree/f01fc3258b305e280e04c7238f4f2cf31b7dc70d

HF metadata labels Apache-2.0. Upstream LICENSE is Apache-2.0 while pyproject metadata
says MIT: preserve this mismatch and require reviewed license provenance, not automatic
permission from a label. pyproject pins torch 2.6.0/transformers 4.52.4; environment
pins Python 3.10.18. Host package/backend and source compatibility must be independently
witnessed. No environment is installed or modified. Future .pt loading needs a separately
reviewed safe deserialization policy; no pickle/checkpoint loading occurs in R0.

## Contract and reuse

Frozen Model/KV/Fuser/Pair/Pin/Evaluation/Witness plus typed Decision.
Model.weights_ref hashes a complete ordered local file/digest manifest; config_ref
pins configuration. Fuser.files_ref covers every projector tensor AND configurations;
models_ref binds both full model manifests, revisions and optional genuine LoRA heads.
layout_ref binds reviewed mapping; runtime_ref binds code/packages/backend/host ABI.
No paths, addresses, prompts, credentials, raw KV or token buffers enter the contract.
No fuser is represented as a LoRA adapter.

Existing task.model_version is the receiver weights manifest digest. Its input_sha256
is input_ref(pair,pin,evaluation); therefore resource profile_key includes the entire
pair/fuser, runtime, device/session generation and benchmark plan. A receiver-only
resource profile is not sufficient. Host must independently calibrate that exact workload.

preflight composes canonical resource_admission.resources.decide with the existing
AdmissionGate.record view. Its measured PRODUCTION_ADMISSION_NOT_CONNECTED abstention
is not treated as permission: a matching VERIFIED Gate record for exact task, resource
profile, source/physical host, live lease and timestamp is additionally required.
No new Host, grant, lease allocator, scheduler, registry or dispatcher is introduced.

Optional genuine receiver LoRA checks delegate to head_eligibility.evaluate, including
full head pin and generation. Existing #207 only qualifies synthetic head proposals;
measured LoRA admission remains blocked. Sharer LoRA is explicitly unqualified in R0.
The published fuser has no demonstrated LoRA-trained pair; training_revisions_bound
must remain false until an independent source proves the exact pair including heads.
A changed head/runtime/cache pin cannot inherit an old fuser qualification.

Host owns verify(witness,pair,task), admission(task), resource Host callbacks and any
head evaluator inputs. A caller/model cannot supply callbacks or self-attested JSON
as authority. verify must independently validate complete artifact hashes and local
presence, training-pair provenance, physical identity, runtime/ABI/KV compatibility,
license scope and current permission for the exact benchmark plan. A self-hash is
integrity only. No arbitrary manifest or true boolean substitutes for that witness.

Bounds: 256 KiB encoded input; canonical resource packet/profile bounds; max two head
specs; evidence/Gate freshness 120s; future timestamps reject; compact receipt <1024 B.
Pin binds pair_ref, runtime_ref, opaque physical node_ref and generation. Upstream
source revisions are immutable 40-hex; file/manifest digests are 64-hex. Models with
GGUF/Ollama tags, mismatched architecture/layout/dtype or reversed pair fail closed.

Decision is READY_FOR_ISOLATED_BENCH or ABSTAIN with explicit cause/origin and digest
links. Missing data uses NO_DATA_* causes or a host-evidence abstention, never inferred
readiness. Even READY means prerequisites only: dispatch_authorized=false and
promotion=NOT_AUTHORIZED. Actual execution requires the existing authorized Session,
final grant/lease recheck, approved isolated worker and a separate experiment decision.
No runtime, network, model loader, GPU, server, training or weight download is invoked.

## Upstream negatives constrain the experiment

- https://github.com/thu-nics/C2C/issues/15 distinguishes a task-trained checkpoint
  from a public generic checkpoint. Do not transfer benchmark claims across artifacts;
  record exact task/checkpoint/data/evaluation identities and independent held-out data.
- https://github.com/thu-nics/C2C/issues/23 reports regression for a DIFFERENT pair.
  This neither disproves nor validates our pair. Require receiver-alone, sharer-alone,
  textual communication and C2C baselines; do not assume improvement or multi-sharer gains.

Evaluation pins heldout_ref, independent judge_ref and reviewed quality_policy_ref;
mandatory flags preserve both restrictions and synthetic/public-data-only scope.
No third-party score is a local benchmark. R1 must measure quality/abstentions, p50/p95
latency, bytes and peak memory under controlled repeats; energy only with a real sensor.
Regression or inconclusive evidence must not promote the route. R0 does not score quality.
Text fallback remains a separately authorized communication route, never an automatic
export of private context when C2C abstains. No raw private RAG/KV leaves a device.

## Six-node evaluation: all ABSTAIN, no connectivity promotion

Latest canonical coordination: Mesa #25 comment 6884823402; #40 comment 6884927928.
These statements are source context, not 120s operational witnesses. Six physical
identities remain external MH-01 inventory; canonical LAB routes are not renamed or
extended to fake a sixth eligible resource slot. No fleet registry is duplicated.

| Node | Available context | Missing R0 evidence / verdict |
|---|---|---|
| Beelink | Ollama GGUF tags previously observed; current CLI package/cache metadata inspected | ABSTAIN: exact HF bytes, compatible isolated runtime, trained-revision binding, whole-pair profile/grant/lease unverified |
| Onexstation | Radeon/ROCm/unified-memory report, SSH observed by owner | ABSTAIN: no exact pair/fuser, HIP/KV/runtime witness or whole-pair profile; unified memory is not dedicated VRAM |
| Orange Pi | Network/service recovery observations, physical binding unresolved | ABSTAIN: physical identity, runtime/checkpoints/resources/permission unverified |
| Raspberry Pi | Network/SSH recovery observations | ABSTAIN: RAM/BF16/runtime/KV/checkpoints/whole-pair budget unverified |
| Jetson | Network/API observations, clock/power-mode limitations | ABSTAIN: trustworthy time, ARM CUDA/runtime/KV and exact pair/checkpoints/profile unverified |
| Fedora C302C / Google Cave | SSH now observed; Intel 7265 WoWLAN declared but disabled/untried | ABSTAIN: CPU/runtime/memory/checkpoints/whole-pair admission unverified; WoWLAN is unrelated to C2C |

Limited current CLI observation: Python 3.14.4 x86_64; package metadata finds no torch,
transformers or rosetta in THIS interpreter. Conventional HF cache has receiver/fuser
repo directories, not sharer; none of the three exact candidate snapshots above exists.
Expected weights at those exact snapshots: receiver 0/2, sharer 0/1, fuser 0/28 present.
No weight contents were read/hashed and other directories/interpreters were not scanned:
NO_DATA(checkpoints_elsewhere), NO_DATA(local_weight_digest_verification),
NO_DATA(other_host_runtime), NO_DATA(accelerator_probe_not_performed),
NO_DATA(fuser_training_model_revisions_unbound), NO_DATA(whole_pair_resource_profile).
Directory existence, downloaded metadata, SSH or network status cannot produce READY.

The six-node fixture executes six distinct opaque node requests with no independent
host witness and returns ABSTAIN/PAIR_HOST_EVIDENCE_NOT_WITNESSED for all six. It does
not assert that six physical nodes were probed or that none can ever run this pair.

## Tests and reproducibility

Fixtures reuse existing AdmissionTests and synthetic task/resource data. Their MEASURED
profile labels are TEST DOUBLES for the existing Gate, not local measurements. A positive
fixture proves only conditional decision behavior; it is not the six-node live result.
Tests cover exact pair/digests/revisions, KV layout/dtype, GGUF incompatibility, checkpoint
presence/provenance, runtime/permission/license, stale/future evidence, impostor host,
resource shortfall, missing/forged/transplanted admission, source/profile mismatch,
generation/cache changes, upstream evaluation constraints, optional genuine head gate,
strict booleans, bounded/private errors, determinism and I/O tripwires.

Run each twice:
- python3 -B -m unittest tests.test_c2c_preflight -v
- python3 -B -m unittest discover -s tests -p 'test_*.py'
- python3 -B test_llms.py
- python3 -B bin/verify_llms_tree.py

Local measurement, Python 3.14.4 / 14 NOV 2026: 23 directed PASS twice;
971 discovery tests OK twice (970 PASS + one inherited skip each), test_llms 2 PASS
twice, tree verifier PASS twice. Skip: test_eval_harness.test_red_suite_verdict_red,
no RED suite available in this tree. Ten in-memory guard mutations detected twice
through assertion failures, no runner errors; some checks overlap, so this count is
not a claim that every removed guard alone admits an exploit. Six no-witness fixture
receipts are identical between runs and all ABSTAIN; no physical host benchmark exists.

External SCRUB receipt records exact HEAD, results, mutations, source metadata checksums
and the six-node abstention receipts. No downloaded source config, private inventory or
external evaluation answer is committed. Scope remains the three approved files.

## Next increments

1. Obtain independent provenance tying fuser to exact training model revisions, and
   reconcile source license/package metadata. No download authorization is inferred.
2. Owner supplies local digest-verified HF checkpoints and approved isolated runtime
   through a separate authorization, plus exact whole-pair profile/current grant/lease.
3. R1 same-host controlled four-arm benchmark after approval, independent judge and
   deterministic task scoring. No promotion from metadata or one favorable metric.
4. Only after R1, propose cross-host privacy/transport/retention and cache lifecycle;
   no mesh, MCP extension, AKV runtime or new server is built by R0.

Sovereign retains integration and experiment activation. No merge or deploy.
