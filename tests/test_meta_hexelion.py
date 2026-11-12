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
from meta_harness.delegation import Failure
from meta_harness.hexelion import ExistingHexelion, public_prompt
from tests.test_meta_delegation import task

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
    def test_existing_proxy_is_reused_with_host_cap_and_without_model_unload(self):
        class Handler(BaseHTTPRequestHandler):
            bodies, calls = [], []
            choice = 'DELEGATE_LOCAL'
            remote = False
            done = True
            def do_GET(self):
                type(self).calls.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'models': [{'name': 'hexelion:latest', 'digest': 'a' * 64}]}).encode())
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
                request = task(input_sha256=hashlib.sha256(public_prompt().encode()).hexdigest())
                value = adapter(request, lambda: False)
                self.assertEqual(adapter.decision, 'DELEGATE_LOCAL')
                self.assertEqual(value['tokens'], 8)
                self.assertEqual(adapter.proxy_sha256, hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(Handler.calls, ['/api/tags', '/api/tags', '/api/generate', '/api/tags'])
                self.assertEqual(Handler.bodies[0]['options']['num_predict'], 64)
                self.assertIs(Handler.bodies[0]['think'], False)
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
