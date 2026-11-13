"""Static worker adapters. Native math is a tool, never a trained Serion model."""
from collections import Counter
import hashlib
from pathlib import Path

from .delegation import Failure, sha, verify
from .transports import LocalModel, PROFILES, sort_prompt, throughput

SPECS = dict(PROFILES, **{'native-sort': ('public-sort-native', 0)})


class NativeSort:
    """Fixed public data, built-in sort, independent monotonic/multiset property judge."""
    def __init__(self):
        self.raw = throughput.FIXTURE.read_bytes()
        throughput.public_input(self.raw)  # canonical public numeric input guard
        self.case_sha256 = hashlib.sha256(self.raw).hexdigest()
        self.input_sha256 = sha({'profile': 'native-sort', 'fixture_sha256': self.case_sha256})
        self.version = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def __call__(self, task, cancelled):
        actual = sha({'profile': 'native-sort', 'fixture_sha256': hashlib.sha256(self.raw).hexdigest()})
        if (task['input_sha256'] != self.input_sha256 or actual != self.input_sha256
                or task['transport'] != 'local_function' or task['max_tokens'] != 0
                or task['task_id'] != 'public-sort-native'):
            raise Failure('PERMISSION')
        if task['model_version'] != self.version:
            raise Failure('MODEL_IDENTITY')
        if cancelled():
            raise Failure('CANCELLED')
        values = throughput.strict_json(self.raw)['values']
        answer = sorted(values)
        valid = (len(answer) == len(values) and Counter(answer) == Counter(values)
                 and all(type(v) is int for v in answer)
                 and all(a <= b for a, b in zip(answer, answer[1:])))
        return {'model_version': self.version, 'output_sha256': sha(answer), 'tokens': 0,
                'grade': 'PASS' if valid else 'TASK_SKILL', 'basis': 'public_deterministic_reference'}


def select_worker(profile, base, model, catalog, *, model_factory=LocalModel):
    if profile == 'native-sort':
        worker = NativeSort()
        return worker, worker.version, 'local-tool', 'baseline-tool', 'local_function'
    if catalog['state'] != 'DECLARED':
        return None, None, 'local-model', 'baseline-model', 'ollama_loopback'
    return model_factory(base, model, profile), catalog['model_version'], 'local-model', 'baseline-model', 'ollama_loopback'


def baseline_spec(task_id):
    profile = next(k for k, spec in SPECS.items() if spec[0] == task_id)
    if profile == 'native-sort':
        return NativeSort().input_sha256, 'baseline-tool', 'local_function', 0
    return hashlib.sha256(sort_prompt(throughput.FIXTURE.read_bytes(), profile).encode()).hexdigest(), \
        'baseline-model', 'ollama_loopback', SPECS[profile][1]


def tool_inventory(version, receipts):
    known = any(verify(r) and r['model_version'] == version and r['outcome'] == 'KNOWN'
                and r['measurement'] is not None for r in receipts)
    return {'source': 'local-tool', 'kind': 'TOOL', 'state': 'MEASURED' if known else 'NO_DATA',
            'cause': None if known else 'no_measured_tool_outcome', 'model_version': version,
            'model_execution': throughput.no_data('native_function_not_model')}
