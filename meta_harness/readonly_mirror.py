"""Allowlisted, local read-only mirror of existing uncertainty views.

This is an in-process host adapter, not an HTTP server or worker. It never
accepts a path, task or authority callback from a request/model.
"""
import copy
from pathlib import Path
import sqlite3

from .delegation import LABEL, sha, validate_task
from .execution_journal import ExecutionJournal
from .host_witness import HostWitness
from .uncertainty_views import project, views


class ReadOnlyJournal(ExecutionJournal):
    def _connect(self):
        self._check()
        db = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=2, isolation_level=None)
        db.execute('PRAGMA query_only=ON')
        return db


class ReadOnlyMirror:
    """Host config is a closed map {source_id: {journal: absolute path, task: exact task}}."""
    def __init__(self, allowlist, *, local_source_witness=None):
        if type(allowlist) is not dict or len(allowlist) > 16:
            raise ValueError('allowlist_invalid')
        self._sources = {}
        self._local_source_witness = local_source_witness
        for source, spec in allowlist.items():
            if (type(source) is not str or not LABEL.fullmatch(source) or type(spec) is not dict
                    or set(spec) != {'journal','task'} or type(spec['journal']) is not str
                    or not Path(spec['journal']).is_absolute()):
                raise ValueError('allowlist_invalid')
            task = copy.deepcopy(spec['task']); validate_task(task)
            self._sources[source] = {'journal':spec['journal'], 'task':task}

    @staticmethod
    def _missing(cause, observed_at):
        record = {'schema':'preceptoros.lab.uncertainty-ack/1', 'kind':'projection',
            'state':'NO_DATA', 'cause':cause, 'acknowledgement':'NO_DATA', 'observed_at':observed_at,
            'journal_id':None, 'task_ref':None, 'resolution_ref':None,
            'reservation':{'state':'NO_DATA','cause':'source_unavailable'},
            'ttl_seconds':0, 'no_retry':True, 'promotion':'NOT_AUTHORIZED',
            'summary':'Uncertain execution state is unavailable; check the host source.'}
        record['projection_ref'] = sha(record)
        return views(record)

    def read(self, source_id, *, observed_at):
        # This is the trusted host's current clock, not a model-provided timestamp.
        from .reuse import instrument
        try:
            instrument('evidence').valid_time(observed_at)
        except Exception:
            return self._missing('host_clock_invalid', None)
        if type(source_id) is not str or source_id not in self._sources:
            return self._missing('source_not_allowlisted', observed_at)
        spec = self._sources[source_id]
        path = Path(spec['journal'])
        try:
            if (not callable(self._local_source_witness)
                    or self._local_source_witness(path) is not True):
                return self._missing('local_source_not_attested', observed_at)
        except Exception:
            return self._missing('local_source_not_attested', observed_at)
        # SQLite WAL/recovery sidecars require a separately reviewed snapshot path.
        # Never use immutable=1, which can silently omit committed WAL content.
        if any(Path(str(path)+suffix).exists() for suffix in ('-wal','-shm','-journal')):
            return self._missing('source_busy_or_wal_not_supported', observed_at)
        try:
            journal = ReadOnlyJournal(str(path))
            witness = HostWitness(journal.identity(), sha(spec['task']))
            journal.resolution_witness = witness.resolution_witness
            record = project(journal, spec['task'], observed_at=observed_at)
            if self._local_source_witness(path) is not True:
                return self._missing('local_source_not_attested', observed_at)
            if any(Path(str(path)+suffix).exists() for suffix in ('-wal','-shm','-journal')):
                return self._missing('source_busy_or_wal_not_supported', observed_at)
            return views(record)
        except Exception:
            return self._missing('source_unavailable_or_unsafe', observed_at)

    def verify(self, packet, source_id, *, observed_at):
        """Re-read the allowlisted source and current host witness; never trust a self-hash."""
        try:
            return packet == self.read(source_id, observed_at=observed_at)
        except Exception:
            return False
