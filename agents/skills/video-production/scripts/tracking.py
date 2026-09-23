#!/usr/bin/env python3
"""Validate source-coordinate tracking and derive safe crop candidates."""
from __future__ import annotations

from contracts import integer, text, time_range


def validate(data):
    if not isinstance(data, dict) or data.get("schema") != "source-tracking" or data.get("version") != 1 or set(data) != {"schema", "version", "sourceId", "coordinateSpace", "tracks"}:
        raise ValueError("tracking requires source-tracking version 1")
    if data["coordinateSpace"] != "source-pixels": raise ValueError("tracking must use source-pixels")
    tracks, seen = [], set()
    for row in data.get("tracks", []):
        if not isinstance(row, dict) or set(row) != {"id", "kind", "frames", "confidence", "points"}: raise ValueError("tracking row fields must be exact")
        if row["kind"] not in {"face", "speaker", "cursor", "ui-region", "object"} or text(row["id"], "track.id") in seen: raise ValueError("tracking ID/kind invalid")
        seen.add(row["id"]); frames = time_range(row["frames"], "track.frames")
        if not isinstance(row["confidence"], (int, float)) or not 0 <= row["confidence"] <= 1: raise ValueError("tracking confidence invalid")
        if not isinstance(row["points"], list) or not row["points"]: raise ValueError("tracking points required")
        for point in row["points"]:
            if not isinstance(point, dict) or set(point) != {"frame", "x", "y", "width", "height"}: raise ValueError("tracking point invalid")
            integer(point["frame"], "tracking point.frame", frames[0])
            if not all(isinstance(point[key], (int, float)) and point[key] >= 0 for key in ("x", "y", "width", "height")): raise ValueError("tracking geometry invalid")
        tracks.append(row)
    return {**data, "tracks": tracks}
