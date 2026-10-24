import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from bin.run_mvp_origin_gates import run

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "fixtures/mvp-regression/baseline.synthetic.json").read_text())


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class OriginGateTests(unittest.TestCase):
    def repository(self, root, label, section, source_path, evidence_path):
        root.mkdir()
        git(root, "init", "-q")
        git(root, "config", "user.name", "Fixture")
        git(root, "config", "user.email", "fixture@example.invalid")
        source = root / source_path
        source.mkdir(parents=True)
        (source / "part.txt").write_text("source")
        git(root, "add", ".")
        git(root, "commit", "-qm", "source")
        tree = git(root, "rev-parse", "HEAD:" + source_path)
        keys = {"narration": "narration", "zoom": "zoom", "contrast": "contrast",
                "export": "export", "task_parity": "task_parity"}
        doc = {"schema": "fixture/1", "source_tree_oid": tree,
               section: BASE[keys[section]]}
        target = root / evidence_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc))
        git(root, "add", evidence_path)
        git(root, "commit", "-qm", "evidence")
        git(root, "update-ref", "refs/remotes/origin/candidate", "HEAD")
        return "refs/remotes/origin/candidate"

    def pair(self, temp):
        web, app = Path(temp) / "web", Path(temp) / "app"
        wr = self.repository(web, "web", "narration", "docs/rebuild/examples",
                             "docs/rebuild/mvp-origin-evidence.json")
        # One evidence document carries all four web gate sections.
        doc = json.loads((web / "docs/rebuild/mvp-origin-evidence.json").read_text())
        doc.update({key: BASE[key] for key in ("zoom", "contrast", "export")})
        (web / "docs/rebuild/examples/part.txt").write_text("source-v2")
        git(web, "add", "docs/rebuild/examples/part.txt")
        git(web, "commit", "-qm", "source v2")
        doc["source_tree_oid"] = git(web, "rev-parse", "HEAD:docs/rebuild/examples")
        (web / "docs/rebuild/mvp-origin-evidence.json").write_text(json.dumps(doc))
        git(web, "add", "docs/rebuild/mvp-origin-evidence.json")
        git(web, "commit", "-qm", "complete evidence")
        git(web, "update-ref", wr, "HEAD")
        ar = self.repository(app, "app", "task_parity", "interface/face",
                             "interface/mvp-origin-evidence.json")
        return web, wr, app, ar

    def test_all_five_gates_green_from_origin_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self.pair(tmp)
            result = run(web, wr, app, ar)
        self.assertEqual(result["verdict"], "GREEN")
        self.assertEqual(len(result["gates"]), 5)
        self.assertTrue(all(g["verdict"] == "GREEN" for g in result["gates"].values()))

    def test_missing_evidence_is_named_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self.pair(tmp)
            (web / "docs/rebuild/mvp-origin-evidence.json").unlink()
            git(web, "rm", "docs/rebuild/mvp-origin-evidence.json")
            git(web, "commit", "-qm", "remove evidence")
            git(web, "update-ref", wr, "HEAD")
            result = run(web, wr, app, ar)
        self.assertEqual(result["gates"]["narration_viewports"]["verdict"], "NO_DATA")

    def test_stale_source_tree_is_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self.pair(tmp)
            evidence = json.loads((web / "docs/rebuild/mvp-origin-evidence.json").read_text())
            evidence["source_tree_oid"] = "0" * 40
            (web / "docs/rebuild/mvp-origin-evidence.json").write_text(json.dumps(evidence))
            git(web, "add", "docs/rebuild/mvp-origin-evidence.json")
            git(web, "commit", "-qm", "stale evidence")
            git(web, "update-ref", wr, "HEAD")
            result = run(web, wr, app, ar)
        self.assertEqual(result["gates"]["narration_viewports"]["verdict"], "RED")

    def test_contrast_drift_is_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self.pair(tmp)
            path = web / "docs/rebuild/mvp-origin-evidence.json"
            evidence = json.loads(path.read_text())
            evidence["contrast"]["pairs"]["basic"][0]["ratio"] = 14.0
            path.write_text(json.dumps(evidence))
            git(web, "add", "docs/rebuild/mvp-origin-evidence.json")
            git(web, "commit", "-qm", "contrast sabotage")
            git(web, "update-ref", wr, "HEAD")
            result = run(web, wr, app, ar)
        self.assertEqual(result["gates"]["contrast_pairs"]["verdict"], "RED")

    def test_task_parity_drift_is_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self.pair(tmp)
            path = app / "interface/mvp-origin-evidence.json"
            evidence = json.loads(path.read_text())
            evidence["task_parity"]["tasks"][0]["app"]["state"] = "different"
            path.write_text(json.dumps(evidence))
            git(app, "add", "interface/mvp-origin-evidence.json")
            git(app, "commit", "-qm", "parity sabotage")
            git(app, "update-ref", ar, "HEAD")
            result = run(web, wr, app, ar)
        self.assertEqual(result["gates"]["task_level_parity"]["verdict"], "RED")

    def test_non_origin_ref_rejected(self):
        with self.assertRaises(ValueError):
            run(Path("/no/repo"), "refs/heads/main", Path("/no/repo"),
                "refs/remotes/origin/candidate")


if __name__ == "__main__":
    unittest.main()
