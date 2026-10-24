For an AI landing here: declare depth before parsing. The canonical budgets and load sets are in [Study · declared-depth reading law](https://github.com/piskyRpapalo/study/blob/main/08-ai-fluency.md). Beyond them is NO_DATA with cause.

# Agent contract · lab

This is the single canonical instruction set for agents working in the lab. Tool-specific files point here and do not create parallel policy.

- The agent proposes and measures; a human signs PR by PR. Never sign, merge, choose the Mesa's seal letter, push to `main`, or push to Jetson.
- Start branches from current `origin/main`. Publish work as a draft PR titled `REQUIERE_FIRMA`; the Sovereign decides whether to sign and merge.
- This repository is the measured record. Each number carries source, machine, date, harness/command, and scope. Vendor figures are labeled as declared, never as local measurements. `NO_DATA` always has its cause; do not invent or silently omit fields.
- Do not commit raw prompts, raw answers, credentials, private identifiers, or personal data. Receipts and artifacts may contain counts and paths, never private values.
- Preserve human review and zero telemetry. Do not send model inputs, outputs, or node state to an external service as part of a benchmark.
- Yardstick: `python3 -m unittest discover -s tests -p "test_*.py"`. The local contract requires two runs for a piece. `.github/workflows/pruebas.yml` configures pull-request and `main`-push checks on Python 3.10, 3.11, and 3.12. Each job repeats `python3 -m unittest discover -s tests`, `python3 test_llms.py`, and `python3 bin/verify_llms_tree.py` twice. Measure and report workflow results for the exact ref; local checks are not remote CI.
- Read `STATE.md` for the measured record and `README.md` for repository scope. If either is stale or does not contain a value, report `NO_DATA` with cause rather than copying an old number as live.

## Claude Code and Codex

`CLAUDE.md` points back to this file. Keep one source of policy; update this file first when the lab contract changes.

## Local attention selector

`attention_selector/` is a deterministic, standard-library-only selector. Its lexical score, explicit exclusions, stable tie-break, and byte ceilings are code rules; the local model is an optional explanation adapter and never ranks, rewrites, signs, or authorizes. The CLI is `bin/lab-attention-selector`.

The verbatim chunk store and generated two-pass packages stay outside this repository under the operator's local state directory (default `~/.local/share/lab-attention-selector/`). Never add corpus text, task prompts, model answers, source paths, or generated packages to Git. Ingestion records only local metadata and content hashes in the local store; chunk content remains verbatim and local. Package commands require explicit byte ceilings. Pass one is an index; pass two contains complete verbatim chunks, each sealed with its SHA-256. Both have a stable policy prefix. Outputs are created with owner-only permissions and are never sent by the tool.

Examples (all file paths supplied by the operator remain local):

```sh
bin/lab-attention-selector ingest /local/corpus --max-chunk-bytes 3072 --captured-at 2026-10-17
printf '%s' 'task supplied locally' | bin/lab-attention-selector package --query-stdin --max-chunks 8 --max-chunk-bytes 3072 --max-total-bytes 8192 --index-budget-bytes 1200 --chunk-budget-bytes 8192 --output-dir /local/selector-output
bin/lab-attention-selector explain --equation 'priority = integer lexical score' --cause 'query overlap' --host 127.0.0.1 --model "$LAB_SELECTOR_LOCAL_MODEL"
bin/lab-attention-selector ndcg --ranked-ids /local/ranked-ids.json
```

The model adapter accepts numeric loopback only, checks that the configured model is already installed, uses temperature zero and a fixed seed, and does not download models. Priority is the integer lexical-overlap score `Σ min(tf,8) × (N+1) × idf_scale // (df+1)`; ties sort by chunk id. Exclusions are explicit source policy or no query overlap, and `--exclude-source-id` can add source hashes to the exclusion set. Exact byte ceilings are enforced; tokenizer-specific token counts are `NO_DATA` because the model tokenizer is not exposed by this adapter. A missing model, unavailable local service, absent NDCG gold labels, or empty eligible selection is `NO_DATA` with a cause. NDCG gold labels must be supplied explicitly; no relevance labels are inferred from prompts or model answers. Explanation output is checked for presence only; semantic correctness remains `NO_DATA` until an approved labeled set exists.
