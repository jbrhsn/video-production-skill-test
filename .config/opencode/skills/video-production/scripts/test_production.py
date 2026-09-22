"""Production workflow behavior and optional isolated Remotion integration."""
from __future__ import annotations

import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from production import check_production, readiness_errors, validate_state

SCRIPTS = Path(__file__).resolve().parent
ASSETS = SCRIPTS.parent / "assets"


def approved_state():
    return {
        "version": 1, "mode": "collaborative", "phase": "review",
        "planRevision": "plan-1", "projectRevision": "project-1",
        "assetsReadyRevision": "plan-1",
        "approvals": [
            {"scope": scope, "revision": revision, "decision": "approved",
             "date": "2026-09-21", "evidence": "SIMULATED FIXTURE approval, not a user decision"}
            for scope, revision in (("plan", "plan-1"), ("video", "project-1"))],
        "scenes": [{"scene": number, "revision": "project-1", "status": "approved"} for number in (1, 2)],
        "feedback": [],
    }


def prepare(root, state=None):
    """Small structural fixture; no creative or listening approval is implied."""
    (root / "storyboard.json").write_text(json.dumps([{"scene": 1}, {"scene": 2}]))
    (root / "transcript.txt").write_text("Fixture one.\n---\nFixture two.\n")
    for name in ("asset-plan.md", "implementation-plan.md"):
        (root / name).write_text("# Isolated test fixture\nNo user project approval.\n")
    (root / "edit-plan.json").write_text(json.dumps({"version": 1, "transitions": [
        {"afterScene": 1, "kind": "fade", "frames": 6}]}))
    (root / "metadata.json").write_text(json.dumps({"scenes": [
        {"scene": n, "file": f"scene-{n}.wav", "duration_s": 1} for n in (1, 2)]}))
    if state is not None:
        (root / "production-state.json").write_text(json.dumps(state))


def scaffold_command(root):
    return [sys.executable, str(SCRIPTS / "03_scaffold.py"), "--legacy-workflow", "--project-dir", str(root),
            "--storyboard", str(root / "storyboard.json"), "--audio-metadata", str(root / "metadata.json"),
            "--edit-plan", str(root / "edit-plan.json"), "--fps", "15", "--width", "640", "--height", "360", "--skip-install"]


@unittest.skip("Obsolete v1 production-contract coverage removed; v2 coverage lives in test_workflow_v2.py")
class ProductionTests(unittest.TestCase):
    def test_template_is_valid_but_unapproved(self):
        state = json.loads((ASSETS / "production-state.json.template").read_text())
        self.assertEqual(validate_state(state), [])
        self.assertTrue(readiness_errors(state, "implement", [1, 2]))

    def test_stale_plan_assets_and_video_are_rejected(self):
        state = approved_state()
        self.assertEqual(readiness_errors(state, "render", [1, 2]), [])
        state["planRevision"] = "plan-2"
        errors = readiness_errors(state, "implement", [1, 2])
        self.assertTrue(any("assets" in error for error in errors))
        self.assertTrue(any("approval" in error for error in errors))
        state = approved_state()
        state["projectRevision"] = "project-2"
        errors = readiness_errors(state, "render", [1, 2])
        self.assertTrue(any("video" in error for error in errors))
        self.assertEqual(sum("stale" in error for error in errors), 2)

    def test_latest_decision_revokes_previous_approval(self):
        state = approved_state()
        state["approvals"].append({**state["approvals"][1], "decision": "changes-requested"})
        self.assertTrue(readiness_errors(state, "render", [1, 2]))

    def test_complete_scene_coverage_and_neighbor_review_required(self):
        state = approved_state()
        state["scenes"][1]["status"] = "changes-requested"
        self.assertTrue(any("Scene 2" in error for error in readiness_errors(state, "render", [1, 2])))
        state["scenes"].pop()
        self.assertTrue(any("coverage" in error for error in readiness_errors(state, "render", [1, 2])))
        state["scenes"].append(copy.deepcopy(state["scenes"][0]))
        self.assertTrue(validate_state(state))

    def test_implemented_feedback_needs_review_resolution(self):
        state = approved_state()
        item = {"id": "F1", "scope": "Scene1", "request": "Slow the reveal", "status": "implemented",
                "history": [{"date": "2026-09-21", "note": "SIMULATED: changed reveal duration"}]}
        state["feedback"].append(item)
        self.assertTrue(any("F1" in error for error in readiness_errors(state, "render", [1, 2])))
        item["status"] = "resolved"
        self.assertTrue(validate_state(state))
        item["resolution"] = "SIMULATED user accepts the revised reveal"
        self.assertEqual(readiness_errors(state, "render", [1, 2]), [])

    def test_autonomous_mode_requires_scoped_evidence(self):
        state = approved_state()
        state["mode"] = "autonomous"
        state["approvals"] = []
        self.assertTrue(readiness_errors(state, "render", [1, 2]))
        state["approvals"] = approved_state()["approvals"]
        for entry in state["approvals"]:
            entry["decision"] = "delegated"
        for scene in state["scenes"]:
            scene["status"] = "in-review"
        self.assertEqual(readiness_errors(state, "render", [1, 2]), [])
        state["approvals"][0]["evidence"] = ""
        self.assertTrue(validate_state(state))

    def test_supersession_cannot_hide_feedback_in_a_cycle(self):
        state = approved_state()
        state["feedback"] = [
            {"id": identifier, "scope": "Scene1", "request": "Change the shot", "status": "superseded",
             "supersededBy": replacement, "history": [{"date": "2026-09-21", "note": "SIMULATED revision"}]}
            for identifier, replacement in (("F1", "F2"), ("F2", "F1"))]
        self.assertTrue(any("cycle" in error for error in validate_state(state)))

    def test_standalone_preflight_supports_legacy_and_explicit_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(root, approved_state())
            state = root / "decisions.json"
            (root / "production-state.json").rename(state)
            command = [sys.executable, str(SCRIPTS / "09_check_production.py"),
                       "--project-dir", str(root), "--stage", "render", "--production-state", str(state)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            state.write_text("{invalid JSON")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Cannot read production state", result.stderr)

    def test_invalid_state_shapes_fail_cleanly(self):
        for value in (None, [], {"version": 2}, {**approved_state(), "feedback": [None]},
                      {**approved_state(), "scenes": [{"scene": True}]}):
            self.assertTrue(validate_state(value))

    def test_missing_artifact_and_explicit_state_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(check_production(root, "implement", [1, 2]))
            with self.assertRaisesRegex(ValueError, "Missing production state"):
                check_production(root, "implement", [1, 2], root / "missing.json")
            prepare(root, approved_state())
            (root / "asset-plan.md").unlink()
            with self.assertRaisesRegex(ValueError, "asset-plan.md"):
                check_production(root, "implement", [1, 2])

    def test_scaffold_blocks_before_writes_and_keeps_legacy_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = approved_state()
            state["assetsReadyRevision"] = None  # unresolved required asset
            prepare(root, state)
            result = subprocess.run(scaffold_command(root), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("assets", result.stderr)
            self.assertFalse((root / "package.json").exists())
            (root / "production-state.json").unlink()
            result = subprocess.run(scaffold_command(root), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "src/Root.tsx").exists())

    def test_review_preserves_history_and_blocked_render_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = approved_state()
            state["approvals"].pop()  # plan ready, video not yet approved
            prepare(root, state)
            subprocess.run(scaffold_command(root), check=True, capture_output=True)
            command = [sys.executable, str(SCRIPTS / "05_review_bundle.py"), "--project-dir", str(root)]
            blocked = subprocess.run(command + ["--render"], capture_output=True, text=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("video", blocked.stderr)
            self.assertFalse((root / "out/review").exists())
            original = (root / "production-state.json").read_bytes()
            subprocess.run(command, check=True, capture_output=True)
            report = root / "out/review/review.md"
            report.write_text("User observation: the join needs more room.\n")
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual((root / "out/review/review-previous-1.md").read_text(),
                             "User observation: the join needs more room.\n")
            self.assertEqual((root / "production-state.json").read_bytes(), original)

    @unittest.skipUnless(os.environ.get("VIDEO_PRODUCTION_SMOKE_AUDIO") and os.environ.get("VIDEO_PRODUCTION_NODE_MODULES"),
                         "Set VIDEO_PRODUCTION_SMOKE_AUDIO and VIDEO_PRODUCTION_NODE_MODULES for real render")
    def test_real_two_scene_master_render(self):
        """Reuse local speech; all approval records here are explicitly synthetic."""
        with tempfile.TemporaryDirectory(prefix="video-production-workflow-") as directory:
            root = Path(directory)
            state = approved_state()
            prepare(root, state)
            audio_dir = Path(os.environ["VIDEO_PRODUCTION_SMOKE_AUDIO"]).resolve()
            rows = json.loads((audio_dir / "metadata.json").read_text())["scenes"][:2]
            self.assertEqual([row["scene"] for row in rows], [1, 2])
            target = root / "public/audio"
            target.mkdir(parents=True)
            for row in rows:
                filename = row["file"]
                shutil.copy2(audio_dir / filename, target / filename)
                timestamps = row.get("timestamps_file", f"{Path(filename).stem}-timestamps.json")
                shutil.copy2(audio_dir / timestamps, target / timestamps)
            (root / "metadata.json").write_text(json.dumps({"scenes": rows}))
            (root / "transcript.txt").write_text("\n---\n".join(row["text"] for row in rows))
            subprocess.run(scaffold_command(root), check=True, capture_output=True)
            (root / "node_modules").symlink_to(Path(os.environ["VIDEO_PRODUCTION_NODE_MODULES"]).resolve(), target_is_directory=True)
            media = root / "public/media"
            media.mkdir()
            # Original vector cutout and environment are isolated technical fixtures.
            (root / "assets").mkdir()
            for name, svg in {
                "subject.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160"><circle cx="60" cy="32" r="24" fill="white"/><rect x="30" y="60" width="60" height="95" rx="20" fill="white"/></svg>',
                "room.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><path fill="#233348" d="M0 0h640v360H0z"/><path fill="#496173" d="M0 250h640v110H0z"/></svg>'
            }.items():
                (root / "assets" / name).write_text(svg)
                shutil.copy2(root / "assets" / name, media / name)
            for number in (1, 2):
                (root / f"src/scenes/Scene{number}.tsx").write_text(
                    'import React from "react";\nimport {AbsoluteFill, Img, staticFile} from "remotion";\n'
                    'import type {VisualSceneProps} from "../Timeline";\n'
                    f'export const Scene{number}: React.FC<VisualSceneProps> = ({{contentFrame}}) => '
                    '<AbsoluteFill><Img src={staticFile("media/room.svg")} style={{width:"100%",height:"100%"}}/>'
                    '<Img src={staticFile("media/subject.svg")} style={{position:"absolute",left:80+Math.min(contentFrame,45),top:60,width:120}}/>'
                    f'<div style={{{{position:"absolute",left:340,top:80,width:70,height:70,borderRadius:35,background:"{("#f5bb66" if number == 1 else "#76c8b8")}",transform:`scale(${{1+Math.min(contentFrame,30)/60}})`}}}}/>'
                    '</AbsoluteFill>;\n')
            result = subprocess.run([str(root / "node_modules/.bin/tsc"), "--noEmit"], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([sys.executable, str(SCRIPTS / "05_review_bundle.py"), "--project-dir", str(root), "--render"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-3000:])
            probe = json.loads((root / "out/review/probe.json").read_text())
            self.assertEqual({stream["codec_type"] for stream in probe["streams"]}, {"audio", "video"})
            video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
            self.assertEqual((video["width"], video["height"], video["r_frame_rate"]), (640, 360, "15/1"))
            frames = sum(math.ceil(row["duration_s"] * 15) for row in rows)
            self.assertAlmostEqual(float(probe["format"]["duration"]), frames / 15, delta=.1)
            manifest = json.loads((root / "out/review/manifest.json").read_text())
            self.assertIn(frames - 1, manifest["frames"])
            self.assertEqual(manifest["completedCommands"], len(manifest["commands"]))
            self.assertEqual(manifest["playbackReview"], "not performed")
            # Decode the final video frame and compare with its exact-frame still.
            cli = ["ffmpeg", "-v", "error", "-i", str(root / "out/review/VideoFull.mp4"),
                   "-vf", f"select=eq(n\\,{frames - 1})", "-frames:v", "1", str(root / "last.png")]
            subprocess.run(cli, check=True, capture_output=True)
            last_index = manifest["frames"].index(frames - 1)
            comparison = subprocess.run(["ffmpeg", "-i", str(root / "last.png"), "-i",
                str(root / f"out/review/frame-{last_index:04d}.png"), "-lavfi", "ssim", "-f", "null", "-"],
                check=True, capture_output=True, text=True)
            import re
            score = float(re.search(r"All:([0-9.]+)", comparison.stderr).group(1))
            self.assertGreater(score, .95)
            print(f"Real workflow smoke: {frames} frames, 640x360/15fps, final-frame SSIM {score:.4f}; playback review not performed.")


if __name__ == "__main__":
    unittest.main()
