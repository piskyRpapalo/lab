import unittest

from bin.faro_forensic import parse_evidence, NO_DATA, CLASSIFIED


def sha(char):
    return char * 64


class FaroForensic(unittest.TestCase):
    def setUp(self):
        self.routes = [f"/page-{i}.html" for i in range(1, 12)]
        a = ["=== GESTURE A ==="]
        c = ["=== GESTURE C ===", "RUN id=40110583184 head_sha=" + "a" * 40 + " status=completed conclusion=failure"]
        for i, route in enumerate(self.routes):
            local = sha("a")
            final = route
            chain = "-"
            if i == 1:
                local = sha("b")
            if i == 2:
                final = "/es/"
                chain = f"{route}>307>{final}"
            a.append(f"A_ROUTE route={route} main_sha256={sha('a')} local_sha256={local} status=200 final_path={final} redirects={chain}")
            c.append(f"CI_DISTINCT route={route} sha256={sha('c')}")
        self.text = "\n".join(a + [
            "=== GESTURE B ===",
            "B_SUMMARY source_sha=" + "a" * 40 + " compared=244 equal=244 changed=0 missing=0 network_errors=0",
        ] + c) + "\n"

    def test_classifies_stale_drift_and_redirect_with_hashes(self):
        receipt = parse_evidence(self.text)
        self.assertEqual(receipt["state"], CLASSIFIED)
        rows = {row["route"]: row for row in receipt["routes"]}
        self.assertEqual(len(rows), 11)
        self.assertEqual(rows[self.routes[0]]["classification"], "EDGE_STALE")
        self.assertEqual(rows[self.routes[1]]["classification"], "REAL_DRIFT")
        self.assertEqual(rows[self.routes[2]]["classification"], "REDIRECT_ARTIFACT")
        self.assertEqual(rows[self.routes[0]]["sha_in"], sha("a"))
        self.assertEqual(rows[self.routes[0]]["sha_out"], sha("a"))

    def test_missing_route_evidence_is_no_data(self):
        text = self.text.replace("CI_DISTINCT route=/page-11.html sha256=" + sha("c") + "\n", "")
        receipt = parse_evidence(text)
        self.assertEqual(receipt["state"], NO_DATA)
        missing = next(row for row in receipt["routes"] if row["route"] == "/page-11.html")
        self.assertEqual(missing["classification"], NO_DATA)
        self.assertIn("missing", missing["cause"])

    def test_truncated_summary_fails_closed(self):
        text = self.text.replace("B_SUMMARY source_sha=" + "a" * 40 + " compared=244 equal=244 changed=0 missing=0 network_errors=0\n", "B_SUMMARY source_sha=" + "a" * 40 + " compared=244 equal=244\n")
        receipt = parse_evidence(text)
        self.assertEqual(receipt["state"], NO_DATA)
        self.assertIn("summary", receipt["cause"])

    def test_bad_encoding_fails_closed(self):
        receipt = parse_evidence(self.text.encode("utf-8") + b"\xff")
        self.assertEqual(receipt["state"], NO_DATA)
        self.assertIn("UTF-8", receipt["cause"])

    def test_duplicate_route_is_no_data(self):
        duplicate = "A_ROUTE route=/page-1.html main_sha256=" + sha("a") + " local_sha256=" + sha("a") + " status=200 final_path=/page-1.html redirects=-\n"
        receipt = parse_evidence(self.text.replace("=== GESTURE B ===", duplicate + "=== GESTURE B ===", 1))
        self.assertEqual(receipt["state"], NO_DATA)
        self.assertIn("duplicate", receipt["cause"])

    def test_three_fetches_do_not_infer_the_other_eight(self):
        lines = []
        in_a = False
        seen = 0
        for line in self.text.splitlines():
            if line == "=== GESTURE A ===":
                in_a = True
                lines.append(line)
            elif line.startswith("=== GESTURE"):
                in_a = False
                lines.append(line)
            elif in_a and line.startswith("A_ROUTE "):
                seen += 1
                if seen <= 3:
                    lines.append(line)
            else:
                lines.append(line)
        receipt = parse_evidence("\n".join(lines))
        self.assertEqual(receipt["state"], NO_DATA)
        missing = next(row for row in receipt["routes"] if row["route"] == "/page-4.html")
        self.assertEqual(missing["classification"], NO_DATA)
        self.assertIn("fetch evidence missing", missing["cause"])

    def test_source_head_mismatch_blocks_edge_inference(self):
        text = self.text.replace("B_SUMMARY source_sha=" + "a" * 40,
                                 "B_SUMMARY source_sha=" + "b" * 40)
        receipt = parse_evidence(text)
        row = next(item for item in receipt["routes"] if item["route"] == "/page-1.html")
        self.assertEqual(row["classification"], NO_DATA)
        self.assertIn("head differs", row["cause"])

    def test_full_run_route_rows_can_supply_missing_local_fetches(self):
        route_lines = [line for line in self.text.splitlines() if line.startswith("A_ROUTE ")]
        ci_lines = [line for line in self.text.splitlines() if line.startswith("CI_DISTINCT ")]
        summary = next(line for line in self.text.splitlines() if line.startswith("B_SUMMARY "))
        lines = (["=== GESTURE A ===", *route_lines[:3], "=== GESTURE B ===", summary]
                 + [line.replace("A_ROUTE ", "B_ROUTE ", 1) for line in route_lines[3:]]
                 + ["=== GESTURE C ===",
                    "RUN id=40110583184 head_sha=" + "a" * 40 + " status=completed conclusion=failure",
                    *ci_lines])
        receipt = parse_evidence("\n".join(lines))
        self.assertEqual(receipt["state"], CLASSIFIED)
        self.assertEqual(len(receipt["routes"]), 11)

    def test_unhealthy_full_run_cannot_support_edge_stale(self):
        text = self.text.replace("equal=244 changed=0", "equal=243 changed=1")
        receipt = parse_evidence(text)
        row = next(item for item in receipt["routes"] if item["route"] == "/page-1.html")
        self.assertEqual(row["classification"], NO_DATA)
        self.assertIn("not byte-clean", row["cause"])

    def test_unrelated_ci_run_is_rejected(self):
        text = self.text.replace("RUN id=40110583184", "RUN id=40110583185")
        receipt = parse_evidence(text)
        self.assertEqual(receipt["state"], NO_DATA)
        self.assertIn("forensic target", receipt["cause"])


if __name__ == "__main__":
    unittest.main()
