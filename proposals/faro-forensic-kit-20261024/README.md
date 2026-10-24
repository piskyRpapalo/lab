# FARO forensic kit · run 40110583184

## Scope and current evidence

This is a local text parser, not an endpoint checker. It reads only pasted
outputs from gestures A, B, and C. It makes no HTTP, DNS, GitHub, or Cloudflare
request. Gesture B (the detached-main full FARO run) was not executed here.
No new output for A/B/C was supplied with this card, so route verdicts remain
`NO_DATA`, cause: the three measured transcripts have not yet been pasted into
the parser.

The prior Mesa receipt for run `40110583184` measured 244 compared, 233 equal,
11 different, 0 absent, and 0 network errors. The new kit does not relabel that
observation. It requires route-level observations from C and bytes from A or
B. In particular, three direct fetches cannot establish the other eight
routes; those rows remain `NO_DATA` until measured. A CI head differing from
B's local source commit also blocks an edge classification.

## Pasted input envelope

Save a UTF-8 text file with these section headers. Preserve the raw A/B/C
transcripts in each section; add the normalized evidence rows below from the
same measured output. A row must not be inferred from an aggregate count.

```text
=== GESTURE A ===
A_ROUTE route=/es/ main_sha256=<64 lowercase hex> local_sha256=<64 lowercase hex> status=200 final_path=/es/ redirects=-

=== GESTURE B ===
B_SUMMARY source_sha=<40 or 64 lowercase hex commit> compared=244 equal=244 changed=0 missing=0 network_errors=0
B_ROUTE route=/creation main_sha256=<64 lowercase hex> local_sha256=<64 lowercase hex> status=200 final_path=/creation redirects=-

=== GESTURE C ===
RUN id=40110583184 head_sha=<40 or 64 lowercase hex> status=completed conclusion=failure
CI_DISTINCT route=/es/index.html sha256=<optional CI body hash>
```

`A_ROUTE` is a direct local fetch; `B_ROUTE` is one path row emitted or
reconstructed from the full local FARO run. Both require the expected main
body hash and the observed body hash. `redirects` is `-` or a path/status
sequence such as `/index.html>307>/es/`; hosts, query strings, and fragments
are rejected. The `B_SUMMARY.source_sha` must equal the CI run head before
routes can be classified. Gesture C needs 11 distinct `CI_DISTINCT` rows for
this incident. The parser merges A and B by route; conflicting rows become
`NO_DATA`.

Run offline from pasted text:

```sh
python3 bin/faro_forensic.py --input faro-gestures.txt --output receipt.json
# or paste the same envelope on stdin
python3 bin/faro_forensic.py < faro-gestures.txt
```

It accepts strict UTF-8 up to 4 MiB. The JSON includes `route`, `classification`,
`sha_in` (main body), `sha_out` (local body), optional `ci_sha256`, `verdict`,
and `recommended_fix`. Exit 0 means all 11 rows classified, 2 means `NO_DATA`.
The top-level input hash pins the exact pasted transcript. `network_used` is
always false.

## Classification contract

- `REAL_DRIFT`: a measured local route body differs from its main body hash.
- `REDIRECT_ARTIFACT`: the raw route's measured redirect chain ends at a
different pretty path. The recommendation is to compare that canonical URL.
- `EDGE_STALE`: A/B show byte equality to main, B's full FARO summary is clean,
and C reports that same route as `DISTINTO` at the identical source commit.
This is **consistent with** a stale edge response; it does not prove which PoP
or that Cloudflare is the only cause. Keep the raw CI evidence for the Mesa.
- `NO_DATA`: a route hash, CI route, source match, complete section, or valid
UTF-8 input is absent/contradictory. The parser never fills gaps from aggregate
counts.

Redirect classification precedes body-hash drift because FARO may have
compared a redirect response against the wrong raw-path artifact. A full local
summary with any changed/missing/network-error count cannot support
`EDGE_STALE`; route-local hashes may still establish `REAL_DRIFT`.

## Contract-only draft: possible `atlas/faro.py` change

This is an inline proposal, not an applied patch. Only consider it if the
forensic receipt classifies the relevant route as `REDIRECT_ARTIFACT`; inspect
the current FARO source and tests at that time before preparing a separate PR.

```diff
--- a/atlas/faro.py
+++ b/atlas/faro.py
@@
+def public_path_to_url(path):
+    """Compare index documents through their canonical pretty URL."""
+    if path.name == "index.html":
+        parent = path.parent.as_posix()
+        return "/" if parent == "." else "/" + parent.strip("/") + "/"
+    return "/" + path.as_posix()
@@
-    url = base_url + "/" + relative_public_path
+    url = base_url.rstrip("/") + public_path_to_url(PurePosixPath(relative_public_path))
```

The hunk anchors are illustrative, not source-verified. Root and localized
`index.html` must each have fixtures for redirect-following, exact bytes,
missing response, and non-redirect drift before any contract change is proposed.

## Red-before-green sabotage corpus

`tests/test_faro_forensic.py` first failed to import the absent parser (RED),
then passed 10/10 with the parser (GREEN). The corpus contains 11 synthetic route
rows including one true local byte drift and one measured 307 redirect, plus
sabotages for a missing route, truncated B summary, invalid mixed-byte UTF-8,
duplicate observations, only three direct fetches, mismatched source head, and
an unrelated CI run id.
No corpus hashes are production values.

## Receipt

- Piece: parser, tests, and this proposal on
  `mistral/faro-forensic-kit-20261024`, based on LAB `c74fd867e7e933060d3eadffe9fd65902b25dc1a`.
- Cost/yardstick: standard-library-only parser; focused sabotage suite 10/10.
  Two full LAB passes: 178 unittest tests each (1 skip, 0 failures),
  `test_llms.py` 2/2, tree verifier 5 indexed paths at 11,695 B <= 12,109 B.
- Current A/B/C forensic verdict: `NO_DATA`, cause: fresh gesture outputs have
  not been supplied. No deploy or live request was made.
- No change to `atlas/faro.py` is included.
