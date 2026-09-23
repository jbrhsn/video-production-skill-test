"""Review-gate trajectories, real command guard integration, and beat validation."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

from production import check_production
from workflow_v2 import snapshot, validate_execution
from timeline import compile_timeline

SCRIPTS = Path(__file__).resolve().parent


def save(root, state):
    (root / "production-state.json").write_text(json.dumps(state))


def approve(root, state, scope, revision):
    state["approvals"].append({"scope": scope, "revision": revision, "decision": "approved",
        "date": "2026-09-21", "evidence": "SIMULATED fixture response, not a real user approval",
        "reviewTarget": f"Fixture {scope} {revision}", "snapshot": snapshot(root, scope)})
    save(root, state)


def fixture(root):
    state = json.loads((SCRIPTS.parent / "assets/production-state.json.template").read_text())
    audio = root / "public/audio"
    audio.mkdir(parents=True)
    (root / "transcript.txt").write_text("One.\n---\nTwo.")
    rows = []
    for n, word in ((1, "One."), (2, "Two.")):
        with wave.open(str(audio / f"scene-{n}.wav"), "wb") as wav:
            wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\x01\x00" * 24000)
        rows.append({"scene": n, "file": f"scene-{n}.wav", "duration_s": 1, "text": word})
        (audio / f"scene-{n}-timestamps.json").write_text(json.dumps({"duration_s": 1,
            "words": [{"word": word, "start": 0, "end": .5}]}))
    (audio / "metadata.json").write_text(json.dumps({"scenes": rows}))
    save(root, state)
    return state


def plan(root, state):
    (root / "storyboard.json").write_text(json.dumps([{"scene": 1}, {"scene": 2}]))
    (root / "edit-plan.json").write_text(json.dumps({"version": 2, "transitions": [], "holds": [], "audio": [],
        "mix": {"targetLufs": -16, "toleranceLufs": 1, "maxTruePeakDbtp": -1}}))
    design = json.loads((SCRIPTS.parent / "assets/design-system.json.template").read_text())
    design["rationale"] = "Fixture uses an explicit light workplace treatment."
    design["backgroundStrategy"] = "Use the light background with semantic accents."
    (root / "design-system.json").write_text(json.dumps(design))
    (root / "asset-manifest.json").write_text('{"version":1,"assets":[]}')
    for name in ("asset-plan.md", "implementation-plan.md"):
        (root / name).write_text("Fixture: animate a code circle growing to show increase; no external dependency.")
    execution = {"version": 2, "fps": 30, "scenes": [
        {"scene": n, "beats": [{"id": f"S{n}-B1", "words": [0, 1], "quote": word, "frames": [0, 15],
         "layers": {"bg": ["code:background"], "mid": ["code:circle"], "fg": []},
         "initial": "Circle radius 10 at center", "action": "Increase radius linearly from 10 to 40",
         "result": "Circle radius 40", "events": [], "steps": [f"In Scene{n}.tsx interpolate radius over frames 0-14"],
         "acceptance": "Circle radius at frame 14 is 40"}]} for n, word in ((1, "One."), (2, "Two."))]}
    (root / "execution-plan.json").write_text(json.dumps(execution))
    state["scenes"] = [{"scene": n, "revision": f"scene-{n}-1", "status": "pending"} for n in (1, 2)]
    state["assetsReadyRevision"] = state["planRevision"]
    return execution


def scaffold(root, visual_style="custom", refresh=False):
    command = [sys.executable, str(SCRIPTS / "03_scaffold.py"), "--project-dir", str(root),
        "--storyboard", str(root / "storyboard.json"), "--audio-metadata", str(root / "public/audio/metadata.json"),
        "--edit-plan", str(root / "edit-plan.json"), "--design-system", str(root / "design-system.json"),
        "--width", "640", "--height", "360", "--visual-style", visual_style, "--skip-install"]
    if refresh:
        command.append("--refresh-generated")
    return subprocess.run(command, capture_output=True, text=True)


class WorkflowV2Tests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.state = fixture(self.root)

    def check(self, stage, scene=None):
        save(self.root, self.state)
        return check_production(self.root, stage, [1, 2], required=True, scene=scene)

    def ready_plan(self):
        approve(self.root, self.state, "narration", "narration-1")
        self.state["phase"] = "planning"
        self.check("plan")
        plan(self.root, self.state)
        self.state["phase"] = "implementation"
        approve(self.root, self.state, "plan", "plan-1")

    def test_sequential_trajectory_requires_each_handoff(self):
        with self.assertRaisesRegex(ValueError, "Narration package approval"):
            self.check("plan")
        self.assertFalse((self.root / "storyboard.json").exists())
        approve(self.root, self.state, "narration", "narration-1")
        self.state["phase"] = "planning"
        self.check("plan")
        plan(self.root, self.state)
        self.state["phase"] = "assets"
        self.state["assetsReadyRevision"] = None
        with self.assertRaisesRegex(ValueError, "Required assets"):
            self.check("implement")
        self.state["assetsReadyRevision"] = "plan-1"
        self.state["phase"] = "implementation"
        with self.assertRaisesRegex(ValueError, "Refined plan approval"):
            self.check("implement")
        approve(self.root, self.state, "plan", "plan-1")
        self.check("implement")
        result = scaffold(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.state["activeScene"] = 1
        self.check("scene", 1)
        self.state["activeScene"] = 2
        with self.assertRaisesRegex(ValueError, "Scene 1 must be reviewed"):
            self.check("scene", 2)
        self.state["scenes"][0]["status"] = "approved"
        approve(self.root, self.state, "scene:1", "scene-1-1")
        self.check("scene", 2)
        self.state["phase"] = "final-review"
        with self.assertRaisesRegex(ValueError, "export approval"):
            self.check("render")

    def test_changed_audio_invalidates_narration_without_revision_bump(self):
        self.ready_plan()
        with (self.root / "public/audio/scene-1.wav").open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaisesRegex(ValueError, "Narration package approval"):
            self.check("implement")

    def test_unapproved_scene_cannot_be_inferred_from_status_or_proceed(self):
        self.ready_plan()
        self.state["activeScene"] = 2
        self.state["scenes"][0]["status"] = "approved"
        with self.assertRaisesRegex(ValueError, "Scene 1 must be reviewed"):
            self.check("scene", 2)

    def test_missing_file_bad_word_coverage_and_early_reveal_rejected(self):
        self.ready_plan()
        original = json.loads((self.root / "execution-plan.json").read_text())
        for mutation in ("missing", "coverage", "timing", "quote"):
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(original)
                beat = value["scenes"][0]["beats"][0]
                if mutation == "missing":
                    beat["layers"]["mid"] = ["public/media/missing.png"]
                elif mutation == "coverage":
                    value["scenes"][0]["beats"] = []
                elif mutation == "timing":
                    beat["frames"] = [10, 25]
                else:
                    beat["quote"] = "Entire scene about Model 1"
                (self.root / "execution-plan.json").write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    validate_execution(self.root, [1, 2])

    def test_scene_specific_edit_preserves_previous_approval_shared_edit_does_not(self):
        self.ready_plan()
        result = scaffold(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.state["scenes"][0]["status"] = "approved"
        approve(self.root, self.state, "scene:1", "scene-1-1")
        self.state["activeScene"] = 2
        (self.root / "src/scenes/Scene2.tsx").write_text("// isolated fixture edit")
        self.check("scene", 2)
        (self.root / "src/Timeline.tsx").write_text("// changed shared behavior")
        with self.assertRaisesRegex(ValueError, "Scene 1 must be reviewed"):
            self.check("scene", 2)

    def test_whiteboard_helpers_are_preserved_on_refresh(self):
        self.ready_plan()
        result = scaffold(self.root, visual_style="whiteboard")
        self.assertEqual(result.returncode, 0, result.stderr)
        helper = self.root / "src/visuals/DoodleAssets.tsx"
        self.assertTrue(helper.is_file())
        authored = helper.read_text() + "\n// authored fixture revision\n"
        helper.write_text(authored)
        result = scaffold(self.root, visual_style="whiteboard", refresh=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(helper.read_text(), authored)

    def test_npm_render_and_hero_block_before_remotion_then_allow_reviewed_inputs(self):
        self.ready_plan()
        result = scaffold(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Fake only the renderer boundary; run real npm, Node wrapper and Python gates.
        cli = self.root / "node_modules/@remotion/cli"
        cli.mkdir(parents=True)
        (cli / "package.json").write_text('{"name":"@remotion/cli","version":"4.0.526"}')
        (cli / "remotion-cli.js").write_text('require("fs").writeFileSync("renderer-invoked", process.argv[2]);')
        for task in ("render", "hero"):
            result = subprocess.run(["npm", "run", task], cwd=self.root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.root / "renderer-invoked").exists())
        self.state["phase"] = "final-review"
        for row in self.state["scenes"]:
            row["status"] = "approved"
            approve(self.root, self.state, f"scene:{row['scene']}", row["revision"])
        approve(self.root, self.state, "video", "project-1")
        for task in ("render", "hero"):
            result = subprocess.run(["npm", "run", task], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / "renderer-invoked").read_text(), "still")
        (self.root / "renderer-invoked").unlink()
        (self.root / "production-state.json").unlink()
        result = subprocess.run(["npm", "run", "render"], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "renderer-invoked").exists())

    def test_new_scaffold_requires_state_even_when_inputs_exist(self):
        plan(self.root, self.state)
        (self.root / "production-state.json").unlink()
        result = scaffold(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing production state", result.stderr)
        self.assertFalse((self.root / "src").exists())

    def test_hero_uses_updated_timeline_after_renewed_approval(self):
        self.ready_plan()
        result = scaffold(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        timeline_path = self.root / "src/timeline-data.json"
        timeline = json.loads(timeline_path.read_text())
        timeline["scenes"][-1]["spanFrames"] += 30
        timeline["scenes"][-1]["visualEnd"] += 30
        timeline["totalFrames"] += 30
        timeline_path.write_text(json.dumps(timeline))
        edit = {"version": 2, "transitions": [], "holds": [{"afterScene": 2, "frames": 30}], "audio": [],
                "mix": {"targetLufs": -16, "toleranceLufs": 1, "maxTruePeakDbtp": -1}}
        for name in ("edit-plan.json", "src/edit-plan.json"):
            (self.root / name).write_text(json.dumps(edit))
        approve(self.root, self.state, "plan", "plan-1")
        cli = self.root / "node_modules/@remotion/cli"
        cli.mkdir(parents=True)
        (cli / "package.json").write_text('{"name":"@remotion/cli","version":"4.0.526"}')
        (cli / "remotion-cli.js").write_text('require("fs").writeFileSync("renderer-args", JSON.stringify(process.argv.slice(2)));')
        self.state["phase"] = "final-review"
        for row in self.state["scenes"]:
            row["status"] = "approved"
            approve(self.root, self.state, f"scene:{row['scene']}", row["revision"])
        approve(self.root, self.state, "video", "project-1")
        result = subprocess.run(["npm", "run", "hero"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--frame=89", json.loads((self.root / "renderer-args").read_text()))

    def test_nonfinite_timestamp_duration_rejected(self):
        self.ready_plan()
        path = self.root / "public/audio/scene-1-timestamps.json"
        timestamps = json.loads(path.read_text())
        timestamps["duration_s"] = float("nan")
        path.write_text(json.dumps(timestamps))
        with self.assertRaisesRegex(ValueError, "inconsistent timestamps"):
            validate_execution(self.root, [1, 2])

    def test_event_anchor_moves_after_hold_and_rejects_bad_audio_asset(self):
        self.ready_plan()
        execution = json.loads((self.root / "execution-plan.json").read_text())
        execution["scenes"][1]["beats"][0]["events"] = [{"id": "contact", "frame": 6, "word": 0}]
        (self.root / "execution-plan.json").write_text(json.dumps(execution))
        media = self.root / "public/media"
        media.mkdir(parents=True)
        with wave.open(str(media / "click.wav"), "wb") as wav:
            wav.setparams((1, 2, 24000, 0, "NONE", "not compressed")); wav.writeframes(b"\x01\x00" * 24000)
        manifest = {"version": 1, "assets": [{"id": "click", "kind": "audio", "stagedPath": "public/media/click.wav",
            "source": "fixture", "rightsStatus": "cleared", "usageBasis": "test fixture", "attribution": "none",
            "status": "accepted", "inspection": "One second synthetic click fixture."}]}
        (self.root / "asset-manifest.json").write_text(json.dumps(manifest))
        cue = {"id": "contact-cue", "assetId": "click", "role": "effect", "purpose": "Confirm contact",
               "required": True, "anchor": {"type": "event", "scene": 2, "beat": "S2-B1", "event": "contact"},
               "durationFrames": 6, "sourceStartSeconds": 0, "gainDb": -9, "duckGainDb": -9,
               "duckAttackFrames": 3, "duckReleaseFrames": 3, "fadeInFrames": 0, "fadeOutFrames": 1,
               "acceptance": "Click occurs at the contact frame."}
        edit = {"version": 2, "transitions": [], "holds": [{"afterScene": 1, "frames": 12}], "audio": [cue],
                "mix": {"targetLufs": -16, "toleranceLufs": 1, "maxTruePeakDbtp": -1}}
        scenes = [{"scene": 1, "duration_frames": 30}, {"scene": 2, "duration_frames": 30}]
        words = {(2, 0, "start"): 0, (2, 0, "end"): 15}
        compiled = compile_timeline(scenes, 30, edit, execution, manifest, words)
        self.assertEqual(compiled["audio"][0]["startFrame"], 48)
        manifest["assets"][0]["kind"] = "image"
        with self.assertRaisesRegex(ValueError, "audio asset"):
            compile_timeline(scenes, 30, edit, execution, manifest, words)

    @unittest.skipUnless(os.environ.get("VIDEO_PRODUCTION_RENDER_SMOKE") and os.environ.get("VIDEO_PRODUCTION_NODE_MODULES"),
                         "Set VIDEO_PRODUCTION_RENDER_SMOKE and VIDEO_PRODUCTION_NODE_MODULES for real guarded export")
    def test_real_guarded_exports(self):
        self.ready_plan()
        result = scaffold(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.root / "node_modules").symlink_to(Path(os.environ["VIDEO_PRODUCTION_NODE_MODULES"]).resolve(), target_is_directory=True)
        for n in (1, 2):
            (self.root / f"src/scenes/Scene{n}.tsx").write_text(
                'import React from "react"; import {AbsoluteFill} from "remotion"; '
                'import type {VisualSceneProps} from "../Timeline"; '
                f'export const Scene{n}: React.FC<VisualSceneProps> = ({{contentFrame}}) => '
                '<AbsoluteFill style={{background:"#172631",justifyContent:"center",alignItems:"center"}}>'
                '<div style={{borderRadius:"50%",width:20+Math.min(contentFrame,14)*60/14,'
                'height:20+Math.min(contentFrame,14)*60/14,background:"#ffb755"}}/></AbsoluteFill>;')
        result = subprocess.run(["npm", "run", "typecheck"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.state["phase"] = "final-review"
        for row in self.state["scenes"]:
            row["status"] = "approved"
            approve(self.root, self.state, f"scene:{row['scene']}", row["revision"])
        approve(self.root, self.state, "video", "project-1")
        for task in ("render", "hero"):
            result = subprocess.run(["npm", "run", task], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr[-1500:])
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json",
                                str(self.root / "out/video.mp4")], check=True, capture_output=True, text=True)
        streams = json.loads(probe.stdout)["streams"]
        self.assertEqual({row["codec_type"] for row in streams}, {"audio", "video"})
        video = next(row for row in streams if row["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"], video["nb_frames"]), (640, 360, "60"))
        self.assertTrue((self.root / "out/video-hero.png").is_file())
        print("V2 guarded exports: 2 scenes, 60 frames, 640x360, audio/video and hero verified; synthetic fixture, no creative approval claimed.")


if __name__ == "__main__":
    unittest.main()
