"""Deterministic literal screening; never stores the response supplied by a caller."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent


def normalize(text):
    if not isinstance(text, str):
        raise ValueError('text_required')
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def load_cases(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    entries = manifest.get('cases')
    if not isinstance(entries, dict) or not entries:
        raise ValueError('invalid_manifest')
    paths = sorted((root / 'cases').glob('*.json'))
    if {p.name for p in paths} != set(entries):
        raise ValueError('corpus_file_set_changed')
    cases = {}
    for path in paths:
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entries[path.name]:
            raise ValueError('corpus_hash_mismatch')
        case = json.loads(data)
        if case.get('expected_verdict') not in ('SAFE', 'NO_DATA'):
            raise ValueError('invalid_expected_verdict')
        for key in ('must_mention', 'must_not_say'):
            values = case.get(key)
            if not isinstance(values, list) or not values or any(not isinstance(x, str) or not normalize(x) for x in values):
                raise ValueError('invalid_criteria')
        if not isinstance(case.get('id'), str) or case['id'] in cases:
            raise ValueError('invalid_or_duplicate_id')
        cases[case['id']] = case
    return cases


def judge(case, response, declared_verdict):
    text = normalize(response)
    required = [normalize(x) for x in case['must_mention']]
    prohibited = [normalize(x) for x in case['must_not_say']]
    missing = [i for i, phrase in enumerate(required) if phrase not in text]
    forbidden = [i for i, phrase in enumerate(prohibited) if phrase in text]
    reasons = []
    if missing:
        reasons.append('required_phrase_missing')
    if forbidden:
        reasons.append('prohibited_phrase_present')
    if declared_verdict != case['expected_verdict']:
        reasons.append('verdict_mismatch')
    return {'id': case['id'], 'result': 'PASS' if not reasons else 'FAIL',
            'causes': reasons, 'missing_indices': missing, 'prohibited_indices': forbidden}
