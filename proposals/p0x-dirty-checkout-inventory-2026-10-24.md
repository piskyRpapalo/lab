# Read-only inventory: local p0x checkout before synchronization

**State:** analysis only. The p0x checkout was not changed, staged, stashed,
cleaned, or switched.
**Measured:** 2026-10-24.
**LAB base:** `origin/main` `108e2412caeebf079ebbe2fc11d20fa6561aa58a`.

## Git and working-tree measurements

| Measurement | Result | Yardstick |
|---|---:|---|
| Local `master` | `2d44943e627dd8abcbc3f6eb3f4d517caaf4f29d` | `git rev-parse master` |
| Local `origin/master` | `9656ff3d4aad6909f22256c4544cf04b98ef0ad3` | `git rev-parse origin/master` |
| Common ancestor | `4d58c58c74b477e749a1912b3c89142c7b61e93b` | `git merge-base master origin/master` |
| Local-only / remote-only commits | `406 / 345` | `git rev-list --left-right --count master...origin/master` |
| Ancestry | neither tip is an ancestor of the other | both `git merge-base --is-ancestor` checks exit 1 |
| Existing commit backup | `respaldo/local-master-pre-rosetta` points to local `master` | `git show-ref refs/heads/respaldo/local-master-pre-rosetta` |
| Modified tracked paths | 2 paths; +13/−0 lines | `git diff --shortstat` |
| Untracked status | 119 collapsed paths in normal status; 916 path entries expanded with `-uall` | Separate `git status --porcelain=v1 -z --untracked-files=normal` and `...--untracked-files=all`; nested repositories can remain one path entry |

This is **diverged**, not a simple fast-forward-behind branch. Moving local
`master` to remote `origin/master` would strand 406 local-only commits unless
they remain reachable through the existing backup ref or another verified
bundle. Keeping only local `master` would omit 345 remote-only commits. The
current branch backup protects the 2d44943 commit graph only; it does not
contain the two tracked edits or untracked paths.

The modified tracked files are `mente/aprendizaje/OPTIMIZACIONES.md` and
`mente/feedback/PENDIENTES.md`. Their paths suggest optimization and feedback
work. I did not read their contents, so author/session provenance and whether
the edits are ready are `NO_DATA`, cause: the inventory was constrained to
metadata-only inspection. Preserve both.

## Untracked groups and likely provenance

Counts below are expanded status-path counts, not claims of unique authorship.
Attribution is a hypothesis from directory/file names and prior context; where
not corroborated by an exact receipt, provenance is marked `NO_DATA`.

| Paths / feature | Count | Assessment and handling |
|---|---:|---|
| `no-publicar/**` | 427 | Includes a dated migration bundle (326 entries), an earlier MCP snapshot (25), and 76 historical capture/evidence/scratch paths. Keep private and preserve. The explicit directory policy forbids publication. Individual contents and owners are `NO_DATA`, cause: not inspected. |
| `hexelion/laboratorio/**` | 158 | Prototype/lab family: `mockup/` 100, `espacios/` 10, `datos_forja/` 8, and 40 source/test/document paths at the lab root. Preserve as potentially live work. Exact session ownership is `NO_DATA`, cause: no per-file receipt found in the context log. |
| `propuestas/**` | 146 | Art and design archive: `obra-abku/` 85, dated visual captures 28, research-source snapshots 8, Claude-tooling notes 6, and 19 other briefs/reports/archive items. Preserve. Content equivalence, licensing of source snapshots, and supersession are `NO_DATA`, cause: contents were not opened. |
| `bronze/agentes/**` | 101 | Hash-named JSON telemetry paths: 18 dated 2026-10-04 and 83 dated 2026-10-05. Preserve in restricted storage; do not publish the opaque names or inspect payloads. Attribution/retention policy is `NO_DATA`, cause: payloads were not read. |
| `estudios/**` | 35 | Includes 34 `bench-fluency/` code/measurement paths and one dated node-map study. Preserve as research/measurement work. Whether any line-oriented measurements contain raw prompts or answers is `NO_DATA`, cause: contents were not inspected; scrub before any publication. |
| `mente/**` | 10 | Six doctrine, two line, one signature, and one telemetry path. Preserve privately. Secret/personal-data status is `NO_DATA`, cause: filenames and contents were not audited for disclosure. |
| `scripts/**` | 9 | Bench and analysis scripts. Preserve; execution safety and ownership are `NO_DATA`, cause: source was not inspected. |
| `bin/**` | 4 | Session-support and verification tools. Preserve; execution safety and ownership are `NO_DATA`, cause: source was not inspected. |
| `preceptoros-downloads/rollback/**` | 3 | Rollback candidates; preserve until a canonical copy is hash-compared. Equivalence is `NO_DATA`, cause: no hashes were measured. |
| Other root/support paths | 23 | 16 dated notes/reports/lock artifacts plus 7 archive, runtime, or nested-checkout paths. Preserve; repository identity, freshness, and equivalence are `NO_DATA`, cause: contents were not inspected. |

The untracked counts sum to 916 (`git status --porcelain=v1 -z
--untracked-files=all`, grouped by path prefix). Normal status collapses some
directories and prints 119 untracked entries instead; this explains the Mesa's
approximate count. The second count is the detailed path inventory yardstick.
Some nested repositories appear as one directory entry, so 916 is not asserted
to be 916 regular files.

### Preserve vs. discard

- **Preserve now:** both modified tracked paths; all untracked groups above;
  the existing `respaldo/local-master-pre-rosetta` branch. Several groups are
  explicitly archival or private, but age or directory name does not prove
  disposability.
- **Potential future cleanup only:** dated snapshots, old visual captures,
  and duplicated-looking drafts. No item is safe to discard today: no content
  comparison, canonical hash, retention rule, or owner decision was measured.
- **Exact provenance gaps:** specific owners/sessions for the migration,
  telemetry, prototype, benchmark, and art files are `NO_DATA`, cause: path
  names do not identify an author or session and contents were intentionally
  not read. Sensitive/opaque path names are summarized by family here rather
  than copied into a public report.

## Safe synchronization recommendation

Do not run `git pull --ff-only` on this `master` as-is. The measured graph has
unique commits on both sides, so fast-forward is mathematically impossible.
That expected refusal has not been executed; no pull was attempted.

1. In an owner-controlled, access-restricted backup location, preserve the
   `--all` refs as a Git bundle, staged and unstaged binary diffs, and the
   untracked paths as a tar archive. Record SHA-256 for every backup file and
   verify the archive listing and hashes. The existing branch backup alone is
   insufficient for the dirty tree. Keep `no-publicar/`, telemetry, signatures,
   nested checkouts, and measurements out of public PRs.
   A paste-ready backup skeleton (the owner supplies both local directory
   variables; no command below was run):

   ```sh
   : "${P0X_CHECKOUT:?set the existing checkout}"
   : "${BACKUP_DIR:?set a restricted destination outside the checkout}"
   umask 077
   mkdir -m 700 -- "$BACKUP_DIR"
   git -C "$P0X_CHECKOUT" bundle create "$BACKUP_DIR/refs.bundle" --all
   git -C "$P0X_CHECKOUT" diff --cached --binary > "$BACKUP_DIR/index.patch"
   git -C "$P0X_CHECKOUT" diff --binary > "$BACKUP_DIR/worktree.patch"
   git -C "$P0X_CHECKOUT" ls-files --others --exclude-standard -z > "$BACKUP_DIR/untracked.nul"
   tar -C "$P0X_CHECKOUT" --null --files-from="$BACKUP_DIR/untracked.nul" \
     --create --file="$BACKUP_DIR/untracked.tar"
   sha256sum "$BACKUP_DIR/refs.bundle" "$BACKUP_DIR/index.patch" \
     "$BACKUP_DIR/worktree.patch" "$BACKUP_DIR/untracked.tar"
   ```
2. Only after that backup is verified, the owner may run `git stash push -u`
   with a dated message. Confirm the stash exists and `git status --porcelain
   --untracked-files=all` is empty. If any nested checkout or path remains, stop;
   do not pull or clean it.
3. Fetch `origin/master` and remeasure both tips, the merge base, and the two
   unique-commit counts. If those values moved, discard this proposed sequence
   and reclassify from fresh output.
4. Because the graph is diverged, keep local `master` and its backup ref. Make
   a **separate worktree** at `origin/master` for the synchronized view:
   `git -C "$P0X_CHECKOUT" worktree add "$SYNC_WORKTREE" origin/master`.
   Do not reset or merge the dirty checkout. Restore approved files selectively
   from the verified archive/diffs. If an owner elects to use the stash, use
   `git stash apply` (not `pop`) and stop on conflicts. Retain the stash and
   backup until every restored path is verified. This avoids hiding the 406
   local-only commits or importing 345 remote-only commits blindly.

No file is classified disposable and no synchronization operation was run.

## Receipt

- Cost: metadata-only status, refs, ancestry, and path-prefix census; no
  untracked payloads or modified-file contents read.
- Yardstick: commands named in the tables; date 2026-10-24.
- Main-to-master “behind” wording: corrected to two-sided divergence by
  measured ancestry/counts.
- Commit/push/PR/merge/deploy/signing: none.

### LAB validation receipt

- Yardstick: `python3 -m unittest discover -s tests -p 'test_*.py'`,
  `python3 test_llms.py`, then `python3 bin/verify_llms_tree.py`, twice on
  this branch. Both passes: 147 tests, 1 skipped, no failures/errors; llms
  2/2; tree 5 indexed paths, depth 11,695 B <= 12,109 B. All commands exit 0.
- Document size after appending: 9,648 B; below the 16,384 B per-piece
  ceiling. `git diff --cached --check` is rerun after staging.
- No live request or p0x mutation.
