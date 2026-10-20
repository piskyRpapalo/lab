import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_a11y_install", ROOT / "bin/verify_a11y_install.py")
verify_a11y_install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_a11y_install)


def make_app(root, voice_body):
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True)
    entry = bin_dir / "instalar-pc"
    entry.write_text("#!/usr/bin/env bash\nif [ \"${1:-}\" = --voz ]; then shift; exec \"$(dirname \"$0\")/instalar-pc-voz\" \"$@\"; fi\nexit 2\n")
    entry.chmod(0o755)
    voice = bin_dir / "instalar-pc-voz"
    voice.write_text(voice_body)
    voice.chmod(0o755)


class VerifyA11yInstallTests(unittest.TestCase):
    def test_missing_app_is_no_data(self):
        with tempfile.TemporaryDirectory() as temp:
            result = verify_a11y_install.verify(Path(temp) / "missing")
        self.assertEqual(result["state"], "NO_DATA")
        self.assertTrue(result["cause"])

    def test_safe_voice_dry_run_is_green_without_files(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "app"
            app.mkdir()
            make_app(app, "#!/usr/bin/env bash\nprintf 'DRY_RUN\\n'\n")
            result = verify_a11y_install.verify(app)
        self.assertEqual(result["state"], "GREEN")
        self.assertEqual(result["checks"]["writes"], 0)

    def test_write_during_dry_run_is_red(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "app"
            app.mkdir()
            make_app(app, "#!/usr/bin/env bash\nmkdir -p \"$HOME/.local\"\nprintf 'DRY_RUN\\n'\n")
            result = verify_a11y_install.verify(app)
        self.assertEqual(result["state"], "RED")
        self.assertIn("wrote", result["cause"])

    def test_receipt_stays_below_one_kibibyte(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "app"
            app.mkdir()
            make_app(app, "#!/usr/bin/env bash\nprintf 'DRY_RUN\\n'\n")
            result = verify_a11y_install.verify(app)
        self.assertLess(len(verify_a11y_install.canonical(result).encode()), 1024)


if __name__ == "__main__":
    unittest.main()
