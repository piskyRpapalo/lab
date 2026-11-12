import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

BIN = Path(__file__).resolve().parents[1] / 'bin'
sys.path.insert(0, str(BIN))
spec = importlib.util.spec_from_file_location('dual', BIN / 'check_dual_judge_evidence.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.serial = 0

    def save(self, obj):
        self.serial += 1
        raw = m.encode(obj)
        name = str(self.serial) + '.json'
        (self.root / name).write_bytes(raw)
        return dict(path=name, sha256=m.digest(raw))

    def record(self, case='a', termination='stop', family='phi', duplicated=False):
        members = [dict(model='qwen-model', family='qwen'),
                   dict(model='phi-model', family=family), dict(model='mistral-model', family='mistral')]
        items = []
        for i, member in enumerate(members):
            prov = self.save(dict(member=member, model_sha256=hex(i+10)[2:]*64))
            items.append(dict(case=case, **{'pass': 1}, member=member, model_sha256=hex(i+10)[2:]*64,
                              provenance=prov, termination='stop'))
        items[0]['termination'] = termination
        response = self.save(items[0])
        judges = [self.save(dict(x, response_sha256=response['sha256'], verdict='SAFE')) for x in items[1:]]
        return dict(case=case, **{'pass': 1}, response=response, judges=[judges[0]]*2 if duplicated else judges)

    def check(self, records):
        return m.check(dict(schema=m.SCHEMA, cases_per_class=60, held_out=True, records=records), self.root)

    def test_positive(self):
        r = self.check([self.record()])
        self.assertEqual(r['counts']['admissible'], 1)
        self.assertIn('NO_DATA', r['independence'])
        self.assertLess(len(m.encode(r))+1, 1024)

    def test_hash_sabotage(self):
        r = self.record()
        r['response']['sha256'] = 'b'*64
        self.assertEqual(self.check([r])['counts']['unknown'], 1)

    def test_duplicate_judge(self):
        self.assertEqual(self.check([self.record(duplicated=True)])['counts']['rejected'], 1)

    def test_same_family(self):
        self.assertEqual(self.check([self.record(family='qwen')])['counts']['rejected'], 1)

    def test_unknown_termination(self):
        self.assertEqual(self.check([self.record(termination='unknown')])['counts']['unknown'], 1)

    def test_missing_reference(self):
        row = self.record()
        (self.root / row['judges'][0]['path']).unlink()
        self.assertEqual(self.check([row])['counts']['unknown'], 1)

    def test_300_repeated(self):
        rows = [self.record(str(i), 'length' if i < 276 else 'stop') for i in range(300)]
        a, b = self.check(rows), self.check(rows)
        self.assertEqual(a, b)
        self.assertEqual(a['counts'], dict(admissible=24, rejected=276, unknown=0, truncated=276, disagree=0))

    def test_duplicate_case(self):
        row = self.record()
        self.assertEqual(self.check([row, row])['counts']['rejected'], 1)

    def test_escape(self):
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / 'artifact.json'
            raw = m.encode({'case': 'a'})
            outside.write_bytes(raw)
            import os
            ref = dict(path=os.path.relpath(outside, self.root), sha256=m.digest(raw))
            with self.assertRaises(ValueError):
                m.artifact(ref, self.root)
            (self.root / 'link.json').symlink_to(outside)
            ref['path'] = 'link.json'
            with self.assertRaises(ValueError):
                m.artifact(ref, self.root)

    def test_artifact_pass_type(self):
        for invalid in (True, 1.0):
            row = self.record()
            item = json.loads((self.root / row['judges'][0]['path']).read_text())
            item['pass'] = invalid
            row['judges'][0] = self.save(item)
            self.assertEqual(self.check([row])['counts']['unknown'], 1)

    def test_equal_weights_under_alias(self):
        row = self.record()
        first = json.loads((self.root / row['judges'][0]['path']).read_text())
        second = json.loads((self.root / row['judges'][1]['path']).read_text())
        second['model_sha256'] = first['model_sha256']
        second['provenance'] = self.save(dict(member=second['member'], model_sha256=second['model_sha256']))
        row['judges'][1] = self.save(second)
        self.assertEqual(self.check([row])['counts']['rejected'], 1)

    def test_nonobject_artifact(self):
        row = self.record()
        row['response'] = self.save([])
        self.assertEqual(self.check([row])['counts']['unknown'], 1)

    def test_empty(self):
        self.assertEqual(self.check([])['state'], 'NO_DATA')
