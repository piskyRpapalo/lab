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

    def test_lab_record_and_ci_contract_match_the_checked_in_workflow(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "pruebas.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("measured record", agents.lower())
        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn('python: ["3.10", "3.11", "3.12"]', workflow)
        self.assertIn("for pasada in 1 2", workflow)
        self.assertIn("python3 -m unittest discover -s tests", workflow)
        self.assertIn("python3 test_llms.py", workflow)
        self.assertIn("python3 bin/verify_llms_tree.py", workflow)
        self.assertIn("workflow results for the exact ref", agents.lower())
        self.assertIn("python3 -m unittest discover -s tests", agents)
        self.assertIn("python3 test_llms.py", agents)
        self.assertIn("python3 bin/verify_llms_tree.py", agents)
        self.assertNotIn("remote ci is not configured", agents.lower())


if __name__ == "__main__":
    unittest.main()
