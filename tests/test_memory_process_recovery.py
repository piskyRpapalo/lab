"""Process-boundary recovery contract over the EXISTING private LAB journal.

No device, server, network, model, real consent, independent witness or
autonomous retry. Both child processes run over a disposable private fixture.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHILD = r"""
import json
from pathlib import Path
import sys
from meta_harness.delegation import Failure, Session
from meta_harness.execution_journal import ExecutionJournal, DurableTokenBudget
from meta_harness.readonly_mirror import ReadOnlyMirror
from tests.test_meta_delegation import STAMP, grant, task, result

db_path = Path(sys.argv[1])
mode = sys.argv[2]
marker = Path(sys.argv[3])
def worker(t, cancelled):
    marker.write_text('DISPATCHED')
    if mode.endswith('unknown'):
        raise OSError('synthetic_uncertain_effect')
    return dict(result(t, cancelled), tokens=3)

if mode.startswith('seed-'):
    journal = ExecutionJournal.create(db_path)
    journal.initialize_budget(128)
else:
    journal = ExecutionJournal(db_path)

session = Session(grant, DurableTokenBudget(journal), journal=journal)
if mode.startswith('seed-'):
    receipt = session.execute(task(), worker, observed_at=STAMP)
    expected = 'UNKNOWN' if mode == 'seed-unknown' else 'KNOWN'
    assert receipt['outcome'] == expected
    assert marker.read_text() == 'DISPATCHED'
    assert session.budget.remaining == (64 if expected == 'UNKNOWN' else 125)
    print(json.dumps({'outcome': receipt['outcome'],
                      'receipt_ref': receipt['receipt_ref'],
                      'remaining': session.budget.remaining}))
elif mode == 'reopen-unknown':
    receipt = session.execute(task(), worker, observed_at=STAMP)
    assert receipt['outcome'] == 'UNKNOWN'
    assert session.budget.remaining == 64
    assert not marker.exists()
    try:
        session.execute(task(run_id='new-work'), worker, observed_at=STAMP)
    except Failure:
        pass
    else:
        raise AssertionError('unsafe_new_dispatch')
    assert not marker.exists()
    mirror = ReadOnlyMirror(
        {'fixture': {'journal': str(db_path), 'task': task()}},
        local_source_witness=lambda _: True,  # TEST DOUBLE, never authentication
    )
    packet = mirror.read('fixture', observed_at=STAMP)
    record = packet['machine']['record']
    assert record['state'] == 'UNKNOWN'
    assert record['acknowledgement'] == 'HITL_REQUIRED'
    assert record['reservation'] == {'state': 'RETAINED', 'tokens': 64}
    assert record['ttl_seconds'] == 0 and record['no_retry'] is True
    assert packet['text']['summary'] == packet['speech']['summary']
    assert len({v['state_ref'] for v in packet.values()}) == 1
    assert mirror.verify(packet, 'fixture', observed_at=STAMP)
    # TTL0: a previous projection cannot certify a later observation.
    assert not mirror.verify(packet, 'fixture', observed_at='2026-11-13T00:00:00Z')
    assert not marker.exists()
    print(json.dumps({'outcome': receipt['outcome'],
                      'receipt_ref': receipt['receipt_ref'],
                      'remaining': session.budget.remaining,
                      'view_state': record['state'],
                      'projection_ref': record['projection_ref'],
                      'retry_blocked': True, 'ttl_zero': True}))
elif mode == 'reopen-known':
    receipt = session.execute(task(), worker, observed_at=STAMP)
    assert receipt['outcome'] == 'KNOWN'
    assert not marker.exists()
    assert session.attests(receipt, task())
    assert session.budget.remaining == 125
    print(json.dumps({'outcome': receipt['outcome'],
                      'receipt_ref': receipt['receipt_ref'],
                      'remaining': session.budget.remaining,
                      'replayed_without_dispatch': True}))
else:
    raise ValueError('invalid_mode')
"""


class CrossProcessMemoryRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = self.root / "journal.sqlite3"
        self.marker = self.root / "worker-marker"

    def child(self, mode):
        # A truly fresh Python process: not a new Session in this interpreter.
        completed = subprocess.run(
            [sys.executable, "-B", "-c", CHILD, str(self.journal), mode,
             str(self.marker)],
            capture_output=True, text=True, timeout=15,
            cwd=Path(__file__).resolve().parent.parent,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr[-800:])
        self.assertFalse(completed.stderr.strip(), completed.stderr[-800:])
        return json.loads(completed.stdout.strip())

    def test_unknown_journal_reopens_in_new_process_without_auto_retry(self):
        seeded = self.child("seed-unknown")
        self.assertEqual(seeded['remaining'], 64)
        self.marker.unlink()  # Observe ONLY dispatches made by the fresh child.
        reopened = self.child("reopen-unknown")
        self.assertEqual((reopened['outcome'], reopened['remaining']),
                         ('UNKNOWN', 64))
        self.assertEqual(reopened['receipt_ref'], seeded['receipt_ref'])
        self.assertEqual(reopened['view_state'], 'UNKNOWN')
        self.assertTrue(reopened['retry_blocked'])
        self.assertTrue(reopened['ttl_zero'])
        self.assertFalse(self.marker.exists())

    def test_completed_receipt_reopens_in_new_process_without_double_charge(self):
        seeded = self.child("seed-known")
        self.assertEqual(seeded['remaining'], 125)
        self.marker.unlink()
        reopened = self.child("reopen-known")
        self.assertEqual(reopened['receipt_ref'], seeded['receipt_ref'])
        self.assertEqual(reopened['remaining'], 125)
        self.assertTrue(reopened['replayed_without_dispatch'])
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
