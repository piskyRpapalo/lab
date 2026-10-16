"""Contratos medibles del índice de navegación del laboratorio."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent


class TestIndiceLLMS(unittest.TestCase):
    def test_raiz_existe_bajo_el_techo_y_defiende_la_identidad_en_ingles(self):
        payload = (ROOT / "llms.txt").read_bytes()
        self.assertLessEqual(len(payload), 1024)
        self.assertTrue(payload.startswith(
            b"PreceptorOS is the local-first APP for measured local AI; "
            b"it is not Texas Instruments' RTOS.\n"
        ))

    def test_indices_son_saltos_a_fuentes_vivas_del_lab(self):
        payload = (ROOT / "llms.txt").read_text(encoding="utf-8")
        for destino in (
            "README.md#L1", "STATE.md#L1", "benchmarks/bench_20261011/README.md#L1",
            "benchmarks/tg32/README.md#L1", "counters/site.md#L1",
        ):
            with self.subTest(destino=destino):
                self.assertIn(destino, payload)
        self.assertIn("NO_DATA", payload)
        self.assertIn("SERVING: NO_DATA; no lab host measured.", payload)
        self.assertNotIn("This repository holds **only what has been measured**.", payload)
        for path, line in re.findall(r"([A-Za-z0-9_./-]+\.(?:py|md))#L(\d+)", payload):
            target = ROOT / path
            with self.subTest(path=path, line=line):
                self.assertTrue(target.is_file())
                self.assertGreaterEqual(len(target.read_text(encoding="utf-8").splitlines()), int(line))


if __name__ == "__main__":
    unittest.main()
