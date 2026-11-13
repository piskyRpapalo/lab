#!/usr/bin/env python3
"""Offline contract replay: actual pinned catalog, synthetic permission, no model.

Not an APP adapter or a permission authority. Test grant is never production HITL.
Historical replay demonstrates abstention, never current node availability.
"""
import copy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from meta_harness import delegation as d
import federated_projection as f
import resource_decision as r
import resource_decision_probe as p

PIN = 'a16605fd146a8b9e1241aa874e0c3de5a79027e6ba00ae30b266142275b47f29'


def report():
    source, backend = f.load_receipt(ROOT / 'benchmarks/receipts',
                                    '20261113-federated-node-d.json', PIN)
    replay = datetime(2026, 11, 13, 9, 42, tzinfo=timezone.utc)
    packet = f.views(f.project(source, replay, PIN, backend))
    task, _, _, policy = p.fixture()
    task['model_version'] = packet['record']['models']['items'][0]['model_version']
    grant = dict(approved=True, task_sha256=d.sha(task), approval_ref='e'*64,
                 expires_ns=1000000, max_tokens=64, max_ms=1000, max_depth=1, local_only=True)

    def validate(t):
        try:
            d.validate_task(t)
            return True
        except d.Failure:
            return False

    def authorize(t):
        try:
            d.check_grant(grant, t, 1)  # SYNTHETIC host clock/grant for this replay only.
            return grant['approval_ref']
        except d.Failure:
            return None

    host = r.Host(validate, authorize, lambda v: f.verify_packet(v, source, replay, PIN, backend),
                  lambda *_: False)  # There is no independent task/resource profile.
    no_profile = r.decide(task, [packet], [], policy, host=host, now=replay)
    forged = copy.deepcopy(packet)
    forged['record']['memory']['available_bytes'] = 10**15
    tampered = r.decide(task, [forged], [], policy, host=host, now=replay)
    later = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    stale = f.views(f.project(source, later, PIN, backend))
    stale_host = r.Host(validate, authorize, lambda v: f.verify_packet(v, source, later, PIN, backend),
                        lambda *_: False)
    expired = r.decide(task, [stale], [], policy, host=stale_host, now=later)
    attack = dict(task, approved=True)
    denied = r.decide(attack, [packet], [], policy, host=host, now=replay)
    out = dict(kind='resource-contract-replay', basis='REAL_PINNED_CATALOG_SYNTHETIC_PERMISSION',
               source_ref=PIN, replay_at=replay.isoformat(), model_calls=0,
               no_profile=no_profile, tampered=tampered, expired=expired, malicious=denied,
               sources_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                               for name in ('meta_harness/delegation.py', 'bin/federated_projection.py',
                                            'bin/resource_decision.py', 'bin/resource_contract_probe.py')})
    out['replay_ref'] = r.sha(out)
    return out


if __name__ == '__main__':
    print(r.encode(report()).decode())
