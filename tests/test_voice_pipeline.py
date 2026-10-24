import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import voice_pipeline


def window(sound=True, reduced=False):
    return {
        "schema": "preceptoros.app.voice-window/1",
        "window_id": "window-1",
        "sound_enabled": sound,
        "reduced_motion": reduced,
        "inventory_complete": True,
        "inventory_source": "registered visible UI elements",
        "hardware_sound_available": True,
        "visible_count": 4,
        "visible_items": [
            {"id": "label", "kind": "label", "text": "Creation"},
            {"id": "state", "kind": "state", "text": "NO_DATA · sound disabled"},
            {"id": "narration", "kind": "narration", "text": "A measured result is ready."},
            {"id": "seal", "kind": "seal", "text": "Seal abjc"},
        ],
    }


class VoicePipelineTests(unittest.TestCase):
    def test_plan_names_every_visible_item_and_uses_fixed_priority(self):
        plan = voice_pipeline.plan(window())
        self.assertEqual([row["id"] for row in plan["queue"]], ["state", "seal", "narration", "label"])
        self.assertEqual(plan["visual_fallback"], [item["text"] for item in window()["visible_items"]])
        self.assertEqual(plan["status"], "READY")

    def test_step_receipts_are_ordered_and_content_addressed(self):
        plan = voice_pipeline.plan(window())
        first = voice_pipeline.advance(plan, None, "state", "completed")
        second = voice_pipeline.advance(plan, first, "seal", "completed")
        self.assertEqual([r["utterance_id"] for r in second["receipts"]], ["state", "seal"])
        self.assertEqual(second["receipts"][0]["text_sha256"], hashlib.sha256(b"NO_DATA \xc2\xb7 sound disabled").hexdigest())
        self.assertTrue(voice_pipeline.verify_receipt_chain(plan, second))

    def test_wrong_priority_order_is_rejected(self):
        plan = voice_pipeline.plan(window())
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.advance(plan, None, "seal", "completed")

    def test_dropped_utterance_cannot_advance(self):
        plan = voice_pipeline.plan(window())
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.advance(plan, None, "state", "dropped")

    def test_fake_or_changed_receipt_fails_verification(self):
        plan = voice_pipeline.plan(window())
        result = voice_pipeline.advance(plan, None, "state", "completed")
        result["receipts"][0]["text"] = "forged"
        self.assertFalse(voice_pipeline.verify_receipt_chain(plan, result))

    def test_sound_off_never_claims_spoken_and_keeps_full_visual_message(self):
        source = window(sound=False, reduced=True)
        plan = voice_pipeline.plan(source)
        self.assertEqual(plan["status"], "NO_DATA")
        self.assertEqual(plan["queue"], [])
        self.assertEqual(plan["visual_fallback"], [item["text"] for item in source["visible_items"]])
        self.assertIn("sound disabled", plan["cause"])
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.advance(plan, None, "state", "completed")
        forged = {"schema": "preceptoros.app.voice-receipts/1", "receipts": [],
                  "spoken_claim": True, "acoustic_output": "HEARD"}
        self.assertFalse(voice_pipeline.verify_receipt_chain(plan, forged))

    def test_reduced_motion_changes_motion_mode_not_message(self):
        normal = voice_pipeline.plan(window(reduced=False))
        reduced = voice_pipeline.plan(window(reduced=True))
        self.assertEqual(normal["visual_fallback"], reduced["visual_fallback"])
        self.assertEqual(reduced["motion_mode"], "static")

    def test_declared_visible_count_mismatch_is_rejected(self):
        source = window()
        source["visible_count"] = 99
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.plan(source)

    def test_unknown_sound_is_not_mislabeled_as_user_disabled(self):
        source = window()
        del source["sound_enabled"]
        plan = voice_pipeline.plan(source)
        self.assertEqual(plan["status"], "NO_DATA")
        self.assertEqual(plan["queue"], [])
        self.assertIn("unknown", plan["cause"])

    def test_malformed_receipt_and_window_inputs_fail_closed(self):
        plan = voice_pipeline.plan(window())
        self.assertFalse(voice_pipeline.verify_receipt_chain(plan, {"receipts": [None]}))
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.advance(plan, "not-an-object", "state", "completed")
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.advance(plan, {"receipts": None}, "state", "completed")
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.plan(None)

    def test_boolean_count_and_non_text_kind_are_rejected(self):
        source = window()
        source["visible_count"] = True
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.plan(source)
        source = window()
        source["visible_items"][0]["kind"] = []
        with self.assertRaises(voice_pipeline.PipelineError):
            voice_pipeline.plan(source)


    def test_unattested_visible_inventory_is_no_data_and_never_queued(self):
        source = window()
        source['inventory_complete'] = False
        plan = voice_pipeline.plan(source)
        self.assertEqual(plan['status'], 'NO_DATA')
        self.assertEqual(plan['queue'], [])
        self.assertIn('inventory', plan['cause'])
        self.assertEqual(len(plan['visual_fallback']), source['visible_count'])

    def test_hardware_sound_off_is_cause_bearing_no_data(self):
        source = window()
        source['hardware_sound_available'] = False
        plan = voice_pipeline.plan(source)
        self.assertEqual(plan['status'], 'NO_DATA')
        self.assertEqual(plan['queue'], [])
        self.assertIn('hardware', plan['cause'])

    def test_inventory_source_is_required(self):
        source = window()
        source.pop("inventory_source")
        plan = voice_pipeline.plan(source)
        self.assertEqual(plan['status'], 'NO_DATA')
        self.assertEqual(plan['queue'], [])

    def test_unknown_motion_preference_is_reported_not_guessed(self):
        source = window()
        del source["reduced_motion"]
        self.assertEqual(voice_pipeline.plan(source)["motion_mode"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
