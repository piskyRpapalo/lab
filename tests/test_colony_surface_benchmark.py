import sys
import unittest
from pathlib import Path


BENCH = Path(__file__).resolve().parents[1] / "benchmarks" / "colony-surface-20261028"
sys.path.insert(0, str(BENCH))
import summarize


def run(intervals, heap=10_000_000):
    return {
        "device": "android",
        "surface": "app",
        "reduced_motion": "on",
        "frame_interval_ms": intervals,
        "fps_median": 50,
        "fps_p05": 20,
        "js_heap_start_bytes": heap,
        "js_heap_bytes_samples": [heap],
        "js_heap_end_bytes": heap,
        "process_memory_scope": "package aggregate PSS",
        "process_memory_kb_start": 300_000,
        "process_memory_kb_samples": [301_000],
        "process_memory_kb_end": 302_000,
        "transition_runs": 0,
        "clicks": 240,
        "viewport_css_px": [360, 692, 3],
        "response_status": 200,
    }


class ColonySurfaceBenchmarkTests(unittest.TestCase):
    def test_nearest_rank_p50_and_lower_tail_use_frame_reciprocals(self):
        result = summarize.summarize([run([10, 20, 40, 50])])[0]
        self.assertEqual(result["fps_median"], 25)
        self.assertEqual(result["fps_p05"], 20)

    def test_constant_rounded_js_heap_is_no_data(self):
        result = summarize.summarize([run([16.67])])[0]
        self.assertIsNone(result["js_heap_median_bytes"])
        self.assertIn("same rounded", result["js_heap_no_data_cause"])
        self.assertEqual(result["process_memory_median_kb"], 301_000)

    def test_single_endpoint_does_not_claim_whole_fleet_weakest(self):
        environment = {
            "network_census": {"online_network_peer_count": 7},
            "android": {"additional_usb_mobile_device_count_without_adb": 3},
        }
        summary = summarize.summarize([run([16.67])])
        weakest = summarize.weakest_endpoint(summary, environment)
        self.assertEqual(weakest["weakest_measured_endpoint"]["state"], "MEDIDO")
        self.assertEqual(weakest["weakest_measured_endpoint"]["aliases"], ["android"])
        self.assertEqual(weakest["whole_fleet_weakest"]["state"], "NO_DATA")
        self.assertIn("seven network peers", weakest["whole_fleet_weakest"]["cause"])


if __name__ == "__main__":
    unittest.main()
