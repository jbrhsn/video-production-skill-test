"""Behavior checks for recorded narration and calculation data."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from finance_model import amortization, investment

SCRIPTS = Path(__file__).parent
spec = importlib.util.spec_from_file_location("import_narration", SCRIPTS / "06_import_narration.py")
recorded = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recorded)


class ExtensionTests(unittest.TestCase):
    def test_loan_accounting_and_known_payment(self):
        result = amortization(300000, .06, 30)
        self.assertAlmostEqual(result["scheduled_monthly_payment"], 1798.651575, places=5)
        self.assertEqual(result["rows"][-1]["balance"], 0)
        self.assertAlmostEqual(sum(r["principal"] for r in result["rows"]), 300000)
        for row in result["rows"]:
            self.assertAlmostEqual(row["payment"], row["interest"] + row["principal"])
        zero = amortization(1200, 0, 1)
        self.assertEqual(zero["scheduled_monthly_payment"], 100)
        self.assertEqual(sum(r["interest"] for r in zero["rows"]), 0)

    def test_investment_contribution_timing_and_annual_conversion(self):
        self.assertAlmostEqual(investment(100, 0, .1, 1)["rows"][-1]["balance"], 110)
        self.assertAlmostEqual(investment(100, 0, -.1, 1)["rows"][-1]["balance"], 90)
        row = investment(100, 10, 0, 1)["rows"][-1]
        self.assertEqual(row["balance"], 220)
        self.assertEqual(row["growth"], 0)
        self.assertEqual(investment(0, 10, .12, 1 / 12)["rows"][-1]["balance"], 10)
        for args in [(100, 10, -1, 1), (100, 10, float("nan"), 1), (100, 10, .1, 0), (100, 10, .1, .01)]:
            with self.assertRaises(ValueError):
                investment(*args)

    def test_real_audio_import_trims_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "take.wav"
            sf.write(source, .2 * np.sin(np.arange(48000) * 2 * np.pi * 440 / 24000), 24000)
            original = source.read_bytes()
            manifest = root / "import.json"
            manifest.write_text(json.dumps({"scenes": [
                {"scene": 1, "source": "take.wav", "start_s": .25, "end_s": .75, "text": "One."},
                {"scene": 2, "source": "take.wav", "start_s": .75, "end_s": 2, "text": "Two."}]}))
            output = root / "imported"
            rows = recorded.import_narration(manifest, output)
            self.assertAlmostEqual(rows[0]["duration_s"], .5, places=4)
            self.assertAlmostEqual(rows[1]["duration_s"], 1.25, places=4)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(sf.info(output / "scene-1.wav").samplerate, 24000)
            with self.assertRaises(ValueError):
                recorded.import_narration(manifest, output)

    def test_invalid_import_leaves_no_deliverable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sf.write(root / "silent.wav", np.zeros(24000), 24000)
            manifest = root / "import.json"
            manifest.write_text(json.dumps({"scenes": [{"scene": 1, "source": "silent.wav", "text": "Missing speech."}]}))
            with self.assertRaises(ValueError):
                recorded.import_narration(manifest, root / "output")
            self.assertFalse((root / "output").exists())
            with self.assertRaises(ValueError):
                recorded.validate_manifest({"scenes": [{"scene": 1, "source": "silent.wav", "text": "Test", "end_s": -1}]}, root)


if __name__ == "__main__":
    unittest.main()
