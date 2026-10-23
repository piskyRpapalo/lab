import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[1] / 'bin/verify_graphic_inventory.py'

class TestGraphicInventory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['public/game/a.js', 'public/assets/b.css']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('body')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.DEVNULL, text=True).strip()
        git('init')
        git('add', 'public')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-m', 'fixture')
        self.sha = git('rev-parse', 'HEAD')
        self.document = self.root / 'inventory.md'
        self.text = f'''Base medida WEB origin/main `{self.sha}`.
### public/game/
| Fichero | B | Clase | Tipo |
|---|---:|:---:|:---:|
| a.js | 4 | C | L |
### public/assets/
| Fichero | B | Clase | Tipo |
|---|---:|:---:|:---:|
| b.css | 4 | R | V |
'''

    def check(self, text):
        self.document.write_text(text)
        return subprocess.run([sys.executable, str(GUARD), '--root', str(self.root), '--inventory', str(self.document)], capture_output=True, text=True)

    def test_exact_measured_tree_passes(self):
        result = self.check(self.text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('2 unique files', result.stdout)

    def test_changed_size_fails(self):
        self.assertNotEqual(self.check(self.text.replace('a.js | 4', 'a.js | 5')).returncode, 0)

    def test_missing_module_fails(self):
        self.assertNotEqual(self.check(self.text.replace('| b.css | 4 | R | V |', '')).returncode, 0)

    def test_duplicate_module_fails(self):
        self.assertNotEqual(self.check(self.text + '| b.css | 4 | R | V |\n').returncode, 0)

    def test_unknown_class_fails(self):
        self.assertNotEqual(self.check(self.text.replace('| R | V |', '| X | V |')).returncode, 0)

    def test_unknown_ref_fails(self):
        self.assertNotEqual(self.check(self.text.replace(self.sha, 'f' * 40)).returncode, 0)

    def test_piece_ceiling_is_utf8_bytes(self):
        self.assertNotEqual(self.check(self.text + 'é' * 8192).returncode, 0)

    def test_visual_class_cannot_claim_logic_role(self):
        self.assertNotEqual(self.check(self.text.replace('| R | V |', '| R | L |')).returncode, 0)
