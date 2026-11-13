"""Bounded SQLite source observation for isolated fixtures, never live authority.

No path or callback comes from a model request. Even a matching double-read and
synthetic witness cannot prove stability against non-cooperating writers. This
contract never returns VERIFIED and is not connected to the APP or dispatcher.
"""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile

from .delegation import HEX, LABEL
from .readonly_mirror import ReadOnlyJournal

MAX_BYTES = 2 * 1024 * 1024
SIDECARS = ('-wal', '-shm', '-journal')


def _result(cause, *, state='NO_DATA', digest=None):
    return {'schema': 'preceptoros.lab.source-capture/1', 'state': state,
            'cause': cause, 'snapshot_sha256': digest,
            'source_integrity': 'NO_DATA(real_host_stability)',
            'real_host_recovery': 'NO_DATA(real_host_recovery)', 'execution_authorized': False,
            'no_retry': True}


def _stat_key(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _sidecars(path):
    # lstat sees symlinks, including broken links; never follow them.
    for suffix in SIDECARS:
        try:
            os.lstat(str(path) + suffix)
            return True
        except FileNotFoundError:
            pass
    return False


def _validate_sqlite(data, journal_id):
    if not data.startswith(b'SQLite format 3\x00'):
        return 'snapshot_corrupt'
    # Only a private copy is opened. Do not use immutable=1 on the live source.
    with tempfile.TemporaryDirectory() as directory:
        copy = Path(directory) / 'snapshot.sqlite3'
        copy.write_bytes(data)
        with closing(sqlite3.connect(copy.as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA trusted_schema=OFF')
            steps = [0]
            def progress():
                steps[0] += 1
                return steps[0] > 5000
            db.set_progress_handler(progress, 100)
            rows = db.execute('PRAGMA quick_check(1)').fetchmany(2)
            if rows != [('ok',)]:
                return 'snapshot_corrupt'
            db.execute('SELECT run_id, task_ref, receipt FROM claims LIMIT 0')
            db.execute('SELECT run_id, task_ref, record FROM resolution_events LIMIT 0')
            identity = db.execute('SELECT id FROM journal_identity LIMIT 2').fetchall()
            if identity != [(journal_id,)]:
                return 'journal_identity_mismatch'
            return None


class FixtureSourceCapture:
    """Host-only allowlist entries: absolute path, pinned dev/inode and journal ID.

    The callbacks are trusted host test capabilities, not serialized booleans.
    Output SIMULATED is explicitly a fixture result, not a real source witness.
    """
    def __init__(self, sources, *, local_witness=None, fixture_witness=None):
        if type(sources) is not dict or len(sources) > 16:
            raise ValueError('allowlist_invalid')
        self._sources = {}
        for key, spec in sources.items():
            if (type(key) is not str or not LABEL.fullmatch(key) or type(spec) is not dict
                    or set(spec) != {'path', 'device', 'inode', 'journal_id'} or type(spec['path']) is not str
                    or not Path(spec['path']).is_absolute()
                    or type(spec['journal_id']) is not str or not HEX.fullmatch(spec['journal_id'])
                    or any(type(spec[x]) is not int or spec[x] < 0 for x in ('device', 'inode'))):
                raise ValueError('allowlist_invalid')
            self._sources[key] = dict(spec)
        self._local, self._fixture = local_witness, fixture_witness

    def capture(self, source_id):
        if type(source_id) is not str or source_id not in self._sources:
            return _result('source_not_allowlisted')
        entry = self._sources[source_id]
        path = Path(entry['path'])
        fd = None
        try:
            if not callable(self._local) or self._local(path) is not True:
                return _result('local_source_not_attested')
            if not callable(self._fixture) or self._fixture(path) is not True:
                return _result('fixture_witness_unavailable')
            if _sidecars(path):
                return _result('source_sidecar_present')
            ReadOnlyJournal(str(path))  # reuse owner, mode, hardlink and symlink checks
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            first = os.fstat(fd)
            if (first.st_dev, first.st_ino) != (entry['device'], entry['inode']):
                return _result('source_identity_mismatch')
            if not 0 < first.st_size <= MAX_BYTES:
                return _result('source_size_invalid')
            one = os.pread(fd, first.st_size + 1, 0)
            after_one = os.fstat(fd)
            if _stat_key(first) != _stat_key(after_one) or len(one) != first.st_size:
                return _result('source_changed')
            if self._fixture(path) is not True:
                return _result('fixture_witness_revoked')
            current = os.lstat(path)
            if (current.st_dev, current.st_ino) != (entry['device'], entry['inode']):
                return _result('source_identity_mismatch')
            if _sidecars(path):
                return _result('source_sidecar_present')
            two = os.pread(fd, first.st_size + 1, 0)
            after_two = os.fstat(fd)
            if _stat_key(first) != _stat_key(after_two) or one != two:
                return _result('source_changed')
            current = os.lstat(path)
            if (current.st_dev, current.st_ino) != (entry['device'], entry['inode']):
                return _result('source_identity_mismatch')
            if _sidecars(path):
                return _result('source_sidecar_present')
            if self._local(path) is not True:
                return _result('local_source_revoked')
            # Witness callbacks may themselves race or change the file.
            if _stat_key(first) != _stat_key(os.fstat(fd)):
                return _result('source_changed')
            current = os.lstat(path)
            if (current.st_dev, current.st_ino) != (entry['device'], entry['inode']):
                return _result('source_identity_mismatch')
            if _sidecars(path):
                return _result('source_sidecar_present')
            try:
                validation_cause = _validate_sqlite(one, entry['journal_id'])
            except sqlite3.DatabaseError:
                validation_cause = 'snapshot_corrupt'
            if validation_cause is not None:
                return _result(validation_cause)
            # Recheck after validation; still no proof against change-and-restore.
            current = os.lstat(path)
            if (current.st_dev, current.st_ino) != (entry['device'], entry['inode']):
                return _result('source_identity_mismatch')
            if _stat_key(first) != _stat_key(os.fstat(fd)):
                return _result('source_changed')
            if _sidecars(path):
                return _result('source_sidecar_present')
            if self._local(path) is not True or self._fixture(path) is not True:
                return _result('witness_revoked')
            current = os.lstat(path)
            if (current.st_dev, current.st_ino) != (entry['device'], entry['inode']):
                return _result('source_identity_mismatch')
            if _stat_key(first) != _stat_key(os.fstat(fd)):
                return _result('source_changed')
            if _sidecars(path):
                return _result('source_sidecar_present')
            return _result('synthetic_fixture_only', state='SIMULATED',
                           digest=hashlib.sha256(one).hexdigest())
        except (sqlite3.Error, OSError, ValueError, TypeError):
            return _result('source_unavailable_or_corrupt')
        except Exception:
            return _result('witness_or_source_unavailable')
        finally:
            if fd is not None:
                os.close(fd)
