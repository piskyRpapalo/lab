"""Existing-proxy interface integration against an entirely synthetic local server."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from meta_harness import cli
from meta_harness.delegation import Failure, Session, TokenBudget, sha
from meta_harness.hexelion import ExistingHexelion, public_prompt, capability_evidence
from tests.test_meta_delegation import task, grant, STAMP, result

FAKE_PROXY = '''import json,urllib.request
MODEL='hexelion:latest'
def ask(text,endpoint=None,opener=None,output_format=None):
 try:
  with opener(urllib.request.Request(endpoint+'/api/tags'),timeout=3) as r:json.load(r)
  body={'model':MODEL,'prompt':text,'stream':False,'think':'low','options':{'num_predict':512},'format':output_format}
  with opener(urllib.request.Request(endpoint+'/api/generate',data=json.dumps(body).encode()),timeout=120) as r:value=json.load(r)
  return {'estado':'MEASURED','texto':value['response'],'medida':{'gen_tokens':value['eval_count']}}
 except Exception:return {'estado':'NO_DATA'}
'''


class HexelionTests(unittest.TestCase):
    def bootstrap(self, choice='DELEGATE_LOCAL', grade='PASS', enabled=True):
        calls = []
        class Local:
            input_sha256 = hashlib.sha256(cli.throughput.public_input(cli.throughput.FIXTURE.read_bytes()).encode()).hexdigest()
            case_sha256 = hashlib.sha256(cli.throughput.FIXTURE.read_bytes()).hexdigest()
            def __init__(self, *args):
                pass
            def __call__(self, request, cancelled):
                calls.append(request['source'])
                return {'model_version': request['model_version'], 'tokens': 3,
                    'output_sha256': 'd' * 64, 'grade': grade, 'basis': 'public_deterministic_reference'}
        class Planner:
            decision, proxy_sha256 = None, None
            def __init__(self, root, base, capability):
                self.capability = capability
                self.input_sha256 = hashlib.sha256(public_prompt(capability).encode()).hexdigest()
            def __call__(self, request, cancelled):
                self.decision, self.proxy_sha256 = choice, 'c' * 64
                return {'model_version': request['model_version'], 'tokens': 7,
                    'output_sha256': 'e' * 64, 'grade': 'PASS', 'basis': 'synthetic'}
        def catalog(base, model, source):
            return {'source': source, 'kind': 'MODEL', 'state': 'DECLARED', 'model_version': 'a' * 64}
        output = io.StringIO()
        args = ['--execute-public', '--approval-ref', 'e' * 64, '--app-root', '/synthetic']
        if enabled:
            args += ['--bootstrap-baseline']
        with patch.object(cli, 'model_catalog', catalog), patch.object(cli, 'LocalModel', Local), \
                patch.object(cli, 'ExistingHexelion', Planner), patch('sys.stdout', output):
            code = cli.main(args)
        return code, json.loads(output.getvalue()), calls

    def test_measured_baseline_enables_only_authorized_delegation_and_shared_budget(self):
        code, report, calls = self.bootstrap()
        self.assertEqual(code, 0)
        self.assertEqual(calls, ['baseline-model', 'baseline-model', 'local-model', 'local-model'])
        self.assertEqual(report['local_token_ceiling'], 768)
        self.assertEqual(report['local_tokens_remaining'], 768 - 4 * 3 - 7)
        self.assertEqual(report['aggregation']['unique_cases'], 1)
        self.assertFalse(report['improvement_proposal']['lora_authorized'])

    def test_hallucinated_delegate_choice_without_evidence_never_executes_worker(self):
        code, report, calls = self.bootstrap(enabled=False)
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertEqual(len(report['receipts']), 1)
        self.assertFalse(report['delegation_decision']['permission_granted_by_model'])

    def test_failed_baseline_or_planner_abstention_never_falls_back(self):
        for choice, grade in [('NO_DATA', 'PASS'), ('DELEGATE_LOCAL', 'OUTPUT_SCHEMA')]:
            code, report, calls = self.bootstrap(choice=choice, grade=grade)
            self.assertEqual(code, 1)
            self.assertEqual(calls, ['baseline-model', 'baseline-model'])

    def test_context_cannot_smuggle_prompt_or_raw_private_data(self):
        for context in ({'prompt': 'fake-secret'}, {'model_version': 'a' * 64,
                'baseline_refs': ['b' * 64, 'b' * 64], 'baseline_passed': 2}):
            with self.assertRaises(Failure):
                public_prompt(context)

    def test_capability_context_is_frozen_and_exact_dispatched_input_rechecked(self):
        context = {'model_version': 'a' * 64, 'baseline_refs': ['b' * 64, 'c' * 64], 'baseline_passed': 2}
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'hexelion_proxy.py').write_text(FAKE_PROXY)
            adapter = ExistingHexelion(directory, 'http://127.0.0.1:1', context)
            request = task(max_tokens=512, input_sha256=adapter.input_sha256)
            original = dict(context, baseline_refs=list(context['baseline_refs']))
            context['baseline_refs'][0] = 'd' * 64
            def worker(target, args, ms, cancelled):
                self.assertEqual(args[-1], original)
                self.assertEqual(hashlib.sha256(public_prompt(args[-1]).encode()).hexdigest(), request['input_sha256'])
                return {'decision': 'DELEGATE_LOCAL', 'proxy_sha256': 'e' * 64,
                        'result': {'synthetic': True}}
            with patch('meta_harness.hexelion.run_worker', worker):
                adapter(request, lambda: False)
            adapter._capability_bytes = json.dumps(context).encode()
            with self.assertRaises(Failure):
                adapter(request, lambda: False)

    def test_capability_requires_current_expected_baseline_tasks_and_session_witness(self):
        digest = 'a' * 64
        input_sha = hashlib.sha256(cli.throughput.public_input(cli.throughput.FIXTURE.read_bytes()).encode()).hexdigest()
        tasks = [cli.task('baseline-' + n, 'serion-sort', digest, 'baseline-model', input_sha, 'ollama_loopback', 64)
                 for n in ('one', 'two')]
        session = Session(grant, TokenBudget(128))
        dispatch = lambda t, c: dict(result(t, c), basis='public_deterministic_reference')
        receipts = [session.execute(t, dispatch, observed_at=STAMP) for t in tasks]
        self.assertIsNotNone(capability_evidence(receipts, tasks, digest, STAMP, witness=session.attests))
        self.assertIsNone(capability_evidence(receipts, tasks, digest, STAMP))
        self.assertIsNone(capability_evidence(receipts, tasks, digest, '2026-11-12T00:03:00Z', witness=session.attests))
        changed = [dict(tasks[0], source='private-model'), tasks[1]]
        self.assertIsNone(capability_evidence(receipts, changed, digest, STAMP, witness=session.attests))
        changed = [dict(tasks[0], input_sha256='f' * 64), tasks[1]]
        self.assertIsNone(capability_evidence(receipts, changed, digest, STAMP, witness=session.attests))
        other_session = Session(grant, TokenBudget(128))
        self.assertIsNone(capability_evidence(receipts, tasks, digest, STAMP, witness=other_session.attests))

    def test_existing_proxy_is_reused_with_host_cap_and_without_model_unload(self):
        class Handler(BaseHTTPRequestHandler):
            bodies, calls = [], []
            choice = 'DELEGATE_LOCAL'
            remote = False
            done = True
            inner_digest_change = False
            def do_GET(self):
                type(self).calls.append(self.path)
                self.send_response(200)
                self.end_headers()
                digest = ('b' if self.inner_digest_change and len(self.calls) == 2 else 'a') * 64
                self.wfile.write(json.dumps({'models': [{'name': 'hexelion:latest', 'digest': digest}]}).encode())
            def do_POST(self):
                type(self).calls.append(self.path)
                type(self).bodies.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                value = {'model': 'hexelion:latest', 'response': json.dumps({'action': self.choice}), 'eval_count': 8}
                if self.done is not None:
                    value['done'] = self.done
                if self.remote:
                    value['remote_host'] = 'fake-private-remote'
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'hexelion_proxy.py'
                source.write_text(FAKE_PROXY)
                adapter = ExistingHexelion(directory, 'http://127.0.0.1:' + str(server.server_port))
                request = task(input_sha256=hashlib.sha256(public_prompt().encode()).hexdigest(), max_tokens=512)
                value = adapter(request, lambda: False)
                self.assertEqual(adapter.decision, 'DELEGATE_LOCAL')
                self.assertEqual(value['tokens'], 8)
                self.assertEqual(adapter.proxy_sha256, hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(Handler.calls, ['/api/tags', '/api/tags', '/api/generate', '/api/tags'])
                self.assertEqual(Handler.bodies[0]['options']['num_predict'], 512)
                self.assertEqual(Handler.bodies[0]['think'], 'low')
                self.assertNotIn('keep_alive', Handler.bodies[0])
                self.assertNotIn('fake-private', json.dumps(value))
                Handler.choice = 'NO_DATA'
                adapter(request, lambda: False)
                self.assertEqual(adapter.decision, 'NO_DATA')
                Handler.choice = 'EXECUTE_ARBITRARY_TOOL'
                with self.assertRaises(Failure) as caught:
                    adapter(request, lambda: False)
                self.assertEqual(caught.exception.category, 'OUTPUT_SCHEMA')
                Handler.choice, Handler.remote = 'DELEGATE_LOCAL', True
                with self.assertRaises(Failure) as caught:
                    adapter(request, lambda: False)
                self.assertEqual(caught.exception.category, 'PERMISSION')
                Handler.remote = False
                for done in (False, None, 1):
                    Handler.done = done
                    with self.assertRaises(Failure) as caught:
                        adapter(request, lambda: False)
                    self.assertEqual(caught.exception.category, 'PROTOCOL')
                    self.assertIsNone(adapter.decision)
                Handler.done, Handler.inner_digest_change, Handler.calls = True, True, []
                with self.assertRaises(Failure) as caught:
                    adapter(request, lambda: False)
                self.assertEqual(caught.exception.category, 'MODEL_IDENTITY')
                self.assertNotIn('/api/generate', Handler.calls)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_private_plan_cannot_authorize_itself_or_change_public_input(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'hexelion_proxy.py').write_text(FAKE_PROXY)
            adapter = ExistingHexelion(directory, 'http://127.0.0.1:1')
            with self.assertRaises(Failure) as caught:
                adapter(task(input_sha256='f' * 64), lambda: False)
            self.assertEqual(caught.exception.category, 'PERMISSION')

    def test_planner_no_data_never_dispatches_specialist(self):
        calls = []
        class Local:
            input_sha256 = 'b' * 64
            def __init__(self, *args):
                pass
            def __call__(self, *args):
                calls.append(1)
                raise AssertionError('specialist should not be called')
        class Planner:
            decision, proxy_sha256 = None, None
            input_sha256 = hashlib.sha256(public_prompt().encode()).hexdigest()
            def __init__(self, *args):
                pass
            def __call__(self, request, cancelled):
                self.decision, self.proxy_sha256 = 'NO_DATA', 'c' * 64
                return {'model_version': request['model_version'], 'tokens': 4,
                    'output_sha256': 'd' * 64, 'grade': 'PASS', 'basis': 'synthetic'}
        def catalog(base, model, source):
            return {'source': source, 'kind': 'MODEL', 'state': 'DECLARED', 'model_version': 'a' * 64}
        output = io.StringIO()
        with patch.object(cli, 'model_catalog', catalog), patch.object(cli, 'LocalModel', Local), \
                patch.object(cli, 'ExistingHexelion', Planner), patch('sys.stdout', output):
            rc = cli.main(['--execute-public', '--approval-ref', 'e' * 64, '--app-root', '/synthetic'])
        report = json.loads(output.getvalue())
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])
        self.assertFalse(report['delegation_decision']['permission_granted_by_model'])
        self.assertEqual(report['delegation_decision']['choice'], 'NO_DATA')
        self.assertEqual(len(report['receipts']), 1)


if __name__ == '__main__':
    unittest.main()
