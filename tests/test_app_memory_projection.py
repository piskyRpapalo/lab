"""APP-RACK-MEMORY-01: only local, synthetic, no node/router/permission."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

from meta_harness import app_memory_projection as P
from meta_harness.delegation import Session, sha
from meta_harness.execution_journal import DurableTokenBudget, ExecutionJournal
from meta_harness.readonly_mirror import ReadOnlyMirror
from tests.test_meta_delegation import STAMP, grant, result, task


class AppRackMemoryProjection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "journal.sqlite3"
        first = ExecutionJournal.create(self.db)
        first.initialize_budget(128)
        # Fixture-only pin: produces byte-for-byte stable public examples.
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("UPDATE journal_identity SET id=?", ("a"*64,))
            c.commit()
        self.calls = 0

    def session(self):
        j = ExecutionJournal(self.db)
        return Session(grant, DurableTokenBudget(j), journal=j)

    def seed(self, outcome):
        def worker(t, cancelled):
            self.calls += 1
            if outcome == "UNKNOWN":
                raise OSError("synthetic_unknown")
            return dict(result(t, cancelled), tokens=3)
        first = self.session().execute(task(), worker, observed_at=STAMP)
        self.assertEqual(first["outcome"], outcome)
        self.assertEqual(self.calls, 1)
        return first

    def mirror(self, source_witness=None):
        if source_witness is None:
            source_witness = lambda p: p == self.db
        return ReadOnlyMirror(
            {"fixture": {"journal": str(self.db), "task": task()}},
            local_source_witness=source_witness,
        )

    def test_unknown_retained_no_retry_and_parity_source(self):
        self.seed("UNKNOWN")
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
            record = P.project(self.mirror(), "fixture", observed_at=STAMP)
        self.assertEqual(record["execution_state"], "UNKNOWN")
        self.assertEqual(record["budget_state"], "RETAINED")
        self.assertEqual(record["retry_policy"], "NO_RETRY")
        self.assertEqual(record["acknowledgement"], "HITL_REQUIRED")
        self.assertEqual(record["evidence_ref"], self.mirror().read(
            "fixture", observed_at=STAMP)["machine"]["record"]["projection_ref"])
        self.assertTrue(P.verify(record, self.mirror(), "fixture", observed_at=STAMP))
        self.assertFalse(P.verify(record, self.mirror(), "fixture",
                                  observed_at="2026-11-12T00:00:01Z"))
        self.assertEqual(record["expires_at"], record["observed_at"])
        self.assertEqual(record["ttl_seconds"], 0)
        self.assertEqual(record["authority"], "NOT_AUTHORIZED")
        self.assertEqual(record["independent_witness"], "NO_DATA")
        self.assertFalse(record["receipt_ref"])
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())
        self.assertEqual(self.calls, 1)
        self.assertLess(len(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()), 1024)
        for forbidden in (str(self.db), "journal_id", "run_id",
                          "specialist", "model_version", "private-key"):
            self.assertNotIn(forbidden, json.dumps(record))

    def test_known_is_verified_receipt_not_mirror_no_data_guess(self):
        old = self.seed("KNOWN")
        mirror = self.mirror()
        self.assertEqual(mirror.read("fixture", observed_at=STAMP)
                         ["machine"]["record"]["cause"], "claim_not_uncertain")
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        record = P.project(mirror, "fixture", observed_at=STAMP)
        self.assertEqual(record["execution_state"], "KNOWN")
        self.assertEqual(record["budget_state"], "SETTLED")
        self.assertEqual(record["retry_policy"], "REPLAY_ONLY")
        self.assertEqual(record["receipt_ref"], old["receipt_ref"])
        self.assertEqual(record["evidence_ref"], old["receipt_ref"])
        self.assertEqual(record["acknowledgement"], "NOT_APPLICABLE")
        self.assertTrue(P.verify(record, mirror, "fixture", observed_at=STAMP))
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())
        def forbidden(*args):
            self.fail("fresh worker dispatched on replay")
        replay = self.session().execute(task(), forbidden, observed_at=STAMP)
        self.assertEqual(replay, old)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.session().budget.remaining, 125)

    def test_source_missing_or_unattested_never_exposes_refs(self):
        self.seed("UNKNOWN")
        for mirror, source, cause in [
            (self.mirror(), "missing", "source_not_allowlisted"),
            (self.mirror(lambda p: False), "fixture", "local_source_not_attested"),
        ]:
            with self.subTest(cause=cause):
                record = P.project(mirror, source, observed_at=STAMP)
                self.assertEqual((record["execution_state"], record["cause"]),
                                 ("NO_DATA", cause))
                self.assertIsNone(record["source_ref"])
                self.assertIsNone(record["task_ref"])
                self.assertEqual(record["retry_policy"], "NO_RETRY")

    def test_read_known_requires_valid_budget_immutable_source(self):
        self.seed("KNOWN")
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("UPDATE budget_reservations SET status='RESERVED'")
            c.commit()
        record = P.project(self.mirror(), "fixture", observed_at=STAMP)
        self.assertEqual((record["execution_state"], record["cause"]),
                         ("NO_DATA", "known_receipt_not_verified"))
        self.assertIsNone(record["receipt_ref"])

    def test_sqlite_wal_symlink_and_tampering_fail_closed(self):
        self.seed("KNOWN")
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("UPDATE claims SET receipt='{}'")
            c.commit()
        record = P.project(self.mirror(), "fixture", observed_at=STAMP)
        self.assertNotEqual(record["execution_state"], "KNOWN")
        self.assertEqual(record["retry_policy"], "NO_RETRY")
        sidecar = Path(str(self.db) + "-wal")
        sidecar.write_bytes(b"synthetic")
        data = P.project(self.mirror(), "fixture", observed_at=STAMP)
        self.assertEqual(data["cause"], "source_busy_or_wal_not_supported")
        sidecar.unlink()
        symlink = self.db.parent / "link.sqlite3"
        symlink.symlink_to(self.db)
        mirror = ReadOnlyMirror({"fixture":{"journal":str(symlink),"task":task()}},
                                local_source_witness=lambda _: True)
        self.assertEqual(P.project(mirror,"fixture",observed_at=STAMP)["execution_state"],
                         "NO_DATA")

    def test_no_fake_known_on_missing_receipt(self):
        self.seed("UNKNOWN")
        with patch.object(ReadOnlyMirror, "read_known",
                          return_value={"journal_id":"a"*64,"task_ref":"b"*64,
                                        "receipt_ref":"c"*64,"budget_state":"SETTLED"}):
            record = P.project(self.mirror(),"fixture",observed_at=STAMP)
        self.assertEqual(record["execution_state"],"UNKNOWN")

    def test_forged_state_ref_is_not_authority(self):
        self.seed("UNKNOWN")
        mirror=self.mirror()
        original=P.project(mirror,"fixture",observed_at=STAMP)
        forged=copy.deepcopy(original)
        forged["execution_state"]="KNOWN"
        forged["budget_state"]="SETTLED"
        forged["state_ref"]=sha({k:v for k,v in forged.items() if k!="state_ref"})
        self.assertFalse(P.verify(forged,mirror,"fixture",observed_at=STAMP))

    def test_fresh_process_recomputes_same_source_and_state(self):
        self.seed("UNKNOWN")
        first=P.project(self.mirror(),"fixture",observed_at=STAMP)
        child = ("import json,sys; from meta_harness.app_memory_projection import project; "
                 "from meta_harness.readonly_mirror import ReadOnlyMirror; "
                 "from tests.test_meta_delegation import task,STAMP; "
                 "p=sys.argv[1]; "
                 "m=ReadOnlyMirror({'fixture':{'journal':p,'task':task()}},"
                 "local_source_witness=lambda x:str(x)==p); "
                 "print(json.dumps(project(m,'fixture',observed_at=STAMP)))")
        cp=subprocess.run([sys.executable,"-B","-c",child,str(self.db)],cwd=Path(__file__).parent.parent,
                          text=True,capture_output=True,timeout=10)
        self.assertEqual(cp.returncode,0,cp.stderr[-400:])
        second=json.loads(cp.stdout)
        self.assertEqual(first,second)
        self.assertEqual(first["state_ref"], second["state_ref"])

    def test_no_data_wrong_clock_and_nonmirror(self):
        self.seed("UNKNOWN")
        missing=P.project(self.mirror(),"fixture",observed_at="invalid")
        self.assertEqual(missing["execution_state"],"NO_DATA")
        self.assertEqual(missing["retry_policy"],"NO_RETRY")
        self.assertEqual(P.project(None,"fixture",observed_at=STAMP)["execution_state"],
                         "NO_DATA")


    def test_committed_examples_are_exact_and_bounded(self):
        directory = Path(__file__).parent / "fixtures"
        for state in ("KNOWN", "UNKNOWN"):
            with self.subTest(state=state):
                # A new fixture per scenario makes the two examples independent.
                case = AppRackMemoryProjection()
                case.setUp()
                try:
                    case.seed(state)
                    record = P.project(case.mirror(), "fixture", observed_at=STAMP)
                    path = directory / ("app_rack_memory_" + state.lower() + ".json")
                    raw = path.read_bytes()
                    self.assertLess(len(raw), 1024)
                    self.assertEqual(json.loads(raw), record)
                    self.assertEqual(
                        raw,
                        (json.dumps(record, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")) + chr(10)).encode(),
                    )
                finally:
                    case.doCleanups()

    def test_source_witness_rechecked_and_invalidated(self):
        self.seed("UNKNOWN")
        checks = iter([True, True, False])
        mirror = self.mirror(lambda p: next(checks, False))
        record = P.project(mirror, "fixture", observed_at=STAMP)
        self.assertEqual(record["execution_state"], "NO_DATA")
        self.assertEqual(record["cause"], "source_changed")
        self.assertIsNone(record["evidence_ref"])

    def test_known_unattested_file_never_becomes_known(self):
        self.seed("KNOWN")
        record = P.project(self.mirror(lambda _: False),
                           "fixture", observed_at=STAMP)
        self.assertEqual(record["execution_state"], "NO_DATA")
        self.assertEqual(record["cause"], "local_source_not_attested")


if __name__ == "__main__":
    unittest.main()
