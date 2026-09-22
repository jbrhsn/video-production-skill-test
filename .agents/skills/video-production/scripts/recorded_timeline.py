"""Compile a recorded edit into a deterministic Remotion timeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from recorded_contract import (read_json, validate_cut_plan, validate_recorded_execution,
                               validate_source_manifest, validate_sync_map, map_session_range_to_source)


def frame(us: int, fps: int) -> int:
    return round(us * fps / 1_000_000)


def public_src(path: str) -> str:
    return path[len("public/"):] if path.startswith("public/") else path


def compile_recorded(manifest, sync, cut, execution, words=None):
    sources = validate_source_manifest(manifest)
    mappings = validate_sync_map(sync, sources)
    clips = validate_cut_plan(cut, sources, mappings)
    plan = validate_recorded_execution(execution, [clip["id"] for clip in clips])
    fps = plan["fps"]
    boundaries = [0]
    elapsed_us = 0
    for clip in clips:
        elapsed_us += clip["sessionRangeUs"][1] - clip["sessionRangeUs"][0]
        boundaries.append(frame(elapsed_us, fps))
    compiled = []
    scene_for = {clip_id: scene for scene in plan["scenes"] for clip_id in scene["clipIds"]}
    for index, clip in enumerate(clips):
        start_frame, end_frame = boundaries[index:index + 2]
        if end_frame <= start_frame:
            raise ValueError(f"clip {clip['id']} becomes empty at {fps} fps")
        session_start, session_end = clip["sessionRangeUs"]
        tracks = {}
        for role, source_id in clip["tracks"].items():
            source_start, source_end = map_session_range_to_source(mappings[source_id], clip["sessionRangeUs"], clip["id"])
            source = sources[source_id]
            playback_rate = (source_end - source_start) / (session_end - session_start)
            tracks[role] = {"sourceId": source_id, "src": public_src(source["stagedPath"]),
                            "sourceStartFrame": frame(source_start, fps), "sourceEndFrame": frame(source_end, fps),
                            "playbackRate": playback_rate,
                            "width": source.get("width"), "height": source.get("height")}
        audio_id = clip["primaryAudio"]["sourceId"]
        audio_start, audio_end = map_session_range_to_source(mappings[audio_id], clip["sessionRangeUs"], clip["id"])
        scene = scene_for[clip["id"]]
        layouts = []
        for event in scene.get("layoutEvents", []):
            if event["clipId"] == clip["id"]:
                if event["atUs"] + event.get("durationUs", 0) > session_end - session_start:
                    raise ValueError(f"layout event {event['id']} lies outside its clip")
                layouts.append({"id": event["id"], "atFrame": frame(event["atUs"], fps),
                                "durationFrames": frame(event.get("durationUs", 0), fps),
                                "layout": event["layout"], "corner": event.get("corner", "top-right")})
        layouts.sort(key=lambda item: item["atFrame"])
        if any(current["atFrame"] < max(previous["atFrame"] + 1,
                                          previous["atFrame"] + previous["durationFrames"])
               for previous, current in zip(layouts, layouts[1:])):
            raise ValueError(f"clip {clip['id']}: layout events must be distinct and cannot overlap")
        default = ("balanced" if set(tracks) == {"screen", "presenter"}
                   else "screen-only" if "screen" in tracks else "presenter-only")
        if not layouts or layouts[0]["atFrame"] != 0:
            layouts.insert(0, {"id": f"{clip['id']}-initial", "atFrame": 0,
                               "durationFrames": 0, "layout": default, "corner": "top-right"})
        clip_masks = []
        for mask in scene.get("masks", []):
            if mask["clipId"] == clip["id"]:
                if "screen" not in tracks:
                    raise ValueError(f"mask {mask['id']} requires an active screen track")
                if mask["clipRangeUs"][1] > session_end - session_start:
                    raise ValueError(f"mask {mask['id']} lies outside its clip")
                clip_masks.append({**mask, "startFrame": frame(mask["clipRangeUs"][0], fps),
                                   "endFrame": frame(mask["clipRangeUs"][1], fps)})
        compiled.append({"id": clip["id"], "scene": scene["scene"], "startFrame": start_frame,
                         "durationFrames": end_frame - start_frame, "tracks": tracks,
                         "audio": {"sourceId": audio_id, "src": public_src(sources[audio_id]["stagedPath"]),
                                   "sourceStartFrame": frame(audio_start, fps),
                                   "playbackRate": (audio_end - audio_start) / (session_end - session_start)},
                         "layouts": layouts, "masks": clip_masks})
    compiled_words = []
    for word in (words or {}).get("words", []):
        start_us, end_us = word.get("sessionRangeUs", [None, None])
        if type(start_us) is not int or type(end_us) is not int or end_us <= start_us:
            raise ValueError("source words require increasing sessionRangeUs")
        for index, clip in enumerate(clips):
            clip_start, clip_end = clip["sessionRangeUs"]
            if clip_start <= start_us and end_us <= clip_end:
                output_offset_us = sum(c["sessionRangeUs"][1] - c["sessionRangeUs"][0] for c in clips[:index])
                compiled_words.append({"id": word.get("id"), "word": word.get("word", ""),
                                       "start": (output_offset_us + start_us - clip_start) / 1_000_000,
                                       "end": (output_offset_us + end_us - clip_start) / 1_000_000})
                break
    scene_rows = []
    for scene in plan["scenes"]:
        rows = [row for row in compiled if row["scene"] == scene["scene"]]
        start = rows[0]["startFrame"]
        end = rows[-1]["startFrame"] + rows[-1]["durationFrames"]
        scene_rows.append({"scene": scene["scene"], "id": scene["id"], "startFrame": start,
                           "durationFrames": end - start})
    return {"version": 3, "track": "recorded-edit", "fps": fps, "width": plan["width"],
            "height": plan["height"], "totalFrames": boundaries[-1], "clips": compiled,
            "scenes": scene_rows, "words": compiled_words,
            "safeArea": plan.get("safeArea", {"top": .06, "right": .06, "bottom": .12, "left": .06})}


def compile_project(project: Path):
    words_path = project / "transcript/source-words.json"
    timeline = compile_recorded(read_json(project / "source/manifest.json"),
                                read_json(project / "sync/map.json"),
                                read_json(project / "cut-plan.json"),
                                read_json(project / "execution-plan.json"),
                                read_json(words_path) if words_path.is_file() else None)
    return timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    timeline = compile_project(project)
    output = Path(args.out).expanduser().resolve() if args.out else project / "src/timeline-data.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    print(f"Compiled {len(timeline['clips'])} clips, {timeline['totalFrames']} frames -> {output}")


if __name__ == "__main__":
    main()
