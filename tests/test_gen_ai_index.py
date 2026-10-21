#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "bin" / "gen_ai_index.py"


def run_gen(root, output, indexed=None, decoys=2, canaries=1):
    cmd = [sys.executable, str(GEN), "--root", str(root), "--output", str(output),
           "--decoys", str(decoys), "--canaries", str(canaries)]
    if indexed:
        cmd += ["--indexed", indexed]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestGenAiIndex(unittest.TestCase):
    def test_generates_valid_schema(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md,llms.txt,AGENTS.md,STATE.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(out.read_text())
            self.assertEqual(d["esquema"], "preceptoros.ai-index/1")
            self.assertIn("budget_words", d)
            self.assertGreater(len(d["entries"]), 0)

    def test_entry_has_required_fields(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(out.read_text())
            e = d["entries"][0]
            for k in ("path", "depth", "words", "bytes", "sha256", "class", "one_liner"):
                self.assertIn(k, e)
            self.assertEqual(len(e["sha256"]), 64)
            self.assertLessEqual(len(e["one_liner"]), 120)

    def test_decoys_have_fake_sha_and_path_not_in_tree(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md", decoys=2)
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(out.read_text())
            self.assertEqual(len(d["decoys"]), 2)
            for dec in d["decoys"]:
                self.assertEqual(len(dec["sha256"]), 64)
                self.assertFalse((REPO / dec["path"]).exists())

    def test_canary_is_real_path_at_depth_99(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md", canaries=1)
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(out.read_text())
            self.assertEqual(len(d["canaries"]), 1)
            self.assertEqual(d["canaries"][0]["depth"], 99)
            self.assertTrue((REPO / d["canaries"][0]["path"]).exists())

    def test_output_under_ceiling(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md,llms.txt,AGENTS.md,STATE.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertLessEqual(out.stat().st_size, 16384)

    def test_over_ceiling_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            big = Path(td) / "big.md"
            big.write_text("word " * 5000)
            out = Path(td) / "ai-index.json"
            r = run_gen(Path(td), out, indexed="big.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("SKIPPED", r.stdout)
            d = json.loads(out.read_text())
            self.assertEqual(len(d["entries"]), 0)

    def test_banned_words_absent(self):
        banned = ["ora" + "cle", "nota" + "ry", "dep" + "in",
                  "to" + "ken", "curren" + "cy", "clea" + "ring",
                  "ma" + "gic", "teleme" + "try"]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md,llms.txt")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = out.read_text().lower()
            for w in banned:
                self.assertNotIn(w, text, f"banned word in output: {w}")

    def test_sha256_matches_file(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ai-index.json"
            r = run_gen(REPO, out, indexed="README.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(out.read_text())
            data = (REPO / "README.md").read_bytes()
            self.assertEqual(d["entries"][0]["sha256"], hashlib.sha256(data).hexdigest())

    def test_deterministic_except_timestamp(self):
        with tempfile.TemporaryDirectory() as td:
            out1 = Path(td) / "a.json"
            out2 = Path(td) / "b.json"
            run_gen(REPO, out1, indexed="README.md,llms.txt")
            run_gen(REPO, out2, indexed="README.md,llms.txt")
            d1 = json.loads(out1.read_text())
            d2 = json.loads(out2.read_text())
            d1.pop("generated_utc")
            d2.pop("generated_utc")
            self.assertEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
