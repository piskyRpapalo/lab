"""Bounded evidence around an injected host permission gate, not an authority service."""
import copy
import hashlib
import re
import threading
import time

from .reuse import instrument

encode = instrument('evidence').encode
FAILURES = frozenset({'NONE', 'PERMISSION', 'BUDGET', 'CANCELLED', 'REPLAY', 'TRANSPORT',
    'PROTOCOL', 'MODEL_IDENTITY', 'OUTPUT_SCHEMA', 'TASK_SKILL', 'EVIDENCE', 'UNKNOWN'})
HEX = re.compile(r'[0-9a-f]{64}\Z')
LABEL = re.compile(r'[a-z][a-z0-9-]{0,31}\Z')
TASK_KEYS = {'schema', 'task_id', 'run_id', 'specialist', 'model_version', 'source',
             'input_sha256', 'max_tokens', 'timeout_ms', 'depth', 'privacy', 'transport'}
NEXT = {'NONE': 'review_receipt', 'PERMISSION': 'request_permission', 'BUDGET': 'revise_budget',
        'CANCELLED': 'check_inflight_outcome', 'REPLAY': 'inspect_run_id',
        'TRANSPORT': 'repair_transport', 'PROTOCOL': 'repair_adapter',
        'MODEL_IDENTITY': 'verify_model', 'OUTPUT_SCHEMA': 'repair_contract',
        'TASK_SKILL': 'collect_independent_holdout', 'EVIDENCE': 'collect_evidence',
        'UNKNOWN': 'diagnose_without_retry'}
PROXY_CAUSES = {'station_rejected_request': 'PROTOCOL', 'station_returned_no_text': 'EVIDENCE',
    'station_response_exceeds_receipt_budget': 'EVIDENCE', 'station_invalid_json': 'PROTOCOL',
    'station_invalid_response': 'PROTOCOL', 'generation_duration_unmeasured': 'EVIDENCE',
    'station_timeout': 'TRANSPORT', 'station_probe_timeout': 'TRANSPORT',
    'station_unavailable': 'TRANSPORT', 'station_model_unconfirmed': 'MODEL_IDENTITY',
    'station_model_unavailable': 'MODEL_IDENTITY'}


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


class Failure(Exception):
    def __init__(self, category, cause=None):
        self.category = category if category in FAILURES - {'NONE'} else 'UNKNOWN'
        self.cause = cause if cause in PROXY_CAUSES and PROXY_CAUSES[cause] == self.category else None
        super().__init__(self.category)


def validate_task(task):
    if type(task) is not dict or set(task) != TASK_KEYS or task['schema'] != 'preceptoros.meta-task/1':
        raise Failure('PROTOCOL')
    for key in ('task_id', 'run_id', 'specialist', 'source'):
        if type(task[key]) is not str or not LABEL.fullmatch(task[key]):
            raise Failure('PROTOCOL')
    for key in ('model_version', 'input_sha256'):
        if type(task[key]) is not str or not HEX.fullmatch(task[key]):
            raise Failure('PROTOCOL')
    for key, lo, hi in [('max_tokens', 0, 512), ('timeout_ms', 1, 30000), ('depth', 0, 1)]:
        if type(task[key]) is not int or not lo <= task[key] <= hi:
            raise Failure('BUDGET')
    if task['privacy'] != 'LOCAL_ONLY':
        raise Failure('PERMISSION')
    if task['transport'] not in ('mcp_stdio', 'ollama_loopback', 'web_manual', 'local_function'):
        raise Failure('TRANSPORT')
    return task


class TokenBudget:
    """Conservative per-session accounting, shared by all consumers of this instance.

    This is not a provider quota meter. Unknown usage keeps its full reservation.
    The host supplies the approved local allowance; no remote spending is implemented.
    """
    def __init__(self, limit):
        if type(limit) is not int or not 0 <= limit <= 4096:
            raise Failure('BUDGET')
        self.remaining = limit
        self.lock = threading.Lock()

    def reserve(self, cap):
        with self.lock:
            if cap > self.remaining:
                raise Failure('BUDGET')
            self.remaining -= cap

    def settle(self, cap, used):
        with self.lock:
            self.remaining += cap - used


def check_grant(grant, task, now):
    keys = {'approved', 'task_sha256', 'approval_ref', 'expires_ns',
            'max_tokens', 'max_ms', 'max_depth', 'local_only'}
    if (type(grant) is not dict or set(grant) != keys or grant['approved'] is not True
            or grant['local_only'] is not True or grant['task_sha256'] != sha(task)
            or type(grant['approval_ref']) is not str or not HEX.fullmatch(grant['approval_ref'])
            or type(grant['expires_ns']) is not int or grant['expires_ns'] <= now):
        raise Failure('PERMISSION')
    for field, task_field in [('max_tokens', 'max_tokens'), ('max_ms', 'timeout_ms'), ('max_depth', 'depth')]:
        if type(grant[field]) is not int or not 0 <= task[task_field] <= grant[field]:
            raise Failure('BUDGET')


def check_result(value, task):
    keys = {'model_version', 'output_sha256', 'tokens', 'grade', 'basis'}
    if type(value) is not dict or set(value) != keys:
        raise Failure('PROTOCOL')
    if value['model_version'] != task['model_version']:
        raise Failure('MODEL_IDENTITY')
    if type(value['output_sha256']) is not str or not HEX.fullmatch(value['output_sha256']):
        raise Failure('PROTOCOL')
    if type(value['tokens']) is not int or not 0 <= value['tokens'] <= task['max_tokens']:
        raise Failure('BUDGET')
    if value['grade'] not in ('PASS', 'OUTPUT_SCHEMA', 'TASK_SKILL', 'NOT_EVALUATED'):
        raise Failure('EVIDENCE')
    if value['basis'] not in ('public_deterministic_reference', 'protocol_roundtrip', 'synthetic'):
        raise Failure('EVIDENCE')
    return value


def seal(receipt):
    receipt['receipt_ref'] = sha(receipt)
    if len(encode(receipt)) >= 1024:
        raise Failure('EVIDENCE')
    return receipt


def verify(receipt):
    keys = {'schema', 'task_id', 'run_id', 'specialist', 'model_version', 'source', 'phase',
            'observed_at', 'measurement', 'failure_class', 'confidence_basis', 'next_action',
            'approval_state', 'task_sha256', 'approval_ref', 'outcome', 'receipt_ref', 'failure_cause'}
    if (type(receipt) is not dict or set(receipt) not in (keys, keys - {'failure_cause'})
            or receipt.get('schema') != 'preceptoros.meta-receipt/1'):
        return False
    body = {k: v for k, v in receipt.items() if k != 'receipt_ref'}
    try:
        for key in ('task_id', 'run_id', 'specialist', 'source'):
            if type(receipt[key]) is not str or not LABEL.fullmatch(receipt[key]):
                return False
        for key in ('model_version', 'task_sha256', 'receipt_ref'):
            if type(receipt[key]) is not str or not HEX.fullmatch(receipt[key]):
                return False
        if receipt['approval_ref'] is not None and (type(receipt['approval_ref']) is not str
                or not HEX.fullmatch(receipt['approval_ref'])):
            return False
        instrument('evidence').valid_time(receipt['observed_at'])
        category = receipt['failure_class']
        if (category not in FAILURES or receipt['next_action'] != NEXT[category]
                or receipt['phase'] not in ('complete', 'failed', 'blocked', 'cancelled')
                or receipt['approval_state'] not in ('EXTERNAL_GATE', 'NO_DATA')
                or receipt['outcome'] not in ('KNOWN', 'UNKNOWN', 'NOT_STARTED')
                or receipt['confidence_basis'] not in ('public_deterministic_reference',
                    'protocol_roundtrip', 'synthetic', 'NO_DATA')):
            return False
        measurement = receipt['measurement']
        if measurement is not None:
            if (type(measurement) is not dict or set(measurement) != {'tokens', 'output_sha256', 'grade'}
                    or type(measurement['tokens']) is not int or not 0 <= measurement['tokens'] <= 512
                    or type(measurement['output_sha256']) is not str or not HEX.fullmatch(measurement['output_sha256'])
                    or measurement['grade'] not in ('PASS', 'OUTPUT_SCHEMA', 'TASK_SKILL', 'NOT_EVALUATED')):
                return False
            expected_class = measurement['grade'] if measurement['grade'] in ('OUTPUT_SCHEMA', 'TASK_SKILL') else 'NONE'
            if (category != expected_class or receipt['outcome'] != 'KNOWN'
                    or receipt['approval_state'] != 'EXTERNAL_GATE'
                    or receipt['confidence_basis'] == 'NO_DATA'):
                return False
        elif receipt['confidence_basis'] != 'NO_DATA' or receipt['outcome'] == 'KNOWN':
            return False
        if category == 'NONE' and (measurement is None or receipt['outcome'] != 'KNOWN'):
            return False
        cause = receipt.get('failure_cause', None if category == 'NONE' else category.lower())
        if cause != (None if category == 'NONE' else category.lower()):
            if type(cause) is not str or PROXY_CAUSES.get(cause) != category:
                return False
        if ((category == 'NONE') != (receipt['phase'] == 'complete')
                or (category == 'CANCELLED') != (receipt['phase'] == 'cancelled')
                or (receipt['approval_state'] == 'EXTERNAL_GATE') != (receipt['approval_ref'] is not None)):
            return False
        return receipt.get('receipt_ref') == sha(body) and len(encode(receipt)) < 1024
    except (TypeError, ValueError, OverflowError):
        return False


class Session:
    """Run-id ledger; optional host journal preserves claims across restarts.

    No automatic retries. Once dispatch may have started, an unknown outcome is cached
    and the token reservation retained. Without a journal, restart/multiple-process
    guarantees are NO_DATA. The host owns journal integrity and budget recovery.
    """
    def __init__(self, authority, budget, *, clock=time.monotonic_ns, admission=None, journal=None):
        self.authority, self.budget, self.clock = authority, budget, clock
        # Optional host-owned resource gate. It never replaces the exact-task grant.
        # Host retains any resource lease until a known outcome/reconciliation.
        self.admission = admission
        self.journal = journal
        self.runs, self.lock = {}, threading.RLock()

    def attests(self, receipt, task):
        """Witness only this host session's completed cached execution, not a self-hash."""
        try:
            with self.lock:
                if self.journal is not None:
                    if self.journal.attests(receipt, sha(task), task['run_id']) is True:
                        return True
                    stored = self.runs.get(task['run_id'])
                    return (receipt.get('outcome') == 'NOT_STARTED' and stored is not None
                            and stored[0] == sha(task) and stored[1] == receipt)
                stored = self.runs.get(task['run_id'])
                if stored is not None and stored[0] == sha(task) and stored[1] == receipt:
                    return True
                return False
        except Exception:
            return False

    def execute(self, task, dispatch, *, observed_at, cancelled=lambda: False):
        # Bad metadata is not echoed into a public receipt.
        validate_task(task)
        instrument('evidence').valid_time(observed_at)
        task = copy.deepcopy(task)
        fingerprint, run_id = sha(task), task['run_id']
        def replay(previous):
            try:
                witnessed = (verify(previous) and previous['task_sha256'] == fingerprint
                    and previous['run_id'] == run_id
                    and self.journal.attests(previous, fingerprint, run_id) is True)
            except Exception:
                witnessed = False
            if not witnessed:
                raise Failure('EVIDENCE')
            return copy.deepcopy(previous)
        with self.lock:
            if self.journal is not None:
                try:
                    previous = self.journal.lookup(run_id, fingerprint)
                except Failure:
                    raise
                except Exception:
                    raise Failure('EVIDENCE') from None
                if previous is not None:
                    return replay(previous)
            previous = self.runs.get(run_id)
            if previous is not None:
                if previous[0] != fingerprint or previous[1] is None:
                    raise Failure('REPLAY')
                return copy.deepcopy(previous[1])
            self.runs[run_id] = (fingerprint, None)
        started, measurement, approval, approval_ref = self.clock(), None, 'NO_DATA', None
        category, phase, dispatched, reserved, cause, claimed = 'NONE', 'complete', False, False, None, False
        try:
            if cancelled():
                raise Failure('CANCELLED')
            if task['transport'] == 'web_manual':
                raise Failure('TRANSPORT')
            grant = self.authority(copy.deepcopy(task))
            check_grant(grant, task, self.clock())
            approval = 'EXTERNAL_GATE'
            approval_ref = grant['approval_ref']
            if cancelled():
                raise Failure('CANCELLED')
            self.budget.reserve(task['max_tokens'])
            reserved = True
            # Validate again immediately before handing execution to the adapter.
            if cancelled():
                raise Failure('CANCELLED')
            now = self.clock()
            if now - started >= task['timeout_ms'] * 1_000_000:
                raise Failure('TRANSPORT')
            check_grant(grant, task, now)
            if self.admission is not None:
                if not callable(self.admission) or self.admission(
                        copy.deepcopy(task), copy.deepcopy(grant), dispatch, cancelled) is not True:
                    raise Failure('EVIDENCE')
                if cancelled():
                    raise Failure('CANCELLED')
                fresh_grant = self.authority(copy.deepcopy(task))
                check_grant(fresh_grant, task, self.clock())
                if fresh_grant['approval_ref'] != grant['approval_ref']:
                    raise Failure('PERMISSION')
                now = self.clock()
                if now - started >= task['timeout_ms'] * 1_000_000:
                    raise Failure('TRANSPORT')
                check_grant(fresh_grant, task, now)
            if self.journal is not None:
                try:
                    previous = self.journal.claim(run_id, fingerprint)
                except Failure:
                    raise
                except Exception:
                    raise Failure('EVIDENCE') from None
                if previous is not None:
                    self.budget.settle(task['max_tokens'], 0)
                    reserved = False
                    value = replay(previous)
                    with self.lock:
                        self.runs[run_id] = (fingerprint, value)
                    return value
                claimed = True
                if cancelled():
                    raise Failure('CANCELLED')
                now = self.clock()
                if now - started >= task['timeout_ms'] * 1_000_000:
                    raise Failure('TRANSPORT')
                check_grant(fresh_grant if self.admission is not None else grant, task, now)
            dispatched = True
            value = check_result(dispatch(copy.deepcopy(task), cancelled), task)
            if cancelled():
                raise Failure('CANCELLED')
            if self.clock() - started > task['timeout_ms'] * 1_000_000:
                raise Failure('TRANSPORT')
            self.budget.settle(task['max_tokens'], value['tokens'])
            measurement = {'tokens': value['tokens'], 'output_sha256': value['output_sha256'],
                           'grade': value['grade']}
            basis = value['basis']
            if value['grade'] in ('OUTPUT_SCHEMA', 'TASK_SKILL'):
                category = value['grade']
                phase = 'failed'
        except Failure as exc:
            category = exc.category
            cause = exc.cause
            phase = 'cancelled' if category == 'CANCELLED' else 'failed' if dispatched else 'blocked'
        except Exception:
            # Do not persist arbitrary adapter exception text, private paths or credentials.
            category, phase = 'UNKNOWN', 'failed' if dispatched else 'blocked'
        if reserved and not dispatched:
            self.budget.settle(task['max_tokens'], 0)
        receipt = {'schema': 'preceptoros.meta-receipt/1', 'task_id': task['task_id'],
            'run_id': run_id, 'specialist': task['specialist'], 'model_version': task['model_version'],
            'source': task['source'], 'phase': phase, 'observed_at': observed_at,
            'measurement': measurement, 'failure_class': category,
            'failure_cause': cause or (None if category == 'NONE' else category.lower()),
            'confidence_basis': basis if measurement is not None else 'NO_DATA',
            'next_action': NEXT[category], 'approval_state': approval,
            'task_sha256': fingerprint, 'approval_ref': approval_ref,
            'outcome': 'KNOWN' if measurement is not None else 'UNKNOWN' if dispatched else 'NOT_STARTED'}
        receipt = seal(receipt)
        with self.lock:
            if self.journal is not None and claimed:
                try:
                    self.journal.finish(run_id, fingerprint, receipt)
                except Failure:
                    raise
                except Exception:
                    raise Failure('EVIDENCE') from None
            self.runs[run_id] = (fingerprint, receipt)
        return copy.deepcopy(receipt)
