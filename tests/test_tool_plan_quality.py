"""Directed, synthetic tests for offline plan-quality diagnostics.

These tests do not measure language understanding, cryptographic grants,
MCP execution, C2C, inference, LoRA training or the live rack.
"""
import copy
import json
import unittest
from dataclasses import replace

from meta_harness.delegation import encode, sha
from meta_harness.tool_plan_quality import (
    HostPolicy, MAX_TASKS, review, views,
)

NODE_A = sha("synthetic-node-a")
NODE_B = sha("synthetic-node-b")
NODE_C = sha("synthetic-node-c")
TOOL_R = sha("synthetic-read-only-capability")
TOOL_W = sha("synthetic-write-capability")


def policy(*, eligible=None):
    return HostPolicy(
        task_ref=sha("host-origin-request"), source_ref=sha("host-source"),
        tool_scope_ref=sha("host-owned-tool-scope"),
        model_ref=sha("host-model"), base_ref=sha("host-base"),
        head_ref=sha("host-head"), generation=2, permission_epoch=7,
        eligible=((NODE_A, TOOL_R), (NODE_B, TOOL_R))
        if eligible is None else eligible,
    )


def proposed(*pairs):
    return json.dumps(
        {"tasks": [{"node_ref": n, "tool_ref": t} for n, t in pairs]},
        sort_keys=True, separators=(",", ":"),
    )


def tested(*pairs, p=None, witness=None):
    return review(policy() if p is None else p, proposed(*pairs),
                  verify_policy=(lambda _: True) if witness is None else witness)


class ToolPlanQualityTests(unittest.TestCase):
    def test_exact_two_operations_not_execution(self):
        r = tested((NODE_A, TOOL_R), (NODE_B, TOOL_R))
        self.assertEqual(r["state"], "EXACT")
        self.assertEqual((r["expected_count"], r["selected_count"]), (2, 2))
        self.assertEqual((r["missing_count"], r["out_of_scope_count"]), (0, 0))
        self.assertFalse(r["execution_authorized"])
        self.assertFalse(r["kv_reuse_authorized"])
        self.assertFalse(r["training_authorized"])
        self.assertLess(len(encode(r)), 1024)

    def test_deterministic_replay_and_order_independence(self):
        x = tested((NODE_A, TOOL_R), (NODE_B, TOOL_R))
        y = tested((NODE_A, TOOL_R), (NODE_B, TOOL_R))
        z = tested((NODE_B, TOOL_R), (NODE_A, TOOL_R))
        self.assertEqual(x, y)
        self.assertEqual(x["state"], z["state"])
        self.assertEqual(x["policy_ref"], z["policy_ref"])

    def test_missing_authorized_operations_is_not_success(self):
        r = tested((NODE_A, TOOL_R))
        self.assertEqual(r["state"], "REVIEW_REQUIRED")
        self.assertEqual(r["cause"], "authorized_targets_omitted")
        self.assertEqual(r["missing_count"], 1)
        self.assertFalse(r["execution_authorized"])

    def test_model_abstention_with_authorized_work_is_not_success(self):
        r = tested()
        self.assertEqual(r["missing_count"], 2)
        self.assertEqual(r["state"], "REVIEW_REQUIRED")

    def test_abstention_when_nothing_eligible_is_exact(self):
        r = tested(p=policy(eligible=()))
        self.assertEqual(r["state"], "EXACT")
        self.assertEqual(r["expected_count"], 0)
        self.assertFalse(r["execution_authorized"])

    def test_extra_and_unauthorized_tool_rejected(self):
        for pairs in (
            ((NODE_A, TOOL_R), (NODE_B, TOOL_R), (NODE_C, TOOL_R)),
            ((NODE_A, TOOL_R), (NODE_B, TOOL_W)),
            ((NODE_C, TOOL_W),),
        ):
            with self.subTest(pairs=pairs):
                r = tested(*pairs)
                self.assertEqual(r["state"], "REJECTED")
                self.assertGreater(r["out_of_scope_count"], 0)

    def test_duplicates_cannot_be_execution_authority(self):
        r = tested((NODE_A, TOOL_R), (NODE_A, TOOL_R), (NODE_B, TOOL_R))
        self.assertEqual(r["state"], "REJECTED")
        self.assertEqual(r["duplicate_count"], 1)
        self.assertEqual(r["selected_count"], 3)

    def test_duplicate_and_extra_reported_separately(self):
        r = tested((NODE_A, TOOL_R), (NODE_C, TOOL_W), (NODE_C, TOOL_W))
        self.assertEqual(r["state"], "REJECTED")
        self.assertEqual((r["duplicate_count"], r["out_of_scope_count"]), (1, 1))

    def test_unwitnessed_source_fails_closed(self):
        result = tested((NODE_A, TOOL_R), witness=lambda _: False)
        self.assertEqual(result["state"], "NO_DATA")
        self.assertEqual(result["cause"], "host_policy_not_witnessed")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(review(policy(), proposed(), verify_policy=None)["cause"],
                         "host_witness_missing")

    def test_source_revoked_during_model_selection_fails_closed(self):
        seen = {"count": 0}
        def witness(_):
            seen["count"] += 1
            return seen["count"] == 1
        r = tested((NODE_A, TOOL_R), (NODE_B, TOOL_R), witness=witness)
        self.assertEqual(r["state"], "NO_DATA")
        self.assertEqual(r["cause"], "host_policy_changed")
        self.assertEqual(seen["count"], 2)

    def test_witness_exception_does_not_leak_source(self):
        def witness(_):
            raise RuntimeError("private user path /owner/private")
        r = tested((NODE_A, TOOL_R), witness=witness)
        self.assertEqual(r["state"], "NO_DATA")
        self.assertNotIn("private", json.dumps(r))

    def test_policy_pins_change_receipt(self):
        base = policy()
        raw = proposed((NODE_A, TOOL_R), (NODE_B, TOOL_R))
        refs = [
            review(replace(base, head_ref=sha("new-head")), raw,
                   verify_policy=lambda _: True),
            review(replace(base, generation=3), raw,
                   verify_policy=lambda _: True),
            review(replace(base, permission_epoch=8), raw,
                   verify_policy=lambda _: True),
            review(replace(base, tool_scope_ref=sha("new-scope")), raw,
                   verify_policy=lambda _: True),
        ]
        old = review(base, raw, verify_policy=lambda _: True)
        self.assertEqual(len({old["policy_ref"]} | {r["policy_ref"] for r in refs}), 5)
        self.assertTrue(all(x["state"] == "EXACT" for x in refs))
        # Same model answer cannot authorize a new head or grant epoch.
        self.assertTrue(all(not x["execution_authorized"] for x in refs))

    def test_invalid_host_policy_fails(self):
        changes = (
            {"permission_epoch": True},
            {"generation": -1},
            {"head_ref": "not-a-hash"},
            {"model_ref": "not-a-hash"},
            {"eligible": ((NODE_A, TOOL_R), (NODE_A, TOOL_R))},
            {"eligible": ((NODE_A, "not-a-hash"),)},
            {"eligible": ((NODE_A, TOOL_R),) * (MAX_TASKS+1)},
        )
        for change in changes:
            with self.subTest(change=change):
                r = review(replace(policy(), **change), proposed(),
                           verify_policy=lambda _: True)
                self.assertEqual(r["cause"], "host_policy_invalid")

    def test_malformed_or_untrusted_json_is_rejected(self):
        samples = (
            '{"tasks":[], "tasks":[]}',
            '{"tasks":[{"node_ref":"not-hex","tool_ref":"bad"}]}',
            '{"tasks":[], "grant":true}',
            '{"tasks":{}}',
            '{"tasks":[{"node_ref":"%s","tool_ref":"%s","command":"rm"}]}'
            % (NODE_A, TOOL_R),
            '{"tasks":[]} trailing',
            '{"tasks":[NaN]}',
            '{"tasks":[]}' + (" " * 4100),
        )
        for input_text in samples:
            with self.subTest(input_text=input_text[:70]):
                r = review(policy(), input_text, verify_policy=lambda _: True)
                self.assertEqual(r["state"], "NO_DATA")
                self.assertEqual(r["cause"], "model_proposal_invalid")
        self.assertEqual(review(policy(), None, verify_policy=lambda _: True)["state"],
                         "NO_DATA")

    def test_more_than_eight_tasks_is_invalid(self):
        p = proposed(*((sha("extra-%d" % i), TOOL_R) for i in range(9)))
        r = review(policy(), p, verify_policy=lambda _: True)
        self.assertEqual(r["cause"], "model_proposal_invalid")

    def test_views_text_speech_machine_share_state(self):
        r = tested((NODE_A, TOOL_R))
        w = views(r)
        self.assertEqual(w["text"], w["speech"])
        self.assertEqual(w["text"]["state_ref"], w["machine"]["state_ref"])
        self.assertEqual(w["text"]["summary"], w["machine"]["summary"])
        self.assertNotIn(NODE_A, json.dumps(w))
        modified = copy.deepcopy(r)
        modified["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "quality_receipt_invalid"):
            views(modified)
        modified = copy.deepcopy(r)
        modified["extra_authority"] = "signature"
        modified["receipt_ref"] = sha({k: v for k, v in modified.items()
                                       if k != "receipt_ref"})
        with self.assertRaisesRegex(ValueError, "quality_receipt_invalid"):
            views(modified)

    def test_no_raw_user_request_or_unsafe_tool_in_receipt(self):
        input_text = proposed((NODE_C, TOOL_W))
        r = review(policy(), input_text, verify_policy=lambda _: True)
        data = json.dumps(r, sort_keys=True)
        self.assertNotIn(NODE_C, data)
        self.assertNotIn(TOOL_W, data)
        self.assertNotIn(input_text, data)
        self.assertEqual(r["source_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
