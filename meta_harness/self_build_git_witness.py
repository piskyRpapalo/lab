"""Host-configured Git snapshot witness; never writes, authorizes or dispatches.

Only committed, clean snapshots are supported. This conservative first slice
accepts regular files under docs/ with .md suffix; a sovereign path policy is
still required. Renames are treated as delete+add so both paths are checked.
"""
import hashlib
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import time

from .improvement import _digest, _hex

HEX40 = re.compile(r'[0-9a-f]{40}\Z')
PATH = re.compile(r'docs/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.md\Z')
MAX_OUTPUT = 4 * 1024 * 1024
SENSITIVE_NAME = re.compile(r'(?:^|[-_.])(install|setup|deploy|launch|entrypoint|bootstrap|permission|permissions|policy|policies|governance|security|authorization|auth|signature|signatures)(?:[-_.]|$)')


class _Stop(Exception):
    pass


def _safe_path(path):
    parts = path.casefold().split('/')
    return (bool(PATH.fullmatch(path)) and all(x not in ('.', '..') and not x.startswith('.') for x in parts)
            and parts[-1] not in ('agents.md', 'claude.md') and not SENSITIVE_NAME.search(parts[-1])
            and not set(parts) & {'security', 'permissions', 'policies', 'governance', 'firmas', 'signatures', 'tests', 'test', 'deploy'})


class GitWitness:
    """Constructed only by a trusted host with exact repo and candidate commit.

    repo_ref is an opaque, host-owned identity, not a Git remote URL. It is
    bound at construction to a physical directory inode and the expected HEAD.
    No model-controlled path or command is accepted by the witness.
    """
    def __init__(self, root, repo_ref, candidate_sha, *, stable_source=None):
        self.root = Path(root).resolve(strict=True)
        self.identity = (self.root.stat().st_dev, self.root.stat().st_ino)
        if not self.root.is_dir() or not _hex(repo_ref) or not isinstance(candidate_sha, str) or not HEX40.fullmatch(candidate_sha):
            raise ValueError('invalid_host_configuration')
        self.repo_ref, self.candidate_sha = repo_ref, candidate_sha
        self.stable_source = stable_source
        self.git = shutil.which('git')
        if not self.git:
            raise ValueError('git_unavailable')

    def _git(self, *args):
        env = {'PATH': os.defpath, 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
               'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_TERMINAL_PROMPT': '0',
               'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_REPLACE_OBJECTS': '1'}
        cmd = [self.git, '-c', 'core.fsmonitor=false', '-c', 'core.quotePath=false',
               '-c', 'core.hooksPath=/dev/null', *args]
        process = subprocess.Popen(cmd, cwd=self.root, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        data = bytearray()
        selector = selectors.DefaultSelector()
        try:
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 10
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise _Stop('git_timeout')
                for key, _ in selector.select(timeout=0.1):
                    part = os.read(key.fd, 65536)
                    if not part:
                        selector.unregister(key.fileobj)
                        continue
                    data.extend(part)
                    if len(data) > MAX_OUTPUT:
                        raise _Stop('output_limit')
            if process.wait(timeout=max(0.01, deadline - time.monotonic())):
                raise _Stop('git_error')
            return bytes(data)
        finally:
            selector.close()
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()

    def _snapshot(self):
        stat = self.root.stat()
        if (stat.st_dev, stat.st_ino) != self.identity:
            raise _Stop('repository_changed')
        top = self._git('rev-parse', '--show-toplevel').rstrip(b'\n')
        if os.fsdecode(top) != str(self.root):
            raise _Stop('repository_mismatch')
        head = self._git('rev-parse', '--verify', 'HEAD^{commit}').strip().decode('ascii')
        if head != self.candidate_sha:
            raise _Stop('head_changed')
        flags = self._git('ls-files', '-v', '-z').split(b'\0')
        if any(entry and not entry.startswith(b'H ') for entry in flags):
            raise _Stop('index_flags_unsupported')
        if self._git('status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignored=matching', '--ignore-submodules=none'):
            raise _Stop('dirty_or_untracked')
        return head

    def inspect(self, binding):
        """Return a bounded cause; only VERIFIED can support the preflight callback."""
        try:
            p = binding['proposal']
            if binding['proposal_ref'] != _digest(p):
                raise _Stop('proposal_mismatch')
            if p['repo_ref'] != self.repo_ref or not HEX40.fullmatch(p['base_sha']):
                raise _Stop('identity_mismatch')
            if not callable(self.stable_source) or self.stable_source() is not True:
                raise _Stop('stable_source_unavailable')
            before = self._snapshot()
            base = p['base_sha']
            self._git('cat-file', '-e', base + '^{commit}')
            self._git('merge-base', '--is-ancestor', base, before)
            raw = self._git('diff', '--raw', '-z', '--no-renames', '--no-ext-diff', '--no-textconv', base, before, '--')
            fields = raw.split(b'\0')
            if fields[-1] != b'' or (len(fields) - 1) % 2:
                raise _Stop('invalid_diff')
            paths = []
            for i in range(0, len(fields) - 1, 2):
                header = fields[i].decode('ascii').split()
                if len(header) != 5 or not header[0].startswith(':') or header[-1] not in ('A', 'D', 'M', 'T'):
                    raise _Stop('unsupported_diff')
                modes = (header[0][1:], header[1])
                if any(m not in ('000000', '100644', '100755') for m in modes):
                    raise _Stop('symlink_or_submodule')
                path = fields[i + 1].decode('ascii')
                if not _safe_path(path):
                    raise _Stop('protected_or_unsupported_path')
                paths.append(path)
            if not paths or len(paths) > 32 or sorted(paths) != sorted(p['paths']):
                raise _Stop('path_mismatch')
            patch = self._git('diff', '--binary', '--full-index', '--no-renames', '--no-ext-diff', '--no-textconv', base, before, '--')
            if hashlib.sha256(patch).hexdigest() != p['patch_ref']:
                raise _Stop('patch_mismatch')
            if self._snapshot() != before:
                raise _Stop('head_changed')
            if self.stable_source() is not True:
                raise _Stop('stable_source_unavailable')
            return {'state': 'VERIFIED', 'cause': 'committed_snapshot_matches'}
        except _Stop as exc:
            return {'state': 'NO_DATA', 'cause': str(exc)}
        except Exception:
            return {'state': 'NO_DATA', 'cause': 'verification_unavailable'}

    def __call__(self, binding):
        return self.inspect(binding)['state'] == 'VERIFIED'
