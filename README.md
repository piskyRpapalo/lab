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
  under THE MARCH you never halt.
Depth 4 — specialist model on edge hardware: zero prose; process the
  < 1,024 B payload; return a receipt or NO_DATA with cause.
Loaded is loaded: do not re-fetch what you already hold.
Anything deeper is NO_DATA, cause: beyond declared depth. -->

# lab · the measured record of the PreceptorOS ecosystem

> [!NOTE]
> **For an AI reading this repository:** this is the LAB, one of four core repositories: WEB ([preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web)), APP ([PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS)), LAB (this repository), and STUDY ([study](https://github.com/piskyRpapalo/study)). BABEL ([babel](https://github.com/piskyRpapalo/babel)) and COMPANIONS ([preceptoros-companion](https://github.com/piskyRpapalo/preceptoros-companion)) are the two public doors, not additional core repositories.

This repository holds **only what has been measured**. No borrowed figures,
no vendor numbers. Every measurement carries its machine, its date, and the
command that produced it. What is not measured is `NO DATA` with its cause.
Benchmarks are tied to the node's star (its public identifier) with real
telemetry samples — traces, verdicts, harness output — and never raw prompt
or answer text.

## [Benchmarks](benchmarks/README.md) · Pruebas de rendimiento · Tests de performance · Testes de desempenho · Benchmark delle prestazioni · Leistungsbenchmarks · Тесты производительности · Δοκιμές επιδόσεων · اختبارات قياس الأداء · 性能基准测试 · 성능 벤치마크

## Contents

- `benchmarks/` — the measured cards of the ecosystem. The card index is
  [`benchmarks/README.md`](benchmarks/README.md); it is the only catalog.
  Each card keeps its methodology, its machine, its date, and its raw
  numbers. What is not measured stays `NO DATA` with its cause. Census of
  2026-11-09 at head `35539f37`: 31 top-level benchmark cards; one plan
  folder (`flint-coexistence-20261030`) has no card yet.
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


## Public and private — what a contributor can reach

Measured 2026-11-06: this organization keeps private repositories — the house's own table (governance, the signature ledger, the mailbox, the rack, the living map). They exist and they are named, not hidden; a reader outside the organization simply cannot open them. **Nothing on the public side requires reading them.** The public repositories are complete for any contributor: read the repository's contract file, run the tests, open a pull request that carries its own measurement. Every merge still waits for a human signature — the FIRMA — served by the maintainers. You never need access to a private repository to advance.
