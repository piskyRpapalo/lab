# Ecosystem hygiene sweep · 2026-10-24

State: measured proposal, no worktree deletion performed. Remote branch ancestry was checked against each repository's fetched default branch before pruning.

## Merged remote branches

| Repository | Result | Evidence / action |
|---|---|---|
| lab | 3 merged `mistral/*` refs | PRs #90, #91, #92 were merged; refs deleted and fetch/prune confirmed no merged refs remain. |
| preceptoros-web | 0 merged refs found | `git branch -r --merged origin/main` filtered to `mistral/*`. |
| PreceptorOS | 0 merged refs found | Same ancestry check against `origin/main`. |
| study | 0 merged refs found | Same ancestry check against `origin/main`. |
| aduana | 1 merged ref | `mistral/aduana-route-runbook-20261024` matched merged PR #5 head; ref deleted and absence verified. |
| p0x | no live `mistral/*` refs observed | Read-only branch listing; no mutation to p0x. |
| buzon | 0 refs found | Read-only remote branch listing. |

Total pruned: 4 merged remote refs across 7 repositories. Counts are refs observed on the fetched remote branches at this sweep, not a count of historical PRs.

## Local worktree inventory

Scope: `git worktree list` in the four inspected root checkouts (lab, web, app, study), 152 entries counted. Status reads used optional-lock suppression; no tree was changed. Claude worktrees, Luna's active worktrees, and every p0x worktree were excluded from inspection and action.

| Classification | Count | Meaning |
|---|---:|---|
| merged | 102 | Clean worktree head is an ancestor of its root checkout's fetched main. |
| alive | 20 | Branch has commits not contained in that main, or is the active root checkout. |
| ambiguous | 26 | Dirty, protected, or ancestry/ownership could not be established safely. |
| stale | 4 | Git reports missing/prunable worktree metadata; files are preserved. |

These are classifications of entries, not permission to delete. Recommended sequence: first obtain an owner review of each merged/clean path; then prune only the individually named entries with `git worktree remove` and `git worktree prune` in a separate reviewed operation. Keep all 26 ambiguous and 4 stale entries untouched until their owners or contents are identified. Do not prune the 20 alive entries. The protected Claude/Luna/p0x exclusions are outside the 152-entry denominator, so their count is NO_DATA (cause: deliberately not inspected).

The inventory did not include independent root checkouts for aduana or buzon. Their local worktree state is NO_DATA (cause: no such root checkout was in the inspected set). Remote branch checks above did include them.

## Receipt

What: merged-branch cleanup plus a read-only worktree inventory. Cost: four remote refs deleted after ancestry/merge verification; 152 available entries classified; zero local worktrees removed. Yardstick: merged history and fetched ancestry for remote refs; `git worktree list` plus per-entry branch ancestry and status for four root repositories. Ambiguity is retained rather than guessed.
