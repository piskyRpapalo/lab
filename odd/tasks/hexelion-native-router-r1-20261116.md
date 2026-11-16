# Hexelion Native Router R1 · Interoperability Contract

## Scope

`meta_harness.specialist_interop.evaluate` is a pure decision adapter. It consumes
the current Junie selector's recommendation shape plus task-bound evidence and
the existing `AdmissionGate.record(task)` shape. It does not dispatch, issue a
grant, choose a fallback for execution, invoke MCP, or create a scheduler.

The existing `delegation.validate_task` and `delegation.sha` define the task
identity. The resource decision is sourced from LAB's `AdmissionGate` contract;
`ExecutionJournal` and `Session` remain the only execution path and must still
revalidate authorization independently.

## Input contract

- Task: closed `preceptoros.meta-task/1`, validated by `validate_task`.
- Recommendation: closed `hexelion.skill-recommendation/1` object with
  `task_ref = sha(task)`, model digest equal to `task.model_version`, Skill ID,
  node/backend, measured score, safety result, fallback metadata, HITL requirement,
  and `origin`.
- Receipt: closed `hexelion.skill-recommendation-receipt/1` binding the exact
  recommendation digest, task digest, and origin. `receipt_ref` is a canonical
  SHA-256 integrity check only; it is not a signature or producer authentication.
- Evidence: exact endpoint, quality, security, context, provenance, and HITL
  records. Each record binds a subject digest and observation timestamp. Quality
  evidence additionally binds the measured score and count of independent cases;
  security evidence binds a numeric risk score. The HITL
  status is descriptive only; this contract does not verify a human signature.
  Security risk must be 0..1; values above 0.2 are rejected. Endpoint evidence binds the exact task, node, backend, and
  model digest.
- Admission: resource record returned by the existing host `AdmissionGate` for
  the same task, including selected node/backend/model and `NOT_AUTHORIZED`
  promotion state. A serialized hash does not independently authenticate a host.

All evidence is bounded by the supplied UTC time and `max_age_seconds`. A real
recommendation is currently `NO_DATA(selector_receipt_or_authenticated_producer_unavailable)`:
the p0x selector export has no authenticated producer receipt or endpoint
accreditation contract. The synthetic positive fixture validates structural
interoperability only.

## Output contract

`hexelion.specialist-proposal/1` returns a deterministic state/cause and
`decision_ref`. Positive fixtures are `SIMULATED_PROPOSAL` with
`source=SIMULATED`; other outcomes are `REJECTED` or `NO_DATA`. Every output has
`authority=none`, `dispatch_authorized=false`, and
`requires_human_authorization=true`. It is not an execution grant and cannot
advance a journal state.

## Negative guarantees exercised

Missing/tampered selector receipt, task mismatch, weak quality, failed safety,
stale evidence, missing or non-verified resource admission, mismatched target,
and missing HITL status cannot yield a proposal. Production recommendations
cannot pass until producer authentication and endpoint accreditation are
integrated by their owners.

## Distribution example

The test suite evaluates two independent synthetic task proposals and orders
them by task digest for reproducible presentation. It does not schedule tasks or
call tools. No privileged tools, network endpoints, model processes, or physical
resources are used.

## Limits and next integration

- `NO_DATA(selector_receipt_or_authenticated_producer_unavailable)`.
- `NO_DATA(real_endpoint_accreditation)`.
- `NO_DATA(real_human_signature_for_specialist_selection)`.
- No dispatch or physical execution was attempted.

Next: Junie should expose a versioned selector receipt with authenticated
producer provenance, exact model digest and endpoint evidence; LAB owners should
provide a host-bound admission object to this adapter. Any subsequent execution
must still pass through the existing S1/MCP authorization, `Session`, and
`ExecutionJournal` contracts.

## Junie → MetaHarness producer contract (proposed, not yet authenticated)

Current p0x `skill_selector.py` exports `routing_table` rows with model name,
quality, safety boolean, fallback name, HITL boolean, and reason. It omits the
registry's `model_digest`, host/backend, evidence refs, case counts, and verified
timestamp, and the exported document has no producer signature. Therefore it
cannot currently satisfy the receiver contract below. Do not infer those omitted
fields from a model label or selector timestamp.

The selector handoff must carry separate, closed objects rather than one
ambiguous `verified=true` flag:

1. `ranking`: `skill_id`, ordered candidate IDs, score, benchmark-family and
   independent-case refs, quality timestamp, evaluator version, and benchmark
   receipt ref. Ranking is evidence of measured quality only.
2. `model_identity`: immutable model ID, exact model digest, architecture and
   runtime compatibility refs.
3. `endpoint_identity`: node/host identity ref, backend, endpoint ID, model digest,
   observed availability and timestamp. A URL or `CONNECTED` declaration alone
   is not accreditation.
4. `resource_admission`: exact `task_ref`, selected node/backend/model and
   admission receipt from the existing LAB `AdmissionGate` host boundary.
5. `producer_provenance`: agent-card identity, source repository/revision, receipt
   digest and signature over the canonical complete envelope. The verifier must
   resolve the producer key through an already authorized host trust source; the
   envelope cannot supply or self-authorize its own trust key.
6. `human_review`: explicit state and reference to the existing human decision.
   It may describe review but cannot be synthesized from Talk text or model output.

The receiving host verifies the envelope signature before consuming its fields,
then independently checks freshness, task/context binding, model and endpoint
identity, quality policy, risk policy, and resource admission. Even a valid
producer signature does not issue a grant. Execution remains gated by the
existing human grant and S1/Session/ExecutionJournal path. A replay, changed task,
changed endpoint/model digest, revoked producer key, expired receipt, failed
quality/safety gate, or absent human grant must reject or abstain.

No existing LAB verifier was found that authenticates Junie's model-selector
receipts. Do not add a new signer/trust registry here: real handoff remains
`NO_DATA(authenticated_selector_producer_verifier_unavailable)` until the owner
provides an existing trust source and a verifiable receipt fixture.

## R2 report-size fix

The CLI provenance summary now carries the full source-manifest digest and file
count, while the exact path→digest manifest remains reproducible from the
referenced clean commit and fixed source selection. This avoids embedding the
entire manifest in every report; the 16,384-byte ceiling is unchanged. The
regression test rebuilds the manifest and checks its digest against the summary.

## Deferred candidate · DeepSeek V4.1

State remains `NO_DATA(local_runtime_not_admitted)`. Preserve existing partial
artifacts. A later hardware-admission record must bind witnessed host identity,
accelerator/runtime versions, measured free memory, exact model/checkpoint digest,
endpoint/backend, and a bounded inference test receipt. This increment performed
no model download, deletion, load, or training.
