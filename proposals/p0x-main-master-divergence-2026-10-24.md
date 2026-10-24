# Read-only record: p0x ref reconciliation

**Type:** read-only analysis for the Sovereign; no change made in p0x.
**Measurement date:** 2026-10-24, this session.
**LAB base:** `origin/main` `108e2412caeebf079ebbe2fc11d20fa6561aa58a`.

## Measured refs

| Ref | Measured value | Yardstick |
|---|---|---|
| GitHub p0x `master` | `9656ff3d4aad6909f22256c4544cf04b98ef0ad3` | GitHub REST ref read for `refs/heads/master` |
| GitHub p0x `main` | absent (`404 Not Found`) | GitHub REST ref read for `refs/heads/main` |
| GitHub branch listing | only `master` returned | GitHub REST branches listing, first 100 |
| Local checkout `master` | `2d44943e627dd8abcbc3f6eb3f4d517caaf4f29d` | `git rev-parse master` in existing checkout; read-only |
| Local `origin/master` | `f1b9a025ee1bc6f44e54a5d6db3e98e6e45c3b9f` | `git rev-parse origin/master`; local ref, not freshly fetched |
| Local `origin/main` | absent | `git show-ref refs/remotes/origin/main`; no output |

The requested GitHub `main` side cannot be mapped: it was not a branch in the
measured API response. Therefore the claim that NORTE 5 lives on GitHub `main`
is `NO_DATA`, cause: that ref returned 404. The local checkout does contain
`mistral/canon-norte5-20261024` at `535b3c09b829317fafa8236cbc45f69544cb9e99`,
but that does not establish a GitHub `main` branch.

## Known ancestry and divergence

GitHub compare from local-known base `f1b9a025...` to current remote `master`
`9656ff3d...` reports **2 commits ahead, 0 behind**, merge base `f1b9a025...`.
The changed paths are `mesa/HUELLA-CONTEXTOS.txt` (+2/−1),
`mesa/aduana-route-runbook-20261024.md` (+9/−0), and
`mesa/norte-y-vision.md` (+24/−0). Yardstick: GitHub compare API response for
those exact SHAs. This confirms the remote master contains the later canon and
runbook updates relative to f1b9.

The local graph comparison is different and stale: `git rev-list --left-right
--count master...origin/master` returns **406 / 345**, with merge base
`4d58c58c74b477e749a1912b3c89142c7b61e93b`. Left is local `master`-only
commits; right is commits only on the checkout's `origin/master` snapshot.
That remote-tracking ref is f1b9, not current GitHub master 9656. These are not
current remote divergence counts and must not be described as such. A fresh
object/ref comparison against 9656 is `NO_DATA`, cause: fetching or updating
the p0x checkout was outside this read-only card and that checkout has local
changes.

The checkout has 2 modified tracked paths (+13 insertions, 0 deletions by
`git diff --shortstat`) and 119 untracked paths by `git status --porcelain`
classification. Their contents were not inspected and are not part of any
commit-count claim. Do not reset, merge, clean, or stage that checkout.

## What a choice could lose

- Choosing the local `master` wholesale risks omitting the 345 commits present
  on its **stale** `origin/master` comparison side, including later canonical
  updates that GitHub master now has. Exact omitted commits versus current
  remote are not measured.
- Choosing GitHub `master` wholesale risks omitting 406 commits unique to the
  local `master` in that same stale comparison. Their intended disposition is
  not measured; the dirty working tree is a separate, uncommitted body of work.
- Choosing a supposed GitHub `main` cannot be evaluated until the Sovereign
  supplies a valid repository/ref or creates one by decree. No main-side
  commits or losses can be named from a missing ref.

## Options for decree

1. **Keep GitHub `master` canonical.** Preserve the local checkout and backup;
   classify local-only commits into small reviewable groups, then propose
   selected changes against `master`. This protects the merged canon while
   avoiding a blind 406-commit import.
2. **Declare an intended `main` ref.** The Sovereign identifies its repository
   URL and exact head (or explicitly authorizes creating it). Then measure
   ancestry and files against that actual object before selecting a migration.
3. **Reconcile in a disposable comparison clone.** Preserve both existing
   histories, fetch current GitHub refs into the disposable clone, and compare
   commits/files by topic before any integration proposal. Keep the dirty rack
   checkout untouched.

No merge-base strategy should be applied to the dirty checkout. A blind merge,
reset, or branch rename could erase information before a safe copy is made.

## Later Mesa closure

After this measurement, the Mesa's follow-up in buzon#19 comment `6386519071`
declared the remote question closed: GitHub keeps `master` as the sole trunk;
the local checkout is behind and has other sessions' uncommitted changes. That
receipt supersedes the request for a new `main`/`master` decree. The safe
remaining action is no action on the dirty checkout; any future recovery of its
local-only work needs a separate owner-led inventory. The counts above remain
historical yardsticks against the refs measured in this analysis, not current
divergence totals. The Mesa calls the checkout “behind”; the stale local graph
measured here is divergent (406/345), so that word is recorded as the Mesa's
status, not as an ancestry result from this session.

## Receipt

- API yardstick: two REST ref reads, branch listing, and compare `f1b9...` →
  `9656...`.
- Local yardstick: `show-ref`, `rev-parse`, `merge-base`, `rev-list`,
  `diff --shortstat`, and status classification; checkout left unchanged.
- Current remote `main` graph: `NO_DATA`, cause: GitHub returned 404.
- Current remote-vs-local exact divergence: `NO_DATA`, cause: local
  `origin/master` is stale and the protected checkout was not fetched.
- Later governance status: Mesa-reported closure at buzon#19 comment
  `6386519071`; no p0x sync was attempted here.
- LAB full gate: two passes. Each pass ran discovery (147 tests, 146 pass,
  1 skip), `test_llms.py` (2/2), and `verify_llms_tree.py` (5 indexed paths
  resolve; 11,695 B <= 12,109 B).
