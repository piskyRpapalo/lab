import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'ai-security-20261028'
spec = importlib.util.spec_from_file_location('security_judge', ROOT / 'judge.py')
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)


class SecurityJudgeTests(unittest.TestCase):
    def test_all_cases_accept_synthetic_criteria_and_refuse_traps(self):
        cases = judge.load_cases()
        for case in cases.values():
            with self.subTest(case=case['id']):
                answer = ' '.join(case['must_mention'])
                result = judge.judge(case, answer, case['expected_verdict'])
                self.assertEqual(result['result'], 'PASS')
                self.assertEqual(result, judge.judge(case, answer.upper(), case['expected_verdict']))
                poisoned = answer + ' ' + case['must_not_say'][0]
                self.assertIn('prohibited_phrase_present', judge.judge(case, poisoned, case['expected_verdict'])['causes'])
                self.assertIn('required_phrase_missing', judge.judge(case, '', case['expected_verdict'])['causes'])
                self.assertIn('verdict_mismatch', judge.judge(case, answer, 'WRONG')['causes'])
                self.assertNotIn(answer, json.dumps(result))

    def test_modified_case_and_deleted_file_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'cases', root / 'cases')
            shutil.copy(ROOT / 'manifest.json', root / 'manifest.json')
            case = root / 'cases' / '01.json'
            case.write_text(case.read_text() + ' ')
            with self.assertRaisesRegex(ValueError, 'corpus_hash_mismatch'):
                judge.load_cases(root)
            case.unlink()
            with self.assertRaisesRegex(ValueError, 'corpus_file_set_changed'):
                judge.load_cases(root)

    def test_missing_criterion_is_rejected_even_with_recomputed_hash(self):
        import hashlib
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'cases', root / 'cases')
            manifest = json.loads((ROOT / 'manifest.json').read_text())
            path = root / 'cases' / '01.json'
            case = json.loads(path.read_text())
            case['must_mention'] = []
            path.write_text(json.dumps(case))
            manifest['cases'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'invalid_criteria'):
                judge.load_cases(root)


if __name__ == '__main__':
    unittest.main()
