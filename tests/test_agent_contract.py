from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AgentContract(unittest.TestCase):
    def test_claude_uses_agents_as_the_single_canonical_contract(self):
        claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", claude)
        self.assertIn("NO_DATA", agents)
        self.assertIn("origin/main", agents)

    def test_lab_record_and_ci_scope_are_explicit(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("measured record", agents.lower())
        self.assertIn("remote ci is not configured", agents.lower())


if __name__ == "__main__":
    unittest.main()
