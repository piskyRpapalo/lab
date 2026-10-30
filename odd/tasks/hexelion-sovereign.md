# Hexelion sovereign — the octopus (mission charter)

Status: PROPOSED · REQUIERE_FIRMA. Under ODD the signature gates the MERGE, never the BUILDING: this charter is live work the moment it is read.

## Objective

Make the unified-memory head of the rack a sovereign coordinator: one head, many arms.
Each fleet device keeps its own small model and its own local corpus (RAG); the head
integrates distilled typed verdicts, never raw corpus. The same semi-deterministic
judge — a grammar-constrained LoRA whose output space is `{choice, score, noul, probs[], no_data cause}`
— runs on every node, so a small arm cannot hallucinate outside the decision space.

## Why

- An octopus keeps two thirds of its neurons in its arms. A head that carries everything
  drowns in context; a head that integrates distilled verdicts stays fast.
- The declared cascade: stdlib → choice model → mini orchestrator → large model, with a
  trace on every output. The choice tier proposes; it never decides alone. Confidence is
  the first suspect.
- Declared law (SPEC-1): web = eyes; app = body; lab = brain. The decision is never taken
  in the web; the deterministic decision is never delegated to a model without a tier-1
  layer in front; the irreversible decision is never taken by an agent without carbon.
- Honest sensors everywhere: an arm that cannot read returns `NO_DATA` with its cause —
  never a stale number, never an invented one.

## Scope (slices)

- **HS0 · head baseline (this PR):** the measured record of the head before the mission —
  three local models, three hot runs each, medians, honest sensor peaks
  (`benchmarks/station-tanda1-20261030/`).
- **HS1 · tentacle census:** enumerate fleet devices over the private mesh; measure
  RAM/VRAM/cores per device; install one runtime per head (llama.cpp or Ollama); one mini
  smoke per node. An unreachable node is `NO_DATA` with cause, not silence.
- **HS2 · mini tanda per tentacle:** three hot runs per candidate small model per node;
  one typed verdict per candidate; nothing published beyond loopback and the mesh.
- **HS3 · arm contract:** each tentacle exposes `/decide` (typed verdict),
  `/rag/query` (hash-cited), `/status` (honest state vector). Loopback and mesh only.
- **HS4 · judge dataset:** harvest typed verdicts from the fleet sensor record plus golden
  cases; hashes and counts only — never raw prompts or answers.
- **HS5 · judge LoRA pilot:** QLoRA over an open-weight ~20B base on the head's iGPU
  (ROCm); grammar-constrained typed output; benched against the deterministic tier and
  the local System-1 router, with causes for every gap.
- **HS6 · `preceptor` launcher:** routes status/census → local sensor; decision → judge;
  code/benchmarks → coder lane; heavy reasoning → head via the existing loopback tunnel.
  The web already carries its own creator lane (preceptoros-web → odd/tasks/preceptor-coder.md).

## Out of this charter (declared, not invented)

- No central corpus on the head: the head keeps context for reasoning, not for storage.
- No public exposure: loopback and private mesh only; no public listeners, ever.
- No vendor figures: every number measured with machine, date, command.
- No tentacle speaks with another's voice: its own model, its own corpus, the shared
  judge — or `NO_DATA` with cause.

## Constraints

- One heavy model resident per node at a time; minis ≤ 2 GB may coexist.
- Propose-only: no merge, no firmware, no services, no ports, no keys. The Sovereign
  signs per piece and per exact head; batches expire.
- English public names; no private identifiers, hostnames, or addresses in public artifacts.
- Benchcards carry `Broadcast receipt:` and `Benchcard:` lines; `NO_DATA` always has a cause.

## Checklist

- [x] HS0 · head baseline measured and published (benchcard in this PR).
- [ ] HS1 · tentacle census receipts per device.
- [ ] HS2 · mini tanda per tentacle.
- [ ] HS3 · arm contract on every reachable tentacle.
- [ ] HS4 · judge dataset sealed (hashes and counts only).
- [ ] HS5 · judge LoRA pilot benched on the head.
- [ ] HS6 · preceptor launcher routes all four lanes.

## Log

- 2026-10-30 · Charter opened under ODD (replacing the monolithic manual SDD flow).
  Base `origin/main` 25cb138.
- 2026-10-30 · The head's firmware UMA carve change (64 → 96 GiB, system left with 30 GB)
  was signed physically by the Sovereign on 2026-10-30; measured records are scoped per
  configuration and never summed across eras.
- 2026-10-30 · A 131,072-context trial on the head measured lower generation and failed
  its semantic probe; verdict NO_PROMOVER, reverted to 65,536 and re-verified. The
  station keeps its measured stable context.
- 2026-10-30 · The private fleet sensor record carries the full head architecture
  proposal (EL_PULPO); this charter is its public ODD form.

## Next step

HS1 tentacle census — commission to the coder lane. Work continues under ODD; the
signature gates the merge, never the building.
