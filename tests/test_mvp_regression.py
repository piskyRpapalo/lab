import base64
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
import mvp_regression

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/mvp-regression/baseline.synthetic.json'


def evidence():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


class MvpRegressionTests(unittest.TestCase):
    def test_baseline_fixture_passes_with_honest_fixture_label(self):
        result = mvp_regression.validate(evidence())
        self.assertEqual(result['verdict'], 'GREEN')
        self.assertIn('synthetic', result['source_kind'])
        self.assertTrue(result['limits']['contrast_is_certification'] is False)

    def test_missing_viewport_case_is_red(self):
        doc = evidence()
        doc['narration']['cases'].pop()
        self.assertIn('viewport coverage incomplete', mvp_regression.validate(doc)['errors'])

    def test_scroll_or_hidden_narration_is_red(self):
        doc = evidence()
        doc['narration']['cases'][0]['page_scroll_px'] = 1
        doc['narration']['cases'][1]['narration_visible'] = False
        result = mvp_regression.validate(doc)
        self.assertIn('narration viewport failed', result['errors'])

    def test_zoom_out_of_bounds_is_red(self):
        doc = evidence()
        doc['zoom']['cases'][0]['map_zoom'] = 0.59
        self.assertIn('zoom samples do not match bounds and unit sample', mvp_regression.validate(doc)['errors'])

    def test_interactive_object_size_drift_is_red(self):
        doc = evidence()
        doc['zoom']['cases'][0]['screen_size_px'] = [55, 56]
        self.assertIn('interactive object size changes with map zoom', mvp_regression.validate(doc)['errors'])

    def test_contrast_fixture_drift_is_red_not_certification(self):
        doc = evidence()
        doc['contrast']['pairs']['zombie'][0]['ratio'] = 14.9
        result = mvp_regression.validate(doc)
        self.assertIn('contrast regression fixture drift', result['errors'])
        self.assertFalse(result['limits']['contrast_is_certification'])

    def test_export_stage_and_1024_byte_limit_are_enforced(self):
        doc = evidence()
        doc['export']['frames'][0]['export_stage'] = 'pre-compile'
        result = mvp_regression.validate(doc)
        self.assertIn('frame is not post-export', result['errors'])


    def test_missing_export_state_does_not_shrink_required_matrix(self):
        doc = evidence()
        doc['export']['states'].pop()
        result = mvp_regression.validate(doc)
        self.assertIn('compiled state inventory hash mismatch', result['errors'])
        self.assertIn('post-export frame coverage incomplete', result['errors'])

    def test_export_hash_and_oversize_sabotages_are_red(self):
        doc = evidence()
        doc['export']['frames'][0]['sha256'] = '0' * 64
        doc['export']['frames'][1]['payload_base64'] = base64.b64encode(b'x' * 1100).decode('ascii')
        result = mvp_regression.validate(doc)
        self.assertIn('exported frame hash mismatch', result['errors'])
        self.assertIn('exported Bubble frame exceeds 1024 UTF-8 bytes', result['errors'])

    def test_web_app_parity_checks_shared_fixture_and_all_task_fields(self):
        doc = evidence()
        doc['task_parity']['tasks'][1]['app']['errors'] = []
        result = mvp_regression.validate(doc)
        self.assertIn('web/app task output mismatch', result['errors'])


    def test_malformed_untrusted_rows_fail_closed(self):
        doc = evidence()
        doc['narration']['cases'][0]['theme'] = []
        doc['zoom']['interactive_objects'] = [{}]
        doc['export']['states'] = [[]]
        result = mvp_regression.validate(doc)
        self.assertEqual(result['verdict'], 'RED')
        self.assertTrue(result['errors'])

    def test_asset_similarity_is_not_a_parity_field(self):
        doc = evidence()
        doc['task_parity']['fields'].append('shared_assets')
        self.assertIn('parity field list must be exact', mvp_regression.validate(doc)['errors'])


if __name__ == '__main__':
    unittest.main()
