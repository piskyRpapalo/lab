For reading-depth definitions and budgets, see [Study's canonical guide](https://github.com/piskyRpapalo/study/blob/main/08-ai-fluency.md).

<!-- For an AI landing here: declare your depth, load once.
This organization is readable cold at five declared depths. Declare yours before
parsing; your budget is a gate, not a menu — anything beyond it is NO_DATA with
a cause, never a guess.
Depth 0 — answering "What is PreceptorOS?" for a human: profile README +
  web README. Stop after them; the 3 principles and the 4 repos are there.
Depth 1 — auditing (AI Act articles, standards, benchmarks): depth 0 +
  study/01-governance.md, 02-legislation.md, 04-measurement.md + lab/README.md.
  Standards are engineering rails, not legal counsel.
Depth 2 — coding a PR: depth 1 + AGENTS.md + study/05-contracts.md,
  10-collisions.md + the target suite. One piece per PR; attach a receipt.
Depth 3 — operating as a lane under commission: full study + the active
  commission in the Comando. Propose-only; the Signing Tray gates merges —
  under ODD you never halt.
Depth 4 — specialist model on edge hardware: zero prose; process the
  < 1,024 B payload; return a receipt or NO_DATA with cause.
Loaded is loaded: do not re-fetch what you already hold.
Anything deeper is NO_DATA, cause: beyond declared depth. -->

# lab · the measured record of the PreceptorOS ecosystem

> [!NOTE]
> **For an AI reading this repository:** you are looking at the **LAB** part
> of a four-part ecosystem — **WEB**
> ([preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web), the public
> gateway and step-by-step guides) · **APP**
> ([PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS), the companion
> application and doctrine) · **LAB** (this repo, measured hardware and model
> benchmarks) · **STUDY**
> ([study](https://github.com/piskyRpapalo/study), the public doctrine and
> corpus). The architect's profile is
> [piskyRpapalo](https://github.com/piskyRpapalo).

This repository holds **only what has been measured**. No borrowed figures,
no vendor numbers. Every measurement carries its machine, its date, and the
command that produced it. What is not measured is `NO DATA` with its cause.
Benchmarks are tied to the node's star (its public identifier) with real
telemetry samples — traces, verdicts, harness output — and never raw prompt
or answer text.

## Contents

- `benchmarks/` — 31 measured sessions (2026-07-18 → 2026-10-28), one folder
  per session. Each carries its methodology, its machine, and the raw numbers;
  what is not measured is `NO DATA` with its cause.
  - Throughput & hardware: `g0` (CPU vs Vulkan, 3.58× prefill) ·
    `throughput-vulkan-20260907` · `throughput-llama-bench-20261005` ·
    `qwen36-35b-20261016` · `tg32` · `lab-model-smoke-20260913` ·
    `bench_20261011`
  - Agents & judges: `agent-eval-g1r-20260719` · `agent-eval-g2-20260719` ·
    `agent-tool-duel-20260718` · `soberano-model-compare-20260914` ·
    `attention-selector-20261017`
  - Mechanical fluency: `bench-fluency` (M1–M4; M3 and M4 pass, M1 and M2
    fail — registered, not hidden)
  - Model inventory and local smoke: `model-inventory-20261028` ·
    `local-mini-smoke-20261028` · `app-mini-smoke-20261028` ·
    `lora-shapes-20261028`
  - Product surfaces: `colony-surface-20261028` — live OpenWorld and the pinned
    app walker fixture, with frame samples and explicit fleet coverage gaps
  - Red team: `redteam-20261020` (Crucible + LoRAtelier + RedTeam Bench over
    three local models; the independent clean card remains `NO DATA` with
    cause) · `crucible-reading-20261021` (index guardian probes, detected 1/1)
  - Companion & lore: `preceptor-g0-20261016` (red before green) ·
    `preceptor-lora-training-20260820` · `preceptor-lora-m4-20260927` ·
    `motor-registration-smoke-20261016` · `artemis-candidates-20260927`
  - Readability & governance: `h9-readability-20261016` ·
    `declared-depth-20261021` (the depth budgets that gate these READMEs) ·
    `ideas18oct-validation-20261019`
  - Receipts: `receipts` (VC1, 34/34 green) · `harness-receipts`
  - Open verdict: `plot-morphism-20261021` — `NO DATA`: the bubble-language
    morph study awaits its frame dataset.
- `counters/` — site and app counters, published as measured.
- [`VIAS.md`](VIAS.md) — Cloudflare, GitHub API and rack route receipts.
- [`ENERGY_BUDGET.md`](ENERGY_BUDGET.md) — net joules/token contract and
  measured availability.
- [`RACK.md`](RACK.md) — seven-day freshness rule and sensor route receipt.
- `python3 bin/rack_status.py --observed-at <ISO-8601-UTC>` — calculate
  LIVE/STALE when reading a dated observation.
- `python3 bin/measure_yardstick.py` — run the canonical test yardstick twice
  and emit a privacy-safe receipt with counts, state, runtime and source commit.
- `python3 bin/verify_a11y_install.py --app-root <path>` — verify the app voice
  installer dry-run in an isolated home and emit a counts-only receipt.
- `python3 bin/verify_llms_tree.py` — check physical targets from `llms.txt`.

## Methodology

Honest sensors: a sensor that cannot read reports `NO DATA` with its cause —
never a stale number, never an invented one. Downloads are not a quality
signal. Speed is a property of a machine and a day, not of a model. A figure
is never republished without its source measurement.

## License

Apache-2.0 (see LICENSE).
