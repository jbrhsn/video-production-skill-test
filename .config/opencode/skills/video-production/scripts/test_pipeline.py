"""Regression tests for pipeline failure handling and generated projects."""
import importlib.util
import json
import subprocess
import sys
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
review = load("05_review_bundle.py")


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
        self.assertIn("audio/voice.wav", scaffold.make_scene_stub(scenes[0]))
        for bad in [{"scenes": []}, {"scenes": [dict(scene=2, file="voice.wav", duration_s=1)]},
                    {"scenes": [dict(scene=1, file="../voice.wav", duration_s=1)]},
                    {"scenes": [dict(scene=1, file="voice.wav", duration_s=float("nan"))]}]:
            with self.assertRaises(ValueError):
                scaffold.resolve_scenes(direction, bad, 30)

    @unittest.skip("Obsolete no-state scaffold coverage removed; v2 scaffolding requires approved production state")
    def test_directorial_cli_generates_measured_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brief = root / "storyboard.json"
            brief.write_text(json.dumps([{"scene": 1, "direction": {"assets": []}}]))
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({"scenes": [{"scene": 1, "file": "voice.wav",
                "duration_s": 1.01, "timestamps_file": "words.json"}]}))
            subprocess.run(["uv", "run", "--no-project", "--python", sys.executable,
                "python", str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root),
                "--storyboard", str(brief), "--audio-metadata", str(metadata), "--skip-install"],
                check=True, capture_output=True)
            config = (root / "src/config.ts").read_text()
            self.assertIn('"durationFrames": 31', config)
            self.assertIn('"timestampsFile": "audio/words.json"', config)
            self.assertIn("--frame=30", json.loads((root / "package.json").read_text())["scripts"]["hero"])

    @unittest.skip("Obsolete no-state scaffold coverage removed; v2 scaffolding requires approved production state")
    def test_scaffold_rerun_preserves_authored_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storyboard = root / "storyboard.json"
            storyboard.write_text(json.dumps([dict(scene=1, title='Quotes " & braces { }',
                duration_s=1.01, duration_frames=31, audio_file="custom.wav",
                timestamps_file="custom.json", hold_frames=0)]))
            command = ["uv", "run", "--no-project", "--python", sys.executable,
                       "python", str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root),
                       "--storyboard", str(storyboard), "--skip-install"]
            subprocess.run(command, check=True, capture_output=True)
            manifest = root / "package.json"
            manifest.write_text('{"private":true}')
            result = subprocess.run(command, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest.read_text(), '{"private":true}')
            scene = root / "src/scenes/Scene1.tsx"
            original = scene.read_text()
            generated_root = (root / "src/Root.tsx").read_text()
            self.assertIn('audio/custom.wav', generated_root)
            self.assertIn('custom.json', generated_root)
            self.assertIn('VisualSceneProps', original)
            scene.write_text("// authored")
            subprocess.run(command + ["--refresh-generated"], check=True, capture_output=True)
            self.assertEqual(scene.read_text(), "// authored")


@unittest.skip("Obsolete version-1 timeline coverage removed; v2 timing/event coverage lives in test_workflow_v2.py")
class TimelineTests(unittest.TestCase):
    @staticmethod
    def scenes(frames=(90, 90)):
        return [dict(scene=i, duration_frames=count) for i, count in enumerate(frames, 1)]

    def test_visual_overlap_preserves_narration_and_total(self):
        for fps in (24, 30, 60):
            for frames in (11, 12):
                with self.subTest(fps=fps, frames=frames):
                    data = scaffold.compile_timeline(self.scenes(), fps, {"version": 1, "transitions": [
                        {"afterScene": 1, "kind": "fade", "frames": frames}]})
                    first, second = data["scenes"]
                    self.assertEqual(data["totalFrames"], 180)
                    self.assertEqual([first["start"], second["start"]], [0, 90])
                    self.assertEqual(first["visualEnd"] - second["visualStart"], frames)
                    self.assertEqual(second["visualStart"], 90 - frames // 2)
                    self.assertEqual(first["visualEnd"], 90 + frames - frames // 2)
                    self.assertEqual(first["contentFrames"], 90)

    def test_holds_shift_speech_and_hero_without_trimming(self):
        data = scaffold.compile_timeline(self.scenes(), 30, {"version": 1, "holds": [
            {"afterScene": 1, "frames": 15}, {"afterScene": 2, "frames": 9}]})
        self.assertEqual(data["scenes"][1]["start"], 105)
        self.assertEqual(data["totalFrames"], 204)
        self.assertEqual([s["contentFrames"] for s in data["scenes"]], [90, 90])
        self.assertIn("--frame=203", json.loads(scaffold.make_package_json("4.0.526", 204))["scripts"]["hero"])

    def test_cut_defaults_and_single_scene(self):
        data = scaffold.compile_timeline(self.scenes((1,)), 30)
        self.assertEqual(data["boundaries"], [])
        self.assertEqual(data["totalFrames"], 1)
        commands, samples = review.build_commands(data)
        self.assertEqual(samples, [0])
        self.assertFalse(any("Boundary" in str(command) for command in commands))

    def test_invalid_edits_fail_before_generation(self):
        bad_plans = [
            {"version": 2}, {"version": True}, {"version": 1, "typo": []},
            {"version": 1, "transitions": [{"afterScene": 2, "kind": "fade", "frames": 8}]},
            {"version": 1, "transitions": [{"afterScene": 1, "kind": "cut", "frames": 8}]},
            {"version": 1, "transitions": [{"afterScene": 1, "kind": "fade", "frames": -1}]},
            {"version": 1, "transitions": [{"afterScene": 1, "kind": "fade", "frames": 180}]},
            {"version": 1, "holds": [{"afterScene": 1, "frames": True}]},
            {"version": 1, "safeArea": {"top": .6, "bottom": .6, "left": 0, "right": 0}},
        ]
        for plan in bad_plans:
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                scaffold.compile_timeline(self.scenes(), 30, plan)
        with self.assertRaises(ValueError):
            scaffold.compile_timeline(self.scenes((90, 10, 90)), 30, {"version": 1, "transitions": [
                {"afterScene": 1, "kind": "slide", "frames": 12},
                {"afterScene": 2, "kind": "wipe", "frames": 12}]})

    def test_audio_cues_cannot_escape_timeline_or_paths(self):
        cue = dict(src="media/music.wav", role="music", startFrame=0, durationFrames=180,
                   volume=.2, duckVolume=.08, fadeFrames=8)
        data = scaffold.compile_timeline(self.scenes(), 30, {"version": 1, "audio": [cue]})
        self.assertEqual(data["audio"][0]["durationFrames"], 180)
        for change in (dict(src="media/../secret.wav"), dict(src="https://example.com/a.wav"),
                       dict(durationFrames=181), dict(volume=float("nan")),
                       dict(duckVolume=.8), dict(fadeFrames=91)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                scaffold.compile_timeline(self.scenes(), 30, {"version": 1, "audio": [{**cue, **change}]})

    def test_boundary_review_uses_compiled_master_window(self):
        data = scaffold.compile_timeline(self.scenes(), 30, {"version": 1, "transitions": [
            {"afterScene": 1, "kind": "wipe", "frames": 12}]})
        boundary = data["boundaries"][0]
        self.assertEqual((boundary["previewStart"], boundary["previewFrames"]), (54, 72))
        commands, frames = review.build_commands(data)
        self.assertTrue(any("Boundary1" in command for command in commands))
        self.assertTrue(any("VideoFull" in command for command in commands))
        self.assertEqual(frames[-1], 179)

    def test_legacy_scene_rejects_edit_plan_without_modifying_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/scenes").mkdir(parents=True)
            scene = root / "src/scenes/Scene1.tsx"
            scene.write_text("// Existing scene owns its narration")
            brief = root / "storyboard.json"
            brief.write_text(json.dumps([dict(scene=1, duration_s=3, duration_frames=90,
                audio_file="voice.wav", timestamps_file="words.json")]))
            plan = root / "edit-plan.json"
            plan.write_text('{"version":1}')
            command = ["uv", "run", "--no-project", "--python", sys.executable, "python",
                str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root), "--storyboard", str(brief),
                "--edit-plan", str(plan), "--skip-install"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Existing scenes own audio/captions", result.stderr)
            self.assertFalse((root / "package.json").exists())
            self.assertEqual(scene.read_text(), "// Existing scene owns its narration")

    def test_horizontal_profile_and_edit_choices_survive_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brief = root / "storyboard.json"
            brief.write_text(json.dumps([dict(scene=i, duration_s=3, duration_frames=90,
                audio_file=f"voice-{i}.wav", timestamps_file=f"words-{i}.json") for i in (1, 2)]))
            plan = root / "edit-plan.json"
            plan.write_text(json.dumps({"version": 1, "transitions": [
                {"afterScene": 1, "kind": "slide", "frames": 12}],
                "holds": [{"afterScene": 2, "frames": 15}]}))
            command = ["uv", "run", "--no-project", "--python", sys.executable, "python",
                str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root), "--storyboard", str(brief),
                "--profile", "youtube-horizontal", "--skip-install"]
            subprocess.run(command + ["--edit-plan", str(plan)], check=True, capture_output=True)
            before = json.loads((root / "src/timeline-data.json").read_text())
            self.assertEqual(before["totalFrames"], 195)
            helper = root / "src/Timeline.tsx"
            helper.write_text("// authored timeline helper")
            subprocess.run(command + ["--refresh-generated"], check=True, capture_output=True)
            self.assertEqual(json.loads((root / "src/timeline-data.json").read_text()), before)
            self.assertEqual(helper.read_text(), "// authored timeline helper")
            self.assertIn("width: 1920", (root / "src/config.ts").read_text())


if __name__ == "__main__":
    unittest.main()
