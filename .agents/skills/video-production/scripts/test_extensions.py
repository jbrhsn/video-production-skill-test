"""Behavior checks for recorded narration, calculation data, and optional visual kits."""
import importlib.util
import json
import os
import subprocess
import sys
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
        for args in [(100, 10, -1, 1), (100, 10, float('nan'), 1), (100, 10, .1, 0), (100, 10, .1, .01)]:
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

    @unittest.skip("Obsolete no-state scaffold coverage removed; v2 scaffolding requires approved production state")
    def test_whiteboard_scaffold_and_refresh_preserve_art(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brief = root / "storyboard.json"
            brief.write_text(json.dumps([{"scene": 1, "direction": {"audience_sees": "A house"}}]))
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({"scenes": [{"scene": 1, "file": "scene-1.wav", "duration_s": 1}]}))
            command = [sys.executable, str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root / "project"),
                       "--storyboard", str(brief), "--audio-metadata", str(metadata), "--skip-install",
                       "--profile", "youtube-horizontal", "--visual-style", "whiteboard"]
            subprocess.run(command, check=True, capture_output=True)
            helper = root / "project/src/visuals/DoodleAssets.tsx"
            self.assertTrue(helper.is_file())
            authored = helper.read_text() + "\n// authored revision\n"
            helper.write_text(authored)
            subprocess.run(command + ["--refresh-generated"], check=True, capture_output=True)
            self.assertEqual(helper.read_text(), authored)

    @unittest.skip("Obsolete no-state scaffold coverage removed; v2 scaffolding requires approved production state")
    def test_single_scene_whiteboard_typechecks_with_empty_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "storyboard.json").write_text(json.dumps([{"scene": 1, "direction": {}}]))
            (root / "metadata.json").write_text(json.dumps({"scenes": [{"scene": 1, "file": "scene-1.wav", "duration_s": 1}]}))
            subprocess.run([sys.executable, str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root),
                "--storyboard", str(root / "storyboard.json"), "--audio-metadata", str(root / "metadata.json"),
                "--visual-style", "whiteboard", "--skip-install"], check=True, capture_output=True)
            (root / "public/audio/scene-1-timestamps.json").write_text('{"words": []}')
            (root / "node_modules").symlink_to(Path(os.environ["VIDEO_PRODUCTION_NODE_MODULES"]).resolve(), target_is_directory=True)
            result = subprocess.run([str(root / "node_modules/.bin/tsc"), "--noEmit"], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
