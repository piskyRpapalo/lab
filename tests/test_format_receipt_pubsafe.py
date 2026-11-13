#!/usr/bin/env python3
"""Publication-safety tests for bin/format_receipt.py.

Verifies that untrusted receipt fields cannot leak private paths,
credentials, machine identifiers, or other sensitive data into the
formatted public draft.

All fixtures are synthetic — no real credentials or private data.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FMT = ROOT / "bin" / "format_receipt.py"
sys.path.insert(0, str(ROOT / "bin"))
import format_receipt as fr


# ---------------------------------------------------------------------------
# Helper: base receipts with clean values
# ---------------------------------------------------------------------------

def _harness(**overrides):
    r = {
        "schema": "preceptoros.lab.harness-receipt/1",
        "suite": "tests",
        "verdict": "GREEN",
        "coverage": 10,
        "total": 10,
        "determinism": True,
        "weight_b": 4173,
        "speed_s": 4.438,
        "sha256": "abc123",
        "observed_at": "2026-10-20T00:00:00Z",
        "runtime": {"machine": "x86_64", "python": "3.12.15", "system": "Linux"},
    }
    r.update(overrides)
    return r


def _yardstick(**overrides):
    r = {
        "schema": "preceptoros.lab.yardstick-receipt/1",
        "state": "GREEN",
        "command": "python3 -m unittest discover -s tests",
        "observed_at": "2026-10-20T00:00:00Z",
        "runs": [{"state": "GREEN", "passed": 34, "tests": 34, "elapsed_s": 0.17}],
        "runtime": {"machine": "x86_64", "python": "3.12.15", "system": "Linux"},
    }
    r.update(overrides)
    return r


# ---------------------------------------------------------------------------
# Private filesystem paths must not appear in output
# ---------------------------------------------------------------------------

class TestPrivatePathLeak(unittest.TestCase):

    def test_ssh_path_in_machine_field(self):
        """Private SSH path in machine field must not reach output."""
        r = _harness(runtime={"machine": "/home/user/.ssh/id_rsa", "python": "3.12"})
        t = fr.format_harness_receipt(r)
        self.assertNotIn(".ssh", t)
        self.assertNotIn("id_rsa", t)

    def test_private_mesa_path_in_suite(self):
        """Private mesa path in suite field must not reach output."""
        r = _harness(suite="/home/user/private-mesa/notes.md")
        t = fr.format_harness_receipt(r)
        self.assertNotIn("private-mesa", t)

    def test_root_path_in_command(self):
        """Root path in yardstick command must not reach output."""
        r = _yardstick(command="cat /root/secret_key")
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("/root/", t)

    def test_etc_shadow_in_cause(self):
        """Sensitive system path in cause field must not reach output."""
        r = _yardstick(cause="read /etc/shadow for auth")
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("/etc/shadow", t)

    def test_config_path_in_verdict(self):
        """Config path in verdict field must not reach output."""
        r = _harness(verdict="/home/user/.config/secrets/token")
        t = fr.format_harness_receipt(r)
        self.assertNotIn(".config/", t)


# ---------------------------------------------------------------------------
# Credential-like strings must not appear in output
# ---------------------------------------------------------------------------

class TestCredentialLeak(unittest.TestCase):

    def test_password_in_cause(self):
        """Password-like value in cause must not reach output."""
        r = _yardstick(cause="password=synthetic_secret_123")
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("synthetic_secret_123", t)

    def test_api_key_in_command(self):
        """API key in command must not reach output."""
        r = _yardstick(command="curl -H 'Authorization: Bearer sk-synthetic-abc123'")
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("sk-synthetic-abc123", t)

    def test_token_in_sha_field(self):
        """Token-like value in sha256 must not reach output."""
        r = _harness(sha256="token_synthetic_abc123")
        t = fr.format_harness_receipt(r)
        self.assertNotIn("token_synthetic", t)

    def test_bearer_token_in_suite(self):
        """Bearer token in suite field must not reach output."""
        r = _harness(suite="Bearer eyJhbGciOiHSynthetic")
        t = fr.format_harness_receipt(r)
        self.assertNotIn("eyJhbGci", t)

    def test_api_key_in_state(self):
        """API key in state field must not reach output."""
        r = _yardstick(state="api_key=sk-live-synthetic")
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("sk-live-synthetic", t)


# ---------------------------------------------------------------------------
# Machine identifiers with private info
# ---------------------------------------------------------------------------

class TestMachineIdLeak(unittest.TestCase):

    def test_hostname_with_private_suffix(self):
        """Machine hostname containing private info must be sanitized."""
        r = _harness(runtime={"machine": "node-internal-secret-01", "python": "3.12"})
        t = fr.format_harness_receipt(r)
        # The raw private hostname should not appear verbatim
        self.assertNotIn("node-internal-secret-01", t)

    def test_ip_address_in_machine(self):
        """Private IP address in machine field must not reach output."""
        r = _yardstick(runtime={"machine": "192.168.1.100", "python": "3.12"})
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("192.168.1.100", t)


# ---------------------------------------------------------------------------
# Word limit enforcement
# ---------------------------------------------------------------------------

class TestWordLimit(unittest.TestCase):

    def test_long_cause_exceeds_word_limit(self):
        """Very long cause field should not produce output exceeding word ceiling."""
        long_cause = " ".join(["word"] * 300)
        r = _yardstick(cause=long_cause)
        t = fr.format_yardstick_receipt(r)
        words = len(t.split())
        self.assertLessEqual(words, fr.CEILING_WORDS * 2,
                             f"Output {words} words exceeds 2x ceiling")

    def test_long_suite_exceeds_word_limit(self):
        """Very long suite field should not produce oversized output."""
        long_suite = " ".join(["test"] * 300)
        r = _harness(suite=long_suite)
        t = fr.format_harness_receipt(r)
        words = len(t.split())
        self.assertLessEqual(words, fr.CEILING_WORDS * 2,
                             f"Output {words} words exceeds 2x ceiling")


# ---------------------------------------------------------------------------
# Missing evidence presented as success
# ---------------------------------------------------------------------------

class TestMissingEvidence(unittest.TestCase):

    def test_no_data_verdict_shows_no_data(self):
        """NO_DATA verdict must be visible, not hidden as success."""
        r = _harness(verdict="NO_DATA")
        t = fr.format_harness_receipt(r)
        self.assertIn("NO_DATA", t)

    def test_empty_state_shows_no_data(self):
        """Empty state must render as NO_DATA, not blank."""
        r = _yardstick(state="")
        t = fr.format_yardstick_receipt(r)
        self.assertIn("NO_DATA", t)


# ---------------------------------------------------------------------------
# Malformed JSON values
# ---------------------------------------------------------------------------

class TestMalformedValues(unittest.TestCase):

    def test_none_cause_does_not_crash(self):
        """None cause should not crash the formatter."""
        r = _yardstick(cause=None)
        t = fr.format_yardstick_receipt(r)
        self.assertIsInstance(t, str)

    def test_int_suite_does_not_crash(self):
        """Integer suite should not crash the formatter."""
        r = _harness(suite=42)
        t = fr.format_harness_receipt(r)
        self.assertIsInstance(t, str)

    def test_none_machine_does_not_crash(self):
        """None machine should not crash the formatter."""
        r = _harness(runtime={"machine": None, "python": "3.12"})
        t = fr.format_harness_receipt(r)
        self.assertIsInstance(t, str)


# ---------------------------------------------------------------------------
# Rejected values must not echo in output
# ---------------------------------------------------------------------------

class TestNoEchoOfRejected(unittest.TestCase):

    def test_rejected_password_not_in_output(self):
        """When a password is rejected, it must not appear in the output."""
        r = _yardstick(cause="my password is synthetic123")
        t = fr.format_yardstick_receipt(r)
        self.assertNotIn("synthetic123", t)
        self.assertNotIn("password", t.lower())

    def test_rejected_ssh_path_not_in_output(self):
        """When an SSH path is rejected, it must not appear in the output."""
        r = _harness(runtime={"machine": "/home/user/.ssh/known_hosts", "python": "3.12"})
        t = fr.format_harness_receipt(r)
        self.assertNotIn("known_hosts", t)


# ---------------------------------------------------------------------------
# Valid fixtures remain green
# ---------------------------------------------------------------------------

class TestValidFixturesGreen(unittest.TestCase):

    def test_normal_harness_still_works(self):
        """Clean harness receipt should format normally."""
        r = _harness()
        t = fr.format_harness_receipt(r)
        self.assertIn("GREEN", t)
        self.assertIn("10/10", t)
        self.assertIn("x86_64", t)
        self.assertIn("FIRMO", t)

    def test_normal_yardstick_still_works(self):
        """Clean yardstick receipt should format normally."""
        r = _yardstick()
        t = fr.format_yardstick_receipt(r)
        self.assertIn("GREEN", t)
        self.assertIn("34/34", t)
        self.assertIn("FIRMO", t)

    def test_word_count_under_ceiling(self):
        """Normal receipt should be under word ceiling."""
        r = _harness()
        t = fr.format_harness_receipt(r)
        self.assertLessEqual(len(t.split()), fr.CEILING_WORDS)


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCLIIntegration(unittest.TestCase):

    def test_cli_rejects_private_path(self):
        """CLI should not output private paths."""
        r = _harness(runtime={"machine": "/home/user/.ssh/id_rsa", "python": "3.12"})
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(r, f)
            path = f.name
        result = subprocess.run(
            [sys.executable, str(FMT), path],
            capture_output=True, text=True, cwd=ROOT
        )
        self.assertNotIn(".ssh", result.stdout)

    def test_cli_rejects_credential(self):
        """CLI should not output credential-like strings."""
        r = _yardstick(cause="api_key=sk-synthetic-abc123")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(r, f)
            path = f.name
        result = subprocess.run(
            [sys.executable, str(FMT), path],
            capture_output=True, text=True, cwd=ROOT
        )
        self.assertNotIn("sk-synthetic-abc123", result.stdout)


if __name__ == "__main__":
    unittest.main()
