# META-HARNESS-01 · Delegate with evidence

Owner: Codex CLI. Commission: [APP #255](https://github.com/piskyRpapalo/preceptoros-app/issues/255),
[Mesa round](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/3#issuecomment-6824470299).
Base: LAB `efaff2959743ffe6017a1d9d28f0637ec915b9be`, actual main after #173.
BUILD/testing authorized; human exact-head FIRMO gates integration. No merge,
deployment, service change, credential provisioning or LoRA training/activation.

## Read depth and reuse

Targeted implementation depth: LAB AGENTS, STATE/README, #173's public fixture and
`bench-repro-01-v1` runner; APP #255 (an issue), LAB-3/LAB-4 factory/voice contracts,
team, typed orchestrator and existing `hexelion_proxy.ask`; private H3 policy,
injectable cycle/bank/registry contracts; native MCP S-1 implementation/allowlist;
existing DFA-06 evidence, B5 family gate, receipt comparator and suite evaluator;
existing LoRA dataset verified-proof input and signed-download boundary. Serion
runtime/training identity is NO_DATA: no accessible specialist implementation was
verified in this scope. No private corpus, stashes or credential configs were read.

The private harness already owns tool selection, its approved dispatcher and the
human tool-execution switch. This piece is an injected **evidence wrapper around
one dispatch**, not another recursive orchestrator, state bus or signing system.
The existing APP proxy remains the only planner adapter. CLI imports it read-only
from the operator's checkout; no private implementation is copied into LAB.
The existing public throughput module supplies loopback/no-proxy/no-redirect guards,
strict JSON, fixture rendering, model digest validation and counters. Its historical
measurements and seed are unchanged. DFA-06 supplies canonical bytes; B5 and the
existing comparator supply their existing checks; eval_harness measures this suite.

## Minimal contracts

`preceptoros.meta-task/1` is the proposed bounded task envelope:
`task_id, run_id, specialist, model_version, source, input_sha256, max_tokens,
timeout_ms, depth, privacy, transport`, plus schema. Logical public labels only;
no endpoints, commands, prompts, paths or credentials arrive through task JSON.
`model_version` binds a service-reported model digest, or the selected MCP script's
SHA-256 for a tool-only task; that is an artifact version, not a model execution.
MCP source kind and NOT_EVALUATED grade prevent a health tool from claiming skill.

The trusted host injects `authority(task)`, budget and dispatch. Grants bind the
exact task hash, approval reference, expiry, token/time/depth ceilings and local-only
scope. Serialized booleans never authenticate a human. The CLI's explicit opt-in
is a narrow operator demonstration, not a public authorization endpoint. Production
H3/APP must inject its existing verified permission capability; a model cannot
mint, widen or renew a grant. Operator references identify evidence; they are not
cryptographic signatures. No replacement key store or authorization service exists.

Only local execution is implemented: WEB_MANUAL is not callable, remote spending
is not implemented, unknown budget fails closed. One dispatch/depth <=1; model
output ceiling64 tokens for the public specialist and512 for the existing Hexelion
planner; timeout <=30 s. Shared session budget is conservative:
reserve worst-case tokens, refund only known unused tokens. Failed/uncertain calls
retain reservation. A run ID executes once per Session; exact replay returns its
cached receipt, changed payload/concurrent duplicate is rejected. Unknown outcomes
are cached too; no automatic retry or paid fallback. This is not durable exactly-once
delivery across restarts/processes; the host must supply that journal if needed.

Cancellation before dispatch does nothing. During a request, only this tool's
client process is stopped; the existing MCP/model service is not stopped or
reconfigured. A server might complete an already sent request: outcome UNKNOWN,
no automatic resend. The shared stop-file callback prevents new executions and
interrupts client waits. Timeout bounds the client, not server compute termination.

`preceptoros.meta-receipt/1`, strictly <1024 UTF-8 bytes, contains the candidate
APP255 fields: task/run/specialist/version/source, phase, observed_at, measurement,
failure_class, confidence_basis, receipt_ref, next_action and approval_state. It
also binds task_sha256, approval_ref and known/unknown/not-started outcome.
An optional closed `failure_cause` preserves known proxy diagnostic codes; older
v1 receipts without that extension remain verifiable at their original hashes.
Measurement is tokens, output hash and deterministic grade, never raw output.
Full SHA-256 seals canonical bytes excluding receipt_ref. Self-hash is integrity,
not origin, human identity, gold validity or model-weight attestation. Consumers
must validate the closed schema and source evidence, not merely recompute a hash.

`preceptoros.meta-evidence/1` is a proposed local report envelope, not a promotion of
the existing throughput or harness-receipt schemas. Preserve their distinct types.
Reports bind task definitions and receipts, selected-target inventory, source hashes,
failure aggregation, improvement decision and three projections. Source commit is
NO_DATA while implementation files are uncommitted. No upload happens automatically.

## Taxonomy and measurement

| Failure class | Required next action |
| --- | --- |
| PERMISSION | Request/verify permission; never execute anyway |
| BUDGET | Revise measured allowance; never infer quota |
| CANCELLED | Check any in-flight outcome; do not retry |
| REPLAY | Inspect run ID/binding; do not execute twice |
| TRANSPORT | Repair endpoint/client transport |
| PROTOCOL | Repair adapter/schema |
| MODEL_IDENTITY | Verify installed model/digest |
| OUTPUT_SCHEMA | Repair the contract/prompt first |
| TASK_SKILL | Collect independent held-out task evidence |
| EVIDENCE | Collect/verify missing sources |
| UNKNOWN | Diagnose without retry |
| NONE | Review the receipt; not a quality certification |

Installed/catalog metadata is DECLARED with a CONNECTED client transport, never a
working-model claim. A verified MCP initialize/list/ping roundtrip proves that tool
path only; uncalled tools remain declared. Private H3's manifest is inspected without
dispatching its data or write tools. SSE/Streamable HTTP/WEB_MANUAL remain caused
NO_DATA without an authorized target; imported configs/credentials are not scanned.
Inventory is explicitly selected targets, not every installed or imported server.
The stdio launcher is Linux-specific: it verifies the expected script hash before
execution, then runs a sealed memfd snapshot with the original import/configuration
directory. Changing the script afterward cannot change those launched top-level
bytes. Its imported modules/configuration are not attested. It never weakens this
binding to a path-only fallback on a platform without the required primitives.

Public skill probe: the existing 16-integer fixture, exactly two sequential samples,
fixed #173 settings, exact model name/digest before and after. Schema checking and
numeric sorting are deterministic judges independent of model wording. A formatting
failure is OUTPUT_SCHEMA; correct format/wrong ordering is TASK_SKILL. Passing says
only this small public task passed; it does not measure general intelligence.
Two repeats of one content hash are **one independent case**, never two gold cases.
Loopback and remote-field rejection do not attest a server's hidden network egress.

## Serion proposal gate

The pure improvement module accepts metadata rows or canonical receipt wrappers.
It deduplicates content/split/arm/repeat, rejects conflicting duplicates and split
leakage, and keeps infrastructure failures out of eligible skill cases. Baseline,
best measured simpler control and candidate need two stable paired repeats, distinct
train/holdout/regression/negative-control splits, >=60 independent holdout cases per
target class and >=20 regression/negative cases. These are conservative **proposed
pilot gates**, not a claim of statistical power, human calibration or canonical law.

It reuses B5's model/family exclusions and existing comparable-receipt checks. Require
paired improvement >=10 percentage points over both baseline and best simpler fix,
no paired regressions, passing negative controls, source/data hashes, provenance,
license/privacy references, bounded compute, rollback and two distinct independently
verified reviewer identities. Trusted verifier callbacks must bind exact evidence,
proposal and review role; a reference-shaped string is not a review.

An adequate synthetic fixture returns SIMULATED_PROPOSAL/collect_more; never an
operational proposal. Verified measured prerequisites can return PROPOSAL_ONLY for
human review. **Every result has `lora_authorized=false`.** No training, adapter
download, installation, dataset export or activation function is present. The existing
signed dataset/import gates remain authoritative and are not called by this piece.
The actual tiny pilot must ask for more independent evidence or a contract fix;
it cannot support a LoRA claim. A candidate may be an already approved adapter or a
non-training intervention; the gate never builds one to satisfy its own prerequisites.

## Reproduce

Python3.10+ standard library. No private dependency is needed for tests:
Live stdio/process tests target Linux, matching this repository's CI runners.

```sh
python3 -B -m unittest tests.test_meta_delegation tests.test_meta_transports \
  tests.test_meta_hexelion tests.test_meta_improvement
python3 -B bin/eval_harness.py --suite tests --pattern 'test_meta_*.py' --runs 2
python3 -B -m meta_harness.cli
```

Last command only probes operator-selected catalogs/transports; no generation.
For an explicitly authorized **public** local run, supply a host approval reference
(64 hex chars), installed public model and, optionally, existing server/proxy paths:

```sh
umask 077
python3 -B -m meta_harness.cli --execute-public --approval-ref "$APPROVAL_REF" \
  --native-mcp "$NATIVE_MCP_SCRIPT" --private-mcp "$PRIVATE_MCP_SCRIPT" \
  --app-root "$EXISTING_APP_CHECKOUT" > meta-evidence.json
```

Private paths are shell configuration only and never enter the report. Use independent
worktrees; check compute contention before opting in. No models are downloaded.
With --app-root, existing Hexelion proxy proposes DELEGATE_LOCAL or NO_DATA; the
adapter preserves the existing512-token/think-low planner contract, validates catalog digests/remote metadata and
strict decision schema. It requests no model unload. The proposal does not approve
anything: the host's grant must still match the exact task. Failed/NO_DATA planner
never falls back to specialist invocation. Without --app-root this is explicitly a
manual operator probe, not a measured Hexelion planning chain. --stop-file PATH lets
the operator signal cancellation without storing its path. JSON is emitted to stdout;
export/publication requires the ordinary review. Exit0 for a successful execute-public
probe requires two valid specialist receipts; failed skill tests still emit evidence.

Use `--bootstrap-baseline` with the existing planner to measure two public worker
samples before requesting a proposal. This is an explicit, host-authorized baseline,
not a model-requested fallback. Only two distinct, current PASS receipt references
bound to the worker's digest enter the planner's fixed public evidence context.
The host additionally refuses delegation without that context even if the model
hallucinates DELEGATE_LOCAL. Baseline and planner/worker sessions share one768-token
budget (128+512+128). A failed baseline or planner abstention invokes no specialist
follow-up. Repeats remain one unique content case, so no LoRA becomes eligible.

## Claude integration and rollback

Read the report once. Preserve inventory `kind` and each receipt's attribution,
phase, observed_at, confidence basis, failures and next action. A MCP tool or timer
is not an active agent. DECLARED catalog entries never become LIVE by projection.
Do not cast this schema to `preceptoros.lab.harness-receipt/1` or `bench-repro-01-v1`.
The existing LAB-3 adapter may read these proposed records after integration.

Text, speech and machine views derive from the same validated receipt set and
state hash; summary <=100 characters, machine frame <1024 B. Views report observed
task receipts, not successful model work or liveness. `verify_projections` rejects
changed words/hash/ref sets. No LLM writes progress text. UI/polling/focus/announcements
remain Claude/Mistral's implementation; screen-reader/phone/APP E2E is NO_DATA until
they measure it. H3 can wrap its existing dispatcher with Session using its host-owned
authority callback and durable journal. No second scheduler or message bus is required.

Rollback: reviewed revert of this PR; no services, keys, models or APP files to restore.
Next mission selected: bind these proposal/receipt records to Claude's existing
LAB-3/4 reader with source identity and freshness tests. Separate ownership CLAIM
before any APP changes; keep the S110 and native MCP infrastructure untouched.

## Verification log · 2026-11-12

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
