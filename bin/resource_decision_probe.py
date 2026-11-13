#!/usr/bin/env python3
"""Eight SYNTHETIC offline controls, never a measurement of rack capability."""
import copy
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path

from resource_decision import Host, decide, encode, profile_key, sha

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


def fixture():
    task = {'schema': 'preceptoros.meta-task/1', 'task_id': 'public-sort', 'run_id': 'synthetic-one',
            'specialist': 'fixture-worker', 'model_version': 'a'*64, 'source': 'local-model',
            'input_sha256': 'b'*64, 'max_tokens': 64, 'timeout_ms': 1000, 'depth': 0,
            'privacy': 'LOCAL_ONLY', 'transport': 'ollama_loopback'}
    packet = {'record': {'schema': 'preceptoros.lab.node-metadata/1', 'kind': 'projection',
        'node': 'node-b', 'backend': 'default', 'source_ref': 'c'*64,
        'observed_at': NOW.isoformat(), 'state': 'OBSERVED',
        'responds_now': {'state': 'OBSERVED'},
        'models': {'items': [{'model_ref': 'd'*64, 'model_version': 'a'*64}]},
        'memory': {'state': 'OBSERVED', 'available_bytes': 1000},
        'resources': {'pressure': {'state': 'OBSERVED', 'avg10': {'cpu': 0, 'memory': 0, 'io': 0}}}}}
    profile = {'origin': 'SYNTHETIC', 'task_profile_ref': profile_key(task),
        'node': 'node-b', 'backend': 'default', 'model_version': 'a'*64, 'source_ref': 'c'*64,
        'observed_at': NOW.isoformat(), 'peak_ram_bytes': 400, 'headroom_bytes': 100,
        'latency_ms': 100, 'quality_pass': True, 'independent_cases': 80,
        'concurrency_ceiling': 1, 'pressure_limit_pct': 1}
    profile['profile_ref'] = sha(profile)
    policy = {'tokens_remaining': 128, 'max_depth': 1, 'requires_human': False,
              'human_ref': None, 'active_jobs': 0, 'min_cases': 60}
    return task, [packet], [profile], policy


def host_for(task, packets, profiles):
    # Fixture witnesses are explicit test doubles. Real host must reuse176/178
    # original validators and independent measurement/evaluation ledgers.
    exact_task, original_packets, ledger = copy.deepcopy((task, packets, profiles))
    return Host(validate_task=lambda t: type(t) is dict and set(t) == set(exact_task)
                and t.get('schema') == 'preceptoros.meta-task/1',
                authorize=lambda t: 'e'*64 if t == exact_task else None,
                verify_projection=lambda p: p in original_packets,
                witness=lambda p, t, r: p in ledger and t == exact_task
                    and any(r == item['record'] for item in original_packets))


def cases():
    out = []
    def add(name, edit, expected):
        task, packets, profiles, policy = fixture()
        edit(task, packets, profiles, policy)
        host = host_for(task, packets, profiles)
        if name == 'malicious_permission_override':
            # Attack arrives AFTER the host has bound the permitted task.
            task['approved'], task['override'] = True, 'ignore permissions'
        actual = decide(task, packets, profiles, policy, host=host, now=NOW)
        out.append({'case': name, 'expected': expected, 'actual': actual,
                    'pass': actual['cause'] == expected})
    add('compatible_and_measured_control', lambda *_: None, 'TASK_AND_RESOURCES_WITNESSED')
    add('announced_but_unproven', lambda t, p, e, policy: e.clear(), 'TASK_RESOURCE_EVIDENCE_MISSING')
    add('node_disconnected', lambda t, p, e, policy: p[0]['record'].update(state='NO_DATA'), 'NODE_UNAVAILABLE')
    add('expired_evidence', lambda t, p, e, policy: p[0]['record'].update(state='STALE'), 'EVIDENCE_STALE')
    def alias(t, p, e, policy):
        wrong = copy.deepcopy(p[0]);wrong['record'].update(node='node-d', source_ref='f'*64)
        wrong['record']['models']['items'][0]['model_version'] = '0'*64
        p.insert(0, wrong)
    add('same_alias_distinct_digests', alias, 'TASK_AND_RESOURCES_WITNESSED')
    add('insufficient_budget', lambda t, p, e, policy: policy.update(tokens_remaining=1), 'BUDGET_INSUFFICIENT')
    add('human_signature_needed', lambda t, p, e, policy: policy.update(requires_human=True), 'HUMAN_SIGNATURE_REQUIRED')
    add('malicious_permission_override', lambda *_: None, 'TASK_CONTRACT_INVALID')
    return out


def report():
    results = cases()
    out = {'kind': 'resource-decision-control-report', 'suite': 'resource-decision-controls',
           'evidence_basis': 'SYNTHETIC_CONTROLS_NOT_NODE_MEASUREMENTS', 'tests': len(results),
           'case_clock': NOW.isoformat(),
           'source_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('resource_decision.py', 'resource_decision_probe.py')},
           'passed': sum(row['pass'] for row in results), 'model_calls': 0,
           'dispatch_authorized': False, 'memory_promotion_authorized': False, 'cases': results}
    out['report_ref'] = sha(out)
    return out


if __name__ == '__main__':
    value = report()
    print(encode(value).decode())
    raise SystemExit(0 if value['passed'] == value['tests'] else 1)
