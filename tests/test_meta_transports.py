"""Real local protocol plumbing against synthetic servers; zero real inference."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from meta_harness.delegation import Failure, Session, TokenBudget, sha, verify
from meta_harness.transports import LocalModel, NativeHealth, StdioMCP, grade_public, throughput
from tests.test_meta_delegation import STAMP, grant, task

FAKE_SERVER = '''import sys,json
for line in sys.stdin:
 m=json.loads(line);method=m['method']
 if method.startswith('notifications/'):continue
 if method=='initialize':v={'protocolVersion':'2025-11-25','serverInfo':{'name':'synthetic','version':'1'},'capabilities':{'tools':{}}}
 elif method=='tools/list':v={'tools':[{'name':'ping','inputSchema':{'type':'object'}}]}
 elif method=='tools/call':v={'content':[{'type':'text','text':json.dumps({'ok':True,'pong':True,'credential':'synthetic-canary'})}]}
 else:v={}
 print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':v}),flush=True)
'''


class MCPTests(unittest.TestCase):
    def make_server(self, directory, text=FAKE_SERVER):
        path = Path(directory) / 'synthetic.py'
        path.write_text(text)
        return path

    def test_stdio_handshake_manifest_and_fixed_tool_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self.make_server(directory)
            adapter = NativeHealth(script)
            request = task(transport='mcp_stdio', model_version=adapter.version,
                           input_sha256=sha({'tool': 'ping'}), max_tokens=0)
            receipt = Session(grant, TokenBudget(0)).execute(request, adapter, observed_at=STAMP)
            self.assertTrue(verify(receipt))
            self.assertEqual(receipt['phase'], 'complete')
            self.assertEqual(receipt['measurement']['grade'], 'NOT_EVALUATED')
            self.assertEqual(adapter.inventory['tools_verified'], ['ping'])
            self.assertEqual(adapter.inventory['model_execution']['state'], 'NO_DATA')
            self.assertNotIn('synthetic-canary', json.dumps([receipt, adapter.inventory]))

    def test_task_cannot_smuggle_exec_or_private_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = NativeHealth(self.make_server(directory))
            with self.assertRaises(Failure):
                adapter(task(transport='mcp_stdio', input_sha256=sha({'tool': 'exec'})), lambda: False)

    def test_absent_tool_rejected_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self.make_server(directory)
            with StdioMCP(script) as client:
                with self.assertRaises(Failure) as caught:
                    client.call('exec')
                self.assertEqual(caught.exception.category, 'PERMISSION')

    def test_replaced_mcp_script_never_executes_and_snapshot_is_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self.make_server(directory)
            adapter = NativeHealth(script)
            request = task(transport='mcp_stdio', model_version=adapter.version,
                           input_sha256=sha({'tool': 'ping'}), max_tokens=0)
            marker = Path(directory) / 'should-not-exist'
            with StdioMCP(script, expected_version=adapter.version) as client:
                script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').touch()\n' + FAKE_SERVER)
                self.assertTrue(client.call('ping')['pong'])
            self.assertFalse(marker.exists())
            with self.assertRaises(Failure) as caught:
                adapter(request, lambda: False)
            self.assertEqual(caught.exception.category, 'MODEL_IDENTITY')
            self.assertFalse(marker.exists())

    def test_snapshot_preserves_registered_python_main_namespace(self):
        prefix = '''from __future__ import annotations
from dataclasses import dataclass,KW_ONLY
import inspect
@dataclass
class Probe:
 a:int
 _:KW_ONLY
 b:int
parameters=inspect.signature(Probe).parameters
assert list(parameters)==['a','b']
assert parameters['b'].kind==inspect.Parameter.KEYWORD_ONLY
'''
        with tempfile.TemporaryDirectory() as directory:
            script = self.make_server(directory, prefix + FAKE_SERVER)
            with StdioMCP(script) as client:
                self.assertTrue(client.call('ping')['pong'])

    def test_wrong_id_duplicate_json_and_remote_error_are_protocol_failures(self):
        for response in ["{'jsonrpc':'2.0','id':999,'result':{}}",
                         "{'jsonrpc':'2.0','id':m['id'],'error':{'message':'fake-key'}}"]:
            script_text = 'import json,sys\nfor l in sys.stdin:\n m=json.loads(l);print(json.dumps(' + response + '),flush=True)\n'
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(Failure) as caught:
                    with StdioMCP(self.make_server(directory, script_text)):
                        pass
                self.assertEqual(caught.exception.category, 'PROTOCOL')
        with tempfile.TemporaryDirectory() as directory:
            script = self.make_server(directory, 'import sys\nfor l in sys.stdin:print(\'{"id":1,"id":1}\',flush=True)\n')
            with self.assertRaises(Failure):
                with StdioMCP(script):
                    pass

    def test_missing_process_timeout_and_cancel_are_bounded(self):
        with self.assertRaises(Failure):
            StdioMCP('/not-present/synthetic.py')
        with tempfile.TemporaryDirectory() as directory:
            script = self.make_server(directory, 'import time\ntime.sleep(10)\n')
            start = time.monotonic()
            with self.assertRaises(Failure):
                with StdioMCP(script, timeout=.05):
                    pass
            self.assertLess(time.monotonic() - start, 2)
            with self.assertRaises(Failure) as caught:
                with StdioMCP(script, cancelled=lambda: True):
                    pass
            self.assertEqual(caught.exception.category, 'CANCELLED')


class ModelTests(unittest.TestCase):
    def test_grader_separates_format_from_skill_and_pass(self):
        raw = throughput.FIXTURE.read_bytes()
        values = throughput.strict_json(raw)['values']
        self.assertEqual(grade_public(','.join(map(str, sorted(values))), raw), 'PASS')
        self.assertEqual(grade_public(','.join(map(str, values)), raw), 'TASK_SKILL')
        self.assertEqual(grade_public('not the contract', raw), 'OUTPUT_SCHEMA')
        self.assertEqual(grade_public(json.dumps(sorted(values)), raw, 'json-array'), 'PASS')
        self.assertEqual(grade_public(json.dumps(values), raw, 'json-array'), 'TASK_SKILL')
        self.assertEqual(grade_public(json.dumps([True] * 16), raw, 'json-array'), 'OUTPUT_SCHEMA')

    def test_profile_mutation_is_denied_and_does_not_inflate_case_identity(self):
        csv = LocalModel('http://127.0.0.1:1', 'synthetic:tiny')
        structured = LocalModel('http://127.0.0.1:1', 'synthetic:tiny', 'json-array')
        self.assertNotEqual(csv.input_sha256, structured.input_sha256)
        self.assertEqual(csv.case_sha256, structured.case_sha256)
        request = task(input_sha256=csv.input_sha256)
        csv.profile = 'json-array'
        with self.assertRaises(Failure) as caught:
            csv(request, lambda: False)
        self.assertEqual(caught.exception.category, 'PERMISSION')

    def test_remote_endpoints_and_cloud_aliases_refused_without_io(self):
        for base in ('http://example.org:80', 'http://127.0.0.1:80@evil.test:80'):
            with self.assertRaises(ValueError):
                LocalModel(base, 'synthetic:tiny')
        with self.assertRaises(Failure):
            LocalModel('http://127.0.0.1:1', 'synthetic:cloud')

    def test_model_worker_against_local_fake_http_and_no_implicit_pull(self):
        class Handler(BaseHTTPRequestHandler):
            paths, bodies = [], []
            response_model = 'synthetic:tiny'
            digest = 'a' * 64
            remote = False
            def do_GET(self):
                type(self).paths.append(self.path)
                value = {'models': [{'name': 'synthetic:tiny', 'digest': self.digest}]}
                if self.remote:
                    value['models'][0]['remote_host'] = 'fake-remote'
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())
            def do_POST(self):
                type(self).paths.append(self.path)
                type(self).bodies.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                value = {'model': self.response_model, 'done': True,
                    'response': ','.join(map(str, sorted(throughput.strict_json(throughput.FIXTURE.read_bytes())['values']))),
                    'eval_count': 32, 'eval_duration': 1000000000, 'load_duration': 0}
                if type(self).bodies[-1].get('format'):
                    value['response'] = json.dumps(sorted(throughput.strict_json(throughput.FIXTURE.read_bytes())['values']))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = LocalModel('http://127.0.0.1:' + str(server.server_port), 'synthetic:tiny')
            request = task(input_sha256=adapter.input_sha256)
            value = adapter(request, lambda: False)
            self.assertEqual(value['grade'], 'PASS')
            self.assertEqual(value['tokens'], 32)
            self.assertEqual(Handler.paths, ['/api/tags', '/api/generate', '/api/tags'])
            self.assertEqual(Handler.bodies[0]['options']['num_predict'], 64)
            self.assertIs(Handler.bodies[0]['think'], False)
            self.assertEqual(Handler.bodies[0]['keep_alive'], 0)
            structured = LocalModel('http://127.0.0.1:' + str(server.server_port), 'synthetic:tiny', 'json-array')
            self.assertEqual(structured(task(input_sha256=structured.input_sha256), lambda: False)['grade'], 'PASS')
            self.assertEqual(Handler.bodies[-1]['format']['maxItems'], 16)
            Handler.paths = []
            Handler.digest = 'b' * 64
            with self.assertRaises(Failure) as caught:
                adapter(request, lambda: False)
            self.assertEqual(caught.exception.category, 'MODEL_IDENTITY')
            self.assertNotIn('/api/generate', Handler.paths)
            Handler.digest, Handler.remote = 'a' * 64, True
            Handler.paths = []
            with self.assertRaises(Failure):
                adapter(request, lambda: False)
            self.assertNotIn('/api/generate', Handler.paths)
            self.assertNotIn('/api/pull', Handler.paths)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_client_cancellation_does_not_claim_model_service_stopped(self):
        adapter = LocalModel('http://127.0.0.1:1', 'synthetic:tiny')
        request = task(input_sha256=adapter.input_sha256)
        with self.assertRaises(Failure) as caught:
            adapter(request, lambda: True)
        self.assertEqual(caught.exception.category, 'CANCELLED')


if __name__ == '__main__':
    unittest.main()
