# Local attention selector · 2026-10-17

Status: implementation measurement, not a relevance-quality claim. The code
and synthetic tests are publishable; the verbatim chunk store and all
generated packages remain in owner-only local storage outside this repository.
No corpus text, task prompt, answer, source path, or per-corpus count is archived
here.

## Contract and implementation

- The pure selector uses integer lexical overlap with inverse document
  frequency, a stable chunk-id tie-break, explicit source exclusions, and
  caller-declared byte ceilings: `attention_selector/core.py:76` and
  `:100-118`.
- Ingestion preserves UTF-8 text byte-for-byte, uses content SHA-256 plus an
  opaque hash of the relative origin, records a caller-supplied
  ISO date, and appends owner-only files:
  `attention_selector/store.py:15-23`, `:33-84`, `:87-138`.
- Two-pass output has a stable policy prefix, bounded index, and complete
  verbatim chunks. Both passes bind the same policy/query hashes and declare
  their byte/count ceilings. Each listed item is `VERBATIM` or `NO_DATA` with
  a cause; a truncated index declares the unlisted count and byte-ceiling cause:
  `attention_selector/package.py:38-118`.
- The reader, model caller, and receipt writer are injected ports:
  `attention_selector/service.py:16-48`. The model adapter is numeric-loopback
  only, checks the installed model before calling it, and uses temperature 0
  with a fixed seed: `attention_selector/local_model.py:10-41`.
- NDCG requires explicit labels. No approved query-to-chunk gold set is
  present, so real-task NDCG is `NO_DATA` with cause:
  `attention_selector/evaluation.py:9-33`.

## Measurements

- Test yardstick: `python3 -m unittest discover -s tests -p "test_*.py"`;
  two independent runs on this branch each measured **23 tests, 0 failures**.
  This is a local test result, not remote CI. The repository contract declares
  that remote CI is not configured.
- Red-before-green: before implementation, the new directed suite failed to
  import `attention_selector.core` because the package did not exist. During
  integration, two directed assertions also exposed an incorrect test access
  and insufficient test byte ceilings; the corrected checks then passed.
- Synthetic package test: deterministic bytes on repeated input; index and
  chunk records match; exact ceilings respected; multibyte text round-trips;
  tampered chunk hash, invalid capture date, disallowed host, absent gold, and
  too-small budgets fail closed. Synthetic NDCG is 1000/1000; this is a unit
  test of the metric, not a live relevance score.
- Local inference adapter: one equation-explanation request reached the
  loopback service on 2026-10-17 and returned a non-empty 584-byte response.
  Method: `LocalModelCaller.explain` with a synthetic equation and cause;
  temperature 0, seed 0; response text was not retained.
  Ollama 0.40.3; blob SHA-256
  `3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6`,
  1,359,279,776 bytes. `ollama ps` measured runner `llamacpp`, 100% GPU,
  context 32,768. Machine: x86_64, AMD Ryzen 7 255 with Radeon 780M Graphics,
  16 logical CPUs, 60,396,292 KiB memory. These identify the measured local
  hardware and model blob; the model label and machine hostname are omitted.
  A non-empty answer does not measure semantic correctness; that remains
  `NO_DATA` without approved labels.
- Tokenizer-specific token counts: `NO_DATA`; the local adapter does not expose
  a tokenizer count. Byte ceilings are exact and measured separately.
- Browser, relay caching, multi-device replay, and remote CI: `NO_DATA`; this
  lab tool has no browser surface and no remote CI configuration.
- Private-tree guardian: `NO_DATA`; `PRECEPTOROS_PRIVATE_SCAN_TOKENS` is absent
  from this local environment and was not created. The check was not counted
  as a pass.

The only live-corpus ingestion test was run into the local owner-only store.
Its receipt and corpus-derived package stayed on the rack and are intentionally
not archived in this repository.
