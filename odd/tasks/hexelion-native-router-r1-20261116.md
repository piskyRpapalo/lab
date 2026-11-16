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
