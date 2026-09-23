"""Validate and compile the canonical lane-based editorial timeline."""
from __future__ import annotations

import math
from fractions import Fraction

from contracts import TRACK_KINDS, TRACK_ROLES, integer, rational, text, time_range, validate_source_manifest


def _floor(time_us: Fraction, fps: Fraction) -> int:
    return time_us.numerator * fps.numerator // (time_us.denominator * fps.denominator * 1_000_000)


def _ceil(time_us: Fraction, fps: Fraction) -> int:
    return math.ceil(time_us.numerator * fps.numerator / (time_us.denominator * fps.denominator * 1_000_000))


def _duration(source_range, rate: Fraction) -> Fraction:
    return Fraction(source_range[1] - source_range[0], 1) / rate


def _source_clip(raw, tracks, sources):
    required = {"id", "trackId", "sourceId", "streamId", "sourceRangeUs", "timelineStartUs", "playbackRate"}
    allowed = required | {"freezeFrameUs", "transitionInUs", "transitionOutUs", "replaceSourceId"}
    if not isinstance(raw, dict) or not required.issubset(raw) or set(raw) - allowed:
        raise ValueError("source clip fields are invalid")
    clip_id = text(raw.get("id"), "clip.id")
    track = tracks.get(raw.get("trackId"))
    source = sources.get(raw.get("sourceId"))
    if track is None or source is None:
        raise ValueError(f"clip {clip_id} has an unknown track or source")
    stream = source["streams"].get(raw.get("streamId"))
    if stream is None or stream["kind"] != track["kind"]:
        raise ValueError(f"clip {clip_id} stream kind must match track kind")
    source_range = time_range(raw.get("sourceRangeUs"), f"clip {clip_id}.sourceRangeUs")
    if source_range[1] > stream["durationUs"]:
        raise ValueError(f"clip {clip_id} exceeds source stream bounds")
    rate = rational(raw.get("playbackRate"), f"clip {clip_id}.playbackRate")
    start = integer(raw.get("timelineStartUs"), f"clip {clip_id}.timelineStartUs")
    for name in ("transitionInUs", "transitionOutUs"):
        if name in raw and integer(raw[name], f"clip {clip_id}.{name}") * 2 >= source_range[1] - source_range[0]:
            raise ValueError(f"clip {clip_id}.{name} leaves no transition handle")
    frozen = raw.get("freezeFrameUs")
    if frozen is not None and (track["kind"] != "video" or type(frozen) is not int or not source_range[0] <= frozen < source_range[1]):
        raise ValueError(f"clip {clip_id}.freezeFrameUs must be a video source position")
    if raw.get("replaceSourceId") is not None and raw["replaceSourceId"] not in sources:
        raise ValueError(f"clip {clip_id} replacement source is unknown")
    return {**raw, "id": clip_id, "track": track, "sourceRangeUs": source_range, "timelineStartUs": start,
            "playbackRate": rate, "timelineEndUs": Fraction(start, 1) + _duration(source_range, rate)}


def _generated_clip(raw, tracks):
    required = {"id", "trackId", "timelineStartUs", "timelineDurationUs", "generator", "payload"}
    if not isinstance(raw, dict) or set(raw) != required:
        raise ValueError("generated clip fields must be exact")
    clip_id = text(raw.get("id"), "generated clip.id")
    track = tracks.get(raw.get("trackId"))
    if track is None or track["kind"] != "generated":
        raise ValueError(f"generated clip {clip_id} requires a generated track")
    start, duration = integer(raw.get("timelineStartUs"), f"generated clip {clip_id}.timelineStartUs"), integer(raw.get("timelineDurationUs"), f"generated clip {clip_id}.timelineDurationUs", 1)
    if raw.get("generator") not in {"title", "shape", "chart", "map", "document", "system", "quote", "comparison", "timeline"} or not isinstance(raw.get("payload"), dict):
        raise ValueError(f"generated clip {clip_id} has unsupported generator or payload")
    return {**raw, "id": clip_id, "track": track, "timelineStartUs": start, "timelineEndUs": Fraction(start + duration, 1)}


def validate_timeline(data, manifest):
    sources = validate_source_manifest(manifest)
    if not isinstance(data, dict) or data.get("schema") != "editorial-timeline" or data.get("version") != 2:
        raise ValueError("timeline requires schema editorial-timeline version 2")
    if set(data) - {"schema", "version", "sequence", "tracks", "clips", "dialogueWords", "markers"}:
        raise ValueError("timeline contains unsupported fields")
    sequence = data.get("sequence")
    if not isinstance(sequence, dict) or set(sequence) != {"id", "fps", "width", "height"}:
        raise ValueError("timeline.sequence requires id, fps, width, and height")
    text(sequence.get("id"), "timeline.sequence.id")
    fps = rational(sequence.get("fps"), "timeline.sequence.fps")
    integer(sequence.get("width"), "timeline.sequence.width", 2); integer(sequence.get("height"), "timeline.sequence.height", 2)
    if not isinstance(data.get("tracks"), list) or not data["tracks"]:
        raise ValueError("timeline.tracks are required")
    tracks = {}
    for raw in data["tracks"]:
        if not isinstance(raw, dict) or set(raw) - {"id", "kind", "role", "allowOverlap", "zIndex", "pitchPolicy"}:
            raise ValueError("track contains unsupported fields")
        track_id = text(raw.get("id"), "track.id")
        if track_id in tracks or raw.get("kind") not in TRACK_KINDS or raw.get("role") not in TRACK_ROLES:
            raise ValueError(f"track {track_id} is invalid or duplicated")
        if type(raw.get("allowOverlap", False)) is not bool or raw.get("pitchPolicy", "preserve") not in {"preserve", "follow-rate", "mute"}:
            raise ValueError(f"track {track_id} has invalid overlap or pitch policy")
        tracks[track_id] = {**raw, "allowOverlap": raw.get("allowOverlap", False), "zIndex": raw.get("zIndex", 0), "pitchPolicy": raw.get("pitchPolicy", "preserve")}
    if not isinstance(data.get("clips"), list) or not data["clips"]:
        raise ValueError("timeline.clips are required")
    clips, ids = [], set()
    for raw in data["clips"]:
        if not isinstance(raw, dict): raise ValueError("clip must be an object")
        track = tracks.get(raw.get("trackId"))
        row = _generated_clip(raw, tracks) if track and track["kind"] == "generated" else _source_clip(raw, tracks, sources)
        if row["id"] in ids: raise ValueError("clip IDs identify occurrences and must be unique")
        ids.add(row["id"]); clips.append(row)
    for track_id, track in tracks.items():
        rows = sorted((row for row in clips if row["trackId"] == track_id), key=lambda row: row["timelineStartUs"])
        if not track["allowOverlap"] and any(current["timelineStartUs"] < previous["timelineEndUs"] for previous, current in zip(rows, rows[1:])):
            raise ValueError(f"track {track_id} has overlapping clips without allowOverlap")
    dialogue = [track for track in tracks.values() if track["role"] == "primary-dialogue"]
    if len(dialogue) != 1 or dialogue[0]["kind"] != "audio" or dialogue[0]["allowOverlap"]:
        raise ValueError("timeline requires one non-overlapping primary-dialogue audio track")
    return {"sequence": sequence, "fps": fps, "tracks": tracks, "clips": clips, "dialogueWords": data.get("dialogueWords", []), "markers": data.get("markers", []), "sources": sources}


def compile_timeline(data, manifest, visual_events=None):
    checked = validate_timeline(data, manifest); fps = checked["fps"]; output, total = [], 0
    for clip in checked["clips"]:
        start, end = _floor(Fraction(clip["timelineStartUs"], 1), fps), _ceil(clip["timelineEndUs"], fps)
        if end <= start: raise ValueError(f"clip {clip['id']} quantizes to no output frames")
        total = max(total, end)
        row = {"id": clip["id"], "trackId": clip["trackId"], "role": clip["track"]["role"], "startFrame": start, "durationFrames": end - start, "zIndex": clip["track"]["zIndex"]}
        if clip["track"]["kind"] == "generated":
            row.update({"kind": "generated", "generator": clip["generator"], "payload": clip["payload"]})
        else:
            stream = checked["sources"][clip["sourceId"]]["streams"][clip["streamId"]]
            row.update({"kind": stream["kind"], "sourceId": clip["sourceId"], "streamId": clip["streamId"], "src": checked["sources"][clip["sourceId"]]["path"].removeprefix("public/"), "sourceRangeUs": list(clip["sourceRangeUs"]), "playbackRate": {"num": clip["playbackRate"].numerator, "den": clip["playbackRate"].denominator}, "sourceFrameRate": ({"num": stream["frameRate"].numerator, "den": stream["frameRate"].denominator} if stream["kind"] == "video" else None), "freezeFrameUs": clip.get("freezeFrameUs"), "pitchPolicy": clip["track"]["pitchPolicy"]})
        output.append(row)
    word_ids, captions = set(), []
    dialogue_track = next(key for key, value in checked["tracks"].items() if value["role"] == "primary-dialogue")
    dialogue_clips = [clip for clip in checked["clips"] if clip["trackId"] == dialogue_track]
    for word in checked["dialogueWords"]:
        if not isinstance(word, dict) or set(word) != {"id", "word", "sourceId", "streamId", "sourceRangeUs"}: raise ValueError("dialogue word fields must be exact")
        word_id = text(word.get("id"), "dialogueWord.id")
        if word_id in word_ids: raise ValueError("dialogue word IDs must be unique")
        word_ids.add(word_id); interval = time_range(word.get("sourceRangeUs"), f"dialogue word {word_id}.sourceRangeUs")
        for clip in dialogue_clips:
            if clip.get("sourceId") == word.get("sourceId") and clip.get("streamId") == word.get("streamId") and clip["sourceRangeUs"][0] <= interval[0] and interval[1] <= clip["sourceRangeUs"][1]:
                start = Fraction(clip["timelineStartUs"], 1) + Fraction(interval[0] - clip["sourceRangeUs"][0], 1) / clip["playbackRate"]
                end = start + Fraction(interval[1] - interval[0], 1) / clip["playbackRate"]
                captions.append({"id": f"{word_id}@{clip['id']}", "sourceWordId": word_id, "clipId": clip["id"], "word": word["word"], "start": float(start / 1_000_000), "end": float(end / 1_000_000)})
    events = []
    if visual_events is not None:
        from visual_events import validate_visual_events
        events = validate_visual_events(visual_events, {"clips": output, "totalFrames": total})
    return {"schema": "render-timeline", "version": 2, "fps": {"num": fps.numerator, "den": fps.denominator}, "width": checked["sequence"]["width"], "height": checked["sequence"]["height"], "totalFrames": total, "tracks": [{"id": key, "kind": value["kind"], "role": value["role"], "allowOverlap": value["allowOverlap"], "zIndex": value["zIndex"]} for key, value in checked["tracks"].items()], "clips": output, "captions": sorted(captions, key=lambda value: (value["start"], value["end"], value["id"])), "markers": checked["markers"], "visualEvents": events}
