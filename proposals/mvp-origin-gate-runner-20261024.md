# Run the MVP regression gates against fetched origin branches

`bin/run_mvp_origin_gates.py` reads Git objects only. It neither fetches nor checks
out branches and never requests a site. Inputs must be exact
`refs/remotes/origin/<branch>` refs already present in the local object store.

Claude's WEB branch supplies `docs/rebuild/mvp-origin-evidence.json` with
`source_tree_oid` equal to its `docs/rebuild/examples` tree. The APP branch supplies
`interface/mvp-origin-evidence.json` with the matching `interface/face` tree. WEB
evidence contains narration, zoom, contrast, and post-export frame sections; APP
evidence contains task parity using the same shared-fixture hash. Tree pins make
evidence stale as soon as its measured source directory changes.

Run:

```sh
python3 bin/run_mvp_origin_gates.py \
  --web-repo /checkout/web --web-ref refs/remotes/origin/claude-web \
  --app-repo /checkout/app --app-ref refs/remotes/origin/claude-app
```

The JSON receipt gives one `GREEN`, `RED`, or `NO_DATA` verdict for each gate:
narration viewports, zoom bounds/object-size invariance, contrast fixture pairs,
UTF-8 byte budget after export, and task-level WEB/APP parity. Missing branch refs or
evidence sections are `NO_DATA` with cause. Malformed, stale, or failed evidence is
`RED`. Contrast values are regression fixtures, not WCAG or EN 301 549 certification.

Validator tests use temporary repositories and synthetic evidence. They cover a
five-gate GREEN, absent evidence, stale source tree, and rejection of non-origin refs.
They do not certify Claude's actual branches; those remain `NO_DATA` until the
Sovereign fetches them and the runner consumes their pinned evidence.
