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

- `benchmarks/` — one folder per measurement session. Each carries its
  methodology, its machine, and the raw numbers.
- `counters/` — site and app counters, published as measured.
- [`VIAS.md`](VIAS.md) — Cloudflare, GitHub API and rack route receipts.
- [`ENERGY_BUDGET.md`](ENERGY_BUDGET.md) — net joules/token contract and
  measured availability.
- [`RACK.md`](RACK.md) — seven-day freshness rule and sensor route receipt.
- `python3 bin/rack_status.py --observed-at <ISO-8601-UTC>` — calculate
  LIVE/STALE when reading a dated observation.
- `python3 bin/verify_llms_tree.py` — check physical targets from `llms.txt`.

## Methodology

Honest sensors: a sensor that cannot read reports `NO DATA` with its cause —
never a stale number, never an invented one. Downloads are not a quality
signal. Speed is a property of a machine and a day, not of a model. A figure
is never republished without its source measurement.

## License

Apache-2.0 (see LICENSE).
