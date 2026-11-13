import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "benchmarks/receipts/20261112-receipt-extraction-qwen25vl-local.json"
CARD = RECEIPT.with_suffix(".md")


class TestLocalReceiptExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.card = CARD.read_text(encoding="utf-8")

    def test_overall_is_the_sum_of_the_fields(self):
        fields = self.r["results"]["fields"].values()
        overall = self.r["results"]["overall"]
        self.assertEqual(sum(f["correct"] for f in fields), overall["correct"])
        self.assertEqual(sum(f["scored"] for f in fields), overall["scored"])
        self.assertEqual(round(100 * overall["correct"] / overall["scored"], 1), overall["accuracy_pct"])

    def test_counts_are_honest(self):
        res = self.r["results"]
        self.assertEqual(res["n_receipts"] + res["n_errored"] + res["n_missing"], 26)
        self.assertLessEqual(res["receipts_fully_correct"]["count"], res["receipts_fully_correct"]["n"])
        self.assertEqual(res["review_gate"]["wrong_reads"],
                         res["receipts_fully_correct"]["n"] - res["receipts_fully_correct"]["count"])

    def test_repeat_is_not_conflated_with_this_run(self):
        rep = self.r["repeatability"]
        self.assertEqual(self.r["results"]["receipts_fully_correct"]["count"]
                         - rep["previous"]["receipts_fully_correct"],
                         rep["receipts_fixed"] - rep["receipts_broken"])
        self.assertTrue(rep["cause_of_earlier_rise"].startswith("NO_DATA"))

    def test_card_quotes_the_receipt(self):
        pct = f'{self.r["results"]["overall"]["accuracy_pct"]}%'
        self.assertIn(f"figure={pct}", self.card)
        self.assertIn(self.r["sha256"]["result_file_at_result_commit"], self.card)
        self.assertIn(self.r["source"]["result_commit"][:7], self.card)
        self.assertNotEqual(self.r["source"]["result_commit"], self.r["sha256"]["result_file_at_result_commit"])

    def test_declared_limits(self):
        for key in ("held_out_test_set", "power", "thermal_control", "independent_replication"):
            self.assertTrue(self.r[key].startswith("NO_DATA"), key)
        self.assertTrue(self.r["not_a_general_vision_benchmark"])
        self.assertEqual(self.r["reporting"], "contributor-reported")
        self.assertTrue(self.r["reference"]["labels_independently_checked"].startswith("NO_DATA"))
        self.assertTrue(self.r["external_reproduction"].startswith("NO_DATA"))
        self.assertTrue(self.r["source"]["human_signoff"].startswith("NO_DATA"))

    def test_scrubbed(self):
        for text in (RECEIPT.read_text(encoding="utf-8"), self.card):
            for forbidden in ("C:\\", "/home/", "/Users/", ".jpg", ".png", "127.0.0.1",
                              "localhost", "api_key", "sk-", "prompt_text", "model_response"):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
