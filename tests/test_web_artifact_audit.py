import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from bin.audit_web_artifacts import audit, NO_DATA, RED, GREEN


class WebArtifactAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "web"
        self.repo.mkdir()
        self.artifacts = self.root / "build"
        self.artifacts.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "fixture@example.invalid"], check=True)
        self.write_source("index.html", b'<script src="/app.js"></script>')
        self.write_source("app.js", b"fetch('/local');")
        subprocess.run(["git", "-C", str(self.repo), "add", "public"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "fixture"], check=True)
        self.commit = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True
        ).strip()
        subprocess.run(
            ["git", "-C", str(self.repo), "update-ref", "refs/remotes/origin/main", self.commit],
            check=True,
        )
        self.copy_source_to_build()
        self.manifest = self.root / "manifest.json"
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_source(self, rel, content):
        path = self.repo / "public" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def copy_source_to_build(self):
        (self.artifacts / "index.html").write_bytes((self.repo / "public/index.html").read_bytes())
        (self.artifacts / "app.js").write_bytes((self.repo / "public/app.js").read_bytes())

    def write_manifest(self, frame_paths=(), source_commit=None, wrong_pin=None):
        rows = []
        for path in sorted((self.repo / "public").rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.repo / "public").as_posix()
            body = path.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            if rel == wrong_pin:
                digest = "0" * 64
            rows.append({
                "path": rel,
                "kind": "bubble_frame" if rel in frame_paths else "asset",
                "size_bytes": len(body),
                "sha256": digest,
            })
        self.manifest.write_text(json.dumps({
            "schema": "preceptoros.lab.web-build-manifest/1",
            "source_commit": source_commit or self.commit,
            "files": rows,
        }), encoding="utf-8")

    def run_audit(self, max_file_bytes=4096, max_total_bytes=8192):
        return audit(
            web_repo=self.repo,
            artifact_root=self.artifacts,
            manifest_path=self.manifest,
            max_file_bytes=max_file_bytes,
            max_total_bytes=max_total_bytes,
        )

    def test_main_artifact_bytes_and_relative_assets_pass(self):
        receipt = self.run_audit()
        self.assertEqual(receipt["state"], GREEN)
        self.assertEqual(receipt["files_checked"], 2)
        self.assertEqual(receipt["external_reference_count"], 0)
        self.assertEqual(receipt["runtime_network"], "NO_DATA: static scan only")
        self.assertEqual(receipt["source_commit"], self.commit)

    def test_changed_build_byte_is_red(self):
        (self.artifacts / "app.js").write_bytes(b"fetch('/other');")
        self.assertEqual(self.run_audit()["state"], RED)

    def test_wrong_integrity_pin_is_red(self):
        self.write_manifest(wrong_pin="app.js")
        self.assertEqual(self.run_audit()["state"], RED)

    def test_missing_or_extra_artifact_is_red(self):
        (self.artifacts / "app.js").unlink()
        (self.artifacts / "extra.css").write_text("body{}", encoding="utf-8")
        receipt = self.run_audit()
        self.assertEqual(receipt["state"], RED)
        self.assertEqual((receipt["missing_count"], receipt["extra_count"]), (1, 1))

    def test_external_literal_is_red_without_network_access(self):
        self.write_source("external.js", b"fetch('https://outside.example/path');")
        subprocess.run(["git", "-C", str(self.repo), "add", "public"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "external fixture"], check=True)
        self.commit = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        subprocess.run(["git", "-C", str(self.repo), "update-ref", "refs/remotes/origin/main", self.commit], check=True)
        (self.artifacts / "external.js").write_bytes((self.repo / "public/external.js").read_bytes())
        self.write_manifest()
        receipt = self.run_audit()
        self.assertEqual(receipt["state"], RED)
        self.assertEqual(receipt["external_reference_count"], 1)

    def test_dynamic_network_target_is_no_data(self):
        self.write_source("app.js", b"fetch(endpoint);")
        subprocess.run(["git", "-C", str(self.repo), "add", "public"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "dynamic fixture"], check=True)
        self.commit = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        subprocess.run(["git", "-C", str(self.repo), "update-ref", "refs/remotes/origin/main", self.commit], check=True)
        (self.artifacts / "app.js").write_bytes((self.repo / "public/app.js").read_bytes())
        self.write_manifest()
        receipt = self.run_audit()
        self.assertEqual(receipt["state"], NO_DATA)
        self.assertIn("dynamic network target", receipt["cause"])

    def test_bubble_frame_ceiling_is_1024_bytes(self):
        body = b"{" + b" " * 1024 + b"}"
        self.write_source("frame.json", body)
        subprocess.run(["git", "-C", str(self.repo), "add", "public"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "large frame fixture"], check=True)
        self.commit = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        subprocess.run(["git", "-C", str(self.repo), "update-ref", "refs/remotes/origin/main", self.commit], check=True)
        (self.artifacts / "frame.json").write_bytes(body)
        self.write_manifest(frame_paths={"frame.json"})
        self.assertEqual(self.run_audit()["state"], RED)

    def test_total_build_ceiling_is_enforced(self):
        receipt = self.run_audit(max_file_bytes=4096, max_total_bytes=4)
        self.assertEqual(receipt["state"], RED)
        self.assertTrue(receipt["total_over_limit"])
        self.assertIn("total build byte ceiling", receipt["cause"])

    def test_manifest_on_wrong_main_is_no_data(self):
        self.write_manifest(source_commit="f" * 40)
        receipt = self.run_audit()
        self.assertEqual(receipt["state"], NO_DATA)
        self.assertIn("manifest source commit", receipt["cause"])


if __name__ == "__main__":
    unittest.main()
