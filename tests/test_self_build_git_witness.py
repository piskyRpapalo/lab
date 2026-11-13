"""Temporary Git repositories only; no real host grant or model is used."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from meta_harness.improvement import _digest
from meta_harness.self_build_git_witness import GitWitness
from meta_harness.self_build_preflight import check
from tests.test_self_build_preflight import proposal


class GitWitnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        (self.root / 'docs').mkdir()
        (self.root / 'docs/a.md').write_text('before\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip().decode()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.DEVNULL)

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'candidate')
        return self.git('rev-parse', 'HEAD').strip().decode()

    def binding(self, paths, head):
        p = proposal()
        p.update(repo_ref='a' * 64, base_sha=self.base, paths=paths,
                 patch_ref=hashlib.sha256(self.git('diff', '--binary', '--full-index', '--no-renames',
                         '--no-ext-diff', '--no-textconv', self.base, head, '--')).hexdigest())
        return {'proposal': p, 'proposal_ref': _digest(p)}

    def legitimate(self):
        (self.root / 'docs/a.md').write_text('after\n')
        head = self.commit()
        return GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True), self.binding(['docs/a.md'], head)

    def test_clean_documentation_and_preflight_reproducible(self):
        witness, b = self.legitimate()
        self.assertEqual(witness.inspect(b), witness.inspect(b))
        self.assertEqual(witness.inspect(b)['state'], 'VERIFIED')
        r = check(b['proposal'], allowed_paths=frozenset({'docs/a.md'}), source_witness=witness,
                  evidence_witness=lambda _: True, independent_judge=lambda _: True)
        self.assertEqual(r['state'], 'PROPOSE_ONLY')
        self.assertFalse(r['execution_authorized'])

    def test_missing_stability_guard_abstains(self):
        witness, b = self.legitimate()
        witness.stable_source = None
        self.assertEqual(witness.inspect(b)['cause'], 'stable_source_unavailable')

    def test_revoked_guard_fails_closed(self):
        witness, b = self.legitimate()
        values = iter((True, False))
        witness.stable_source = lambda: next(values)
        self.assertEqual(witness.inspect(b)['cause'], 'stable_source_unavailable')

    def test_committed_omitted_path_rejected(self):
        (self.root / 'docs/a.md').write_text('changed\n')
        (self.root / 'docs/b.md').write_text('added\n')
        head = self.commit()
        w = GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True)
        self.assertEqual(w.inspect(self.binding(['docs/a.md'], head))['cause'], 'path_mismatch')

    def test_assume_unchanged_index_flag_is_rejected(self):
        witness, b = self.legitimate()
        self.git('update-index', '--assume-unchanged', 'docs/a.md')
        self.assertEqual(witness.inspect(b)['cause'], 'index_flags_unsupported')

    def test_wrong_base_or_patch_ref(self):
        witness, b = self.legitimate()
        for field, value in [('base_sha', '0' * 40), ('patch_ref', '0' * 64), ('repo_ref', '0' * 64)]:
            p = dict(b['proposal'], **{field: value})
            self.assertEqual(witness.inspect({'proposal': p, 'proposal_ref': _digest(p)})['state'], 'NO_DATA')

    def test_rename_to_protected_file(self):
        (self.root / 'docs/a.md').rename(self.root / 'docs/AGENTS.md')
        head = self.commit()
        w = GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True)
        self.assertEqual(w.inspect(self.binding(['docs/a.md', 'docs/AGENTS.md'], head))['state'], 'NO_DATA')

    def test_symlink_to_protected_area(self):
        (self.root / 'docs/link.md').symlink_to('../.git/config')
        head = self.commit()
        w = GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True)
        self.assertEqual(w.inspect(self.binding(['docs/link.md'], head))['cause'], 'symlink_or_submodule')

    def test_gitmodules_is_refused(self):
        (self.root / '.gitmodules').write_text('[submodule "x"]\n path = x\n')
        head = self.commit()
        w = GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True)
        self.assertEqual(w.inspect(self.binding(['.gitmodules'], head))['state'], 'NO_DATA')

    def test_concurrent_head_change(self):
        witness, b = self.legitimate()
        original = witness._snapshot
        count = []
        def changed():
            count.append(1)
            if len(count) == 2:
                self.git('reset', '--hard', '-q', self.base)
            return original()
        with patch.object(witness, '_snapshot', side_effect=changed):
            self.assertEqual(witness.inspect(b)['cause'], 'head_changed')

    def test_index_and_worktree_diverge(self):
        witness, b = self.legitimate()
        (self.root / 'docs/a.md').write_text('staged\n')
        self.git('add', 'docs/a.md')
        (self.root / 'docs/a.md').write_text('unstaged\n')
        self.assertEqual(witness.inspect(b)['cause'], 'dirty_or_untracked')

    def test_untracked_omitted_file(self):
        witness, b = self.legitimate()
        (self.root / 'docs/extra.md').write_text('untracked\n')
        self.assertEqual(witness.inspect(b)['cause'], 'dirty_or_untracked')

    def test_protected_change_hidden_among_legitimate_changes(self):
        (self.root / 'docs/a.md').write_text('after\n')
        (self.root / 'docs/AGENTS.md').write_text('policy\n')
        head = self.commit()
        w = GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True)
        self.assertEqual(w.inspect(self.binding(['docs/a.md'], head))['state'], 'NO_DATA')

    def test_false_rejection_non_document_feature_is_explicit(self):
        (self.root / 'feature.py').write_text('pass\n')
        head = self.commit()
        w = GitWitness(self.root, 'a' * 64, head, stable_source=lambda: True)
        self.assertEqual(w.inspect(self.binding(['feature.py'], head))['cause'], 'protected_or_unsupported_path')
