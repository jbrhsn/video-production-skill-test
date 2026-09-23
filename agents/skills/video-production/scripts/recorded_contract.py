"""Validation and time mapping for recorded-video edit projects."""
from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path


LAYOUTS = {"screen-focus", "presenter-focus", "balanced", "presenter-only", "screen-only"}
CORNERS = {"top-left", "top-right", "bottom-left", "bottom-right"}
ROLES = {"screen", "presenter", "voice", "system-audio"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def integer(value, label, minimum=0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def range_us(value, label):
    if (not isinstance(value, list) or len(value) != 2
            or any(type(item) is not int for item in value)
            or value[0] < 0 or value[1] <= value[0]):
        raise ValueError(f"{label} must be [startUs, endUs] with increasing nonnegative integers")
    return value


def validate_source_manifest(data, project: Path | None = None):
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("track") != "recorded-edit":
        raise ValueError("source manifest requires version 1 and track recorded-edit")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("source manifest requires nonempty sources")
    result = {}
    for source in sources:
        if not isinstance(source, dict) or not text(source.get("id")) or source["id"] in result:
            raise ValueError("sources require unique nonempty IDs")
        if source.get("role") not in ROLES:
            raise ValueError(f"source {source['id']}: unsupported role")
        staged = source.get("stagedPath")
        if not text(staged) or not staged.startswith("public/media/") or ".." in Path(staged).parts:
            raise ValueError(f"source {source['id']}: stagedPath must be under public/media")
        integer(source.get("durationUs"), f"source {source['id']}.durationUs", 1)
        if source["role"] in ("screen", "presenter"):
            integer(source.get("width"), f"source {source['id']}.width", 1)
            integer(source.get("height"), f"source {source['id']}.height", 1)
        if not text(source.get("sha256")) or len(source["sha256"]) != 64:
            raise ValueError(f"source {source['id']}: sha256 is required")
        if project is not None:
            staged_file = project / staged
            if not staged_file.is_file():
                raise ValueError(f"source {source['id']}: staged file is missing: {staged}")
            digest = hashlib.sha256()
            with staged_file.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != source["sha256"]:
                raise ValueError(f"source {source['id']}: staged content differs from its immutable hash")
        result[source["id"]] = source
    return result


def validate_sync_map(data, sources):
    if not isinstance(data, dict) or data.get("version") != 1 or not text(data.get("referenceSourceId")):
        raise ValueError("sync map requires version 1 and referenceSourceId")
    if data["referenceSourceId"] not in sources:
        raise ValueError("sync reference source is unknown")
    mappings = data.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("sync map requires mappings")
    result = {}
    for mapping in mappings:
        source_id = mapping.get("sourceId") if isinstance(mapping, dict) else None
        if source_id not in sources or source_id in result:
            raise ValueError("sync mappings require unique known source IDs")
        sections = mapping.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ValueError(f"sync mapping {source_id} requires sections")
        previous_session = 0
        checked = []
        for index, section in enumerate(sections):
            session = range_us(section.get("sessionRangeUs"), f"sync {source_id} section {index}.sessionRangeUs")
            source = range_us(section.get("sourceRangeUs"), f"sync {source_id} section {index}.sourceRangeUs")
            if session[0] < previous_session:
                raise ValueError(f"sync {source_id}: sections overlap or are unordered")
            if source[1] > sources[source_id]["durationUs"]:
                raise ValueError(f"sync {source_id}: source range exceeds media duration")
            if section.get("status") not in ("confirmed", "estimated"):
                raise ValueError(f"sync {source_id}: section status must be confirmed or estimated")
            previous_session = session[1]
            checked.append({**section, "sessionRangeUs": session, "sourceRangeUs": source})
        result[source_id] = checked
    missing = set(sources) - set(result)
    if missing:
        raise ValueError(f"sync mappings missing sources: {sorted(missing)}")
    return result


def validate_cut_plan(data, sources, mappings):
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("track") != "recorded-edit":
        raise ValueError("cut plan requires version 1 and track recorded-edit")
    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("cut plan requires nonempty clips")
    seen = set()
    checked = []
    for index, clip in enumerate(clips):
        clip_id = clip.get("id") if isinstance(clip, dict) else None
        if not text(clip_id) or clip_id in seen:
            raise ValueError("clips require unique nonempty IDs")
        seen.add(clip_id)
        session = range_us(clip.get("sessionRangeUs"), f"clip {clip_id}.sessionRangeUs")
        tracks = clip.get("tracks")
        if not isinstance(tracks, dict) or not tracks or set(tracks) - {"screen", "presenter"}:
            raise ValueError(f"clip {clip_id}: tracks must contain screen and/or presenter")
        for role, source_id in tracks.items():
            if source_id not in sources or sources[source_id]["role"] != role:
                raise ValueError(f"clip {clip_id}: {role} references an incompatible source")
            map_session_range_to_source(mappings[source_id], session, clip_id)
        audio = clip.get("primaryAudio")
        if not isinstance(audio, dict) or audio.get("sourceId") not in sources:
            raise ValueError(f"clip {clip_id}: primaryAudio requires a known sourceId")
        audio_source = sources[audio["sourceId"]]
        if "audioStreams" in audio_source and not audio_source["audioStreams"]:
            raise ValueError(f"clip {clip_id}: primaryAudio source has no probed audio stream")
        if len(audio_source.get("audioStreams", [])) > 1:
            raise ValueError(f"clip {clip_id}: stage the selected audio stream as a separate source before editing")
        map_session_range_to_source(mappings[audio["sourceId"]], session, clip_id)
        checked.append({**clip, "sessionRangeUs": session})
    return checked


def map_session_to_source(sections, session_us, label="time", allow_end=False):
    for section in sections:
        start, end = section["sessionRangeUs"]
        inside = start <= session_us < end or (allow_end and session_us == end)
        if inside:
            source_start, source_end = section["sourceRangeUs"]
            progress = (session_us - start) / (end - start)
            return round(source_start + progress * (source_end - source_start))
    raise ValueError(f"{label}: session time {session_us} is outside synchronized coverage")


def map_session_range_to_source(sections, session_range, label):
    start_us, end_us = session_range
    for section in sections:
        start, end = section["sessionRangeUs"]
        if start <= start_us and end_us <= end:
            return (map_session_to_source([section], start_us, label),
                    map_session_to_source([section], end_us, label, allow_end=True))
    raise ValueError(f"{label}: interval crosses a synchronization gap or section boundary; split the clip")


def validate_recorded_execution(data, clip_ids):
    if not isinstance(data, dict) or data.get("version") != 3 or data.get("track") != "recorded-edit":
        raise ValueError("recorded execution plan requires version 3 and track recorded-edit")
    fps = integer(data.get("fps"), "execution fps", 1)
    integer(data.get("width"), "execution width", 2)
    integer(data.get("height"), "execution height", 2)
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("recorded execution plan requires scenes")
    used = []
    events = []
    masks = []
    annotations = []
    beat_ids = []
    creative_core = any("beats" in scene or "treatment" in scene for scene in scenes if isinstance(scene, dict))
    for number, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or scene.get("scene") != number or not text(scene.get("id")):
            raise ValueError("recorded scenes need consecutive scene numbers and stable IDs")
        ids = scene.get("clipIds")
        if not isinstance(ids, list) or not ids or any(item not in clip_ids for item in ids):
            raise ValueError(f"scene {number}: clipIds must reference cut-plan clips")
        used.extend(ids)
        if creative_core:
            if not text(scene.get("treatment")) or not isinstance(scene.get("beats"), list) or not scene["beats"]:
                raise ValueError(f"scene {number}: creative plans require treatment and nonempty beats")
            for beat in scene["beats"]:
                if not isinstance(beat, dict) or not text(beat.get("id")) or beat.get("clipId") not in ids:
                    raise ValueError(f"scene {number}: invalid creative beat")
                timing_key = "correctedTranscriptRangeUs" if "correctedTranscriptRangeUs" in beat else "timelineRangeUs"
                range_us(beat.get(timing_key), f"beat {beat.get('id')}.{timing_key}")
                modern_text = ("editorialPurpose", "intendedEffect", "primaryMediaRole", "authoredAdditionRole")
                legacy_text = ("viewerQuestion", "sourceEvidenceRole", "authoredVisualRole", "newUnderstanding")
                if (not all(text(beat.get(key)) for key in modern_text)
                        and not all(text(beat.get(key)) for key in legacy_text)):
                    raise ValueError(f"beat {beat.get('id')}: editorial purpose, audience effect, and media roles are required")
                if not all(text(beat.get(key)) for key in ("captionPolicy", "soundPolicy")):
                    raise ValueError(f"beat {beat.get('id')}: caption and sound decisions are required")
                progression = beat.get("progression")
                states = beat.get("states")
                modern_progression = isinstance(progression, dict) and all(
                    text(progression.get(key)) for key in ("entry", "development", "exit"))
                legacy_progression = isinstance(states, dict) and all(
                    text(states.get(key)) for key in ("initial", "action", "result"))
                if not modern_progression and not legacy_progression:
                    raise ValueError(f"beat {beat.get('id')}: entry/development/exit progression is required")
                beat_ids.append(beat["id"])
        for event in scene.get("layoutEvents", []):
            if (not isinstance(event, dict) or event.get("clipId") not in ids
                    or event.get("layout") not in LAYOUTS):
                raise ValueError(f"scene {number}: invalid layout event")
            integer(event.get("atUs"), "layout event atUs")
            integer(event.get("durationUs", 0), "layout event durationUs")
            if event.get("corner", "top-right") not in CORNERS:
                raise ValueError("layout event corner is invalid")
            if event.get("fromLayout") is not None and event["fromLayout"] not in LAYOUTS:
                raise ValueError("layout event fromLayout is invalid")
            if not text(event.get("id")):
                raise ValueError("layout events require IDs")
            events.append(event["id"])
        for mask in scene.get("masks", []):
            if not isinstance(mask, dict) or mask.get("clipId") not in ids or not text(mask.get("id")):
                raise ValueError(f"scene {number}: invalid mask")
            relative = range_us(mask.get("clipRangeUs"), f"mask {mask.get('id')}.clipRangeUs")
            rect = mask.get("rect")
            if (not isinstance(rect, list) or len(rect) != 4
                    or any(type(value) not in (int, float) or not math.isfinite(value) for value in rect)
                    or rect[0] < 0 or rect[1] < 0 or rect[2] <= 0 or rect[3] <= 0
                    or rect[0] + rect[2] > 1 or rect[1] + rect[3] > 1):
                raise ValueError(f"mask {mask.get('id')}: rect must be normalized [x,y,width,height]")
            if mask.get("strategy") not in ("solid", "blur"):
                raise ValueError(f"mask {mask.get('id')}: strategy must be solid or blur")
            masks.append({**mask, "clipRangeUs": relative})
        for annotation in scene.get("annotations", []):
            if not isinstance(annotation, dict) or annotation.get("clipId") not in ids or not text(annotation.get("id")):
                raise ValueError(f"scene {number}: invalid annotation")
            relative = range_us(annotation.get("clipRangeUs"), f"annotation {annotation.get('id')}.clipRangeUs")
            rect = annotation.get("rect")
            if (not isinstance(rect, list) or len(rect) != 4
                    or any(type(value) not in (int, float) or not math.isfinite(value) for value in rect)
                    or rect[0] < 0 or rect[1] < 0 or rect[2] <= 0 or rect[3] <= 0
                    or rect[0] + rect[2] > 1 or rect[1] + rect[3] > 1):
                raise ValueError(f"annotation {annotation.get('id')}: rect must be normalized [x,y,width,height]")
            if annotation.get("style", "outline") not in ("outline", "highlight"):
                raise ValueError(f"annotation {annotation.get('id')}: unsupported style")
            if (not text(annotation.get("sourceFrame")) or type(annotation.get("sourceTimeUs")) is not int
                    or annotation["sourceTimeUs"] < 0 or not text(annotation.get("invalidatedBy"))):
                raise ValueError(f"annotation {annotation.get('id')}: sourceFrame, sourceTimeUs, and invalidatedBy are required")
            annotations.append({**annotation, "clipRangeUs": relative})
    if used != clip_ids:
        raise ValueError("execution scenes must cover cut-plan clips exactly once in order")
    if (len(events) != len(set(events)) or len([m["id"] for m in masks]) != len(set(m["id"] for m in masks))
            or len([a["id"] for a in annotations]) != len(set(a["id"] for a in annotations))
            or len(beat_ids) != len(set(beat_ids))):
        raise ValueError("beat, layout, mask, and annotation IDs must be unique")
    return {**data, "fps": fps, "scenes": scenes}
