# LORA-RUNTIME-WITNESS-01 · Rotating heads witnessed, no second router

Owner: Codex GPT-6 Web, independent LAB lane. Authority: Sovereign HITL for
isolated experiment, 2026-11-18. Integration remains a draft PR; merge and
deployment require review and human exact-head FIRMO. WEB/APP untouched.

## Existing ground truth and problem

Reuse APP adaptador_registro.py (compatibility and resource constraints),
LAB meta_harness/head_eligibility.py (head filter), c2c_preflight.py (exact
cache scope), context.py (source freshness) and delegation/Session for real
authorization. The private ARMORY v2 plan already specifies llama.cpp LoRA.
No new model router, adapter catalog, cache store, permission service or RAG.

The missing connection is evidence that a specific local llama.cpp instance
reports operator-pinned base and LoRA artifacts, plus a safe mapping from
host-approved adapter digest to per-request numeric ID. An unknown LoRA ID
can return HTTP 200 with the unadapted base response; status 200 is not
successful head selection.

## Native addition

- meta_harness/lora_runtime_probe.py::snapshot performs GET /props and
  GET /lora-adapters twice on numeric 127.0.0.1 only. No arbitrary routes,
  proxies, redirects, credentials, POST or model text. JSON <=16KiB.
  Operator-provided artifact paths are opened read-only with O_NOFOLLOW and
  their bytes hashed; the reported paths and stable metadata must match.
  Duplicate IDs, unknown adapters, changed scales, changed task name or
  prompt prefix and unstable readbacks fail closed. No paths or text in receipts.
- prepare_request_head binds a host-selected base+adapter SHA to an observed
  adapter ID, a fresh observation (max 120s), session, selected context,
  S1 tool policy and permission revision. It REQUIRES an independently
  injected host witness callback. The output is a bounded per-request LoRA
  field, never an inference command, a signature or an execution grant.
- Both receipt types are under 1024 UTF-8 bytes and declare
  dispatch_authorized=false, cache_reuse_authorized=false and
  promotion=NOT_AUTHORIZED. Self-hash means integrity, not identity.
- A GET snapshot cannot prove which head the server applied on a specific
  inference. The existing dispatcher must enforce exact task/grant, revalidate
  source and tool scope, independently test inference and record its own
  receipt. Do NOT use global POST /lora-adapters in a shared service.

## Rack measurement · 2026-11-18

Machine: Beelink rack (x86_64), CPU-only llama.cpp b10488-9d77fa172,
2 threads, 512-token context, single slot; loopback-only temporary server.
Used a pre-existing 135M GGUF base (SHA prefix 4abade0d5f0a) and two
already-trained PEFT LoRA checkpoints. Existing converter generated the
rank-8 adapter (4,913,728 bytes, SHA prefix dace6b4a98cb) and the rank-16
adapter (9,798,208 bytes, SHA prefix e7ce08f2d2b0). No downloads,
training, permanent service or existing service changes.

1. Isolated server GET /health HTTP 200; GET /props identified its local
   base path and GET /lora-adapters listed both adapter IDs. POST to its
   private /lora-adapters switched (0,0), (1,0), (0,1), (0,0) without server
   restart. Eight native chat completions (n=2 for each state) were nonempty,
   repeat-stable and had different output hashes for base, rank 8, rank 16.
   Returning to base reproduced exactly the original base hash.
2. Safer per-request LoRA experiment: global adapter scales stayed (0,0).
   Same synthetic fixed question, temp 0, fixed seed, cache_prompt=false.
   Two completions each for base, rank 8, rank 16, restored base, and invalid
   numeric ID 999: ten nonempty responses, all HTTP 200. Authorized variants
   produced three distinct deterministic hashes; returning to base matched
   the baseline. Reported cached prompt tokens were zero in all ten calls.
3. Critical negative: nonexistent ID 999 produced HTTP 200 and the same
   output digest as base, twice. The native request binding prevents unknown
   IDs from being accepted as selected specialists. Initial six calls using
   raw completion without the proper chat template returned empty EOS; they
   are NOT counted as successful generations and motivated the corrected
   chat-route measurement.
4. Trial telemetry and model-output digests are stored locally in a private
   temporary workspace. LAB commits contain no raw prompt, model output,
   private filesystem path, credential or model tensors.

## Reproduction and gates

From an operator-selected compatible base and two checked adapters, launch a
new loopback-only llama-server with explicit CPU limits, parallel=1, loading
adapters by the existing --lora and --lora-init-without-apply flags. Run:

    python3 -B -m meta_harness.lora_runtime_probe --help

Then provide the absolute local base/adapter paths and SHA-256 flags and
numeric loopback endpoint. The CLI itself only executes GET. Optional live
inference must be manually authorized, sent through the existing client
using the bound per-request lora field, and evaluated base/adapter/base
with the SAME controlled synthetic workload, n>=2, source hashes, timings
and cache counters. Never run a global adapter switch on a shared service.

Directed and canonical gates (twice, exact branch head):

    PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_lora_runtime_probe
    PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_*.py

Additional exact-head gates (Codex GPT-6 Web review, 2026-11-18):
commit 9928e84, directed 23/23 PASS x2; full LAB 1256 total
(1255 PASS + 1 SKIP) x2, zero failures. A deliberate digest-check
mutation made the directed regression RED; unmodified code GREEN.
Counts supersede the earlier pre-commit suite census in the local trial.

**Limitations / NO_DATA:** real loaded-tensor attestation, original HF model
revision used during training, independently scored semantic quality,
LoRA KV sharing, cross-model C2C transfer, concurrent tenant isolation,
production transport, physical joules, integration into APP/S1 runtime and
Acho physical audio/screen-reader parity. Cache prompt token count zero
is NOT evidence of cross-head KV reuse.

Sources for continuation: LAB c2c_preflight.CacheKey, head_eligibility,
APP adaptador_registro.py, Mesa private #39/#40. Scientific comparison:
llama.cpp native per-request routing vs LRAgent/PReCache style shared KV,
with a verified compatibility and cache invalidation witness before
performance claims. Never add another agent or register a second authority.
