"""Bind original task and execution pins before the existing host grants it.

No grant, route, lease, source capture, scheduler or remote permission is issued.
"""
import json
from .delegation import Failure, HEX, encode, sha, validate_task
from .resource_admission import resources

PIN_KEYS = frozenset({'session_ref', 'generation', 'node_ref', 'base_ref', 'head_ref',
                      'runtime_ref', 'selection_ref', 'constraints_ref', 'observed_at'})
REF_KEYS = PIN_KEYS - {'generation', 'observed_at', 'head_ref'}


def _flat(value):
    # Inspect exact primitive types BEFORE hashing/copying hostile metadata.
    return (type(value) is dict and len(value) <= 16
            and all(type(k) is str for k in value)
            and all(type(v) in (str, int, bool, type(None)) for v in value.values())
            and all(type(v) is not str or len(v) <= 128 for v in value.values()))


def _ref(value):
    return type(value) is str and HEX.fullmatch(value) is not None


class BoundWorker:
    """Host-owned wrapper consumed by native Session.execute, not a dispatcher.

    The original worker receives its unchanged original task/input convention.
    The Session sees a DIFFERENT input hash covering the original task plus pins.
    Its authority callback must independently approve that exact new task.
    Native resource admission must attest this wrapper's route, not the old worker.
    """
    def __init__(self, original, pin, *, local_node_ref, worker, witness, now):
        if not _flat(original) or not _flat(pin):
            raise Failure('PROTOCOL')
        validate_task(original)
        if (set(pin) != PIN_KEYS or not all(_ref(pin[k]) for k in REF_KEYS)
                or pin['head_ref'] is not None and not _ref(pin['head_ref'])
                or type(pin['generation']) is not int or not 0 <= pin['generation'] < 2**63
                or type(pin['observed_at']) is not str
                or not _ref(local_node_ref) or pin['node_ref'] != local_node_ref
                or pin['base_ref'] != original['model_version']
                or not all(callable(v) for v in (worker, witness, now))):
            raise Failure('EVIDENCE')
        self._original = encode(original).decode()
        self._pin = encode(pin).decode()
        self._worker, self._witness, self._now = worker, witness, now
        bound = dict(original)
        bound['input_sha256'] = sha({'schema': 'preceptoros.execution-binding/1',
                                    'original_task_ref': sha(original), 'pin': pin})
        self._bound = encode(bound).decode()

    def task(self):
        return json.loads(self._bound)

    def record(self):
        row = dict(schema='preceptoros.execution-binding/1', task_ref=sha(self.task()),
                   original_task_ref=sha(json.loads(self._original)),
                   pin_ref=sha(json.loads(self._pin)), authority='none',
                   dispatch_authorized=False, remote_authorized=False)
        row['binding_ref'] = sha(row)
        return row

    def _check(self, cancelled):
        if cancelled():
            raise Failure('CANCELLED')
        original, pin = json.loads(self._original), json.loads(self._pin)
        stamp = pin['observed_at']
        try:
            age = resources.age_seconds(stamp, self._now())
            if age > 120 or self._witness(original, pin) is not True:
                raise Failure('EVIDENCE')
            if resources.age_seconds(stamp, self._now()) > 120:
                raise Failure('EVIDENCE')
        except Failure:
            raise
        except Exception:
            raise Failure('EVIDENCE') from None
        if cancelled():
            raise Failure('CANCELLED')

    def __call__(self, task, cancelled):
        if not _flat(task) or task != self.task():
            raise Failure('EVIDENCE')
        self._check(cancelled)
        value = self._worker(json.loads(self._original), cancelled)
        # Do not deliver a result under a changed head, generation or source selection.
        self._check(cancelled)
        return value
