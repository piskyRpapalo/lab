# BENCH-REPRO-01 · Public local throughput

Owner: Codex CLI. Source: [LAB #172](https://github.com/piskyRpapalo/lab/issues/172),
[SWARM-4 Mesa](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/3#issuecomment-6823235772).
Base: `031da33c117e0258929b840de00c505c335c1120`. BUILD and draft PR authorized;
human exact-head FIRMO gates integration. No merge, deployment or service changes.

## Read depth and reuse

Targeted source reading, not a rack census: complete LAB AGENTS, STATE, README,
benchmarks/README and benchmark-status-20261111; #172 and #164; latest Mesa claims;
current private signing book and decisions. Six candidate instruments inspected:
station `smoke.py` is the reusable two-pass runner; `sweep.py` currently performs
one pass despite its docstring; `large.py` is a fixed 70B experiment; self-preference
is a judge experiment; Gemma receipt tests and synthetic matrix aggregation consume
other evidence. This piece extends smoke, preserving the legacy stdin settings and
historical receipts. It adds no benchmark framework or APP panel.

The private historical #164 input is unavailable. This new public numeric fixture
does **not** reconstruct that experiment. Model output equality is reported, never
assumed from temperature/seed. Generated-token speed is not task accuracy.

## Reproduce independently

Python 3.10+ standard library and an already installed Ollama model suffice.
No PreceptorOS, credentials, private rack files or package installation is needed.
Choose the exact installed public model name; the runner never pulls weights.

```sh
python3 -B benchmarks/station-96-first-pass-20261029/smoke.py \
  --model YOUR_INSTALLED_MODEL --public-fixture > receipt.json
sha256sum benchmarks/fixtures/throughput-public-v1.json receipt.json
python3 -B -m unittest tests.test_public_throughput
```

An alternate numeric loopback listener may be selected with `--base-url
http://127.0.0.1:PORT`. HTTP only, numeric loopback only, explicit port, no userinfo,
query or fragment; redirects and environment proxies are disabled. No hostname,
remote fallback, retries, model pull or telemetry. Only tags, version and generation
endpoints are callable. Responses have a 1 MiB ceiling and 180 s per-request timeout;
the operator can cancel the foreground process. The server might finish an in-flight
generation after cancellation: cancellation does not prove service-side termination.
Never restart another worker's service or unload its models manually.

Cloud model aliases and service metadata `remote_model`/`remote_host` are refused
before generation; remote-marked responses are rejected too. These fields follow
[Ollama's API types](https://github.com/ollama/ollama/blob/main/api/types.go).
Loopback is a client transport boundary, not server egress attestation. Use a trusted
local server with cloud disabled/network egress blocked for strict offline operation;
the runner never reconfigures that service. `server_egress` remains NO_DATA because
a server could hide forwarding. No network-isolation certification is claimed.

Fixed public profile: `stream=false`, `think=false`, `temperature=0`, `seed=42`,
`num_predict=64`, `num_ctx=2048`, `keep_alive=0`. Two sequential attempts, no hidden
retry. Unloading is requested, not verified cold-cache equivalence. Older servers
may not support all parameters; server adherence is not independently attested.
`--disable-thinking` remains a legacy-only option; legacy seed stays 20261028.

The fixture is explicitly public synthetic numeric data; prompt rendering is fixed
in source. The CLI does not read stdin in this profile. No private input option is
provided. Only hashes, counts and fixed causes are retained; raw answers/errors
and local endpoints/paths never enter the public receipt.

## Receipt and consumption contract

JSON `bench-repro-01-v1` contains source commit (or caused NO_DATA for dirty source),
runner SHA-256, raw fixture and rendered input SHA-256, model name and service-reported
digest before/after, service version, date, fixed settings and two numbered samples.
Each successful sample carries generated count, eval duration, generation tok/s,
wall time, separate load time, response length/hash. Failed samples remain in order
and in attempted/succeeded/failed counts; absent/invalid preflight prevents generation.
Zero, missing, negative, boolean, non-integer and excessive generation timings are
rejected. Changed/missing postflight digest prevents a MEASURED overall verdict.
Even then per-attempt observations remain available as unconfirmed observations.

`hardware_class` defaults to NO_DATA; `--hardware-class cpu|integrated-gpu|discrete-gpu|mixed`
is explicitly DECLARED, never a placement measurement. Backend, CPU/GPU split and power
are NO_DATA with causes. Service-reported digest is not rehashed weights or attestation.
Quality, energy, regulatory compliance, RAM and device identity are not measured.

`comparison_key` seals experimental controls (schema, fixture/input, settings,
model digest and service version). Different fixtures or controls cannot form an
exact comparison. Equal keys do not establish comparable hardware, provenance,
successful samples or semantic correctness. Check overall state, sample failures
and limitations before reading rates. File SHA-256 identifies bytes, not authorship.
Exit 0 means both attempts passed validation and digest stayed stable; 1 means NO_DATA.

APP/WEB consumers can read this JSON as an untrusted receipt. They must preserve
state, source and causes and never turn declared hardware or service counters into
independently VERIFIED/LIVE data. No APP or WEB files are changed.

## External contribution guide

Use the existing [broadcast fields](../../benchmarks/README.md) and your experiment's
own methodology. Include public experiment ID, date, machine class, source commit,
runner/input hashes, parameters, run counts, failures and limitations; retain the
original contributor's authorship and sources. If fixture data cannot be public,
publish only approved hashes and say exact independent reproduction is NO_DATA.
Scrub names, credentials, raw private inputs/answers and identifying file paths.

The collaborator's offline CPU Qwen2.5-VL photographed-receipt experiment must keep
its own corpus consent, ground truth, error categories and accuracy denominator.
Do not rank its precision against these generated-token throughput samples.
CPU placement, offline operation and accuracy each need their own evidence.
No such collaborator result is measured by this change. A docs-only contribution
may cite this common provenance checklist without adopting this throughput schema.

## Verification, risks and rollback

Directed tests exercise two samples, deterministic fake clocks, changed fixtures,
absent models/service, malformed answers, bad timing, changed digest, privacy canaries,
external endpoints, forbidden pull, redirect/proxy bypass, ambiguous/oversized JSON.
These tests make no model calls; transport tests use a disposable local HTTP server.
Run the whole canonical CI command set twice. Review and measured results are appended
after execution; no inherited count is asserted as current.

2026-11-12 local verification: 549 Python discovery tests (one existing skip),
norte 5, llms 2, Node chunk-responder tests, tree gate 11996/12109 B, all twice GREEN.
Twenty new directed tests are included in discovery. Six deliberate code mutations
(invalid timing accepted, digest change ignored, fixture hash erased, raw answer
leaked, cloud preflight bypassed, HTTP protocol errors uncaught) were detected twice
in disposable copies. Clean source was never mutated. H5 initially found two real
blockers: cloud-backed loopback models and missing HTTPException handling. Both are
fixed with regression tests, including malformed chunked HTTP through the actual CLI;
independent recheck is pending before draft publication. No inference occurred in tests.

Fixture SHA-256: `5bf9fa9a054054d541696c016b04f340bed289700cbd2b8ebeb9826e88020f8c`.

Risks: benchmark calls consume local compute and may contend with another worker;
fixed settings do not attest server execution; public labels are operator-selected;
timings vary with hardware/cache/load. Do not infer ranking from two short samples.
Legacy transport now rejects ambiguous JSON, redirects and proxies too; legacy seed,
input and receipt remain unchanged. Rollback: revert this PR's commits, no services,
settings, models or historical data require restoration.

Next mission selected: source-identity contract for Notebook agent receipts, using
the existing producer/consumer contracts and the Web beacon diagnosis. No second
state bus; separate CLAIM and Claude ownership check required before any code.
