import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'ai-security-20261028' / 'cases'
CATEGORIES = {'prompt-injection', 'indirect-injection-rag', 'agentic-security',
              'model-supply-chain', 'pii-sanitization', 'owasp-llm-top10', 'red-teaming'}


class CorpusContract(unittest.TestCase):
    def test_case_shapes_and_coverage(self):
        paths = sorted(ROOT.glob('*.json'))
        self.assertEqual(len(paths), 12)
        cases = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
        self.assertEqual(len({case['id'] for case in cases}), len(cases))
        self.assertEqual({case['category'] for case in cases}, CATEGORIES)
        self.assertEqual({case['expected_verdict'] for case in cases}, {'SAFE', 'NO_DATA'})
        for path, case in zip(paths, cases):
            with self.subTest(path=path.name):
                self.assertLess(path.stat().st_size, 16384)
                self.assertTrue(case['scenario'].strip())
                for field in ('must_mention', 'must_not_say'):
                    self.assertTrue(case[field])
                    self.assertTrue(all(isinstance(x, str) and x.strip() for x in case[field]))
                self.assertTrue(set(case['must_mention']).isdisjoint(case['must_not_say']))
                self.assertTrue(case['run'].startswith('NO_DATA:'))


if __name__ == '__main__':
    unittest.main()
