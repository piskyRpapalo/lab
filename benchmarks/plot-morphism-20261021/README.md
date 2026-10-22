# M9 · plot-morphism study · 2026-10-21
Benchcard: machine=NO_DATA (machine class absent from card) | date=2026-10-21 | runner=NO_DATA (runner absent or not singular) | quant=NO_DATA (quant absent from card) | sha256=4ef57960a2f3e195f66e8afa963733b65f7f819369b15c25f58c90b0997194bc

Verdict: `NO_DATA` — the current evidence cannot decide whether every visible web element fits one page represented by bubble language.

## Inputs

- LAB base: `5df0a663c3a2b036a71e2b4b772a81193746c294`.
- `study_spec.json`: 461 B, SHA-256 `4ef57960a2f3e195f66e8afa963733b65f7f819369b15c25f58c90b0997194bc`.
- `data/study_spec.schema.json`: 3,215 B, SHA-256 `ff5f42792ff1682428a83c21047d3d462ca1217e4309c84c584bfc5dd8cdbe65`.
- The five study variables are all `NO_DATA`, each with a cause; the schema has no visual-scope, frame-inventory, or completeness field.
- Read-only WEB source: `origin/main` `92278ba4d5f80e5ee9f8c907733f11094304f21a`.

## Measured source census

Commands against that WEB tree: `find public -type f -name '*.html' | wc -l` → 10 served HTML files; `find public/game -maxdepth 1 -type f -name '*.js' | wc -l` → 128 `public/game/*.js` modules; `find public/assets -maxdepth 1 -type f -name '*.js' | wc -l` → 40 `public/assets/*.js` modules. These are file counts, not a count of rendered visual elements. No approved frame dataset or mapping from each rendered element to a bubble-language frame is declared, so a one-page fit score remains `NO_DATA` with that cause.

## Reproduction

Run `python3 -m unittest tests.test_study_spec tests.test_plot_morphism_card`; the first suite validates the existing template/schema and the second checks this receipt against the measured inputs. No study input or template value was changed.
