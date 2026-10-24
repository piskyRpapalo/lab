import json
import unittest

from bin.record_lab_ci_run import consume, NO_DATA


class RemoteCIRun(unittest.TestCase):
    def test_successful_json_run_and_two_gate_passes(self):
        metadata = json.dumps({"databaseId": 42, "headSha": "0123456789abcdef0123456789abcdef01234567",
                              "status": "completed", "conclusion": "success"}, indent=2)
        text = metadata + '''
GATE unittest
Ran 147 tests in 1.2s
OK (skipped=1)
GATE test_llms
Ran 2 tests in 0.0s
OK
GATE verify_llms_tree
LIVE · 5 indexed paths resolve inside the physical tree
'''
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], "GREEN")
        self.assertEqual(result["run_id"], 42)
        self.assertEqual(result["head_sha"], "0123456789abcdef0123456789abcdef01234567")
        self.assertEqual(result["gates"][0]["tests_run"], 147)
        self.assertEqual({gate["name"] for gate in result["gates"]},
                         {"unittest", "test_llms", "verify_llms_tree"})

    def test_missing_log_is_no_data(self):
        result = consume("", expected_run_id=42)
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("absent", result["cause"])

    def test_unrelated_run_is_no_data(self):
        text = '{"databaseId":41,"headSha":"0123456789abcdef0123456789abcdef01234567","status":"completed","conclusion":"success"}\n'
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("does not match", result["cause"])

    def test_incomplete_gate_summary_is_no_data(self):
        text = '{"databaseId":42,"headSha":"0123456789abcdef0123456789abcdef01234567","status":"completed","conclusion":"success"}\nGATE unittest\nRan 147 tests in 1.2s\n'
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("incomplete", result["cause"])

    def test_cancelled_run_is_no_data_and_not_green(self):
        text = '{"databaseId":42,"headSha":"0123456789abcdef0123456789abcdef01234567","status":"completed","conclusion":"cancelled"}\n'
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], NO_DATA)
        self.assertEqual(result["status"], "cancelled")

    def test_in_flight_run_is_no_data(self):
        text = '{"databaseId":42,"headSha":"0123456789abcdef0123456789abcdef01234567","status":"in_progress","conclusion":null}\npartial log\n'
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("flight", result["cause"])

    def test_missing_gate_is_no_data(self):
        text = '{"databaseId":42,"headSha":"0123456789abcdef0123456789abcdef01234567","status":"completed","conclusion":"success"}\nGATE unittest\nRan 1 test in 0.1s\nOK\n'
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("incomplete", result["cause"])

    def test_tab_separated_job_log_tracks_both_workflow_passes(self):
        head = "0123456789abcdef0123456789abcdef01234567"
        lines = [f"RUN id=42 head_sha={head} status=completed conclusion=success"]
        for pass_no in (1, 2):
            lines.extend([
                f"python 3.11\tSuite completa n=2\tt0\ttanda {pass_no}/2",
                "python 3.11\tSuite completa n=2\tt1\tpython3 -m unittest discover -s tests",
                "python 3.11\tSuite completa n=2\tt2\tRan 147 tests in 1.2s",
                "python 3.11\tSuite completa n=2\tt3\tOK (skipped=1)",
                "python 3.11\tSuite completa n=2\tt4\tpython3 test_llms.py",
                "python 3.11\tSuite completa n=2\tt5\tRan 2 tests in 0.0s",
                "python 3.11\tSuite completa n=2\tt6\tOK",
                "python 3.11\tSuite completa n=2\tt7\tpython3 bin/verify_llms_tree.py",
                "python 3.11\tSuite completa n=2\tt8\tLIVE · 5 indexed paths",
            ])
        result = consume("\n".join(lines), expected_run_id=42)
        self.assertEqual(result["state"], "GREEN")
        self.assertEqual(len(result["gates"]), 6)
        self.assertEqual({gate["pass"] for gate in result["gates"]}, {1, 2})
        self.assertEqual(result["gates"][-1]["checks_observed"], 5)

    def test_failure_text_is_preserved_verbatim(self):
        failure = "AssertionError: expected 7, got 8"
        text = ('{"databaseId":42,"headSha":"0123456789abcdef0123456789abcdef01234567","status":"completed","conclusion":"failure"}\n'
                'GATE unittest\nFAIL: test_x (tests.Test)\n' + failure + '\nRan 1 test in 0.1s\nFAILED (failures=1)\n'
                'GATE test_llms\nRan 2 tests in 0.1s\nOK\n'
                'GATE verify_llms_tree\nLIVE · 5 indexed paths\n')
        result = consume(text, expected_run_id=42)
        self.assertEqual(result["state"], "RED")
        self.assertIn(failure, result["failures"][0]["verbatim"])

    def test_gh_run_view_three_column_log_format(self):
        head = "0123456789abcdef0123456789abcdef01234567"
        lines = [f"RUN id=42 head_sha={head} status=completed conclusion=success"]
        for pass_no in (1, 2):
            lines.extend([
                f"python 3.11\tSuite completa n=2\t2026-10-24T19:29:24Z tanda {pass_no}/2",
                "python 3.11\tSuite completa n=2\t2026-10-24T19:29:24Z Ran 221 tests in 3.7s",
                "python 3.11\tSuite completa n=2\t2026-10-24T19:29:24Z OK (skipped=1)",
                "python 3.11\tSuite completa n=2\t2026-10-24T19:29:25Z Ran 2 tests in 0.0s",
                "python 3.11\tSuite completa n=2\t2026-10-24T19:29:25Z OK",
                "python 3.11\tSuite completa n=2\t2026-10-24T19:29:26Z LIVE · 5 indexed paths",
            ])
        result = consume("\n".join(lines), expected_run_id=42)
        self.assertEqual(result["state"], "GREEN")
        self.assertEqual(len(result["gates"]), 6)
        self.assertEqual({g["job"] for g in result["gates"]}, {"python 3.11"})


if __name__ == "__main__":
    unittest.main()
