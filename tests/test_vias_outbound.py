import unittest
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "VIAS.md"


class OutboundRouteProposalTests(unittest.TestCase):
    def test_four_routes_are_documented_as_unmeasured_proposals(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertLess(len(DOC.read_bytes()), 16_384)
        self.assertIn("## External publishing routes · proposal only", text)
        for label in ("LinkedIn", "Hugging Face", "Bluesky", "Mastodon"):
            self.assertIn(label, text)
        self.assertIn("NO_DATA", text)
        self.assertIn("no external calls were made by this proposal", text.lower())

    def test_human_review_and_export_limits_are_explicit(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "review before each send",
            "explicit human approval",
            "filter is not a privacy guarantee",
            "rejects host imports",
        ):
            self.assertIn(phrase, text)

    def test_authoritative_references_are_present(self):
        text = DOC.read_text(encoding="utf-8")
        for url in (
            "https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api",
            "https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api",
            "https://docs.bsky.app/docs/tutorials/creating-a-post",
            "https://docs.joinmastodon.org/methods/statuses/",
        ):
            self.assertIn(url, text)


if __name__ == "__main__":
    unittest.main()
