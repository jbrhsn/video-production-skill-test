"""Validate visual-story events bound to the compiled master clock."""
from __future__ import annotations

from contracts import text, time_range


PRESENTATIONS = {"presenter", "overlay", "split-screen", "picture-in-picture", "full-screen-editorial", "chart", "map", "document", "montage"}
LAYERS = {"background", "midground", "foreground"}


def validate_visual_events(data, render_timeline):
    if not isinstance(data, dict) or data.get("schema") != "visual-story-events" or data.get("version") != 1:
        raise ValueError("visual events require schema visual-story-events version 1")
    if set(data) != {"schema", "version", "events"} or not isinstance(data.get("events"), list):
        raise ValueError("visual events require an events array")
    clip_ids = {clip["id"] for clip in render_timeline.get("clips", [])}
    dialogue_ids = {clip["id"] for clip in render_timeline.get("clips", []) if clip.get("role") == "primary-dialogue"}
    total_frames = render_timeline.get("totalFrames")
    if type(total_frames) is not int or total_frames < 1:
        raise ValueError("render timeline is invalid")
    checked, seen = [], set()
    for event in data["events"]:
        required = {"id", "dialogueClipId", "frames", "purpose", "presentation", "layers", "sequence", "reentry", "acceptance"}
        if not isinstance(event, dict) or set(event) != required:
            raise ValueError("visual event fields must be exact")
        event_id = text(event.get("id"), "visual event id")
        if event_id in seen:
            raise ValueError("visual event IDs must be unique")
        seen.add(event_id)
        if event.get("dialogueClipId") not in dialogue_ids:
            raise ValueError(f"visual event {event_id} references an unknown primary dialogue occurrence")
        frames = time_range(event.get("frames"), f"visual event {event_id}.frames")
        if frames[1] > total_frames:
            raise ValueError(f"visual event {event_id} exceeds the master timeline")
        if not text(event.get("purpose"), f"visual event {event_id}.purpose") or not text(event.get("acceptance"), f"visual event {event_id}.acceptance"):
            raise ValueError(f"visual event {event_id} requires purpose and acceptance")
        if event.get("presentation") not in PRESENTATIONS:
            raise ValueError(f"visual event {event_id} has unsupported presentation")
        layers = event.get("layers")
        if not isinstance(layers, dict) or set(layers) - LAYERS:
            raise ValueError(f"visual event {event_id} layers are invalid")
        for name, values in layers.items():
            if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
                raise ValueError(f"visual event {event_id}.{name} must list concrete assets or code visuals")
        sequence = event.get("sequence")
        if not isinstance(sequence, list) or not sequence or any(not isinstance(step, str) or not step for step in sequence):
            raise ValueError(f"visual event {event_id} requires a motion sequence")
        reentry = event.get("reentry")
        if not isinstance(reentry, dict) or set(reentry) != {"method", "sourceClipId"} or reentry["sourceClipId"] not in clip_ids:
            raise ValueError(f"visual event {event_id} requires explicit source re-entry")
        checked.append({**event, "frames": list(frames)})
    return checked
