import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('compat', ROOT / 'bin/nvidia_readonly_compat.py')
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


class Compatibility(unittest.TestCase):
    def test_only_two_readonly_commands_and_no_generation_or_settings(self):
        calls = []
        def run(args):
            calls.append(args)
            if args[0] == 'dpkg-query':
                return 'nvidia-jetpack\t6.2.1\nlibnvinfer10\t10.3.0\ncuda-cudart-12-6\t12.6.68\n'
            return 'ollama version is 0.33.2'
        value = c.collect(run=run, read_file=lambda _: '# R36 (release), REVISION: 4.4, PRIVATE',
                          exists=lambda _: True, which=lambda _: '/private/tool', now='2026-11-13T00:00:00Z')
        self.assertEqual([args[0] for args in calls], ['dpkg-query', 'ollama'])
        self.assertEqual(calls[1], ['ollama', '--version'])
        self.assertEqual(value['jetpack']['package_version'], '6.2.1')
        self.assertEqual(value['backend_cli']['version'], '0.33.2')
        self.assertEqual(value['l4t']['release'], '36')
        self.assertEqual(value['compatibility']['state'], 'NO_DATA')
        self.assertFalse(value['settings_changed'])
        self.assertNotIn('PRIVATE', json.dumps(value))
        self.assertNotIn('/private', json.dumps(value))
        ref = value.pop('compatibility_ref')
        self.assertEqual(ref, c.sha(value))

    def test_missing_stack_is_unknown_not_installed_or_compatible(self):
        result = c.collect(run=lambda _: None, read_file=lambda _: None,
                           exists=lambda _: False, which=lambda _: None)
        for field in ('l4t', 'jetpack', 'cuda', 'tensorrt', 'backend_cli', 'compatibility'):
            self.assertEqual(result[field]['state'], 'NO_DATA')
        self.assertEqual(result['model_catalog']['cause'], 'not_recensused')


if __name__ == '__main__':
    unittest.main()
