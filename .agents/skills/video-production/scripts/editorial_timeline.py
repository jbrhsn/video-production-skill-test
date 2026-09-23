"""Validate and compile the lane-based editorial timeline contract."""
from __future__ import annotations

import math
from fractions import Fraction

from contracts import (TRACK_KINDS, TRACK_ROLES, integer, rational, text, time_range,
                       validate_source_manifest)


def _frame_floor(time_us: Fraction, fps: Fraction) -> int:
    return time_us.numerator * fps.numerator // (time_us.denominator * fps.denominator * 1_000_000)


def _frame_ceil(time_us: Fraction, fps: Fraction) -> int:
    numerator = time_us.numerator * fps.numerator
    denominator = time_us.denominator * fps.denominator * 1_000_000
    return math.ceil(numerator / denominator)


def _timeline_duration(source_range, playback_rate: Fraction) -> Fraction:
    return Fraction(source_range[1] - source_range[0], 1) / playback_rate


def validate_timeline(data, manifest):
    sources = validate_source_manifest(manifest)
    if not isinstance(data, dict) or data.get("schema") != "editorial-timeline" or data.get("version") != 1:
        raise ValueError("timeline requires schema editorial-timeline version 1")
    if set(data) - {"schema", "version", "sequence", "tracks", "clips", "dialogueWords"}:
        raise ValueError("timeline contains unsupported fields")
    sequence = data.get("sequence")
    if not isinstance(sequence, dict) or set(sequence) != {"id", "fps", "width", "height"}:
        raise ValueError("timeline.sequence requires id, fps, width, and height")
    text(sequence.get("id"), "timeline.sequence.id")
    fps = rational(sequence.get("fps"), "timeline.sequence.fps")
    integer(sequence.get("width"), "timeline.sequence.width", 2)
    integer(sequence.get("height"), "timeline.sequence.height", 2)
    tracks = data.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("timeline.tracks are required")
    track_by_id = {}
    for track in tracks:
        if not isinstance(track, dict) or set(track) - {"id", "kind", "role", "allowOverlap", "zIndex"}:
            raise ValueError("track contains unsupported fields")
        track_id = text(track.get("id"), "track.id")
        if track_id in track_by_id:
            raise ValueError("track IDs must be unique")
        if track.get("kind") not in TRACK_KINDS or track.get("role") not in TRACK_ROLES:
            raise ValueError(f"track {track_id} has unsupported kind or role")
        if type(track.get("allowOverlap", False)) is not bool:
            raise ValueError(f"track {track_id}.allowOverlap must be boolean")
        track_by_id[track_id] = {**track, "allowOverlap": track.get("allowOverlap", False)}
    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("timeline.clips are required")
    seen = set()
    compiled = []
    for clip in clips:
        required = {"id", "trackId", "sourceId", "streamId", "sourceRangeUs", "timelineStartUs", "playbackRate"}
        if not isinstance(clip, dict) or set(clip) != required:
            raise ValueError("clip fields must be exact")
        clip_id = text(clip.get("id"), "clip.id")
        if clip_id in seen:
            raise ValueError("clip IDs identify occurrences and must be unique")
        seen.add(clip_id)
        track = track_by_id.get(clip.get("trackId"))
        if track is None:
            raise ValueError(f"clip {clip_id} references an unknown track")
        source = sources.get(clip.get("sourceId"))
        if source is None:
            raise ValueError(f"clip {clip_id} references an unknown source")
        stream = source["streams"].get(clip.get("streamId"))
        if stream is None:
            raise ValueError(f"clip {clip_id} references an unknown stream")
        if stream["kind"] != track["kind"]:
            raise ValueError(f"clip {clip_id} stream kind must match track kind")
        source_range = time_range(clip.get("sourceRangeUs"), f"clip {clip_id}.sourceRangeUs")
        if source_range[1] > stream["durationUs"]:
            raise ValueError(f"clip {clip_id} exceeds source stream bounds")
        start = integer(clip.get("timelineStartUs"), f"clip {clip_id}.timelineStartUs")
        rate = rational(clip.get("playbackRate"), f"clip {clip_id}.playbackRate")
        duration = _timeline_duration(source_range, rate)
        end = Fraction(start, 1) + duration
        compiled.append({**clip, "track": track, "sourceRangeUs": source_range,
                         "timelineStartUs": start, "playbackRate": rate, "timelineEndUs": end})
    for track_id, track in track_by_id.items():
        rows = sorted((clip for clip in compiled if clip["trackId"] == track_id), key=lambda row: row["timelineStartUs"])
        for prior, following in zip(rows, rows[1:]):
            if not track["allowOverlap"] and following["timelineStartUs"] < prior["timelineEndUs"]:
                raise ValueError(f"track {track_id} has overlapping clips without allowOverlap")
    primary_dialogue = [track for track in track_by_id.values() if track["role"] == "primary-dialogue"]
    if len(primary_dialogue) != 1:
        raise ValueError("timeline requires exactly one primary-dialogue track")
    if primary_dialogue[0]["kind"] != "audio" or primary_dialogue[0]["allowOverlap"]:
        raise ValueError("primary-dialogue must be a non-overlapping audio track")
    return {"sequence": sequence, "fps": fps, "tracks": track_by_id, "clips": compiled,
            "dialogueWords": data.get("dialogueWords", []), "sources": sources}


def compile_timeline(data, manifest):
    checked = validate_timeline(data, manifest)
    fps = checked["fps"]
    output_clips = []
    total_frames = 0
    for clip in checked["clips"]:
        start_frame = _frame_floor(Fraction(clip["timelineStartUs"], 1), fps)
        end_frame = _frame_ceil(clip["timelineEndUs"], fps)
        if end_frame <= start_frame:
            raise ValueError(f"clip {clip['id']} quantizes to no output frames")
        total_frames = max(total_frames, end_frame)
        source_path = checked["sources"][clip["sourceId"]]["path"]
        output_clips.append({"id": clip["id"], "trackId": clip["trackId"], "role": clip["track"]["role"],
                             "sourceId": clip["sourceId"], "streamId": clip["streamId"],
                             "src": source_path.removeprefix("public/"),
                             "sourceRangeUs": list(clip["sourceRangeUs"]), "startFrame": start_frame,
                             "durationFrames": end_frame - start_frame,
                             "playbackRate": {"num": clip["playbackRate"].numerator, "den": clip["playbackRate"].denominator}})
    captions = []
    dialogue_track = next(track_id for track_id, track in checked["tracks"].items() if track["role"] == "primary-dialogue")
    dialogue_clips = [clip for clip in checked["clips"] if clip["trackId"] == dialogue_track]
    word_ids = set()
    for word in checked["dialogueWords"]:
        if not isinstance(word, dict) or set(word) != {"id", "word", "sourceId", "streamId", "sourceRangeUs"}:
            raise ValueError("dialogue word fields must be exact")
        word_id = text(word.get("id"), "dialogueWord.id")
        if word_id in word_ids:
            raise ValueError("dialogue word IDs must be unique")
        word_ids.add(word_id)
        text(word.get("word"), f"dialogueWord {word_id}.word")
        word_range = time_range(word.get("sourceRangeUs"), f"dialogueWord {word_id}.sourceRangeUs")
        matched = [clip for clip in dialogue_clips if clip["sourceId"] == word.get("sourceId")
                   and clip["streamId"] == word.get("streamId")
                   and clip["sourceRangeUs"][0] <= word_range[0] and word_range[1] <= clip["sourceRangeUs"][1]]
        for clip in matched:
            offset = Fraction(word_range[0] - clip["sourceRangeUs"][0], 1) / clip["playbackRate"]
            word_duration = Fraction(word_range[1] - word_range[0], 1) / clip["playbackRate"]
            start = Fraction(clip["timelineStartUs"], 1) + offset
            captions.append({"id": f"{word_id}@{clip['id']}", "sourceWordId": word_id, "clipId": clip["id"],
                             "word": word["word"], "start": float(start / 1_000_000),
                             "end": float((start + word_duration) / 1_000_000)})
    captions.sort(key=lambda item: (item["start"], item["end"], item["id"]))
    return {"schema": "render-timeline", "version": 1,
            "fps": {"num": fps.numerator, "den": fps.denominator},
            "width": checked["sequence"]["width"], "height": checked["sequence"]["height"],
            "totalFrames": total_frames, "tracks": [{"id": track_id, "kind": track["kind"], "role": track["role"],
            "allowOverlap": track["allowOverlap"]} for track_id, track in checked["tracks"].items()],
            "clips": output_clips, "captions": captions}
