"""Adversarial false-success judge tests.

Covers all 7 cases (A–G) with positive and negative scenarios.
Uses only synthetic data — no credentials, private logs, or personal data.
"""

import importlib.util
import pathlib
import unittest

_spec = importlib.util.spec_from_file_location(
    "judge_adversarial",
    pathlib.Path(__file__).parents[1] / "bin" / "judge_adversarial.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


# ---------------------------------------------------------------------------
# Case A — Unknown evidence
# ---------------------------------------------------------------------------

class CaseAUnknownEvidence(unittest.TestCase):

    def test_no_data_with_verified_interpretation_fails(self):
        """NO_DATA + VERIFIED interpretation = false positive."""
        r = _mod.case_a({"estado": "NO_DATA", "interpretation": "VERIFIED"})
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("false_positive", r["cause"])

    def test_no_data_with_valido_interpretation_fails(self):
        """NO_DATA + VALIDO interpretation = false positive."""
        r = _mod.case_a({"estado": "NO_DATA", "interpretation": "VALIDO"})
        self.assertEqual(r["state"], "FAIL")

    def test_no_data_with_tested_interpretation_fails(self):
        r = _mod.case_a({"estado": "NO_DATA", "interpretation": "TESTED"})
        self.assertEqual(r["state"], "FAIL")

    def test_no_data_with_live_service_interpretation_fails(self):
        r = _mod.case_a({"estado": "NO_DATA", "interpretation": "LIVE_SERVICE"})
        self.assertEqual(r["state"], "FAIL")

    def test_no_data_with_end_to_end_verified_interpretation_fails(self):
        r = _mod.case_a({"estado": "NO_DATA", "interpretation": "END_TO_END_VERIFIED"})
        self.assertEqual(r["state"], "FAIL")

    def test_no_data_with_evidence_passes(self):
        """NO_DATA + VERIFIED + independent evidence = acceptable."""
        r = _mod.case_a({
            "estado": "NO_DATA",
            "interpretation": "VERIFIED",
            "evidence": "independent_log_sha256_abc123",
        })
        self.assertEqual(r["state"], "PASS")

    def test_no_data_without_verified_claim_passes(self):
        """NO_DATA + no false claim = correct behavior."""
        r = _mod.case_a({"estado": "NO_DATA", "interpretation": "PENDING"})
        self.assertEqual(r["state"], "PASS")

    def test_no_data_empty_interpretation_passes(self):
        r = _mod.case_a({"estado": "NO_DATA"})
        self.assertEqual(r["state"], "PASS")

    def test_verified_estado_passes(self):
        """Non-NO_DATA estado is not a false-positive case."""
        r = _mod.case_a({"estado": "VERIFIED", "interpretation": "VERIFIED"})
        self.assertEqual(r["state"], "PASS")

    def test_empty_estado_with_verified_fails(self):
        """Empty estado treated as NO_DATA."""
        r = _mod.case_a({"estado": "", "interpretation": "VERIFIED"})
        self.assertEqual(r["state"], "FAIL")

    def test_non_dict_returns_no_data(self):
        r = _mod.case_a("not a dict")
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Case B — Wrong identity
# ---------------------------------------------------------------------------

class CaseBWrongIdentity(unittest.TestCase):

    def test_identity_mismatch_fails(self):
        """Receipt declares node B, external ID maps to node C."""
        r = _mod.case_b({
            "nodo": "node-B",
            "external_id": "key_hash_xyz",
            "id_registry": {"key_hash_xyz": "node-C"},
        })
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("identity_mismatch", r["cause"])

    def test_identity_match_passes(self):
        r = _mod.case_b({
            "nodo": "node-A",
            "external_id": "key_hash_abc",
            "id_registry": {"key_hash_abc": "node-A"},
        })
        self.assertEqual(r["state"], "PASS")

    def test_missing_nodo_fails(self):
        r = _mod.case_b({"external_id": "k", "id_registry": {"k": "x"}})
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("missing declared node", r["cause"])

    def test_missing_external_id_fails(self):
        r = _mod.case_b({"nodo": "A", "id_registry": {}})
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("missing external identifier", r["cause"])

    def test_external_id_not_in_registry_fails(self):
        r = _mod.case_b({
            "nodo": "A",
            "external_id": "unknown_key",
            "id_registry": {"other_key": "B"},
        })
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("not in registry", r["cause"])

    def test_non_dict_returns_no_data(self):
        r = _mod.case_b(42)
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Case C — Contradictory execution
# ---------------------------------------------------------------------------

class CaseCContradictoryExecution(unittest.TestCase):

    def test_ok_true_rc_nonzero_fails(self):
        """ok=true but rc=1 = contradictory."""
        r = _mod.case_c({"ok": True, "rc": 1})
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("contradictory_execution", r["cause"])

    def test_ok_true_rc_127_fails(self):
        r = _mod.case_c({"ok": True, "rc": 127})
        self.assertEqual(r["state"], "FAIL")

    def test_ok_false_rc_zero_fails(self):
        """ok=false but rc=0 = contradictory."""
        r = _mod.case_c({"ok": False, "rc": 0})
        self.assertEqual(r["state"], "FAIL")

    def test_ok_true_with_error_no_rc_fails(self):
        """ok=true with error message but no rc = soft contradiction."""
        r = _mod.case_c({"ok": True, "error": "command not found"})
        self.assertEqual(r["state"], "FAIL")

    def test_ok_true_rc_zero_passes(self):
        r = _mod.case_c({"ok": True, "rc": 0})
        self.assertEqual(r["state"], "PASS")

    def test_ok_false_rc_nonzero_passes(self):
        r = _mod.case_c({"ok": False, "rc": 1})
        self.assertEqual(r["state"], "PASS")

    def test_success_field_alias(self):
        """success field is an alias for ok."""
        r = _mod.case_c({"success": True, "exit_code": 2})
        self.assertEqual(r["state"], "FAIL")

    def test_string_ok_true(self):
        r = _mod.case_c({"ok": "true", "rc": 1})
        self.assertEqual(r["state"], "FAIL")

    def test_unparseable_rc_fails(self):
        r = _mod.case_c({"ok": True, "rc": "abc"})
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("unparseable", r["cause"])

    def test_non_dict_returns_no_data(self):
        r = _mod.case_c(None)
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Case D — Missing execution proof
# ---------------------------------------------------------------------------

class CaseDMissingProof(unittest.TestCase):

    def test_no_receipts_fails(self):
        r = _mod.case_d({"request_id": "req-001", "receipts": []})
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("no completion receipt", r["cause"])

    def test_no_receipts_key_fails(self):
        r = _mod.case_d({"request_id": "req-001"})
        self.assertEqual(r["state"], "FAIL")

    def test_valid_receipt_passes(self):
        r = _mod.case_d({
            "request_id": "req-001",
            "receipts": [{"request_id": "req-001", "estado": "VALIDO"}],
        })
        self.assertEqual(r["state"], "PASS")

    def test_verified_receipt_passes(self):
        r = _mod.case_d({
            "request_id": "req-001",
            "receipts": [{"request_id": "req-001", "status": "VERIFIED"}],
        })
        self.assertEqual(r["state"], "PASS")

    def test_completed_receipt_passes(self):
        r = _mod.case_d({
            "request_id": "req-001",
            "receipts": [{"id": "req-001", "estado": "COMPLETED"}],
        })
        self.assertEqual(r["state"], "PASS")

    def test_wrong_request_id_fails(self):
        r = _mod.case_d({
            "request_id": "req-001",
            "receipts": [{"request_id": "req-999", "estado": "VALIDO"}],
        })
        self.assertEqual(r["state"], "FAIL")

    def test_invalid_status_fails(self):
        r = _mod.case_d({
            "request_id": "req-001",
            "receipts": [{"request_id": "req-001", "estado": "FAILED"}],
        })
        self.assertEqual(r["state"], "FAIL")

    def test_receipt_not_required_passes(self):
        r = _mod.case_d({
            "request_id": "req-001",
            "receipts": [],
            "receipt_required": False,
        })
        self.assertEqual(r["state"], "PASS")

    def test_missing_request_id_fails(self):
        r = _mod.case_d({"receipts": []})
        self.assertEqual(r["state"], "FAIL")

    def test_non_dict_returns_no_data(self):
        r = _mod.case_d("string")
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Case E — Duplicate operation
# ---------------------------------------------------------------------------

class CaseEDuplicateOperation(unittest.TestCase):

    def test_duplicate_task_id_fails(self):
        r = _mod.case_e({
            "operations": [
                {"task_id": "task-1", "nodo": "A"},
                {"task_id": "task-1", "nodo": "A"},
            ],
        })
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("duplicate_operation", r["cause"])

    def test_unique_operations_pass(self):
        r = _mod.case_e({
            "operations": [
                {"task_id": "task-1", "nodo": "A"},
                {"task_id": "task-2", "nodo": "B"},
            ],
        })
        self.assertEqual(r["state"], "PASS")

    def test_single_operation_passes(self):
        r = _mod.case_e({"operations": [{"task_id": "task-1"}]})
        self.assertEqual(r["state"], "PASS")

    def test_empty_operations_passes(self):
        r = _mod.case_e({"operations": []})
        self.assertEqual(r["state"], "PASS")

    def test_three_with_one_dup_fails(self):
        r = _mod.case_e({
            "operations": [
                {"task_id": "a", "nodo": "X"},
                {"task_id": "b", "nodo": "Y"},
                {"task_id": "a", "nodo": "X"},
            ],
        })
        self.assertEqual(r["state"], "FAIL")

    def test_different_task_same_node_passes(self):
        """Same node, different tasks = not a duplicate."""
        r = _mod.case_e({
            "operations": [
                {"task_id": "t1", "nodo": "A"},
                {"task_id": "t2", "nodo": "A"},
            ],
        })
        self.assertEqual(r["state"], "PASS")

    def test_non_dict_returns_no_data(self):
        r = _mod.case_e(123)
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Case F — Privacy boundary
# ---------------------------------------------------------------------------

class CaseFPrivacyBoundary(unittest.TestCase):

    def test_ssh_path_leak_fails(self):
        r = _mod.case_f({
            "public_projection": {"log": "reading /home/user/.ssh/id_rsa"},
        })
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("privacy_leak", r["cause"])

    def test_password_field_leak_fails(self):
        r = _mod.case_f({
            "public_projection": {"password": "synthetic_secret_123"},
        })
        self.assertEqual(r["state"], "FAIL")

    def test_api_key_field_leak_fails(self):
        r = _mod.case_f({
            "public_projection": {"api_key": "sk-synthetic-abc"},
        })
        self.assertEqual(r["state"], "FAIL")

    def test_private_mesa_path_leak_fails(self):
        r = _mod.case_f({
            "public_projection": {"ref": "/home/user/private-mesa/notes.md"},
        })
        self.assertEqual(r["state"], "FAIL")

    def test_nested_leak_fails(self):
        r = _mod.case_f({
            "public_projection": {
                "data": {"nested": {"token": "synthetic_tok"}},
            },
        })
        self.assertEqual(r["state"], "FAIL")

    def test_list_leak_fails(self):
        r = _mod.case_f({
            "public_projection": {"items": ["/home/user/.ssh/known_hosts"]},
        })
        self.assertEqual(r["state"], "FAIL")

    def test_clean_projection_passes(self):
        r = _mod.case_f({
            "public_projection": {"title": "Benchmark", "score": 42},
        })
        self.assertEqual(r["state"], "PASS")

    def test_empty_projection_passes(self):
        r = _mod.case_f({"public_projection": {}})
        self.assertEqual(r["state"], "PASS")

    def test_non_dict_returns_no_data(self):
        r = _mod.case_f("not a dict")
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Case G — Receipt limits
# ---------------------------------------------------------------------------

class CaseGReceiptLimits(unittest.TestCase):

    def test_exceeds_limit_fails(self):
        r = _mod.case_g({
            "payload": "x" * 200,
            "declared_limit": 100,
        })
        self.assertEqual(r["state"], "FAIL")
        self.assertIn("size_exceeded", r["cause"])

    def test_within_limit_passes(self):
        r = _mod.case_g({
            "payload": "x" * 50,
            "declared_limit": 100,
        })
        self.assertEqual(r["state"], "PASS")

    def test_exact_limit_passes(self):
        r = _mod.case_g({
            "payload": "x" * 100,
            "declared_limit": 100,
        })
        self.assertEqual(r["state"], "PASS")

    def test_no_limit_passes(self):
        r = _mod.case_g({"payload": "anything"})
        self.assertEqual(r["state"], "PASS")

    def test_negative_limit_fails(self):
        r = _mod.case_g({"payload": "x", "declared_limit": -1})
        self.assertEqual(r["state"], "FAIL")

    def test_unparseable_limit_fails(self):
        r = _mod.case_g({"payload": "x", "declared_limit": "abc"})
        self.assertEqual(r["state"], "FAIL")

    def test_dict_payload_serialized(self):
        r = _mod.case_g({
            "payload": {"key": "value" * 50},
            "declared_limit": 10,
        })
        self.assertEqual(r["state"], "FAIL")

    def test_unicode_bytes(self):
        """Unicode characters count as their UTF-8 byte length."""
        r = _mod.case_g({
            "payload": "\u00e9" * 11,  # 2 bytes each = 22 bytes > 20 limit
            "declared_limit": 20,
        })
        self.assertEqual(r["state"], "FAIL")

    def test_non_dict_returns_no_data(self):
        r = _mod.case_g(True)
        self.assertEqual(r["state"], "NO_DATA")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

class TestDispatch(unittest.TestCase):

    def test_judge_dispatches_a(self):
        r = _mod.judge("A", {"estado": "NO_DATA", "interpretation": "VERIFIED"})
        self.assertEqual(r["state"], "FAIL")

    def test_judge_dispatches_g(self):
        r = _mod.judge("G", {"payload": "x" * 200, "declared_limit": 100})
        self.assertEqual(r["state"], "FAIL")

    def test_unknown_case_returns_no_data(self):
        r = _mod.judge("Z", {})
        self.assertEqual(r["state"], "NO_DATA")
        self.assertIn("unknown case", r["cause"])

    def test_case_id_case_insensitive(self):
        r = _mod.judge("a", {"estado": "NO_DATA", "interpretation": "VERIFIED"})
        self.assertEqual(r["state"], "FAIL")


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestReproducibility(unittest.TestCase):
    """Running the same judge twice must produce identical results."""

    def test_repeated_case_a(self):
        rec = {"estado": "NO_DATA", "interpretation": "VERIFIED"}
        self.assertEqual(_mod.case_a(rec), _mod.case_a(rec))

    def test_repeated_case_b(self):
        rec = {"nodo": "A", "external_id": "k", "id_registry": {"k": "B"}}
        self.assertEqual(_mod.case_b(rec), _mod.case_b(rec))

    def test_repeated_case_c(self):
        rec = {"ok": True, "rc": 1}
        self.assertEqual(_mod.case_c(rec), _mod.case_c(rec))

    def test_repeated_case_d(self):
        rec = {"request_id": "r1", "receipts": []}
        self.assertEqual(_mod.case_d(rec), _mod.case_d(rec))

    def test_repeated_case_e(self):
        rec = {"operations": [{"task_id": "t1"}, {"task_id": "t1"}]}
        self.assertEqual(_mod.case_e(rec), _mod.case_e(rec))

    def test_repeated_case_f(self):
        rec = {"public_projection": {"password": "synthetic"}}
        self.assertEqual(_mod.case_f(rec), _mod.case_f(rec))

    def test_repeated_case_g(self):
        rec = {"payload": "x" * 200, "declared_limit": 100}
        self.assertEqual(_mod.case_g(rec), _mod.case_g(rec))


if __name__ == "__main__":
    unittest.main()
