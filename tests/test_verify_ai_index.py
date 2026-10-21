#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERIFY = REPO / "bin" / "verify_ai_index.py"
SCHEMA = "preceptoros.ai-index/1"
BUDGET = {"L0": 700, "L1": 3000, "L2": 6000, "L3": 20000, "L4": 1024}


def make_index(root, entries, decoys=None, canaries=None, budget=None):
    return {
        "esquema": SCHEMA,
        "version": "1.0.0",
        "generated_utc": "2026-10-22T00:00:00Z",
        "generated_by": "test",
        "budget_words": budget or BUDGET,
        "entries": entries,
        "decoys": decoys or [],
        "canaries": canaries or [],
    }


def entry_for(root, rel, depth=1):
    p = root / rel
    data = p.read_bytes()
    text = data.decode("utf-8", errors="replace")
    return {
        "path": rel,
        "depth": depth,
        "words": len(text.split()),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "class": "doc",
        "one_liner": "test entry",
    }


def run_verify(root, index_path):
    return subprocess.run(
        [sys.executable, str(VERIFY), "--root", str(root), "--index", str(index_path)],
        capture_output=True, text=True,
    )


class TestVerifyAiIndex(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        (self.root / "README.md").write_text("# Test\nhello world\n")
        (self.root / "STATE.md").write_text("# State\nmeasured\n")

    def tearDown(self):
        self.td.cleanup()

    def write_index(self, d):
        p = self.root / "ai-index.json"
        p.write_text(json.dumps(d))
        return p

    def test_live_valid_index(self):
        d = make_index(self.root, [entry_for(self.root, "README.md")])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("LIVE", r.stdout)

    def test_missing_index_is_red(self):
        r = run_verify(self.root, self.root / "nonexistent.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("RED", r.stdout)

    def test_wrong_schema_is_red(self):
        d = make_index(self.root, [entry_for(self.root, "README.md")])
        d["esquema"] = "wrong/schema/9"
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("esquema mismatch", r.stdout)

    def test_sha_mismatch_is_red(self):
        e = entry_for(self.root, "README.md")
        e["sha256"] = "0" * 64
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("sha256 mismatch", r.stdout)

    def test_bytes_mismatch_is_red(self):
        e = entry_for(self.root, "README.md")
        e["bytes"] = 99999
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("bytes mismatch", r.stdout)

    def test_missing_entry_path_is_red(self):
        e = entry_for(self.root, "README.md")
        e["path"] = "ghost.md"
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing or outside tree", r.stdout)

    def test_decoy_existing_in_tree_is_red(self):
        d = make_index(
            self.root,
            [entry_for(self.root, "README.md")],
            decoys=[{"path": "README.md", "sha256": "0" * 64, "reason": "bad decoy"}],
        )
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("decoy path unexpectedly exists", r.stdout)

    def test_decoy_not_in_tree_is_live(self):
        d = make_index(
            self.root,
            [entry_for(self.root, "README.md")],
            decoys=[{"path": "docs/fake.md", "sha256": "1" * 64, "reason": "decoy"}],
        )
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_canary_depth_not_99_is_red(self):
        d = make_index(
            self.root,
            [entry_for(self.root, "README.md")],
            canaries=[{"path": "README.md", "depth": 2, "reason": "bad canary"}],
        )
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("canary depth is not 99", r.stdout)

    def test_canary_real_path_depth_99_is_live(self):
        d = make_index(
            self.root,
            [entry_for(self.root, "README.md")],
            canaries=[{"path": "README.md", "depth": 99, "reason": "canary"}],
        )
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_canary_missing_path_is_red(self):
        d = make_index(
            self.root,
            [entry_for(self.root, "README.md")],
            canaries=[{"path": "ghost.md", "depth": 99, "reason": "canary"}],
        )
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("canary path does not exist", r.stdout)

    def test_budget_missing_level_is_red(self):
        bad_budget = {"L0": 700, "L1": 3000}
        d = make_index(self.root, [entry_for(self.root, "README.md")], budget=bad_budget)
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("budget_words missing level", r.stdout)

    def test_entry_missing_key_is_red(self):
        e = entry_for(self.root, "README.md")
        del e["sha256"]
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing key", r.stdout)

    def test_duplicate_entry_is_red(self):
        e = entry_for(self.root, "README.md")
        d = make_index(self.root, [e, dict(e)])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("duplicate entry", r.stdout)

    def test_over_ceiling_index_is_red(self):
        big = self.root / "big-index.json"
        big.write_text("x" * 20000)
        r = run_verify(self.root, big)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("exceeds", r.stdout)

    def test_depth_out_of_range_is_red(self):
        e = entry_for(self.root, "README.md")
        e["depth"] = 7
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("depth out of range", r.stdout)

    def test_one_liner_over_120_is_red(self):
        e = entry_for(self.root, "README.md")
        e["one_liner"] = "x" * 121
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("one_liner over 120", r.stdout)

    def test_empty_entries_is_red(self):
        d = make_index(self.root, [])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("entries missing or empty", r.stdout)

    def test_sabotage_false_green_is_red(self):
        e = entry_for(self.root, "README.md")
        e["sha256"] = hashlib.sha256(b"tampered").hexdigest()
        d = make_index(self.root, [e])
        p = self.write_index(d)
        r = run_verify(self.root, p)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("RED", r.stdout)


if __name__ == "__main__":
    unittest.main()
