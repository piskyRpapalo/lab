# SWARM-01 · LAB measurement charter and device preflight

**Agent:** Codex · GPT-6 · **Date:** 2026-11-11. **Mode:** PROPOSE-ONLY. This is a measurement companion to the Private Mesa swarm commission, **not** a new canonical mission ID. No remote device enrollment, model download or deployment.
**Canonical anchors:** LAB F6 (live device benchmarks); Study H9 and DFA specs; APP A6/B6; WEB D2/D3/D4/D5/H6; Acho C8/A9; ATLAS device provenance. Economic `F6-01` is a distinct A2A synthetic testnet mission.

## Observed sources and truth levels

The [machine-readable preflight](../../benchmarks/receipts/20261111-swarmi-hardware-preflight.json) records the connected rack's actual tool observations on 2026-11-11T01:00:54Z. It is a single **snapshot**, not a continuously running health service. An independently observed Claude CLI process was active at 01:07Z; that is why **no new GPU inference was run during this preparation**. Each builder must refresh the loaded-process check and ownership before any inference.

At preflight: rack Ollama returned 29 installed models and zero loaded; tunnel returned 17 installed models and zero loaded, but remote station OS, process ownership and thermals are NO_DATA. Local memory available was 45,168 MiB. ADB listed **zero authorized Android devices**; a MediaTek USB interface was visible but does not independently identify a phone. ADB enumeration itself can start a local ADB daemon. The user may authorize a physical phone later; do not bypass Android USB debugging authorization.

Past evidence: LAB [#158](https://github.com/piskyRpapalo/lab/pull/158) Gemma2 B5 candidate RED 4/8 ×2, malformed output 1/run; [#159](https://github.com/piskyRpapalo/lab/pull/159) measured mini CPU/GPU; [#160](https://github.com/piskyRpapalo/lab/pull/160) matched Qwen digest across two Ollama endpoints. Those are candidate measurements in draft PRs, **not merged source or a proof of quality**. LAB #150–#157 are separate synthetic feature drafts. #153 is stacked on #150. Never rebuild their instruments blindly.

## Model and device verification schedule (Claude chooses construction order)

| Claim to test | Existing piece / source | Proposed measured gate | Unresolved dependency |
|---|---|---|---|
| **Mini-logic and abstention** | H9, Crucible, B2 scorer draft #156, B5 family gate #157 | >=24 *unique*, balanced local synthetic rules with independent gold; 2 isolated model runs; class confusion, malformed, false certainty, honest NO_DATA; report latency and generated tokens separately | Fixture reference validation, permission to use GPU, consent for any human labels |
| **Private Talk actually chats** | Existing APP chat route and citation guard | 10 source-defined *held-out* questions; exact literal citation or correct NO_DATA, no unsupported claims; original draft retained on failures | APP-LIVE owner claim, valid sources and local browser access |
| **Public building really chats** | Existing WEB building/classroom chat adapter | 10 source-defined questions in visitor scope; no private data or privileged actions; NO_DATA if backend unavailable | WEB owner and opt-in guest route |
| **Acho state parity** | `preceptoros.acho/1`, WEB paint/sonify, H6 | same state digest in machine/text/visual/audio representation; 240 deterministic ticks; 44px actionable targets; stale/NO_DATA sabotage | Audio/source truth and physical assistive test separate |
| **Panel opening and novice game** | APP nine-panel layout; WEB terminal switches, tutorial and battle | 10 open/close/back cycles at 320x568, 420x640, 1024x768; focus returns; no invisible active content; win/loss game receipts | APP/WEB owners; physical phone still unavailable |
| **Physical phone plug & play** | Existing PWA and potential Android endpoint | physical touch, focus, soft keyboard, offline shell, source-backed reply, microphone consent; inspect actual screen/text/audibility | NO_DATA: ADB does not enumerate authorized device |
| **Device throughput/provenance** | canonical LAB F6, #159/#160 | exact model digest and backend, cold vs warm timings, steady throughput, RAM/VRAM, load/thermal, independently validated energy if available | no model lease; tunnel does not attest OS/hardware |
| **Economic A2A fence** | existing F6 probes in main; draft #151 | reject 3 synthetic economic attacks; real signed receiver only after ACHO trust | NO_DATA: live signed testnet not proven |

The model inventory includes small installed candidates `qwen3:1.7b`, `gemma2:2b-instruct-q4_K_M`, `phi4-mini:latest`. Availability is not model suitability. Do **not** choose a judge from the same model family as the manipulator or substitute a fresh speed benchmark for held-out logic accuracy. No raw prompts or generated responses in Git.

## Swarm lanes, independent verification and safe lease

Claude chooses which independent missions to implement after its PLAN is approved. Codex LAB owns fixture protocols, score aggregation, sabotage tests and source-qualified receipts. Codex WEB owns art/game/terminal source. Codex STUFF owns APP/service/install integration. Mistral BEACON checks mission collisions and exact PR head; Sovereign signs.

**Before each GPU job:** observe other active agent sessions, `ollama ps`, CPU/memory pressure and model owner. If any relevant resource is occupied: **NO_DATA: occupied_by_other_worker**; do not kill or unload the other worker. A shared-GPU lease requires explicit owner coordination in Private Mesa #3. Use one model/batch at a time; release only the model this agent loaded. Any E-STOP preserves receipts and aborts the affected lane.

**Receipt shape:** `source_ref, exact_head_sha, host_role, device_attestation, observed_at_utc, model_digest, workload_digest, n_unique, n_runs, pass_index, command, metrics, red_controls, failures, scope, NO_DATA_cause, reviewer`. Same 8 items twice are 8 unique, not 16. Scope names must distinguish `SYNTHETIC`, `BROWSER`, `DEVICE`, `E2E_PHYSICAL`.

**Code gate:** `python3 -m unittest discover -s tests -p 'test_*.py'` ×2, `python3 test_llms.py` ×2, `python3 bin/verify_llms_tree.py` ×2, and PR CI on the exact head. Measurement work is not automatically deployment work. No merge without per-SHA Sovereign review.

## Immediate next bounded piece

When Claude confirms compute access is free, run a **local mini-logic held-out batch** using the existing H9/quaternary assessment path; build a declared reference manifest with at least six unique examples per class, label unknown true-world facts NO_DATA, and publish only aggregate confusion/throughput and sha256. Do not copy prompt text to Git. With the phone authorized, repeat APP/WEB browser journeys physically; until then publish `NO_DATA: adb_devices_empty`.
