# Self-preference benchmark · 2026-10-25
Broadcast receipt: figure=same 2/6 (33.3%); cross 4/6 (66.7%); combined 6/12 (50.0%) | model=3 open families: Mistral 7B, Qwen2.5 Coder 1.5B, Granite Dense 8B | machine=x86_64; fleet-ring coverage NO_DATA (cause: no approved ring mapping) | date=2026-10-25 | sha256=1069062c37be1ec7adfd1790836856d3bb62f9ac111418aa362f55f43b0aa098
Benchcard: machine=x86_64 (architecture only; fleet node NO_DATA: endpoint has no ring identity) | date=2026-10-25 | runner=benchmark.py, local loopback Ollama | quant=NO_DATA (not applicable) | sha256=1069062c37be1ec7adfd1790836856d3bb62f9ac111418aa362f55f43b0aa098

## Law and source

**WHO WROTE NEVER PROBES THEIR OWN FAMILY.** The benchmark adopts the term
*self-preference* from Panickssery, Bowman, and Feng, “LLM Evaluators Recognize
and Favor Their Own Generations,” NeurIPS 2024, [arXiv:2404.13076](https://arxiv.org/abs/2404.13076).
The authors coined and studied that term; this artifact cites their work and
measures family attribution, not preference in scoring or human-rated quality.

## Method

`benchmark.py` asks three open model families to answer one neutral prompt.
Each answer is presented to a judge from the third family, with the source model
and source family hidden. The judge is asked whether the answer came from the
named target family. A judge family is always different from both candidate
author families. The three declared cohorts cover general instruction, coding,
and enterprise instruction. The exact local tags, prompt, seed schedule, and
scoring code are in `benchmark.py`.

Two passes use seed base `240425`; pass two offsets each pass-one seed by 100.
Each pass records three generations and six binary judgments. The same-family
and cross-family rates are correct judgments divided by measured judgments in
each class. No answer text or prompt text is stored in the results; generation
hashes, labels, seeds, predictions, causes, and timings are retained.

## First measurement · 2026-10-25

| Class | Correct | Measured | Detection rate |
|---|---:|---:|---:|
| Same-family | 2 | 6 | 33.3% |
| Cross-family | 4 | 6 | 66.7% |
| Combined | 6 | 12 | 50.0% |

The model endpoint was a reachable loopback Ollama service. Architecture stamp:
`x86_64`. The endpoint did not disclose a public fleet-node or ring identity;
three-ring coverage is **NO_DATA**, cause: the endpoint has no approved ring
mapping or per-ring roster. These figures describe only the three model tags in
this run and are not fleet-wide results. A separate invocation with the same
script hash and seeds reproduced all 6/6 generation hashes and 12/12 judge
predictions. Results and the replication count are in `results.json`.

Reproduce from the repository root:

```sh
python3 benchmarks/self-preference-20261025/benchmark.py --output benchmarks/self-preference-20261025/results.json
```

Validation: `python3 -m unittest discover -s tests -p "test_*.py"` ran twice
on 2026-10-25; each run measured 236 tests, 0 failures, and 1 skip. The skip is
`tests/test_eval_harness.py:47`: no RED suite is available in this tree.
Remote CI is **NO_DATA**, cause: CI is not configured in this repository.
