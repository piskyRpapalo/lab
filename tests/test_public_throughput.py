"""No inference: fake service plus isolated loopback HTTP transport sabotage."""
import contextlib
import copy
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('public_smoke', ROOT /
    'benchmarks/station-96-first-pass-20261029/smoke.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
RAW = runner.FIXTURE.read_bytes()
MODEL = 'fixture-model:tiny'
DIGEST = 'a' * 64
ANSWER = 'synthetic-answer-secret-canary'
GOOD = {'model': MODEL, 'done': True, 'response': ANSWER,
        'eval_count': 16, 'eval_duration': 2_000_000_000, 'load_duration': 10}


class Service:
    def __init__(self, responses=None, post_digest=DIGEST):
        self.responses = iter(responses or [GOOD, GOOD])
        self.calls = []
        self.tags = 0
        self.post_digest = post_digest

    def __call__(self, path, body=None):
        self.calls.append((path, copy.deepcopy(body)))
        if path == '/api/version':
            return {'version': '0.40.3'}
        if path == '/api/tags':
            self.tags += 1
            return {'models': [{'name': MODEL,
                               'digest': DIGEST if self.tags == 1 else self.post_digest}]}
        if path == '/api/generate':
            value = next(self.responses)
            if isinstance(value, Exception):
                raise value
            return copy.deepcopy(value)
        raise AssertionError('unexpected endpoint')


class PublicThroughput(unittest.TestCase):
    def run_receipt(self, service=None, raw=RAW):
        clock = iter([0, 3_000_000_000, 4_000_000_000, 7_000_000_000])
        return runner.run_public(MODEL, raw, call=service or Service(),
            clock=lambda: next(clock), measured_at='2026-11-12T00:00:00+00:00')

    def test_two_samples_fixed_controls_separate_load_and_wall(self):
        service = Service()
        receipt = self.run_receipt(service)
        self.assertEqual((receipt['state'], receipt['attempted'], receipt['succeeded'], receipt['failed']),
                         ('MEASURED', 2, 2, 0))
        self.assertEqual(receipt['samples'][0]['generation_tokens_per_s'], 8)
        self.assertEqual(receipt['samples'][0]['wall_ns'], 3_000_000_000)
        self.assertEqual(receipt['samples'][0]['load_ns'], 10)
        self.assertEqual(receipt['fixture_sha256'], hashlib.sha256(RAW).hexdigest())
        self.assertEqual(receipt['model_digest'], DIGEST)
        requests = [b for p, b in service.calls if p == '/api/generate']
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0], requests[1])
        self.assertEqual(requests[0]['options'], {'temperature': 0, 'seed': 42,
            'num_predict': 64, 'num_ctx': 2048})
        for key in ('stream', 'think', 'keep_alive'):
            self.assertEqual(requests[0][key], runner.SETTINGS[key])
        self.assertEqual([p for p, _ in service.calls],
            ['/api/version', '/api/tags', '/api/generate', '/api/generate', '/api/tags'])

    def test_deterministic_counters_and_digest_with_controlled_clock(self):
        a, b = self.run_receipt(), self.run_receipt()
        self.assertEqual(a, b)
        self.assertEqual(runner.comparison_key(a), runner.comparison_key(b))

    def test_fixture_change_breaks_comparison(self):
        fixture = json.loads(RAW)
        fixture['values'][0] += 1
        a, b = self.run_receipt(), self.run_receipt(raw=json.dumps(fixture).encode())
        self.assertNotEqual(runner.comparison_key(a), runner.comparison_key(b))
        self.assertNotEqual(a['input_sha256'], b['input_sha256'])

    def test_same_rendered_input_different_fixture_bytes_still_separates(self):
        a = self.run_receipt()
        b = self.run_receipt(raw=json.dumps(json.loads(RAW), indent=2).encode())
        self.assertEqual(a['input_sha256'], b['input_sha256'])
        self.assertNotEqual(a['fixture_sha256'], b['fixture_sha256'])
        self.assertNotEqual(runner.comparison_key(a), runner.comparison_key(b))

    def test_missing_model_never_generates_or_pulls(self):
        service = Service()
        def missing(path, body=None):
            return {'models': []} if path == '/api/tags' else service(path, body)
        receipt = self.run_receipt(missing)
        self.assertEqual(receipt['attempted'], 0)
        self.assertEqual(receipt['state'], 'NO_DATA')
        self.assertFalse(any(p in ('/api/generate', '/api/pull') for p, _ in service.calls))

    def test_cloud_preflight_refuses_before_any_generation(self):
        for field in ('remote_model', 'remote_host'):
            service = Service()
            def remote_tags(path, body=None):
                value = service(path, body)
                if path == '/api/tags':
                    value['models'][0][field] = 'remote-fake-canary'
                return value
            receipt = self.run_receipt(remote_tags)
            self.assertEqual(receipt['cause'], 'remote_model_refused')
            self.assertEqual(receipt['attempted'], 0)
            self.assertFalse(any(path == '/api/generate' for path, _ in service.calls))
            self.assertNotIn('remote-fake-canary', json.dumps(receipt))
        with self.assertRaises(ValueError):
            runner.run_public('model:cloud', RAW)

    def test_remote_generation_cannot_be_promoted(self):
        for field in ('remote_host', 'remote_model'):
            receipt = self.run_receipt(Service([dict(GOOD, **{field: 'remote-fake-canary'}), GOOD]))
            self.assertEqual(receipt['state'], 'NO_DATA')
            self.assertEqual(receipt['samples'][0]['cause'], 'remote_model_refused')
            self.assertEqual(receipt['failed'], 1)
            self.assertNotIn('remote-fake-canary', json.dumps(receipt))

    def test_http_protocol_failures_retain_both_attempts_and_cli_json(self):
        service = Service([http.client.BadStatusLine('fake-private-value'),
                           http.client.IncompleteRead(b'fake-private-content')])
        output = io.StringIO()
        with patch.object(runner.sys, 'argv', ['smoke.py', '--model', MODEL, '--public-fixture']), \
                contextlib.redirect_stdout(output), patch.object(runner, 'request',
                    lambda path, body=None, base=None: service(path, body)):
            self.assertEqual(runner.main(), 1)
        receipt = json.loads(output.getvalue())
        self.assertEqual((receipt['attempted'], receipt['failed']), (2, 2))
        self.assertEqual([s['cause'] for s in receipt['samples']], ['local_protocol_error'] * 2)
        self.assertNotIn('fake-private', output.getvalue())

    def test_real_malformed_chunk_is_retained_by_cli(self):
        class Handler(BaseHTTPRequestHandler):
            generations = 0
            def do_GET(self):
                value = {'version': '0.40.3'} if self.path == '/api/version' else {
                    'models': [{'name': MODEL, 'digest': DIGEST}]}
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())
            def do_POST(self):
                type(self).generations += 1
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('Transfer-Encoding', 'chunked')
                self.end_headers()
                self.wfile.write(b'INVALID-CHUNK\r\n')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        output = io.StringIO()
        try:
            with patch.object(runner.sys, 'argv', ['smoke.py', '--model', MODEL, '--public-fixture',
                    '--base-url', 'http://127.0.0.1:' + str(server.server_port)]), contextlib.redirect_stdout(output):
                self.assertEqual(runner.main(), 1)
            receipt = json.loads(output.getvalue())
            self.assertEqual(Handler.generations, 2)
            self.assertEqual((receipt['attempted'], receipt['failed']), (2, 2))
            self.assertEqual(receipt['samples'][0]['cause'], 'local_protocol_error')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_service_unavailable_scrubs_exception(self):
        def unavailable(*args):
            raise OSError('credential-fake-123 /private/source')
        receipt = self.run_receipt(unavailable)
        self.assertEqual(receipt['cause'], 'local_endpoint_unavailable')
        self.assertNotIn('credential-fake', json.dumps(receipt))
        self.assertNotIn('/private', json.dumps(receipt))

    def test_timing_sabotage(self):
        for key in ('eval_count', 'eval_duration'):
            for value in (None, 0, -1, True, '12', 1.5, float('nan'), 10**19):
                with self.subTest(key=key, value=value):
                    broken = dict(GOOD, **{key: value})
                    receipt = self.run_receipt(Service([broken, GOOD]))
                    self.assertEqual(receipt['state'], 'NO_DATA')
                    self.assertEqual(receipt['failed'], 1)
                    self.assertEqual(receipt['samples'][0]['cause'], 'invalid_timing')

    def test_malformed_responses_and_first_failure_retained(self):
        bad = [None, [], {}, dict(GOOD, done=1), dict(GOOD, response=None),
               dict(GOOD, response=''), dict(GOOD, model='other'),
               ValueError('private-text'), OSError('private-endpoint')]
        for response in bad:
            with self.subTest(response=type(response).__name__):
                receipt = self.run_receipt(Service([response, GOOD]))
                self.assertEqual(receipt['attempted'], 2)
                self.assertEqual(receipt['failed'], 1)
                self.assertEqual(receipt['succeeded'], 1)
                self.assertEqual(len(receipt['samples']), 2)
                self.assertEqual(receipt['samples'][0]['state'], 'NO_DATA')

    def test_digest_change_never_certifies_measurement(self):
        receipt = self.run_receipt(Service(post_digest='b' * 64))
        self.assertEqual(receipt['state'], 'NO_DATA')
        self.assertEqual(receipt['cause'], 'model_not_stable')
        self.assertEqual(receipt['succeeded'], 2)
        self.assertFalse(receipt['model_stable'])

    def test_missing_load_is_not_zero(self):
        receipt = self.run_receipt(Service([dict(GOOD, load_duration=None), GOOD]))
        self.assertEqual(receipt['samples'][0]['load_ns'], runner.no_data('load_duration_unavailable'))

    def test_response_and_prompt_never_appear_in_receipt(self):
        text = json.dumps(self.run_receipt())
        self.assertNotIn(ANSWER, text)
        self.assertNotIn(runner.public_input(RAW), text)
        self.assertLess(len(text.encode()), 16384)

    def test_public_fixture_accepts_only_small_numeric_data(self):
        for raw in (b'{}', b'[]', b'{"schema":"throughput-public-v1","schema":"x"}',
                    json.dumps({'schema': 'throughput-public-v1', 'values': ['secret'] * 16}).encode()):
            with self.assertRaises((ValueError, TypeError)):
                runner.public_input(raw)

    def test_labels_and_hardware_cannot_inject_content(self):
        for model in ('secret\nkey', 'x' * 129, 'https://host?token=x'):
            with self.assertRaises(ValueError):
                runner.run_public(model, RAW)
        with self.assertRaises(ValueError):
            runner.run_public(MODEL, RAW, hardware_class='/private/host')

    def test_endpoints_rejected_before_any_socket(self):
        for base in ('https://127.0.0.1:11434', 'http://localhost:11434',
                     'http://example.org:80', 'http://192.168.1.2:11434',
                     'http://127.0.0.1:80@evil.example:80', 'http://127.0.0.1:80?x=y',
                     'http://127.0.0.1:80/#x', 'http://127.0.0.1:80/api', 'http://127.0.0.1'):
            with self.subTest(base=base), patch.object(runner.urllib.request, 'build_opener') as opener:
                with self.assertRaises(ValueError):
                    runner.request('/api/tags', base=base)
                opener.assert_not_called()
        with self.assertRaises(ValueError):
            runner.request('/api/pull', {})
        self.assertEqual(runner.local_url('http://[::1]:11434'), 'http://[::1]:11434')

    def test_cli_public_profile_does_not_read_private_stdin(self):
        fake = io.StringIO()
        service = Service()
        with patch.object(runner.sys, 'argv', ['smoke.py', '--model', MODEL, '--public-fixture']), \
                patch.object(runner.sys, 'stdin') as stdin, contextlib.redirect_stdout(fake), \
                patch.object(runner, 'request', lambda path, body=None, base=None: service(path, body)):
            self.assertEqual(runner.main(), 0)
            stdin.read.assert_not_called()
        self.assertEqual(json.loads(fake.getvalue())['state'], 'MEASURED')

    def test_transport_refuses_redirect_proxy_oversize_and_ambiguous_json(self):
        class Handler(BaseHTTPRequestHandler):
            payload = b'{"version":"0.40.3"}'
            redirect = False
            hits = 0
            def do_GET(self):
                type(self).hits += 1
                self.send_response(302 if self.redirect else 200)
                if self.redirect:
                    self.send_header('Location', '/unexpected')
                self.end_headers()
                self.wfile.write(self.payload)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        try:
            with patch.dict(os.environ, {'http_proxy': 'http://127.0.0.1:1', 'no_proxy': ''}):
                self.assertEqual(runner.request('/api/version', base=base)['version'], '0.40.3')
            Handler.redirect = True
            before = Handler.hits
            with self.assertRaises(ValueError):
                runner.request('/api/tags', base=base)
            self.assertEqual(Handler.hits - before, 1)
            Handler.redirect = False
            for raw in (b'x' * 1048577, b'{"x":1,"x":2}', b'{"x":NaN}', b'not-json'):
                Handler.payload = raw
                with self.assertRaises(ValueError):
                    runner.request('/api/tags', base=base)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
