import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from bin.record_web_faro_receipt import record, GREEN, RED, NO_DATA


class FaroReceipt(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "web"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "fixture@example.invalid"], check=True)
        (self.repo / "public").mkdir()
        (self.repo / "public/index.html").write_bytes(b"main artifact\n")
        (self.repo / "atlas").mkdir()
        (self.repo / "atlas/faro.py").write_bytes(b"# faro fixture\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "public", "atlas"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "fixture"], check=True)
        self.commit = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        subprocess.run(["git", "-C", str(self.repo), "update-ref", "refs/remotes/origin/main", self.commit], check=True)
        self.transcript = self.root / "faro.txt"
        self.write_output(0, 1, 1, 0, 0)

    def tearDown(self):
        self.temp.cleanup()

    def write_output(self, code, compared, equal, drift, errors):
        self.transcript.write_text(
            f"ficheros comparados: {compared}\nLIVE iguales: {equal}\n"
            f"DRIFT distintos: {drift}\nDRIFT ausentes: 0\nERRORES de red: {errors}\n",
            encoding="utf-8",
        )
        self.exit_code = code

    def run_record(self):
        return record(
            web_repo=self.repo, faro_output=self.transcript, faro_exit_code=self.exit_code,
            deployment="measured-deploy", observed_at="2026-10-24T00:00:00Z",
        )

    def test_exact_live_counts_are_green(self):
        result = self.run_record()
        self.assertEqual(result["state"], GREEN)
        self.assertEqual(result["source_commit"], self.commit)
        self.assertEqual(result["public_file_count"], 1)
        self.assertEqual(result["transcript_sha256"], hashlib.sha256(self.transcript.read_bytes()).hexdigest())

    def test_drift_is_red(self):
        self.write_output(1, 1, 0, 1, 0)
        self.assertEqual(self.run_record()["state"], RED)

    def test_network_failure_is_no_data(self):
        self.write_output(2, 1, 0, 0, 1)
        result = self.run_record()
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("network", result["cause"])

    def test_incomplete_transcript_is_no_data(self):
        self.transcript.write_text("LIVE iguales: 1\n", encoding="utf-8")
        result = self.run_record()
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("summary", result["cause"])

    def test_dirty_source_is_no_data(self):
        (self.repo / "untracked.txt").write_text("uncommitted", encoding="utf-8")
        result = self.run_record()
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("clean", result["cause"])

    def test_head_must_equal_origin_main(self):
        subprocess.run(["git", "-C", str(self.repo), "checkout", "--detach", "HEAD"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "--allow-empty", "-qm", "stale"], check=True)
        result = self.run_record()
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("HEAD", result["cause"])


if __name__ == "__main__":
    unittest.main()
