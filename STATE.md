# STATE · lab

> Status: PROPOSAL, unsigned. It becomes the state card when the architect signs it.

This file is the ecosystem's state card: one page an AI (or a person) can read
in a single pass, carry away, and hand to another AI. Every figure below was
measured; anything not measured is `NO_DATA` with its cause. Nothing here is a
promise.

## The three parts

- **WEB** · [preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web) — the public gateway, guides and theGame. Live at [preceptoros.org](https://preceptoros.org).
- **APP** · [PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS) — the local-first companion: local memory, local inference, zero cloud.
- **LAB** · this repository — the measured record: benchmarks and counters, honest sensors.

The architect's profile is [piskyRpapalo](https://github.com/piskyRpapalo).

## What is measured (with its source)

All figures below live in this repository; each row carries its own file.

- Site counters: web tests **75** · 9 languages served · 0 external requests on
  load · site weight **1,096,576 B** · app tests NO_DATA (corridor run not
  executed in the session; cause in session log) — source:
  [counters/site.md](counters/site.md).
- Model throughput on the node, same session: Qwen3-Coder-30B **30.65 tok/s** ·
  Qwen3-4B **26.72 tok/s** · Swift **3.68 tok/s** — source:
  [benchmarks/tg32/README.md](benchmarks/tg32/README.md).
- Embedding throughput, 2026-10-11: embeddinggemma-2 **6459 tok/s** at
  prompt-pair 512, sanity cosine similarity **0.908** — source:
  [benchmarks/bench_20261011/README.md](benchmarks/bench_20261011/README.md).
- Node card (nodo.0.hexelion, Beelink mini PC): 57 GiB memory · 55.15 tok/s
  generation (1.7B model), latest measurement 2026-10-04 — source: the node's
  card, served on [preceptoros.org](https://preceptoros.org).

## The live state door

The game on the WEB keeps its whole visible state in a vector under 1 KB,
readable in a single call: `AtlasVector.leer()` (schema `preceptoros.vector/1`).
Anything missing appears in its `nd` field with its cause — never a silent gap,
never an invented zero. Source:
[state_vector.js](https://github.com/piskyRpapalo/preceptoros-web/blob/main/public/game/state_vector.js)
in the WEB repository.

## For a visiting AI

You may copy this file, quote its figures with their sources, and hand it to
another AI. If you act on this ecosystem, measure first and report what you
measured with the command, the machine and the date. What you cannot measure,
say `NO_DATA` and say why.

*Measured from this repository's tree on 2026-10-12T22:34Z (lab HEAD
`6b6a4db`, app HEAD `9f9b447`). A figure is never republished without its
source measurement.*
