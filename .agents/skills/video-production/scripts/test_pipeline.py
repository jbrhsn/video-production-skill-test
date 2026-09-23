"""Regression tests for pipeline failure handling."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

SCRIPTS = Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tts = load("01_tts.py")
timestamps = load("02_timestamps.py")
scaffold = load("03_scaffold.py")


class PipelineTests(unittest.TestCase):
    def test_transcript_only_splits_separator_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.txt"
            path.write_text("A---B\n---\n\n---\nSecond scene")
            self.assertEqual(tts.parse_transcript(path), ["A---B", "Second scene"])

    def test_invalid_assets_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "kokoro").mkdir()
            for name in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
                (root / "kokoro" / name).write_text("Entry not found")
            with self.assertRaises(SystemExit):
                tts.check_assets(root)

    def test_bad_synthesis_does_not_write_silent_success(self):
        class Fake:
            def create(self, *args, **kwargs):
                return self.samples, self.rate

        fake = Fake()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "scene.wav"
            for samples, rate in [([], 24000), ([0, 0], 24000), ([float("nan")], 24000), ([1], 16000)]:
                fake.samples, fake.rate = samples, rate
                with self.assertRaises(ValueError):
                    tts.synthesize_scene(fake, "Test", "af_heart", "en-us", output)
                self.assertFalse(output.exists())

    def test_audio_duration_includes_trailing_silence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short.wav"
            sf.write(path, np.zeros(2400), 24000, subtype="FLOAT")
            self.assertEqual(timestamps.get_audio_duration(path), 0.1)
            output = Path(directory) / "words.json"
            args = type("Args", (), dict(audio=str(path), out=str(output), model="base",
                                         model_dir=None, language="en"))()
            with patch.object(timestamps, "parse_args", return_value=args), patch.object(timestamps.whisper, "load_model") as model:
                timestamps.main()
                model.assert_not_called()
            self.assertEqual(json.loads(output.read_text())["words"], [])

    def test_storyboard_rejects_bad_timing_and_paths(self):
        scene = dict(scene=1, duration_s=1.01, duration_frames=31,
                     audio_file="custom.wav", timestamps_file="custom.json", hold_frames=0)
        scaffold.validate_storyboard([scene], 30)
        for updates in [dict(duration_frames=30), dict(scene=2), dict(audio_file="../secret.wav"),
                        dict(duration_s=float("nan")), dict(hold_frames=31)]:
            with self.assertRaises(ValueError):
                scaffold.validate_storyboard([{**scene, **updates}], 30)

    def test_downloader_http_failure_preserves_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / ".video_production_assets" / "kokoro"
            cache.mkdir(parents=True)
            target = cache / "kokoro-v1.0.onnx"
            target.write_text("Entry not found")
            binary = root / "bin"
            binary.mkdir()
            curl = binary / "curl"
            curl.write_text("#!/bin/sh\nexit 22\n")
            curl.chmod(0o755)
            import os
            result = subprocess.run(["bash", str(SCRIPTS / "04_setup_assets.sh"), str(root)],
                                    env={**os.environ, "PATH": str(binary) + ":" + os.environ["PATH"]},
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(), "Entry not found")
            self.assertEqual(list(cache.glob(".download.*")), [])

    def test_direction_is_independent_of_measured_timing(self):
        direction = [dict(scene=1, direction={"audience_sees": "A world unfolds",
                     "assets": [], "custom_directorial_note": "Follow the transformation"})]
        metadata = {"scenes": [dict(scene=1, file="voice.wav", duration_s=0.1)]}
        scenes = scaffold.resolve_scenes(direction, metadata, 30)
        self.assertEqual(scenes[0]["duration_frames"], 3)
        self.assertEqual(scenes[0]["timestamps_file"], "voice-timestamps.json")
        self.assertNotIn("duration_frames", direction[0])
        stub = scaffold.make_scene_stub(scenes[0])
        self.assertIn("VisualSceneProps", stub)
        self.assertNotIn("audio/voice.wav", stub)
        for bad in [{"scenes": []}, {"scenes": [dict(scene=2, file="voice.wav", duration_s=1)]},
                    {"scenes": [dict(scene=1, file="../voice.wav", duration_s=1)]},
                    {"scenes": [dict(scene=1, file="voice.wav", duration_s=float("nan"))]}]:
            with self.assertRaises(ValueError):
                scaffold.resolve_scenes(direction, bad, 30)


if __name__ == "__main__":
    unittest.main()
