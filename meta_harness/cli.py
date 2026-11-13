"""Operator-run local evidence demo. No server, scheduler, remote API, or training path."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

from .delegation import Failure, Session, TokenBudget, encode, sha, verify
from .improvement import aggregate, evaluate
from .reuse import ROOT, PATHS, instrument
from .transports import LocalModel, NativeHealth, StdioMCP, PROFILES
from .hexelion import ExistingHexelion, public_prompt, capability_evidence
from .workers import SPECS, select_worker, tool_inventory

throughput = instrument('throughput')


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def task(run_id, specialist, version, source, input_hash, transport, tokens):
    return {'schema': 'preceptoros.meta-task/1', 'task_id': 'public-health' if tokens == 0 else 'public-sort',
        'run_id': run_id, 'specialist': specialist, 'model_version': version, 'source': source,
        'input_sha256': input_hash, 'max_tokens': tokens, 'timeout_ms': 30000,
        'depth': 1, 'privacy': 'LOCAL_ONLY', 'transport': transport}


def demo_gate(approved_tasks, approval_ref):
    """Trusted operator wiring only; CLI consent is NOT cryptographic human identity.

    Host APP/H3 must inject its existing authority verifier instead in integration.
    This closure admits only the exact fixed public tasks prepared by this CLI.
    """
    allowed = frozenset(sha(t) for t in approved_tasks)
    if type(approval_ref) is not str or not __import__('re').fullmatch('[0-9a-f]{64}', approval_ref):
        raise Failure('PERMISSION')
    def authorize(request):
        return {'approved': sha(request) in allowed, 'task_sha256': sha(request),
            'approval_ref': approval_ref, 'expires_ns': time.monotonic_ns() + 30_000_000_000,
            'max_tokens': 512 if request['source'] == 'private-model' else
                0 if request['task_id'] == 'public-sort-native' else 128 if request['task_id'] == 'public-sort-json128' else 64,
            'max_ms': 30000, 'max_depth': 1, 'local_only': True}
    return authorize


def projections(receipts, observed_at):
    if any(not verify(r) for r in receipts):
        raise Failure('EVIDENCE')
    failed = sum(r['failure_class'] != 'NONE' for r in receipts)
    text = f'{len(receipts)} task receipts; {failed} failed. Training is not authorized.'
    state = {'observed_at': observed_at, 'receipt_refs': [r['receipt_ref'] for r in receipts],
             'state': 'MEASURED' if receipts else 'NO_DATA',
             'cause': None if receipts else 'no_task_receipts', 'summary': text}
    fingerprint = sha(state)
    views = {'text': {'state_ref': fingerprint, 'summary': text},
             'speech': {'state_ref': fingerprint, 'summary': text},
             'machine': {'state_ref': fingerprint, 'record': state}}
    if len(text) > 100 or len(encode(views['machine'])) >= 1024:
        raise Failure('EVIDENCE')
    return views


def verify_projections(views, receipts, observed_at):
    try:
        return views == projections(receipts, observed_at)
    except (ValueError, TypeError, Failure):
        return False


def model_catalog(base, model, source):
    try:
        base = throughput.local_url(base)
        digest = throughput.model_digest(throughput.request('/api/tags', base=base), model)
        try:
            version = throughput.request('/api/version', base=base).get('version')
            if type(version) is not str or not __import__('re').fullmatch(r'\d+\.\d+\.\d+', version):
                version = throughput.no_data('version_not_measured')
        except Exception:
            version = throughput.no_data('version_not_measured')
        return {'source': source, 'kind': 'MODEL', 'state': 'DECLARED', 'transport_state': 'CONNECTED',
            'model_name': model if model in ('qwen3:1.7b', 'hexelion:latest', 'gemma2:2b') else 'operator-selected',
            'model_version': digest, 'ollama_version': version, 'basis': 'service_reported_catalog',
            'generation': throughput.no_data('no_generation_probe'),
            'server_egress': throughput.no_data('server_network_isolation_not_attested')}
    except Exception:
        return {'source': source, 'kind': 'MODEL', 'state': 'NO_DATA',
                'cause': 'model_catalog_unavailable_or_refused'}


def mcp_catalog(script, source):
    try:
        with StdioMCP(script) as client:
            return {'source': source, 'kind': 'MCP', 'transport': 'stdio', 'state': 'CONNECTED',
                'basis': 'initialize_tools_list', 'manifest_sha256': client.manifest_sha256,
                'tools_declared': len(client.tools), 'tools_verified': [],
                'model_execution': throughput.no_data('no_model_invoked')}
    except Exception:
        return {'source': source, 'kind': 'MCP', 'state': 'NO_DATA', 'cause': 'mcp_handshake_failed'}


def provenance():
    paths = sorted((ROOT / 'meta_harness').glob('*.py')) + [
        ROOT / 'benchmarks/fixtures/meta-harness-public-v1.json', throughput.FIXTURE]
    paths += [ROOT / p for p in PATHS.values()]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    relative = sorted(hashes)
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                                         stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *relative], cwd=ROOT).returncode
        tracked = subprocess.check_output(['git', 'ls-files', '--', *relative], cwd=ROOT, text=True).splitlines()
        if dirty or set(tracked) != set(relative):
            commit = throughput.no_data('uncommitted_evidence_code')
    except (OSError, subprocess.CalledProcessError):
        commit = throughput.no_data('git_source_unavailable')
    return {'commit': commit, 'source_sha256': sha(hashes), 'files': hashes,
            'throughput_contract': 'bench-repro-01-v1 helpers; meta receipts have their own schema'}


def pilot_rows(receipts, input_hash):
    models = [r for r in receipts if r['source'] in ('local-model', 'local-tool')]
    if not models:
        models = [r for r in receipts if r['source'] in ('baseline-model', 'baseline-tool')]
    target = 'OUTPUT_SCHEMA' if any(r['failure_class'] == 'OUTPUT_SCHEMA' for r in models) else 'TASK_SKILL'
    return [{'content_sha256': input_hash, 'split': 'holdout', 'target': target,
             'arm': 'baseline', 'repeat': index, 'failure': r['failure_class'], 'origin': 'MEASURED'}
            for index, r in enumerate(models, 1)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-mcp', type=Path)
    parser.add_argument('--private-mcp', type=Path)
    parser.add_argument('--base-url', default='http://127.0.0.1:11434')
    parser.add_argument('--model', default='qwen3:1.7b')
    parser.add_argument('--private-base-url', default='http://127.0.0.1:21434')
    parser.add_argument('--private-model', default='hexelion:latest')
    parser.add_argument('--execute-public', action='store_true')
    parser.add_argument('--approval-ref')
    parser.add_argument('--stop-file', type=Path)
    parser.add_argument('--app-root', type=Path, help='reuse existing APP Hexelion proxy for planner measurement')
    parser.add_argument('--run-prefix', help='public session label; no device identity')
    parser.add_argument('--bootstrap-baseline', action='store_true', help='measure two public baselines before planner')
    parser.add_argument('--worker-profile', choices=tuple(SPECS), default='csv')
    args = parser.parse_args(argv)
    if args.execute_public and not args.approval_ref:
        parser.error('--execute-public requires host approval reference')
    if args.app_root is not None and args.private_model != 'hexelion:latest':
        parser.error('existing APP proxy uses hexelion:latest; no alias substitution')
    if args.bootstrap_baseline and (not args.execute_public or args.app_root is None):
        parser.error('--bootstrap-baseline requires explicit execution and existing APP planner')
    cancelled = lambda: args.stop_file is not None and args.stop_file.exists()
    worker_id, worker_cap = SPECS[args.worker_profile]
    resources = [model_catalog(args.base_url, args.model, 'local-model'),
                 model_catalog(args.private_base_url, args.private_model, 'private-model')]
    for script, source in [(args.native_mcp, 'native-mcp'), (args.private_mcp, 'private-mcp')]:
        resources.append(mcp_catalog(script, source) if script is not None else {
            'source': source, 'kind': 'MCP', 'state': 'NO_DATA', 'cause': 'no_operator_target'})
    tasks, adapters, planner_task, planner, baseline_receipts, capability = [], [], None, None, [], None
    prefix = args.run_prefix or 'r' + sha([utc_now(), time.monotonic_ns()])[:12]
    if args.execute_public:
        try:
            if args.native_mcp is not None:
                native = NativeHealth(args.native_mcp)
                tasks.append(task(prefix + '-health', 'health', native.version, 'native-mcp',
                                  sha({'tool': 'ping'}), 'mcp_stdio', 0))
                adapters.append(native)
            model = resources[0]
            local, version, worker_source, baseline_source, transport = select_worker(
                args.worker_profile, args.base_url, args.model, model, model_factory=LocalModel)
            if local is not None:
                for suffix in ('one', 'two'):
                    tasks.append(task(prefix + '-' + suffix, 'serion-sort', version,
                                      worker_source, local.input_sha256, transport, worker_cap))
                    tasks[-1]['task_id'] = worker_id
                    adapters.append(local)
            baseline_tasks = []
            ceiling = (512 if args.app_root is not None else 0) + (4 if args.bootstrap_baseline else 2) * worker_cap
            budget = TokenBudget(ceiling)
            if args.bootstrap_baseline and local is not None:
                baseline_tasks = [task(prefix + '-base-' + suffix, 'serion-sort', version,
                    baseline_source, local.input_sha256, transport, worker_cap) for suffix in ('one', 'two')]
                for t in baseline_tasks:
                    t['task_id'] = worker_id
                baseline_session = Session(demo_gate(baseline_tasks, args.approval_ref), budget)
                baseline_receipts = [baseline_session.execute(t, local, observed_at=utc_now(), cancelled=cancelled)
                                     for t in baseline_tasks]
            capability = None
            if len(baseline_receipts) == 2:
                candidate = capability_evidence(baseline_receipts, baseline_tasks, version,
                    utc_now(), witness=baseline_session.attests)
                if candidate is not None:
                    capability = candidate
            if args.app_root is not None and resources[1]['state'] == 'DECLARED':
                planner = ExistingHexelion(args.app_root, args.private_base_url, capability)
                planner_task = task(prefix + '-plan', 'hexelion', resources[1]['model_version'],
                    'private-model', planner.input_sha256, 'ollama_loopback', 512)
            authority = demo_gate(tasks + ([planner_task] if planner_task else []), args.approval_ref)
            session = Session(authority, budget)
            receipts = list(baseline_receipts)
            if planner_task is not None:
                receipts.append(session.execute(planner_task, planner, observed_at=utc_now(), cancelled=cancelled))
            can_delegate = args.app_root is None or (capability is not None and planner is not None and planner.decision == 'DELEGATE_LOCAL'
                and receipts and receipts[-1]['phase'] == 'complete')
            for t, adapter in zip(tasks, adapters):
                if t['source'] != worker_source or can_delegate:
                    receipts.append(session.execute(t, adapter, observed_at=utc_now(), cancelled=cancelled))
            for t, adapter in zip(tasks, adapters):
                if isinstance(adapter, NativeHealth) and adapter.inventory is not None:
                    resources[2] = dict(adapter.inventory, source='native-mcp', kind='MCP')
            local_receipts = [r for r in receipts if r['source'] == worker_source]
            if local_receipts and worker_source == 'local-model':
                resources[0]['generation'] = {'state': 'MEASURED' if any(r['outcome'] == 'KNOWN'
                    for r in local_receipts) else 'NO_DATA', 'receipt_refs': [r['receipt_ref'] for r in local_receipts]}
            if worker_source == 'local-tool':
                resources.append(tool_inventory(version, local_receipts))
            rows = pilot_rows(receipts, local.case_sha256) if local_receipts or baseline_receipts else []
        except Exception:
            print(json.dumps(throughput.no_data('public_demo_failed_without_retry')))
            return 1
    else:
        receipts, rows, budget = [], [], TokenBudget(0)
    stamp = utc_now()
    planner_receipt = next((r for r in receipts if r['source'] == 'private-model'), None)
    decision = {'state': 'PROPOSED' if planner is not None and planner.decision else 'NO_DATA',
        'choice': planner.decision if planner is not None else None,
        'cause': None if planner is not None and planner.decision else 'private_planner_not_measured',
        'receipt_ref': planner_receipt['receipt_ref'] if planner_receipt else None,
        'proxy_sha256': planner.proxy_sha256 if planner is not None else None,
        'permission_granted_by_model': False}
    if planner_receipt:
        resources[1]['generation'] = {'state': 'MEASURED' if planner_receipt['outcome'] == 'KNOWN' else 'NO_DATA',
                                     'receipt_ref': planner_receipt['receipt_ref']}
    report = {'schema': 'preceptoros.meta-evidence/1', 'mission': 'META-HARNESS-01', 'observed_at': stamp, 'source': provenance(),
        'inventory': resources, 'inventory_scope': 'operator_selected_targets_only', 'worker_profile': args.worker_profile,
        'unprobed_transports': {k: throughput.no_data('no_authorized_endpoint_supplied')
            for k in ('mcp_sse', 'mcp_streamable_http', 'web_manual')},
        'configuration_import': throughput.no_data('credential_configs_not_read'),
        'tasks': (baseline_tasks if args.execute_public else []) + tasks + ([planner_task] if planner_task else []),
        'receipts': receipts, 'delegation_decision': decision,
        'local_tokens_remaining': budget.remaining,
        'local_token_ceiling': ceiling if args.execute_public else 0,
        'aggregation': aggregate(rows), 'improvement_proposal': evaluate(rows),
        'projections': projections(receipts, stamp),
        'limits': ['Client loopback and catalog fields do not attest server egress or weights.',
            'Operator-initiated public routing probe; not autonomous operation or APP end-to-end proof.',
            'One public input repeated twice is one independent case, not two.',
            'No LoRA trained, downloaded, activated or authorized.',
            'Client cancellation does not certify server termination; no retry on uncertain outcome.',
            'Run-id deduplication is session-local; durable multi-process delivery is not attested.']}
    raw = encode(report)
    if len(raw) >= 16384:
        print(json.dumps(throughput.no_data('report_byte_ceiling')))
        return 1
    print(raw.decode())
    completed = len([r for r in receipts if r['source'] in ('local-model', 'local-tool')]) == 2
    return 0 if not args.execute_public or completed and all(r['failure_class'] == 'NONE' for r in receipts) else 1


if __name__ == '__main__':
    raise SystemExit(main())
