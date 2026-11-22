# STATE · LAB ecosystem

## Benchmark pulse · checked 2026-11-11 UTC

[Verified per-PR states, exact SHA, workflow receipts and limits](odd/tasks/benchmark-status-20261111.md) · [Comando receipt](https://github.com/piskyRpapalo/buzon/issues/61#issuecomment-6790565281).

- **Nov 10:** LAB #144–#149, APP #235, WEB #799 merged; exact-head CI SUCCESS. LAB #150–#154 were created late Nov 10 and merged Nov 11; CI SUCCESS.
- **Nov 11 (20:53 UTC):** LAB #155–#162, #167, #169 MERGED; CI SUCCESS. #158 experiment RED. #165/#166 OPEN; CI queued.
- **NO_DATA:** solar energy/J per token, human-gold calibration, unattended dispatch and physical accessibility; not measured in these reports.

### Archived snapshot · Oct 22 (not current)

> Snapshot date 2026-10-22 · measurement hour: NO_DATA (not captured). Proposal, unsigned; values link to dated evidence.

## Live repositories

- WEB `01f8b077` · [preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web)
- APP `d1c8084e` · [PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS)
- LAB `ee537371` · this repository

## Measurements

Machine: Linux x86_64, AMD Ryzen 7 255, 16 logical CPUs; Python 3.14.4.

- LAB `unittest discover -s tests -p 'test_*.py'`: 138 tests, 137 pass, 1 skip, 0 fail ×2 separate runs at `ee537371`.
- LAB live PR workflow, Python 3.10/3.11/3.12: all three jobs RED before tests complete. Each ran 138 tests (137 pass, 1 skip), then `test_llms.py` 2/2; tree verifier rejected INDEX total **13,684 B > 12,109 B**. The same verifier is already RED on clean main: **13,071 B > 12,109 B**. This card compaction is intended to restore the index budget; do not alter the declared budget.
- `.github/workflows/pruebas.yml` exists despite `AGENTS.md` saying remote CI is not configured. Conflict recorded; neither policy changed.
- WEB site counter: **1,429,750 B** at `01f8b077`, from `public/counters.json`; method at WEB `contadores.py:55-65`. WEB and APP suites: `NO_DATA`, cause: not run in this LAB refresh.

## Rack snapshot

Read-only aggregate on this machine, 2026-10-22: Ollama lists **45 models**, summed size **253,307,000,000 B**, with **0 active**; `~/.preceptoros` has **263 files / 49 directories / 5,060,141,941 B**; port 8740 has a listener, PID unavailable; process-name scan found **0** `preceptoros` processes; Tailscale is Running, self online, **5/8 peers online**. No model or peer names copied into this public card.

## Archived benchmark evidence

Measurements remain dated and scoped; they were not rerun for this snapshot. Source cards retain raw provenance:

- Qwen 35B-A3B, 2026-10-16: Vulkan generation 20.760 tok/s (2 samples); CPU 2.114 tok/s (2). [`qwen36-35b`](benchmarks/qwen36-35b-20261016/README.md).
- Local role check, 2026-10-16: unavailable-engine sabotage rejected; two responses matched by hash. One narrow task, not a general capability score. [`preceptor-g0`](benchmarks/preceptor-g0-20261016/README.md).
- H9 synthetic readability, 2026-10-16: map 4/8 exact reads; dense stimulus 0/8 vs prose 2/8. Association only; documents differ. [`h9`](benchmarks/h9-readability-20261016/README.md).
- Embedding, 2026-10-11: embeddinggemma-2 6,459 tok/s, prompt-pair 512. [`bench_20261011`](benchmarks/bench_20261011/README.md).
- Older `tg32` values remain reported; date, machine, command and repetitions are `NO_DATA` because the session log is absent. See [`tg32`](benchmarks/tg32/README.md).

Current temperature, energy, sustained-load behavior, general model quality and live browser performance: `NO_DATA`; these sources do not measure them. Benchmark index: [`benchmarks/README.md`](benchmarks/README.md).


## Evidence pulse · GitHub readback 2026-11-22 UTC (not a new benchmark)

**Scope:** documentation-only audit by Codex GPT-6 Web through GitHub connector; source is the public `main` readback and linked cards/PRs, **not** a fresh test run, model invocation, physical measurement or deployment. This pulse does not supersede the dated 2026-11-11 snapshot above.

| Research line | Source-backed state on this readback | Limit / missing witness |
|---|---|---|
| 2D context alignment | [2026-11-20 card](benchmarks/context-fusion-20261120/README.md): **64/64** aligned vs **19/64** unaligned; poisoned anchors refused **64/64**. Synthetic evidence slots, not tokens. | `NO_DATA(cross_model_real_KV_alignment_or_attested_grants)`; controlled geometry, not LoRA/real host proof. |
| Hexelion host-policy planner | [2026-11-20 card](benchmarks/hexelion-v1-host-policy-20261120/README.md): **17/24 exact**, **21/24 valid JSON**, seven permitted targets omitted, synthetic grants. | RED effectiveness; `NO_DATA(actual_signed_multi_host_MCP_dispatch_in_this_holdout)`. |
| Multi-turn and longer-horizon statistics | Existing `meta_harness/multi_turn_first_failure.py` and `long_horizon_gate.py` are **pure evaluators** with explicitly untrusted/synthetic supplied events. | Presence of source code does **not** imply a running judge, real attack, authenticated witness or a sound recording. |
| New security-study G0/G1 lens | [LAB PR #244](https://github.com/piskyRpapalo/lab/pull/244) remains **DRAFT / OPEN**, separate from this branch. External receipt describes synthetic 11/11 ×2 with CI success at its own head. | `NO_DATA(confirmatory_GOLD_or_owner_authorized_host_effect)`; do not duplicate or edit that PR's files. |
| Remote Inkling/LFM3 | [LAB PR #243](https://github.com/piskyRpapalo/lab/pull/243) is reflected in main merge `5fc67df6a999aab776874095ab3063083e40eaf1`. | Benchmark conditions remain the card's own; no new measurement in this pulse. |
| TRAIN-02 Qwen job | The active scientific commission is outside this doc-only branch; evidence must be read from the current private Mesa and OWNER's job-specific physical receipt. | `NO_DATA(authenticated_remote_training_output_not_independently_observed_by_this_readback)`. A staged script or SHA check does not prove GPU training, EDGE delivery, quality acceptance or model promotion. |
| Sovereign S1 revocation | [p0x PR #139](https://github.com/piskyRpapalo/p0x/pull/139) is merged; the private S1 change is not duplicated here. | `NO_DATA(116B_to_S1_to_MCP_independent_effect_witness)`. Synthetic revocation tests do not authorize tools. |

**Strict separation:** SOURCE FILE / DRAFT PR / MERGED MAIN / DEPLOYED SERVICE / PHYSICAL E2E are different states. No model weights, CLI, OWNER grant, S1 authorization, app installation, external data or agent execution has been altered. The 24-case planner holdout is already exposed and must not silently become training GOLD. The new security study must freeze gold/witness independently before any confirmatory trial.

**Verification performed here:** current GitHub `main` HEAD readback and linked source files; **`NO_DATA(two_local_test_runs_not_executed_read_write_only)`**. The exact-head CI of this documentation PR, if any, is a separate future gate; do not describe it as already green.
