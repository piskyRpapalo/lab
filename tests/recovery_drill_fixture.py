"""Disposable Git-only recovery drill fixture; never accepts user paths or commands."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from meta_harness.improvement import _digest
from meta_harness.sealed_patch_snapshot import capture
from meta_harness.self_build_git_witness import GitWitness
from meta_harness.self_build_lineage import Lineage, binding_ref
from tests.test_self_build_preflight import proposal

GOOD = b'def add(a, b):\n    return a + b\n'
BAD = b'def add(a, b):\n    return a - b\n'
TEST = "import runpy; assert runpy.run_path('docs/feature.md')['add'](2, 3) == 5"


class Drill:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        self.env = dict(os.environ, GIT_AUTHOR_DATE='2026-11-13T00:00:00+0000',
                        GIT_COMMITTER_DATE='2026-11-13T00:00:00+0000',
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
        self.git(self.repo, 'init', '-q')
        self.git(self.repo, 'config', 'user.name', 'Sandbox Fixture')
        self.git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.repo, 'config', 'commit.gpgsign', 'false')
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs/feature.md').write_bytes(GOOD)
        self.git(self.repo, 'add', '--', 'docs/feature.md')
        self.git(self.repo, 'commit', '-qm', 'baseline')
        self.base = self.git(self.repo, 'rev-parse', 'HEAD').strip().decode()
        self.base_tree = self.git(self.repo, 'rev-parse', 'HEAD^{tree}').strip().decode()
        self.baseline_ns, self.baseline_ok = self.check(self.repo)
        (self.repo / 'docs/feature.md').write_bytes(BAD)
        self.git(self.repo, 'commit', '-qam', 'candidate')
        self.head = self.git(self.repo, 'rev-parse', 'HEAD').strip().decode()
        self.candidate_ns, self.candidate_ok = self.check(self.repo)
        self.patch = self.git(self.repo, 'diff', '--binary', '--full-index', '--no-renames',
                              '--no-ext-diff', '--no-textconv', self.base, self.head, '--')
        self.patch_ref = hashlib.sha256(self.patch).hexdigest()
        self.p = proposal()
        self.p.update(repo_ref='a'*64, base_sha=self.base, paths=['docs/feature.md'], patch_ref=self.patch_ref)
        self.proposal_ref = _digest(self.p)
        self.operation_ref = _digest({'fixture': 'isolated-recovery-drill/1', 'base': self.base, 'head': self.head})
        self.witness = GitWitness(self.repo, 'a'*64, self.head, stable_source=lambda: True)  # synthetic
        self.lineage = Lineage(self.witness, self.operation_ref)
        self.snap, self.capture_status = self.new_snapshot()
        self.copy = self.root / 'restore-copy'
        self.git(self.root, 'clone', '-q', '--no-local', '--', str(self.repo), str(self.copy))

    def git(self, cwd, *args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args],
                                       cwd=cwd, env=self.env, stderr=subprocess.DEVNULL, timeout=10)

    def check(self, cwd):
        start = time.monotonic_ns()
        result = subprocess.run([sys.executable, '-I', '-c', TEST], cwd=cwd, env=self.env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        return time.monotonic_ns() - start, result.returncode == 0

    def new_snapshot(self, *, clock=time.monotonic, lifetime=30):
        return capture(self.patch, proposal_ref=binding_ref(self.proposal_ref, self.head, self.operation_ref),
                       patch_ref=self.patch_ref, lifetime_seconds=lifetime, clock=clock)

    def assess(self, snapshot=None, operation=None):
        return self.lineage.assess(self.p, self.proposal_ref, self.head,
                                   self.operation_ref if operation is None else operation,
                                   self.snap if snapshot is None else snapshot)

    def restore(self):
        start = time.monotonic_ns()
        self.git(self.copy, 'checkout', '-q', '--detach', self.base)
        return time.monotonic_ns() - start

    def same_tree(self):
        tree = self.git(self.copy, 'rev-parse', 'HEAD^{tree}').strip().decode()
        status = self.git(self.copy, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignored=matching')
        try:
            payload = (self.copy / 'docs/feature.md').read_bytes()
        except OSError:
            return False
        return tree == self.base_tree and not status and payload == GOOD

    def run(self):
        before = self.assess()
        if self.baseline_ok is not True or self.candidate_ok is not False or before['integrity'] != 'INTEGRITY_VERIFIED':
            raise AssertionError('fixture_prerequisites_failed')
        restore_ns = self.restore()
        tree_equal = self.same_tree()
        restored_ns, restored_ok = self.check(self.copy)
        after = self.assess()
        if not tree_equal or not restored_ok or after['integrity'] != 'INTEGRITY_VERIFIED':
            raise AssertionError('sandbox_restoration_failed')
        return {'state': 'DEMONSTRATED_IN_SANDBOX', 'scope': 'temporary_fixture_only',
                'base_sha': self.base, 'base_tree': self.base_tree, 'candidate_sha': self.head,
                'patch_sha256': self.patch_ref, 'proposal_ref': self.proposal_ref,
                'operation_ref': self.operation_ref, 'baseline_pass': self.baseline_ok,
                'candidate_pass': self.candidate_ok, 'restored_pass': restored_ok,
                'restored_tree_matches': tree_equal,
                'timings_ns': {'baseline': self.baseline_ns, 'candidate': self.candidate_ns,
                               'restore': restore_ns, 'restored': restored_ns},
                'lineage_integrity': after['integrity'], 'source': 'NO_DATA(real_host_stability)',
                'real_host_recovery': 'NO_DATA', 'execution': 'NOT_AUTHORIZED',
                'host_witness': 'SYNTHETIC'}

    def close(self):
        if self.snap is not None:
            self.snap.revoke()
        self.temp.cleanup()
