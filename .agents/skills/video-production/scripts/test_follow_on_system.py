from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analyze_editorial import analyze
from build_state import plan
from editorial_timeline import compile_timeline, validate_timeline
from interchange import export_manifest, srt
from qc_production import bounded_repair, check
from test_editorial_timeline import sources, timeline
from tracking import validate as validate_tracking
from visual_events import validate_visual_events


class FollowOnTests(unittest.TestCase):
    def test_generated_and_freeze_lanes_compile_without_stopping_dialogue(self):
        data = timeline()
        data["tracks"].append({"id": "graphics", "kind": "generated", "role": "graphics", "allowOverlap": True, "zIndex": 2})
        data["clips"].append({"id": "chart", "trackId": "graphics", "timelineStartUs": 5_000_000, "timelineDurationUs": 1_000_000, "generator": "chart", "payload": {"title": "Proof", "items": ["A", "B"]}})
        data["clips"][1].update({"freezeFrameUs": 1_000_000, "freezeAssetPath": "public/assets/freeze.png"})
        compiled = compile_timeline(data, sources())
        self.assertEqual(next(row for row in compiled["clips"] if row["id"] == "chart")["kind"], "generated")
        self.assertTrue(next(row for row in compiled["clips"] if row["id"] == "picture-a")["freezeFrameUs"])
        self.assertEqual(next(row for row in compiled["clips"] if row["id"] == "dialogue-a")["durationFrames"], 150)

    def test_events_require_dialogue_and_are_compiled(self):
        event = {"schema": "visual-story-events", "version": 1, "events": [{"id": "takeover", "dialogueClipId": "dialogue-b", "frames": [150, 170], "purpose": "Show relationship", "presentation": "chart", "layers": {"background": ["code:grid"], "midground": ["code:bars"]}, "sequence": ["reveal"], "reentry": {"method": "cut", "sourceClipId": "picture-b"}, "acceptance": "Bars appear"}]}
        compiled = compile_timeline(timeline(), sources(), event)
        self.assertEqual(compiled["visualEvents"][0]["id"], "takeover")
        event["events"][0]["dialogueClipId"] = "picture-b"
        with self.assertRaisesRegex(ValueError, "primary dialogue"):
            validate_visual_events(event, compiled)

    def test_analysis_reports_context_and_unavailable_detectors(self):
        report = analyze({"schema": "corrected-transcript", "version": 2, "words": [{"id": "a", "word": "That", "start": 0, "end": .2}, {"id": "b", "word": "is.", "start": .2, "end": .4}, {"id": "c", "word": "Actually", "start": 2.5, "end": 2.8}, {"id": "d", "word": "better.", "start": 2.8, "end": 3.1}]})
        self.assertTrue(report["unavailableDetectors"])
        self.assertIn("candidate-context-dependent-extract", {row["type"] for row in report["candidates"]})
        self.assertEqual(report["events"][0]["classification"], "dramatic")

    def test_qc_never_calls_uninstrumented_coverage_a_pass_and_repair_is_bounded(self):
        report = check(compile_timeline(timeline(), sources()), {"schema": "render-observations", "version": 1, "coverage": {"layout": "unavailable"}, "findings": [{"rule": "asset.missing", "severity": "error", "frames": [2, 3]}]})
        self.assertEqual(report["coverage"]["layout"], "unavailable")
        repairs = bounded_repair(report, {"enabledRules": ["asset.missing"], "maxRepairs": 1})
        self.assertEqual(repairs["repairs"][0]["status"], "queued")

    def test_tracking_and_interchange_are_explicit_about_coordinates_and_fidelity(self):
        tracking = validate_tracking({"schema": "source-tracking", "version": 1, "sourceId": "camera", "coordinateSpace": "source-pixels", "tracks": [{"id": "face", "kind": "face", "frames": [0, 5], "confidence": .9, "points": [{"frame": 0, "x": 1, "y": 2, "width": 20, "height": 30}]}]})
        self.assertEqual(tracking["coordinateSpace"], "source-pixels")
        compiled = compile_timeline(timeline(), sources())
        handoff = export_manifest(compiled, sources(), compiled["captions"])
        self.assertIn("constant-positive-rate", handoff["fidelity"]["native"])
        self.assertIn("-->", srt(compiled["captions"]))

    def test_content_hash_change_invalidates_resumable_build(self):
        prior = plan(["one"], {"timeline": "a"}); prior["chapters"]["one"] = "complete"
        self.assertEqual(plan(["one"], {"timeline": "a"}, prior)["chapters"]["one"], "cached")
        self.assertTrue(plan(["one"], {"timeline": "b"}, prior)["resume"]["invalidated"])


if __name__ == "__main__": unittest.main()
