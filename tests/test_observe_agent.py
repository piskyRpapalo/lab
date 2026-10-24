import hashlib
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import observe_agent


class ObserveAgentTests(unittest.TestCase):
    def repo(self, root):
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        (root / "file.txt").write_text("one\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "file.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "one"], check=True)
        return root

    def test_first_snapshot_is_explicit_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            web = self.repo(base / "web")
            app = self.repo(base / "app")
            log = base / "claude.md"
            log.write_text("line one\n", encoding="utf-8")
            receipt = observe_agent.observe(web, app, log)
        self.assertEqual(receipt["worktrees"]["web"]["commits_since_previous"]["status"], "NO_DATA")
        self.assertEqual(receipt["log_append"]["status"], "NO_DATA")
        self.assertEqual(receipt["log_append"]["cause"], "no previous observation receipt")
        self.assertFalse(receipt["fences"]["network_used"])

    def test_diffs_commit_and_log_append_from_previous_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            web = self.repo(base / "web")
            app = self.repo(base / "app")
            log = base / "claude.md"
            log.write_text("base\n", encoding="utf-8")
            before = observe_agent.observe(web, app, log)
            (web / "file.txt").write_text("two\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(web), "add", "file.txt"], check=True)
            subprocess.run(["git", "-C", str(web), "commit", "-qm", "two"], check=True)
            (app / "staged.txt").write_text("staged\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(app), "add", "staged.txt"], check=True)
            (app / "loose.txt").write_text("loose\n", encoding="utf-8")
            with log.open("a", encoding="utf-8") as stream:
                stream.write("append\n")
            receipt = observe_agent.observe(web, app, log, previous=before)
        self.assertEqual(receipt["worktrees"]["web"]["commits_since_previous"]["count"], 1)
        self.assertEqual(receipt["worktrees"]["app"]["staged_count"], 1)
        self.assertEqual(receipt["worktrees"]["app"]["untracked_count"], 1)
        self.assertEqual(receipt["log_append"]["text"], "append\n")
        self.assertEqual(receipt["log_append"]["sha256"], hashlib.sha256(b"append\n").hexdigest())

    def test_non_prefix_log_is_not_reported_as_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            web, app = self.repo(base / "web"), self.repo(base / "app")
            log = base / "claude.md"
            log.write_text("base\n", encoding="utf-8")
            before = observe_agent.observe(web, app, log)
            log.write_text("rewritten\n", encoding="utf-8")
            receipt = observe_agent.observe(web, app, log, previous=before)
        self.assertEqual(receipt["log_append"]["status"], "NO_DATA")
        self.assertEqual(receipt["log_append"]["cause"], "previous log bytes are not a prefix")

    def test_listener_check_reads_local_port_without_connecting(self):
        rows = (b"LISTEN 0 128 localhost:18765 *:*\n"
                b"LISTEN 0 128 [::1]:5037 [::]:*\n")
        with patch.object(observe_agent, "_run", return_value=rows) as run:
            result = observe_agent._listener_ports((18765, 18766, 5037))
        self.assertTrue(result["18765"]["listening"])
        self.assertFalse(result["18766"]["listening"])
        self.assertTrue(result["5037"]["listening"])
        run.assert_called_once_with(["ss", "-H", "-ltn"])

    def test_unavailable_worktree_and_log_are_named_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            app = self.repo(base / "app")
            receipt = observe_agent.observe(base / "missing", app, base / "missing-log")
        self.assertEqual(receipt["worktrees"]["web"]["status"], "NO_DATA")
        self.assertIn("worktree", receipt["worktrees"]["web"]["cause"])
        self.assertEqual(receipt["log"]["status"], "NO_DATA")
        self.assertIn("session log", receipt["log"]["cause"])

    def test_malformed_prior_head_is_no_data_not_a_git_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            web, app = self.repo(base / "web"), self.repo(base / "app")
            log = base / "claude.md"
            log.write_text("base\n", encoding="utf-8")
            previous = {"worktrees": {"web": {"head": "--all"}},
                        "log": {"byte_length": 5, "sha256": hashlib.sha256(b"base\n").hexdigest()}}
            receipt = observe_agent.observe(web, app, log, previous)
        self.assertEqual(receipt["worktrees"]["web"]["commits_since_previous"]["status"], "NO_DATA")

    def test_malformed_previous_receipt_does_not_abort_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            web, app = self.repo(base / "web"), self.repo(base / "app")
            log = base / "claude.md"
            log.write_text("base\n", encoding="utf-8")
            receipt = observe_agent.observe(web, app, log, previous=["malformed"])
        self.assertEqual(receipt["worktrees"]["web"]["commits_since_previous"]["status"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
