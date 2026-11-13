import hashlib
import copy
import socket
import sqlite3
from contextlib import closing
from pathlib import Path
import unittest
from unittest.mock import patch

from meta_harness.readonly_mirror import ReadOnlyJournal, ReadOnlyMirror
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.fixture=synthetic.HumanUncertainty();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.path=self.fixture.path
        self.mirror=ReadOnlyMirror({'owned':{'journal':str(self.path),'task':task()}},
                                   local_source_witness=lambda _:True)  # synthetic only

    def test_unknown_projection_is_local_read_only_and_consistent(self):
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')):
            packet=self.mirror.read('owned',observed_at=STAMP)
        r=packet['machine']['record']
        self.assertEqual((r['state'],r['acknowledgement']),('UNKNOWN','HITL_REQUIRED'))
        self.assertEqual(r['reservation'],{'state':'RETAINED','tokens':64})
        self.assertEqual({v['state_ref'] for v in packet.values()},{r['projection_ref']})
        self.assertEqual(packet['text']['summary'],packet['speech']['summary'])
        self.assertEqual(before,hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertNotIn(str(self.path),str(packet))
        self.assertEqual(r['ttl_seconds'],0)

    def test_read_only_connection_refuses_sql_writes(self):
        journal=ReadOnlyJournal(str(self.path))
        with closing(journal._connect()) as db:
            with self.assertRaises(sqlite3.OperationalError):db.execute('CREATE TABLE forbidden (x)')

    def test_unknown_source_symlink_and_sidecars_fail_closed_without_paths(self):
        self.assertEqual(self.mirror.read('missing',observed_at=STAMP)['machine']['record']['cause'],'source_not_allowlisted')
        alias=self.path.parent/'link.sqlite3';alias.symlink_to(self.path)
        mirror=ReadOnlyMirror({'link':{'journal':str(alias),'task':task()}},local_source_witness=lambda _:True)
        self.assertEqual(mirror.read('link',observed_at=STAMP)['machine']['record']['state'],'NO_DATA')
        sidecar=Path(str(self.path)+'-wal');sidecar.write_bytes(b'fixture')
        packet=self.mirror.read('owned',observed_at=STAMP)
        self.assertEqual(packet['machine']['record']['cause'],'source_busy_or_wal_not_supported')
        self.assertNotIn(str(self.path),str(packet))

    def test_real_host_boundary_never_accepts_synthetic_human_ack(self):
        p=self.fixture.proposal();self.fixture.accepted.add(p['resolution_ref']);self.fixture.acknowledge(p)
        r=self.mirror.read('owned',observed_at=STAMP)['machine']['record']
        self.assertEqual((r['state'],r['acknowledgement']),('UNKNOWN','AUTHORITY_NOT_VERIFIED'))
        self.assertIsNone(r['resolution_ref'])
        self.assertEqual(r['reservation'],{'state':'RETAINED','tokens':64})

    def test_allowlist_is_closed_and_host_owned(self):
        with self.assertRaises(ValueError): ReadOnlyMirror({'bad':{'journal':'relative','task':task()}})
        with self.assertRaises(ValueError): ReadOnlyMirror({'bad':{'journal':str(self.path),'task':task(),'approval':True}})
        self.assertEqual(self.mirror.read('/private/path',observed_at=STAMP)['machine']['record']['state'],'NO_DATA')

    def test_local_filesystem_witness_is_mandatory_and_rechecked(self):
        spec={'owned':{'journal':str(self.path),'task':task()}}
        self.assertEqual(ReadOnlyMirror(spec).read('owned',observed_at=STAMP)['machine']['record']['cause'],
                         'local_source_not_attested')
        calls=iter([True,False])
        mirror=ReadOnlyMirror(spec,local_source_witness=lambda _:next(calls,False))
        self.assertEqual(mirror.read('owned',observed_at=STAMP)['machine']['record']['cause'],
                         'local_source_not_attested')
        self.assertEqual(self.mirror.read('owned',observed_at='invalid')['machine']['record']['cause'],
                         'host_clock_invalid')

    def test_stale_or_resealed_projection_is_recomputed_from_host(self):
        packet=self.mirror.read('owned',observed_at=STAMP)
        self.assertTrue(self.mirror.verify(packet,'owned',observed_at=STAMP))
        self.assertFalse(self.mirror.verify(packet,'owned',observed_at='2026-11-12T00:00:01Z'))
        forged=copy.deepcopy(packet)
        forged['machine']['record']['acknowledgement']='HUMAN_ACKNOWLEDGED'
        from meta_harness.delegation import sha
        from meta_harness.uncertainty_views import views
        r=forged['machine']['record'];r['projection_ref']=sha({k:v for k,v in r.items() if k!='projection_ref'})
        self.assertFalse(self.mirror.verify(views(r),'owned',observed_at=STAMP))
