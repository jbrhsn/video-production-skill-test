from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from editorial_timeline import compile_timeline
from qc_timeline import check_timeline
from analyze_editorial import analyze
from production_workflow import check_export, snapshot
from style_profile import resolve_style
from test_editorial_timeline import sources, timeline
from visual_events import validate_visual_events


SCRIPTS = Path(__file__).parent


class ProductionSystemTests(unittest.TestCase):
    def setUp(self):
        catalog_path = Path(__file__).parent.parent / "assets/style-profiles.json"
        self.catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.render_timeline = compile_timeline(timeline(), sources())

    def test_style_resolution_is_deterministic_and_records_origins(self):
        first = resolve_style(self.catalog, {"profile": "premium-documentary"},
                              {"tokens": {"captions": {"fontFamily": "Inter"}}},
                              {"captions": {"maxLines": 3}})
        second = resolve_style(self.catalog, {"profile": "premium-documentary"},
                               {"tokens": {"captions": {"fontFamily": "Inter"}}},
                               {"captions": {"maxLines": 3}})
        self.assertEqual(first["digest"], second["digest"])
        self.assertEqual(first["values"]["captions"]["maxLines"], 3)
        self.assertEqual(first["provenance"]["captions.maxLines"], "project")

    def test_hybrid_event_requires_dialogue_occurrence_and_reentry(self):
        event = {"schema": "visual-story-events", "version": 1, "events": [{
            "id": "map-takeover", "dialogueClipId": "dialogue-b", "frames": [150, 180],
            "purpose": "Explain expansion", "presentation": "map",
            "layers": {"background": ["code:map"], "midground": ["code:countries"], "foreground": ["code:arrows"]},
            "sequence": ["reveal-map", "highlight-expansion"],
            "reentry": {"method": "motion-match", "sourceClipId": "picture-b"},
            "acceptance": "The expansion is visible before the speaker returns"}]}
        self.assertEqual(validate_visual_events(event, self.render_timeline)[0]["id"], "map-takeover")
        event["events"][0]["reentry"]["sourceClipId"] = "missing"
        with self.assertRaisesRegex(ValueError, "re-entry"):
            validate_visual_events(event, self.render_timeline)

    def test_timeline_qc_reports_out_of_bounds_caption(self):
        report = check_timeline(self.render_timeline)
        self.assertEqual(report["status"], "pass")
        bad = {**self.render_timeline, "captions": [{"id": "bad", "start": 0, "end": 20}]}
        self.assertEqual(check_timeline(bad)["status"], "fail")

    def test_scaffold_generates_lane_renderer_without_installing_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "editorial").mkdir()
            (root / "source").mkdir()
            (root / "editorial/timeline.json").write_text(json.dumps(timeline()), encoding="utf-8")
            (root / "source/manifest.json").write_text(json.dumps(sources()), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "13_scaffold_production.py"),
                                     "--project-dir", str(root), "--skip-install"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            compiled = json.loads((root / "src/timeline-data.json").read_text())
            self.assertEqual(compiled["clips"][0]["src"], "media/camera.mp4")
            self.assertIn("EditorialTimeline", (root / "src/Root.tsx").read_text())
            self.assertTrue((root / "scripts/production/run_qc.py").is_file())
            self.assertTrue((root / "scripts/production/qc_production.py").is_file())

    def test_style_catalog_contains_all_twenty_direct_profiles(self):
        self.assertEqual(len(self.catalog["profiles"]), 20)
        self.assertEqual(self.catalog["profiles"]["screen-recording-tutorial"]["family"], "recorded")

    def test_editorial_analysis_preserves_repeats_as_candidates(self):
        transcript = {"schema": "corrected-transcript", "version": 2, "words": [
            {"id": "w1", "word": "This", "start": 0, "end": .2},
            {"id": "w2", "word": "is", "start": .2, "end": .3},
            {"id": "w3", "word": "important.", "start": .3, "end": .6},
            {"id": "w4", "word": "This", "start": 2, "end": 2.2},
            {"id": "w5", "word": "is", "start": 2.2, "end": 2.3},
            {"id": "w6", "word": "important.", "start": 2.3, "end": 2.6}
        ]}
        report = analyze(transcript)
        self.assertEqual(report["events"][0]["type"], "silence")
        repeated = next(row for row in report["candidates"] if row["type"] == "candidate-repeated-phrase")
        self.assertTrue(repeated["requiresEditorialDecision"])

    def test_export_requires_current_master_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = {"schema": "video-production-project", "version": 1, "id": "project-1",
                       "route": "faceless-editorial", "autonomy": "guided",
                       "artifacts": {"timeline": "timeline/render.json", "state": "production-state.json",
                                     "assetLibraryReview": "analysis/asset-library-review.json"}}
            (root / "timeline").mkdir()
            (root / "analysis").mkdir()
            (root / "timeline/render.json").write_text("{}", encoding="utf-8")
            (root / "analysis/asset-library-review.json").write_text(json.dumps({
                "schema": "video-production-asset-library-review", "version": 1, "route": "faceless-editorial",
                "assetsDir": ".video_production_assets", "collections": ["images"],
                "queries": [{"beatId": "b1", "query": "map", "candidates": []}],
                "dispositions": [{"beatId": "b1", "outcome": "no-fit", "reason": "Fixture uses code graphics."}]}), encoding="utf-8")
            (root / "project.json").write_text(json.dumps(project), encoding="utf-8")
            state = {"schema": "production-state", "version": 1, "projectId": "project-1", "route": "faceless-editorial",
                     "autonomy": "guided", "phase": "master-review", "pendingReview": None, "approvals": [], "feedback": []}
            state["approvals"].append({"scope": "master", "decision": "approved", "target": "VideoFull", "snapshot": snapshot(root, project), "evidence": "fixture"})
            (root / "production-state.json").write_text(json.dumps(state), encoding="utf-8")
            self.assertEqual(check_export(root)["approval"]["scope"], "master")
            (root / "timeline/render.json").write_text('{"changed":true}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                check_export(root)


if __name__ == "__main__":
    unittest.main()
