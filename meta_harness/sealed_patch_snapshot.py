"""Linux sealed in-memory patch bytes; not a Git provenance or authority witness.

The host supplies bytes and the expected proposal/patch digests. Kernel file
seals protect the captured bytes, not the source repository or the process.
Do not pass a model-controlled clock. No result authorizes execution.
"""
import fcntl
import hashlib
import os
import re
import threading
import time

HEX = re.compile(r'[0-9a-f]{64}\Z')
MAX_BYTES = 4 * 1024 * 1024
_REQUIRED_SEALS = tuple(getattr(fcntl, name, 0) for name in
                        ('F_SEAL_WRITE', 'F_SEAL_GROW', 'F_SEAL_SHRINK', 'F_SEAL_SEAL'))
SEALS = sum(_REQUIRED_SEALS) if all(_REQUIRED_SEALS) else 0


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _ref(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _result(cause, integrity='NO_DATA'):
    return {'state': 'NO_DATA', 'cause': cause, 'snapshot_integrity': integrity,
            'source_stability': 'NO_DATA', 'execution_authorized': False}


class SealedPatch:
    """Private host-process handle. Not a sandbox against hostile Python code.

    Expiration and revocation govern future calls, not bytes already returned or
    other duplicated file descriptors. Caller must revalidate action authority at
    use and must separately establish source provenance and host stability.
    """
    def __init__(self, fd, proposal_ref, patch_ref, size, deadline, clock):
        self._fd, self._proposal_ref, self._patch_ref = fd, proposal_ref, patch_ref
        self._size, self._deadline, self._clock = size, deadline, clock
        stat = os.fstat(fd)
        self._identity = (stat.st_dev, stat.st_ino)
        self._last = None
        self._lock = threading.RLock()

    def revoke(self):
        with self._lock:
            self._revoke()

    def _revoke(self):
        if self._fd is not None:
            fd, self._fd = self._fd, None
            try:
                os.close(fd)
            except OSError:
                pass

    def read(self, proposal_ref):
        """Return (bytes or None, status), never a positive provenance verdict."""
        with self._lock:
            return self._read(proposal_ref)

    def _read(self, proposal_ref):
        fd = None
        try:
            if self._fd is None:
                return None, _result('snapshot_revoked')
            now = self._clock()
            if type(now) not in (int, float) or not 0 <= now < self._deadline or (self._last is not None and now < self._last):
                self.revoke()
                return None, _result('snapshot_expired_or_clock_invalid')
            self._last = now
            if proposal_ref != self._proposal_ref:
                return None, _result('proposal_mismatch')
            fd = os.dup(self._fd)
            stat = os.fstat(fd)
            if ((stat.st_dev, stat.st_ino) != self._identity or stat.st_size != self._size
                    or fcntl.fcntl(fd, fcntl.F_GET_SEALS) & SEALS != SEALS):
                self.revoke()
                return None, _result('snapshot_integrity_failed')
            payload = os.pread(fd, self._size + 1, 0)
            if len(payload) != self._size or _digest(payload) != self._patch_ref:
                self.revoke()
                return None, _result('snapshot_integrity_failed')
            after = self._clock()
            if type(after) not in (int, float) or not now <= after < self._deadline:
                self.revoke()
                return None, _result('snapshot_expired_or_clock_invalid')
            self._last = after
            return payload, _result('real_host_stability', 'VERIFIED')
        except Exception:
            self.revoke()
            return None, _result('snapshot_unavailable')
        finally:
            if fd is not None:
                os.close(fd)


def capture(payload, *, proposal_ref, patch_ref, lifetime_seconds, clock=time.monotonic):
    """Capture provided bytes only; no assertion is made about their origin."""
    fd = None
    try:
        if (type(payload) is not bytes or not 0 < len(payload) <= MAX_BYTES
                or not _ref(proposal_ref) or not _ref(patch_ref) or _digest(payload) != patch_ref
                or type(lifetime_seconds) not in (int, float) or not 0 < lifetime_seconds <= 60
                or not callable(clock) or not SEALS or not hasattr(os, 'memfd_create')):
            return None, _result('invalid_or_unsupported_snapshot')
        now = clock()
        if type(now) not in (int, float) or not 0 <= now < now + lifetime_seconds:
            return None, _result('clock_invalid')
        fd = os.memfd_create('preceptoros-patch', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        view = memoryview(payload)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError('short write')
            view = view[count:]
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, SEALS)
        snapshot = SealedPatch(fd, proposal_ref, patch_ref, len(payload), now + lifetime_seconds, clock)
        fd = None
        verified, status = snapshot.read(proposal_ref)
        if verified != payload:
            snapshot.revoke()
            return None, status
        return snapshot, status
    except Exception:
        return None, _result('snapshot_unavailable')
    finally:
        if fd is not None:
            os.close(fd)
