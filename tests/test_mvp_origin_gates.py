import subprocess
import tempfile
import unittest
from pathlib import Path

from bin.run_mvp_origin_gates import NETWORK, run


PASS_LOG = """
one window: no page scroll; PASS
basic (quiet): 4 shared frames < 1,024 B; contrast fg/bg 15.80, accent 9.91; PASS
atlantis (zones): 4 shared frames < 1,024 B; contrast fg/bg 18.27, accent 9.61; PASS
zombie (terminal): 4 shared frames < 1,024 B; contrast fg/bg 15.11, accent 11.93; PASS
4 reachable states; worst frame 900 UTF-8 bytes of 1,024; PASS
app parity: face files byte-identical; PASS
"""


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class OriginGateTests(unittest.TestCase):
    def _repo(self, root, files):
        root.mkdir(parents=True)
        git(root, "init", "-q")
        git(root, "config", "user.name", "Fixture")
        git(root, "config", "user.email", "fixture@example.invalid")
        for name, body in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "static source")
        ref = "refs/remotes/origin/candidate"
        git(root, "update-ref", ref, "HEAD")
        return ref

    def _pair(self, tmp, log=PASS_LOG):
        web, app = Path(tmp) / "web", Path(tmp) / "app"
        wr = self._repo(web, {
            "docs/rebuild/examples/validate.mjs": f"console.log({log!r});\n",
            "docs/rebuild/examples/face.css": "html,body{height:100%;overflow:hidden}.face{height:100dvh;overflow:hidden}",
            "docs/rebuild/examples/tools/face.tpl.html": '<p role="status" aria-live="polite"></p>',
            "public/game/map_zoom.js": "var MIN = 0.6, MAX = 3; function f(v){return Math.max(MIN, Math.min(MAX, v));}",
        })
        ar = self._repo(app, {"interface/face/basic.html": "<main>fixture</main>"})
        return web, wr, app, ar

    def test_origin_refs_measure_static_gates_and_name_dynamic_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self._pair(tmp)
            result = run(web, wr, app, ar)
            expected_head = git(web, "rev-parse", wr)
        self.assertEqual(result["refs"]["web"]["head"], expected_head)
        self.assertEqual(result["gates"]["contrast_pairs"]["verdict"], "GREEN")
        self.assertEqual(result["gates"]["byte_budget_post_export"]["pre_export_model"], "GREEN")
        self.assertEqual(result["gates"]["byte_budget_post_export"]["maximum_generated_frame_utf8_bytes"], 900)
        self.assertEqual(result["gates"]["zoom_bounds"]["static_bounds"], "GREEN")
        self.assertEqual(result["gates"]["narration_viewports"]["verdict"], "NO_DATA")
        self.assertEqual(result["gates"]["task_level_parity"]["verdict"], "NO_DATA")
        self.assertEqual(result["verdict"], "NO_DATA")
        self.assertFalse(result["network_used"])
        self.assertTrue(result["read_only"])

    def test_contrast_sabotage_red_then_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self._pair(tmp, PASS_LOG.replace("15.80, accent 9.91", "9.00, accent 9.91"))
            red = run(web, wr, app, ar)
            self.assertEqual(red["gates"]["contrast_pairs"]["verdict"], "RED")
            validator = web / "docs/rebuild/examples/validate.mjs"
            validator.write_text(f"console.log({PASS_LOG!r});\n", encoding="utf-8")
            git(web, "add", "docs/rebuild/examples/validate.mjs")
            git(web, "commit", "-qm", "restore measured contrast")
            git(web, "update-ref", wr, "HEAD")
            green = run(web, wr, app, ar)
        self.assertEqual(green["gates"]["contrast_pairs"]["verdict"], "GREEN")

    def test_non_origin_ref_is_rejected(self):
        with self.assertRaises(ValueError):
            run(Path("/no/repo"), "refs/heads/main", Path("/no/repo"),
                "refs/remotes/origin/candidate")

    def test_network_detector_covers_fetch_and_node_modules(self):
        self.assertTrue(NETWORK.search("fetch('https://example.invalid')"))
        self.assertTrue(NETWORK.search("import x from 'node:https'"))

    def test_network_dependency_is_refused_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            web, wr, app, ar = self._pair(tmp)
            (web / "docs/rebuild/examples/face_world.js").write_text(
                "function external(){ return fetch('https://example.invalid'); }", encoding="utf-8")
            (web / "docs/rebuild/examples/validate.mjs").write_text(
                "import './face_world.js';\nconsole.log('should not run');\n", encoding="utf-8")
            git(web, "add", "docs/rebuild/examples")
            git(web, "commit", "-qm", "network sabotage")
            git(web, "update-ref", wr, "HEAD")
            result = run(web, wr, app, ar)
        self.assertIn("network API; execution refused", result["validator"]["cause"])
        self.assertIsNone(result["validator"]["exit_code"])


if __name__ == "__main__":
    unittest.main()
