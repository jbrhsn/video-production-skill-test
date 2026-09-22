from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from recorded_contract import validate_source_manifest
from recorded_timeline import compile_project
from recorded_workflow import check_v3, snapshot


SCRIPTS = Path(__file__).parent


class RecordedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ("source", "sync", "transcript", "analysis", "public/media"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        sources = []
        for source_id, role, payload in (("screen", "screen", b"screen-fixture"),
                                         ("presenter", "presenter", b"presenter-fixture")):
            path = self.root / f"public/media/{source_id}.mp4"
            path.write_bytes(payload)
            sources.append({"id": source_id, "role": role, "stagedPath": f"public/media/{source_id}.mp4",
                            "sha256": hashlib.sha256(payload).hexdigest(), "durationUs": 12_100_000,
                            "width": 1920 if role == "screen" else 1280,
                            "height": 1080 if role == "screen" else 720})
        self.write("source/manifest.json", {"version": 1, "track": "recorded-edit", "sources": sources})
        self.write("sync/map.json", {"version": 1, "referenceSourceId": "presenter", "mappings": [
            {"sourceId": "presenter", "sections": [{"sessionRangeUs": [0, 12_000_000],
                "sourceRangeUs": [0, 12_000_000], "status": "confirmed"}]},
            {"sourceId": "screen", "sections": [{"sessionRangeUs": [0, 12_000_000],
                "sourceRangeUs": [100_000, 12_100_000], "status": "confirmed"}]},
        ]})
        self.write("cut-plan.json", {"version": 1, "track": "recorded-edit", "clips": [
            {"id": "c1", "sessionRangeUs": [0, 4_000_000], "tracks": {"screen": "screen", "presenter": "presenter"},
             "primaryAudio": {"sourceId": "presenter"}},
            {"id": "c2", "sessionRangeUs": [5_000_000, 12_000_000], "tracks": {"screen": "screen", "presenter": "presenter"},
             "primaryAudio": {"sourceId": "presenter"}},
        ]})
        self.write("transcript/source-words.json", {"version": 1, "words": [
            {"id": "w1", "word": "keep", "sessionRangeUs": [1_000_000, 1_400_000]},
            {"id": "w2", "word": "cut", "sessionRangeUs": [4_200_000, 4_500_000]},
            {"id": "w3", "word": "theory", "sessionRangeUs": [6_000_000, 6_500_000]},
        ]})
        self.write("execution-plan.json", {"version": 3, "track": "recorded-edit", "fps": 30,
            "width": 1920, "height": 1080, "scenes": [
                {"scene": 1, "id": "intro", "clipIds": ["c1"], "layoutEvents": [
                    {"id": "l1", "clipId": "c1", "atUs": 0, "durationUs": 0, "layout": "screen-focus"},
                    {"id": "l2", "clipId": "c1", "atUs": 2_000_000, "durationUs": 500_000,
                     "layout": "presenter-focus", "corner": "bottom-right"}], "masks": []},
                {"scene": 2, "id": "demo", "clipIds": ["c2"], "layoutEvents": [], "masks": [
                    {"id": "m1", "clipId": "c2", "clipRangeUs": [1_000_000, 2_000_000],
                     "rect": [.1, .1, .2, .1], "strategy": "solid"}]},
            ]})
        self.write("design-system.json", {"version": 1, "captions": {"fontFamily": "Arial",
            "text": "#fff", "background": "#111", "active": "#ff0", "radius": 4}})
        for name in ("brief.md", "storyboard.json", "edit-plan.json", "asset-plan.md", "asset-manifest.json",
                     "implementation-plan.md", "source/derivatives.json", "analysis/observations.json",
                     "analysis/cut-proposals.json", "source/sensitive-regions.json"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[]\n" if path.suffix == ".json" else "fixture\n")
        self.state = {"version": 3, "track": "recorded-edit", "mode": "collaborative", "phase": "implementation",
            "sourceRevision": "source-1", "editRevision": "edit-1", "planRevision": "plan-1",
            "projectRevision": "project-1", "activeScene": 1, "reviewOrder": [1, 2], "pendingReview": None,
            "approvals": [], "scenes": [{"scene": 1, "revision": "scene-1", "status": "pending"},
                                        {"scene": 2, "revision": "scene-1", "status": "pending"}], "feedback": []}
        self.approve("source", "source-1")
        self.approve("edit", "edit-1")
        self.approve("plan", "plan-1")

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")

    def approve(self, scope, revision):
        self.state["approvals"].append({"scope": scope, "revision": revision, "decision": "approved",
            "date": "2026-01-01T00:00:00Z", "evidence": "fixture approval", "reviewTarget": scope,
            "snapshot": snapshot(self.root, scope)})
        self.write("production-state.json", self.state)

    def test_compiler_keeps_parallel_tracks_and_remaps_words(self):
        data = compile_project(self.root)
        self.assertEqual(data["totalFrames"], 330)
        self.assertEqual(len(data["words"]), 2)
        self.assertAlmostEqual(data["words"][1]["start"], 5.0)
        self.assertEqual(data["clips"][0]["tracks"]["screen"]["sourceStartFrame"], 3)
        self.assertEqual(data["clips"][0]["layouts"][1]["layout"], "presenter-focus")
        self.assertEqual(data["clips"][1]["masks"][0]["startFrame"], 30)

    def test_stale_source_and_plan_are_rejected(self):
        check_v3(self.root, self.state, "implement")
        (self.root / "public/media/screen.mp4").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "immutable hash"):
            check_v3(self.root, self.state, "implement")

    def test_review_order_allows_interior_pilot(self):
        self.state["reviewOrder"] = [2, 1]
        self.state["activeScene"] = 2
        self.write("production-state.json", self.state)
        check_v3(self.root, self.state, "scene", scene=2, draft=True)

    def test_scaffold_writes_recorded_contract_without_install(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "11_scaffold_recorded.py"),
            "--project-dir", str(self.root), "--skip-install"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        marker = json.loads((self.root / "src/timeline-contract.json").read_text())
        self.assertEqual(marker, {"version": 3, "track": "recorded-edit"})
        self.assertIn("playbackRate", (self.root / "src/RecordedTimeline.tsx").read_text())
        self.assertEqual(json.loads((self.root / "src/timeline-data.json").read_text())["totalFrames"], 330)
        modules = os.environ.get("VIDEO_PRODUCTION_NODE_MODULES")
        if modules:
            (self.root / "node_modules").symlink_to(Path(modules).resolve(), target_is_directory=True)
            checked = subprocess.run(["npm", "run", "typecheck"], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_manifest_rejects_changed_media(self):
        validate_source_manifest(json.loads((self.root / "source/manifest.json").read_text()), self.root)
        (self.root / "public/media/presenter.mp4").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "immutable hash"):
            validate_source_manifest(json.loads((self.root / "source/manifest.json").read_text()), self.root)

    def test_clip_must_split_at_sync_section_boundary(self):
        sync = json.loads((self.root / "sync/map.json").read_text())
        sync["mappings"][0]["sections"] = [
            {"sessionRangeUs": [0, 6_000_000], "sourceRangeUs": [0, 6_000_000], "status": "confirmed"},
            {"sessionRangeUs": [6_000_000, 12_000_000], "sourceRangeUs": [6_000_000, 12_000_000], "status": "confirmed"},
        ]
        self.write("sync/map.json", sync)
        with self.assertRaisesRegex(ValueError, "split the clip"):
            compile_project(self.root)

    def test_ingest_probes_and_stages_immutable_source(self):
        case = self.root / "ingest-case"
        source = self.root / "incoming.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "color=c=blue:s=160x90:r=30:d=0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        str(source)], check=True)
        intake = self.root / "intake.json"
        intake.write_text(json.dumps({"sources": [{"id": "camera", "path": str(source), "role": "presenter"}]}))
        result = subprocess.run([sys.executable, str(SCRIPTS / "12_ingest_recorded.py"),
                                 "--project-dir", str(case), "--intake", str(intake)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((case / "source/manifest.json").read_text())
        self.assertEqual((manifest["sources"][0]["width"], manifest["sources"][0]["height"]), (160, 90))
        self.assertTrue((case / "source/raw/camera.mp4").is_file())

    @unittest.skipUnless(os.environ.get("VIDEO_PRODUCTION_RENDER_SMOKE") and os.environ.get("VIDEO_PRODUCTION_NODE_MODULES"),
                         "Set VIDEO_PRODUCTION_RENDER_SMOKE and VIDEO_PRODUCTION_NODE_MODULES for a real recorded render")
    def test_real_parallel_render_and_guards(self):
        for source_id, color, tone, duration in (("presenter", "#2d68c4", 440, "12.1"),
                                                  ("screen", "#e8edf4", 660, "12.1")):
            output = self.root / f"public/media/{source_id}.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                f"color=c={color}:s=640x360:r=30:d={duration}", "-f", "lavfi", "-i",
                f"sine=frequency={tone}:sample_rate=48000:duration={duration}", "-shortest",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(output)], check=True)
        manifest = json.loads((self.root / "source/manifest.json").read_text())
        for row in manifest["sources"]:
            path = self.root / row["stagedPath"]
            row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            row["width"], row["height"] = 640, 360
        self.write("source/manifest.json", manifest)
        execution = json.loads((self.root / "execution-plan.json").read_text())
        execution["width"], execution["height"] = 640, 360
        self.write("execution-plan.json", execution)
        self.state["approvals"] = []
        self.approve("source", "source-1"); self.approve("edit", "edit-1"); self.approve("plan", "plan-1")
        result = subprocess.run([sys.executable, str(SCRIPTS / "11_scaffold_recorded.py"),
            "--project-dir", str(self.root), "--skip-install"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (self.root / "node_modules").symlink_to(Path(os.environ["VIDEO_PRODUCTION_NODE_MODULES"]).resolve(), target_is_directory=True)
        self.state["phase"] = "final-review"
        self.state["activeScene"] = None
        for row in self.state["scenes"]:
            row["status"] = "approved"
            self.approve(f"scene:{row['scene']}", row["revision"])
        self.approve("video", self.state["projectRevision"])
        for task in ("typecheck", "render", "hero"):
            result = subprocess.run(["npm", "run", task], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,width,height,nb_frames", "-of", "json", str(self.root / "out/video.mp4")],
            check=True, capture_output=True, text=True)
        streams = json.loads(probe.stdout)["streams"]
        self.assertEqual({row["codec_type"] for row in streams}, {"audio", "video"})
        video = next(row for row in streams if row["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"], video["nb_frames"]), (640, 360, "330"))
        self.assertTrue((self.root / "out/video-hero.png").is_file())


if __name__ == "__main__":
    unittest.main()
