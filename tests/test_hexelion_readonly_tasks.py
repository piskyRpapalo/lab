import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOPBACK = "http://127.0.0.1:8765/api/rack-map"
ALLOWED_KINDS = {"http", "local-files", "pure-function"}


def valid_contract(data):
    assert data["schema"] == "hexelion.task-contract/1"
    assert data["ground_truth_schema"] == "hexelion.ground-truth/1"
    tasks = data["tasks"]
    assert len(tasks) == 3
    assert len({task["id"] for task in tasks}) == 3
    for task in tasks:
        assert task["mode"] == "solo-read-only"
        assert task["action"]["kind"] in ALLOWED_KINDS
        assert task["writes"] == []
        assert task["judge"]["kind"] == "pure"
        assert task["failure"]["state"] == "NO_DATA"
        assert task["failure"]["cause"].strip()
        if "invalid" in task:
            assert task["invalid"]["state"] == "REJECTED"
            assert task["invalid"]["cause"].strip()
        assert task["sources"]
        for source in task["sources"]:
            pinned = source.get("blob_sha") or source.get("repo_head")
            assert pinned and len(pinned) == 40 and all(char in "0123456789abcdef" for char in pinned)
    nodecard = next(task for task in tasks if task["id"] == "read-local-nodecard")
    assert nodecard["action"]["method"] == "GET"
    assert nodecard["action"]["url"] == LOOPBACK
    assert nodecard["action"]["network_scope"] == "numeric-loopback-only"
    source_index = next(task for task in tasks if task["id"] == "lookup-pinned-source-index")
    assert source_index["action"]["network"] is False
    wake = next(task for task in tasks if task["id"] == "judge-wake-envelope-offline")
    assert wake["action"]["network"] is False
    assert wake["action"]["clock"] is False
    assert wake["judge"]["sending"] is False


class HexelionReadOnlyTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "contracts/hexelion-readonly-tasks.v1.json").read_text(encoding="utf-8"))

    def test_contract_and_three_candidates(self):
        valid_contract(self.data)

    def test_each_task_is_read_only_and_cited(self):
        for task in self.data["tasks"]:
            self.assertEqual(task["writes"], [])
            self.assertTrue(task["sources"])
            self.assertTrue(task["failure"]["cause"])

    def test_sabotage_write_verb_is_rejected(self):
        broken = json.loads(json.dumps(self.data))
        broken["tasks"][0]["action"]["method"] = "POST"
        with self.assertRaises(AssertionError):
            valid_contract(broken)

    def test_wake_candidate_never_sends(self):
        task = next(task for task in self.data["tasks"] if task["id"] == "judge-wake-envelope-offline")
        self.assertFalse(task["action"]["network"])
        self.assertFalse(task["judge"]["sending"])
        self.assertTrue(task["judge"]["never_echo_message"])


if __name__ == "__main__":
    unittest.main()
