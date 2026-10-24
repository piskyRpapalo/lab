# Proposal: Bubble scene-geometry parity across themes

**State:** staged proposal; visual comparison and served-example binding are
not measured.
**Branch:** `mistral/bubble-theme-parity-20261024`.
**Base:** LAB `origin/main` at `108e2412caeebf079ebbe2fc11d20fa6561aa58a`.

## Contract

`bin/check_bubble_theme_parity.py` takes three `preceptoros.bubble/1` JSON
frames named `basic`, `atlantis`, and `zombie`. It computes the UTF-8 byte
length of each supplied frame and enforces 1,024 bytes. It compares normalized
scene data: canvas, atom ordering and nouns, primitive ordering/types, and all
primitive geometry parameters. Palette bands, fill/stroke colors, text labels,
frame ids/scroll positions, lighting, and style are excluded from the geometry
digest. Product-panel layout is neither an input nor part of the compared
scene, so three different layouts cannot fail parity.

All three palette fingerprints must differ. A geometry change or reused palette
is red. Missing/invalid inputs are `NO_DATA` with cause. The result says
explicitly that it does not prove pixel parity, family-friendly semantics,
runtime behavior, or that the frames are the ones bound to the three served
examples. Those require the Bubble contract/renderer cases and a later artifact
pin.

Run:

```sh
python3 bin/check_bubble_theme_parity.py \
  --basic basic-frame.json --atlantis atlantis-frame.json \
  --zombie zombie-frame.json
```

## Yardstick

Local judge: `python3 -m unittest tests.test_bubble_theme_parity`. Its six
synthetic cases cover matching scene geometry under different panel layouts,
coordinate drift, palette reuse, oversize frames, missing themes, and an
unsupported frame version. Layouts are deliberately supplied only as ignored
metadata in the passing test; the implementation does not load them.

## Receipt

- WEB contract citation read from fetched local `origin/main` object
  `8c4eeed840757a02bf5b6cc85b67f40fdbced78a`: `docs/bubble-language.md`,
  sections 1–3 and 5; frame under 1,024 UTF-8 bytes and primitive geometry.
- Local judge: 6 tests passed after implementation; initial missing-module
  import was the red baseline.
- LAB full gate: two passes. Each pass ran discovery (153 tests, 152 pass,
  1 skip), `test_llms.py` (2/2), and `verify_llms_tree.py` (5 indexed paths
  resolve; 11,695 B <= 12,109 B).
- Physical/browser appearance and actual binding to the forthcoming examples:
  `NO_DATA`, cause: no rendered-theme artifacts were supplied to this judge.
- Remote CI: `NO_DATA`, cause: no PR has been opened.
