# Head eligibility P0 · technical contract

Base LAB d9807a96982b03ae5acea7ea289e4f32bd571a5f. Existing ROUTING-PLAN-01,
Mesa3 BUILD claim6883903808; #40 heads/C2C, #38 H-LEARN, #39 context remain owners.
Scope:meta_harness/head_eligibility.py,tests/test_head_eligibility.py,this contract.
No second catalog,Host,grant,lease,scheduler,worker or memory. No live inventory
or model/accelerator operations. Missing fleet witnesses remain NO_DATA in the
owning inventories;fixtures do not assert any device availability.

API evaluate(task,heads,checks,packets,profiles,policy,host,verify_head,now,
generation,pin=None,cache=None). The existing task is unchanged and closed.
Canonical resources module is imported from resource_admission,avoiding duplicate
Host class identities. resources.decide enforces existing grants,budget,identity,
resource evidence and120s operational freshness. Its non-synthetic result remains
ABSTAIN (including PRODUCTION_ADMISSION_NOT_CONNECTED),not an execution approval.

Heads are immutable JSON manifests sealed by head_ref:base_ref,adapter_ref,
revision_ref,runtime_ref are exact64hex;architecture,rank,alpha,targets,node,backend.
Reports bind head/task/generation,base/architecture/runtime,rank/targets support,
license_allowed,provenance_ref,permission,observed_at,origin and exact resource
profile_ref. The host witness must bind that profile to the entire head configuration. verify_head is a
trusted bounded host callback,not populated by model JSON;hashes alone authenticate
nothing. Production reports cannot become synthetic positive controls. Caller
must provide separately witnessed aggregate resource profiles for the exact
configuration;P0 does not estimate adapter RAM,quality or GPU capacity from rank.

32 manifests/32 reports,256KiB total JSON input. Deterministic sorted per-head
ref/cause details;summary<1024bytes contains their digest and candidate count,
task/resource/decision refs. No arbitrary labels,private identifiers or payloads
are echoed. Errors fail closed;input copies protect caller objects. Pin and cache
bind exact base/adapter/full head_ref/generation;no silent switch or implicit base fallback.
Baseline model selection remains existing resource policy;head ordering is stable
by digest,not a new quality rank or scheduler. Base-without-adapter and C2C cache
layout/peer compatibility are future explicitly scoped contracts,not inferred here.

Output {summary,details}:SIMULATED_ELIGIBLE only for wholly synthetic compatible
controls,otherwise ABSTAIN with cause. dispatch_authorized and
memory_promotion_authorized always false. P0 neither loads nor attests a physical
head,issues permission,reserves leases nor executes. Real Session/AdmissionGate
must later bind exact-head route,permissions,lease and loader witness. H-LEARN
consumes these diagnostics;C2C requires additional exact-pair/layout bindings;
Acho projects these states without promoting simulation into operation.

Validation:directed positives/negatives and source mutations twice;full LAB
unittest discovery,test_llms.py,bin/verify_llms_tree.py twice. No tests hide RED
or skips. Remote CI is separate. Owner-approved runtime witnesses,live hardware,
LoRA training,C2C execution and model-initiated MCP remain NO_DATA(not_executed).
Publish only a draft through existing authorized transport;no merge/deploy.
