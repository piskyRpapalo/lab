import importlib.util
import json
from pathlib import Path
import subprocess
from datetime import datetime,timedelta,timezone
import unittest
from unittest.mock import patch

s=importlib.util.spec_from_file_location('completion_probe',Path(__file__).parents[1]/'bin/node_completion_probe.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NOW=datetime(2026,11,15,tzinfo=timezone.utc)


class ProbeTests(unittest.TestCase):
    def wire(self,edit=None):
        def transport(alias,payload):
            r=json.loads(payload)
            v={k:r[k] for k in ('node_ref','nonce','context_ref','request_ref')}
            v.update(schema='public-sort-completion/1',values=sorted(m.VALUES),observed_at=NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
            if edit:edit(v)
            return m.encoded(v)
        return transport

    def test_synthetic_completion_never_claims_live_auth_or_authority(self):
        r=m.probe('test-node','a'*64,transport=self.wire(),clock=lambda:NOW)
        self.assertEqual(r['state'],'PROBE_COMPLETED');self.assertEqual(r['origin'],'SIMULATED')
        self.assertFalse(r['native_dispatch_authorized']);self.assertFalse(r['APP_E2E'])
        self.assertEqual(r['authority'],'none');self.assertEqual(r['portable_authentication'],'NO_DATA')
        self.assertLess(len(m.encoded(r)),1024)

    def test_wrong_node_task_context_nonce_and_result(self):
        for field,value in [('node_ref','b'*64),('request_ref','b'*64),('context_ref','b'*64),
                            ('nonce','0'*32),('values',[0]),('values',[-2,0,True,7,11]),('schema','other')]:
            with self.subTest(field=field):
                r=m.probe('test-node','a'*64,transport=self.wire(lambda v:v.update({field:value})),clock=lambda:NOW)
                self.assertEqual(r['state'],'NO_DATA')

    def test_future_and_expired_no_clock_tampering_claim(self):
        for delta in (1,-1):
            r=m.probe('test-node','a'*64,transport=self.wire(lambda v:v.update(observed_at=(NOW+timedelta(seconds=delta)).strftime('%Y-%m-%dT%H:%M:%SZ'))),clock=lambda:NOW)
            self.assertEqual(r['state'],'NO_DATA')
        times=iter([NOW,NOW+timedelta(seconds=31)])
        self.assertEqual(m.probe('test-node','a'*64,transport=self.wire(),clock=lambda:next(times))['state'],'NO_DATA')

    def test_timeout_network_loss_and_bad_json_never_retry(self):
        for error in (TimeoutError(),OSError('synthetic-private'),subprocess.TimeoutExpired('ssh',8)):
            calls=[]
            def fail(*a):calls.append(1);raise error
            r=m.probe('test-node','a'*64,transport=fail,clock=lambda:NOW)
            self.assertEqual(calls,[1]);self.assertEqual(r['state'],'NO_DATA')
            self.assertNotIn('synthetic-private',str(r))
        for raw in (b'[]',b'not-json',b'x'*1025,b'{"x":1,"x":2}'):
            self.assertEqual(m.probe('test-node','a'*64,transport=lambda *a:raw,clock=lambda:NOW)['state'],'NO_DATA')

    def test_no_explicit_config_no_process(self):
        with patch.object(m,'explicit_alias',return_value=False),patch.object(m,'ssh_transport') as t:
            r=m.probe('test-node','a'*64,clock=lambda:NOW)
            self.assertEqual(r['attempts'],0);t.assert_not_called()

    def test_alias_and_context_injection_rejected(self):
        for alias in ('-oProxyCommand=bad','test;bad','../host','user@host'):
            with self.assertRaises(ValueError):m.probe(alias,'a'*64,transport=self.wire(),clock=lambda:NOW)
        with self.assertRaises(ValueError):m.probe('test-node','bad',transport=self.wire(),clock=lambda:NOW)

    def test_request_tamper_not_hidden_by_checksum_of_reply(self):
        r=m.request('a'*64,'b'*64,'c'*32,NOW)
        reply=json.loads(self.wire()('test-node',m.encoded(r)))
        r['context_ref']='f'*64
        self.assertFalse(m.verify_completion(r,reply,NOW))


if __name__=='__main__':unittest.main()
