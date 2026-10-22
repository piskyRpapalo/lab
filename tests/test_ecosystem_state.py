import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from bin.estado_ecosistema import ceiling_refs, overall_status, parse_pair, receipt, repo_state, route_state, scrub_file


class EcosystemStateTests(unittest.TestCase):
    def test_repo_pair_requires_label_and_path(self):
        self.assertEqual(parse_pair("web=/tmp/web"), ("web", Path("/tmp/web")))
        with self.assertRaises(ValueError):
            parse_pair("/tmp/web")

    def test_repo_state_reports_cached_main_divergence_without_paths(self):
        values = iter(["a" * 40, "2 3", ""])
        from unittest.mock import patch
        with patch("bin.estado_ecosistema.run_git", side_effect=lambda *a: next(values)):
            result = repo_state("web", Path("."))
        self.assertEqual((result["behind"], result["ahead"]), (2, 3))
        self.assertNotIn("path", result)

    def test_missing_checkout_is_no_data(self):
        result = repo_state("app", Path("/path/that/does/not/exist"))
        self.assertEqual(result["status"], "NO_DATA")

    def test_route_counter_output_is_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bin").mkdir()
            (root / "bin" / "contar_rutas.py").write_text(
                "print('shell_entries=191 shell_unique=190 shell_duplicates=1')\n",
                encoding="utf-8",
            )
            result = route_state(root)
        self.assertEqual(result["shell_entries"], 191)
        self.assertEqual(result["shell_duplicates"], 1)

    def test_route_document_mismatch_is_red(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bin").mkdir()
            (root / "bin" / "contar_rutas.py").write_text(
                "import sys\nprint('shell_entries=191 shell_unique=190 shell_duplicates=1')\n"
                "raise SystemExit('--check-doc' in sys.argv)\n",
                encoding="utf-8",
            )
            result = route_state(root, root / "DEPLOY.md")
        self.assertEqual(result["status"], "RED")
        self.assertEqual(result["document"], "MISMATCH")

    def test_ceiling_references_are_reported_by_relative_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "AGENTS.md").write_text("Piece 16,384 B; channel < 1,024 B.\n", encoding="utf-8")
            result = ceiling_refs("lab", root)
        self.assertEqual(result[0]["file"], "AGENTS.md")
        self.assertEqual(set(result[0]["values"]), {"16,384 B", "1,024 B"})

    def test_scrub_finds_sabotage_and_clean_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "clean.py").write_text("value = 1\n", encoding="utf-8")
            (root / "bad.py").write_text("token = 'probe'\n", encoding="utf-8")
            self.assertEqual(scrub_file("app", root, "bad.py")["status"], "RED")
            self.assertEqual(scrub_file("app", root, "clean.py")["status"], "GREEN")

    def test_receipt_is_hashed_and_below_channel_ceiling(self):
        args = Namespace(date="2026-10-22", machine="local", repo=[], web_root=None,
                         route_doc=None, scrub_file=[])
        import json
        result = receipt(args)
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.assertLess(len(encoded.encode("utf-8")), 1024)
        self.assertEqual(len(result["sha256"]), 64)

    def test_scrub_hit_makes_overall_verdict_red(self):
        self.assertEqual(overall_status([{"status": "MEASURED"}],
                                        {"status": "MEASURED"},
                                        [{"status": "RED", "hits": 1}]), "RED")

    def test_missing_scrub_evidence_is_no_data(self):
        self.assertEqual(overall_status([{"status": "MEASURED"}],
                                        {"status": "MEASURED"},
                                        [{"status": "NO_DATA"}]), "NO_DATA")


if __name__ == "__main__":
    unittest.main()
