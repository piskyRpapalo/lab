from pathlib import Path
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "benchmarks/README.md",
    "benchmarks/g0/README.md",
    "benchmarks/h9-readability-20261016/README.md",
    "benchmarks/bench-fluency/M1/README.md",
    "benchmarks/bench-fluency/M2/README.md",
    "benchmarks/bench-fluency/M3/README.md",
    "benchmarks/bench-fluency/M4/README.md",
]

class ArchiveContract(unittest.TestCase):
    def test_required_fiches_exist(self):
        missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
        self.assertEqual(missing, [])

    def test_evidence_hash_manifests(self):
        for rel in ("benchmarks/h9-readability-20261016/evidence", "benchmarks/bench-fluency/evidence"):
            evidence = ROOT / rel
            manifest = evidence / "SHA256SUMS"
            self.assertTrue(manifest.is_file())
            rows = manifest.read_text().splitlines()
            self.assertTrue(rows)
            for row in rows:
                digest, name = row.split("  ", 1)
                self.assertEqual(hashlib.sha256((evidence / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(len(list((ROOT / "benchmarks/bench-fluency/evidence").glob("*.jsonl"))), 19)

if __name__ == "__main__":
    unittest.main()
