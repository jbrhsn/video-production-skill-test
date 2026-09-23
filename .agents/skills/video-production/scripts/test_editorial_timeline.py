from __future__ import annotations

import unittest

from editorial_timeline import compile_timeline, validate_timeline
from route_production import route


def sources():
    digest = "a" * 64
    return {"schema": "source-manifest", "version": 3, "sources": [
        {"id": "camera", "path": "public/media/camera.mp4", "sha256": digest, "durationUs": 20_000_000,
         "streams": [{"id": "video-0", "kind": "video", "durationUs": 20_000_000, "width": 1920, "height": 1080, "frameRate": {"num": 30, "den": 1}},
                     {"id": "audio-0", "kind": "audio", "durationUs": 20_000_000}]}
    ]}


def timeline():
    return {"schema": "editorial-timeline", "version": 2,
            "sequence": {"id": "master", "fps": {"num": 30, "den": 1}, "width": 1920, "height": 1080},
            "tracks": [{"id": "dialogue", "kind": "audio", "role": "primary-dialogue"},
                       {"id": "picture", "kind": "video", "role": "primary-picture"}],
            "clips": [
                {"id": "dialogue-a", "trackId": "dialogue", "sourceId": "camera", "streamId": "audio-0",
                 "sourceRangeUs": [0, 5_000_000], "timelineStartUs": 0, "playbackRate": {"num": 1, "den": 1}},
                {"id": "picture-a", "trackId": "picture", "sourceId": "camera", "streamId": "video-0",
                 "sourceRangeUs": [0, 5_000_000], "timelineStartUs": 0, "playbackRate": {"num": 1, "den": 1}},
                {"id": "dialogue-b", "trackId": "dialogue", "sourceId": "camera", "streamId": "audio-0",
                 "sourceRangeUs": [12_000_000, 18_000_000], "timelineStartUs": 5_000_000, "playbackRate": {"num": 1, "den": 1}},
                {"id": "picture-b", "trackId": "picture", "sourceId": "camera", "streamId": "video-0",
                 "sourceRangeUs": [12_600_000, 18_000_000], "timelineStartUs": 5_600_000, "playbackRate": {"num": 1, "den": 1}}
            ],
            "dialogueWords": [
                {"id": "w-a", "word": "before", "sourceId": "camera", "streamId": "audio-0", "sourceRangeUs": [1_000_000, 1_300_000]},
                {"id": "w-b", "word": "after", "sourceId": "camera", "streamId": "audio-0", "sourceRangeUs": [12_600_000, 13_000_000]}
            ]}


class EditorialTimelineTests(unittest.TestCase):
    def test_j_cut_has_independent_picture_and_dialogue_clock(self):
        compiled = compile_timeline(timeline(), sources())
        picture = next(clip for clip in compiled["clips"] if clip["id"] == "picture-b")
        dialogue = next(clip for clip in compiled["clips"] if clip["id"] == "dialogue-b")
        self.assertEqual((dialogue["startFrame"], picture["startFrame"]), (150, 168))
        self.assertEqual(picture["durationFrames"], 162)
        self.assertEqual(picture["src"], "media/camera.mp4")
        caption = next(item for item in compiled["captions"] if item["sourceWordId"] == "w-b")
        self.assertEqual(caption["clipId"], "dialogue-b")
        self.assertAlmostEqual(caption["start"], 5.6)

    def test_repeated_dialogue_source_creates_two_caption_occurrences(self):
        data = timeline()
        repeated = dict(data["clips"][2], id="dialogue-b-repeat", timelineStartUs=11_000_000)
        data["clips"].append(repeated)
        compiled = compile_timeline(data, sources())
        matches = [item for item in compiled["captions"] if item["sourceWordId"] == "w-b"]
        self.assertEqual([item["clipId"] for item in matches], ["dialogue-b", "dialogue-b-repeat"])
        self.assertAlmostEqual(matches[1]["start"], 11.6)

    def test_primary_dialogue_overlap_fails(self):
        data = timeline()
        data["clips"].append({"id": "dialogue-overlap", "trackId": "dialogue", "sourceId": "camera", "streamId": "audio-0",
                              "sourceRangeUs": [8_000_000, 9_000_000], "timelineStartUs": 5_100_000,
                              "playbackRate": {"num": 1, "den": 1}})
        with self.assertRaisesRegex(ValueError, "overlapping"):
            validate_timeline(data, sources())

    def test_source_bounds_fail_before_compile(self):
        data = timeline()
        data["clips"][0]["sourceRangeUs"] = [0, 21_000_000]
        with self.assertRaisesRegex(ValueError, "bounds"):
            compile_timeline(data, sources())

    def test_router_selects_all_four_routes(self):
        self.assertEqual(route({"recordedMedia": False, "generatedNarration": True, "needsExplanation": False, "autonomy": "guided"})["route"], "faceless-standard")
        self.assertEqual(route({"recordedMedia": False, "generatedNarration": True, "needsExplanation": True, "autonomy": "guided"})["route"], "faceless-editorial")
        self.assertEqual(route({"recordedMedia": True, "generatedNarration": False, "needsExplanation": False, "autonomy": "producer"})["route"], "recorded-edit")
        self.assertEqual(route({"recordedMedia": True, "generatedNarration": False, "needsExplanation": True, "autonomy": "autonomous"})["route"], "hybrid-editorial-edit")


if __name__ == "__main__":
    unittest.main()
