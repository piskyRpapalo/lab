"""Protect the pre-existing evidence; feature log may only append."""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
PRESERVED = [
    ('benchmarks/receipts/20261113-federated-node-b-models-1.json', 7889, '930286a7aed8b7eb8b5491d637ea4cd2b9f87b1e9b254b2a9038ab0209822115'),
    ('benchmarks/receipts/20261113-federated-node-b-models-2.json', 7908, 'd21fc12af187eb170f57bc9e1428720c7bb2631a962ba3700afd17f9fca0f5bf'),
    ('benchmarks/receipts/20261113-federated-node-b-models-3.json', 7177, 'ce064600e2dbaf11b01c42eb3abcfe29fdbe42d6c6ea3892697b844297d92ee0'),
    ('benchmarks/receipts/20261113-federated-node-b.json', 1678, 'd3dd63005f60b06026448b9fcba7a5da159607cca26305b2cfeac195abef379d'),
    ('benchmarks/receipts/20261113-federated-node-c-primary-models-1.json', 7661, '8ca64845f847e47807f781287f46954ae9a011401b85e5a655ae96a4943aec86'),
    ('benchmarks/receipts/20261113-federated-node-c-primary-models-2.json', 5291, '3c519bd4b3eeebadc6a364c771d3766a62ebe824b5e4c92766ca99dff388a449'),
    ('benchmarks/receipts/20261113-federated-node-c-primary.json', 1251, '237d1efa6a540249e023e5ce2129bbb8d44fb087b073302f31680db6a16e81c2'),
    ('benchmarks/receipts/20261113-federated-node-c-secondary-models-1.json', 1428, '9a0ebd37b51a679012fc4fb5698cfc4ea3c3baf014a861d47ecb8acc78d7cf96'),
    ('benchmarks/receipts/20261113-federated-node-c-secondary.json', 1421, 'ff258d6b43d5cee804e2eafbe4210f57e72a1598873c487ab5ef24d8035827ff'),
    ('benchmarks/receipts/20261113-federated-node-d-models-1.json', 4780, '48baeb486cdb0f7491b3da288d74a50901bdc4f0ed407e32c5b7cb9ad5cce22f'),
    ('benchmarks/receipts/20261113-federated-node-d.json', 1544, 'bf01a47b741559e9626c2f04b1bb15f4ac7f2c07d536cb4675d3adab1733e845'),
    ('benchmarks/receipts/20261113-federated-node-e-models-1.json', 799, '5cd3e81fe2b48bce3ca4af42e38db2f07ecba9b02e4287d58446a05f32167ef4'),
    ('benchmarks/receipts/20261113-federated-node-e.json', 1538, 'd951209bfef29f87fcc63bab8190cfea82ec295cd73c29ee6dd4d8db41985a06'),
    ('benchmarks/receipts/20261113-federated-summary.md', 10347, '4f42a5814af1b7fe493dc5db71c53aa108bab5c42fee4d998941a25456775d6b'),
    ('odd/tasks/federated-evidence-01.md', 6695, 'b0c1b936a63fce604f0198486ff687367d50bb30c07593e4785eafa79d81baf8'),
    ('tests/test_federated_evidence_receipts.py', 3657, 'ba60e444c76f6d8d4093249cfaf0c047f38a470a6f61c75f5759a5042856d110'),
]

class Preservation(unittest.TestCase):
    def test_original_bytes_are_preserved(self):
        for name, size, expected in PRESERVED:
            raw = (ROOT / name).read_bytes()
            if name == "odd/tasks/federated-evidence-01.md":
                raw = raw[:size]  # Append-only implementation log; original remains intact.
            self.assertEqual(len(raw), size, name)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected, name)

if __name__ == "__main__":
    unittest.main()
