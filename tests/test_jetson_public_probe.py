import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

P=Path(__file__).parents[1]/'bin/jetson_public_probe.py'
spec=importlib.util.spec_from_file_location('jetson_probe',P)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class ProbeTests(unittest.TestCase):
    def test_known_units_and_missing_fields_remain_distinct(self):
        self.assertEqual(p.parse_tegrastats('RAM 1234/7620MB GR3D_FREQ 83%@[918] VDD_IN 5100mW/4200mW'),
                         {'ram_vendor_MB':1234,'gpu_util_pct':83,'vdd_in_mw':5100})
        self.assertEqual(p.parse_tegrastats('GR3D_FREQ 0% VDD_IN 900/800'),{'gpu_util_pct':0,'vdd_in_mw':900})
        self.assertEqual(p.parse_tegrastats('GPU unavailable'),{})
        self.assertNotIn('gpu_util_pct',p.parse_tegrastats('GR3D_FREQ 999%'))

    def test_pseudo_file_short_read_and_unreadable_are_not_fabricated_values(self):
        with patch('builtins.open',side_effect=TypeError('kernel pseudo-file')):
            self.assertIsNone(p.read('/unused'))
        with patch.object(p,'read',return_value='MemTotal: 1000 kB\nMemAvailable: 123 kB\n'):
            self.assertEqual(p.memory(),{'MemTotal':1024000,'MemAvailable':125952})

    def test_occupied_measurement_window_never_starts_observer_or_generation(self):
        runner=MagicMock()
        runner.model_digest.return_value='a'*64
        runner.strict_json.return_value={'models':[{'digest':'unowned'}]}
        with patch('urllib.request.build_opener'),patch.object(p,'memory',return_value={'MemAvailable':8*1024**3}),\
             patch.object(p,'temperatures',return_value=[55000]),patch.object(p.subprocess,'Popen') as start:
            out=p.run(runner,lambda *_:'PASS',b'{}','fixture','a'*64,source={})
        self.assertEqual(out['model_calls'],0)
        self.assertEqual(out['cause'],'measurement_window_not_idle_or_safe')
        start.assert_not_called()
        runner.run_public.assert_not_called()

