"""Metadata boundaries; no sockets or model inference in portable tests."""
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta
import unittest
from io import BytesIO

SPEC = importlib.util.spec_from_file_location('snapshot', Path(__file__).parents[1] / 'bin/federated_node_snapshot.py')
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class Fake:
    def __init__(self, entries):
        self.entries = entries
        self.calls = []

    def read(self, route, model=None):
        self.calls.append((route, model))
        data = {'version': '0.1.0'} if route == 'version' else {'models': self.entries if route == 'tags' else []}
        if route == 'show':
            data = {'license': 'PRIVATE LICENSE BODY', 'system': 'PRIVATE SYSTEM',
                    'template': 'PRIVATE TEMPLATE', 'parameters': 'num_ctx 4096\n',
                    'capabilities': ['completion', 'injected-private-string']}
        return {'state': 'VERIFIED', 'rtt_ms': 1, 'data': data}


class Boundaries(unittest.TestCase):
    def test_client_bounds_and_safe_errors(self):
        class Opener:
            def __init__(self, content):
                self.content = content
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return BytesIO(self.content)
        client = snapshot.Metadata(11434)
        for content, cause in ((b'x' * (snapshot.MAX_BYTES + 1), 'metadata_byte_limit'),
                               (b'[]', 'metadata_schema'),
                               (b'PRIVATE error text', 'metadata_unavailable_or_invalid')):
            client.opener = Opener(content)
            result = client.read('tags')
            self.assertEqual(result, snapshot.no_data(cause))
            self.assertNotIn('PRIVATE', str(result))
        client.opener = Opener(b'{"capabilities":[]}')
        self.assertEqual(client.read('show', 'x')['state'], 'VERIFIED')
        self.assertEqual(client.opener.request.get_method(), 'POST')
        self.assertEqual(client.opener.request.full_url, 'http://127.0.0.1:11434/api/show')
        self.assertEqual(client.opener.timeout, 4)

    def test_expiry_tamper_and_future_fail_closed(self):
        result = snapshot.collect('node-a', Fake([]))
        captured = datetime.fromisoformat(result['observed_at'])
        self.assertEqual(snapshot.freshness(result, captured)['state'], 'VERIFIED')
        self.assertEqual(snapshot.freshness(result, captured + timedelta(seconds=121))['state'], 'STALE')
        self.assertEqual(snapshot.freshness(result, captured - timedelta(seconds=1))['state'], 'NO_DATA')
        result['max_age_seconds'] = 1000000
        self.assertEqual(snapshot.freshness(result, captured)['cause'], 'snapshot_integrity')
        result.pop('snapshot_ref')
        result['snapshot_ref'] = snapshot.digest(result)
        self.assertEqual(snapshot.freshness(result, captured + timedelta(seconds=121))['state'], 'STALE')
        self.assertEqual(snapshot.freshness(result, captured.replace(tzinfo=None))['state'], 'NO_DATA')

    def test_failure_is_not_zero_inventory(self):
        fake = Fake(None)
        result = snapshot.collect('node-a', fake)
        self.assertEqual(result['catalog_state'], 'NO_DATA')
        self.assertEqual(result['admission']['state'], 'NO_DATA')

    def test_only_metadata_and_private_text_never_exported(self):
        fake = Fake([{'name': 'PRIVATE MODEL', 'digest': 'a'*64, 'size': 123,
                      'details': {'format': 'gguf', 'context_length': 8192}}])
        result = snapshot.collect('node-b', fake)
        self.assertNotIn('PRIVATE', str(result))
        self.assertNotIn('injected-private-string', str(result))
        self.assertEqual([c[0] for c in fake.calls], ['version', 'ps', 'tags', 'show'])
        model = result['models'][0]
        self.assertEqual(model['configured_context'], {'state': 'DECLARED', 'value': 4096})
        self.assertEqual(model['architecture_context']['value'], 8192)
        self.assertEqual(model['task_quality']['state'], 'NO_DATA')
        self.assertEqual(model['license']['value']['review'], 'NOT_REVIEWED')
        self.assertEqual(result['training'], 'NOT_AUTHORIZED')
        ref = result.pop('snapshot_ref')
        self.assertEqual(ref, snapshot.digest(result))

    def test_unknown_context_not_architectural_limit(self):
        model = snapshot.model_record({'details': {'context_length': 1000000}}, {'state': 'NO_DATA'})
        self.assertEqual(model['configured_context']['state'], 'NO_DATA')
        self.assertEqual(model['architecture_context']['state'], 'DECLARED')

    def test_tunnel_does_not_borrow_collector_memory(self):
        result = snapshot.collect('node-c', Fake([]), backend_only=True)
        self.assertEqual(result['host'], snapshot.no_data('backend_transport_only'))

    def test_malformed_metadata_cannot_export_freeform_text(self):
        model = snapshot.model_record({'details': {'format': 'PRIVATE', 'quantization_level': '/private/path',
                                                  'context_length': 'PRIVATE'}},
                                      {'state': 'VERIFIED', 'data': {'capabilities': None}})
        self.assertNotIn('PRIVATE', str(model))
        self.assertNotIn('/private', str(model))

    def test_malformed_or_oversize_catalog_refused_before_show(self):
        for entries in ([{}], [{'name': 'x', 'digest': 'bad'}], [{}]*257):
            fake = Fake(entries)
            result = snapshot.collect('node-a', fake)
            self.assertEqual(result['catalog_state'], 'NO_DATA')
            self.assertFalse(any(route == 'show' for route, _ in fake.calls))

    def test_routes_ports_and_redirects_refused(self):
        for port in (0, 65536, True, '11434'):
            with self.assertRaises(ValueError):
                snapshot.Metadata(port)
        client = snapshot.Metadata(11434)
        for route in ('pull', 'generate', 'chat', 'create', 'delete'):
            with self.assertRaises(ValueError):
                client.read(route)
        with self.assertRaises(ValueError):
            snapshot.NoRedirect().redirect_request(None, None, 302, '', {}, 'http://example.org')
        with self.assertRaises(ValueError):
            snapshot.collect('private-host', Fake([]))


if __name__ == '__main__':
    unittest.main()
