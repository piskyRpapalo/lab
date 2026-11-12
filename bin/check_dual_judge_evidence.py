#!/usr/bin/env python3
"""Offline evidence integrity, never semantic accuracy or model certification."""
import argparse
import hashlib
import json
from pathlib import Path
from dfa_b5_family_blind_gate import assess, SCHEMA as PAIR_SCHEMA

SCHEMA = 'preceptoros.lab.dual-evidence/1'
LIMIT = 4 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def artifact(ref, root):
    if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
        raise ValueError('reference_invalid')
    if not isinstance(ref['path'], str) or Path(ref['path']).is_absolute():
        raise ValueError('relative_path_required')
    path = (root / ref['path']).resolve(strict=True)
    path.relative_to(root.resolve())
    if not path.is_file():
        raise ValueError('regular_file_required')
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT or digest(raw) != ref['sha256']:
        raise ValueError('artifact_invalid')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('artifact_object_required')
    return value


def check(doc, root):
    if doc['schema'] != SCHEMA or not isinstance(doc['records'], list):
        raise ValueError('manifest_invalid')
    counts = dict(admissible=0, rejected=0, unknown=0, truncated=0, disagree=0)
    seen = set()
    for row in doc['records']:
        try:
            key = (row['case'], row['pass'])
            if not isinstance(key[0], str) or type(key[1]) is not int:
                raise ValueError('identity_invalid')
            if key in seen:
                counts['rejected'] += 1
                continue
            seen.add(key)
            response = artifact(row['response'], root)
            judges = [artifact(r, root) for r in row['judges']]
            if len(judges) != 2:
                raise ValueError('two_judges_required')
            items = [response] + judges
            if any(not isinstance(x['case'], str) or type(x['pass']) is not int or x['case'] != key[0] or x['pass'] != key[1] for x in items):
                raise ValueError('binding_invalid')
            if any(j['response_sha256'] != row['response']['sha256'] for j in judges):
                raise ValueError('response_binding_invalid')
            if any(x['termination'] == 'length' for x in items):
                counts['truncated'] += 1
                counts['rejected'] += 1
                continue
            if any(x['termination'] != 'stop' for x in items):
                raise ValueError('termination_unknown')
            members = [x['member'] for x in items]
            gates = [assess(dict(schema=PAIR_SCHEMA, manipulator=members[0], judge=j,
                                cases_per_class=doc['cases_per_class'], held_out=doc['held_out']))
                     for j in members[1:]]
            if any(g['state'] == 'DENY' for g in gates) or members[1]['model'] == members[2]['model'] or members[1]['family'] == members[2]['family']:
                counts['rejected'] += 1
                continue
            for item in items:
                provenance = artifact(item['provenance'], root)
                if provenance.get('member') != item['member'] or provenance.get('model_sha256') != item['model_sha256']:
                    raise ValueError('provenance_mismatch')
                if not isinstance(item['model_sha256'], str) or len(item['model_sha256']) != 64 or any(c not in '0123456789abcdef' for c in item['model_sha256']):
                    raise ValueError('model_digest_invalid')
            if any(j['verdict'] not in ('SAFE', 'UNSAFE', 'UNCERTAIN') for j in judges):
                raise ValueError('verdict_invalid')
            if len({x['model_sha256'] for x in items}) != 3:
                counts['rejected'] += 1
                continue
            counts['admissible'] += 1
            counts['disagree'] += judges[0]['verdict'] != judges[1]['verdict']
        except (KeyError, TypeError, ValueError, OSError):
            counts['unknown'] += 1
    return dict(schema=SCHEMA, counts=counts, input_sha256=digest(encode(doc)),
                state='REJECTED' if counts['rejected'] else 'NO_DATA' if counts['unknown'] or not doc['records'] else 'INTEGRITY_CHECKED',
                cause='offline_artifact_checks_only',
                independence='NO_DATA: provenance authenticity not externally attested',
                semantic_accuracy='NO_DATA: no_independent_gold')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.manifest.open('rb') as stream:
            raw = stream.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('manifest_over_limit')
        result = check(json.loads(raw), args.manifest.parent)
    except (OSError, ValueError, KeyError, TypeError):
        result = dict(state='NO_DATA', cause='manifest_unavailable_or_invalid')
    output = encode(result) + b'\n'
    assert len(output) < 1024
    print(output.decode(), end='')
    return 0 if result['state'] == 'INTEGRITY_CHECKED' else 1 if result['state'] == 'REJECTED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
