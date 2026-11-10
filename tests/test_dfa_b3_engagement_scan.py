"""DFA-B3 static signal probes: signals require review, not compliance verdicts."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "bin" / "dfa_b3_engagement_scan.py"
spec = importlib.util.spec_from_file_location("dfa_b3", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestDfaB3Static(unittest.TestCase):
    def rule(self, text, kind="html"):
        return [f["rule"] for f in m.scan_text(text, kind)["flags"]]

    def test_video_autoplay(self):
        self.assertIn("media_autoplay", self.rule("<video autoplay></video>"))

    def test_audio_autoplay_upper(self):
        self.assertIn("media_autoplay", self.rule("<AUDIO AUTOPLAY='false'></AUDIO>"))

    def test_multiline_autoplay(self):
        self.assertIn("media_autoplay", self.rule("<video\ncontrols\nautoplay>"))

    def test_not_autoplay_data_attr(self):
        self.assertNotIn("media_autoplay", self.rule("<video data-autoplay='1'>"))

    def test_video_without_autoplay(self):
        self.assertEqual(self.rule("<video controls></video>"), [])

    def test_source_with_both_media_types(self):
        self.assertEqual(self.rule("<video autoplay><audio autoplay>").count("media_autoplay"), 2)

    def test_notification_permission(self):
        self.assertIn("notification_permission_call", self.rule("Notification.requestPermission()", "js"))

    def test_window_notification_permission(self):
        self.assertIn("notification_permission_call", self.rule("window.Notification . requestPermission ()", "js"))

    def test_notification_constructor(self):
        self.assertIn("notification_constructor", self.rule("new Notification('sample')", "js"))

    def test_reward_for_hover(self):
        self.assertIn("passive_reward_hook", self.rule("rewardForHover()", "js"))

    def test_reward_for_scroll(self):
        self.assertIn("passive_reward_hook", self.rule("rewardForScroll()", "js"))

    def test_reward_for_watch(self):
        self.assertIn("passive_reward_hook", self.rule("rewardForWatch()", "js"))

    def test_reward_for_dwell(self):
        self.assertIn("passive_reward_hook", self.rule("rewardForDwell()", "js"))

    def test_mjs_support(self):
        self.assertIn("notification_constructor", self.rule("new Notification('a')", "mjs"))

    def test_no_unsupported_type(self):
        with self.assertRaises(ValueError):
            m.scan_text("hi", "py")

    def test_no_empty_source_is_pass(self):
        r = m.scan_text("", "html")
        self.assertEqual(r["state"], "NO_DATA")
        self.assertIsNone(r["engagement_restraint_score"])

    def test_detected_source_requires_review(self):
        self.assertEqual(m.scan_text("<video autoplay>", "html")["state"], "REVIEW_REQUIRED")

    def test_no_name_or_source_content_output(self):
        r = m.scan_text("rewardForDwell('private-value')", "js")
        self.assertNotIn("private-value", str(r))

    def test_line_number(self):
        r = m.scan_text("// text\n\nnew Notification('x');", "js")
        self.assertEqual(r["flags"][0]["line"], 3)

    def test_findings_over_ceiling(self):
        s = "\n".join("new Notification('x')" for _ in range(201))
        self.assertEqual(m.scan_text(s, "js")["state"], "NO_DATA")

    def test_oversized_source(self):
        with self.assertRaises(ValueError):
            m.scan_text("a" * 131073, "js")

    def test_order_deterministic(self):
        src = "<video autoplay>\nNotification.requestPermission()"
        self.assertEqual(m.scan_text(src, "html"), m.scan_text(src, "html"))


if __name__ == "__main__":
    unittest.main()
