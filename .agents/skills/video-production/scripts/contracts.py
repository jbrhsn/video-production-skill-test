"""Canonical contracts for the AI-native video production system.

The skill keeps source truth, editorial intent, and render state in separate
artifacts. These validators deliberately reject unknown shapes at the boundary
so a renderer never has to guess which clock or source an edit refers to.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path


ROUTES = {"faceless-standard", "faceless-editorial", "recorded-edit", "hybrid-editorial-edit"}
AUTONOMY_MODES = {"guided", "producer", "autonomous"}
STREAM_KINDS = {"audio", "video"}
TRACK_KINDS = {"audio", "video", "generated"}
TRACK_ROLES = {"primary-dialogue", "music", "sfx", "primary-picture", "broll", "graphics", "overlay", "titles", "effects"}


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def time_range(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{label} must be [startUs, endUs]")
    start, end = (integer(item, label, 0) for item in value)
    if end <= start:
        raise ValueError(f"{label} must increase")
    return start, end


def rational(value, label, positive=True):
    if not isinstance(value, dict) or set(value) != {"num", "den"}:
        raise ValueError(f"{label} must contain only num and den")
    numerator = integer(value["num"], f"{label}.num", 1 if positive else 0)
    denominator = integer(value["den"], f"{label}.den", 1)
    return Fraction(numerator, denominator)


def validate_project(data):
    if not isinstance(data, dict) or data.get("schema") != "video-production-project" or data.get("version") != 1:
        raise ValueError("project requires schema video-production-project version 1")
    required = {"schema", "version", "id", "route", "autonomy", "artifacts"}
    if set(data) - required:
        raise ValueError("project contains unsupported fields")
    text(data.get("id"), "project.id")
    if data.get("route") not in ROUTES:
        raise ValueError("project.route is unsupported")
    if data.get("autonomy") not in AUTONOMY_MODES:
        raise ValueError("project.autonomy is unsupported")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("project.artifacts must be a nonempty object")
    for name, artifact in artifacts.items():
        text(name, "artifact name")
        path = text(artifact, f"artifact {name}")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"artifact {name} must be a project-relative path")
    return data


def validate_source_manifest(data):
    if not isinstance(data, dict) or data.get("schema") != "source-manifest" or data.get("version") != 3:
        raise ValueError("source manifest requires schema source-manifest version 3")
    if set(data) != {"schema", "version", "sources"}:
        raise ValueError("source manifest contains unsupported fields")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("source manifest requires sources")
    checked = {}
    for source in sources:
        if not isinstance(source, dict) or set(source) - {"id", "path", "sha256", "durationUs", "streams", "roles", "provenance", "derivative"}:
            raise ValueError("source contains unsupported fields")
        source_id = text(source.get("id"), "source.id")
        if source_id in checked:
            raise ValueError("source IDs must be unique")
        path = text(source.get("path"), f"source {source_id}.path")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"source {source_id}.path must be project-relative")
        digest = text(source.get("sha256"), f"source {source_id}.sha256")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
            raise ValueError(f"source {source_id}.sha256 must be SHA-256")
        duration = integer(source.get("durationUs"), f"source {source_id}.durationUs", 1)
        streams = source.get("streams")
        if not isinstance(streams, list) or not streams:
            raise ValueError(f"source {source_id}.streams are required")
        stream_ids = set()
        checked_streams = {}
        for stream in streams:
            if not isinstance(stream, dict) or set(stream) - {"id", "kind", "durationUs", "timeBase", "startUs", "width", "height", "frameRate", "sampleRate", "channels"}:
                raise ValueError(f"source {source_id} stream contains unsupported fields")
            stream_id = text(stream.get("id"), f"source {source_id} stream.id")
            if stream_id in stream_ids:
                raise ValueError(f"source {source_id} stream IDs must be unique")
            stream_ids.add(stream_id)
            if stream.get("kind") not in STREAM_KINDS:
                raise ValueError(f"source {source_id} stream {stream_id}.kind is unsupported")
            stream_duration = integer(stream.get("durationUs", duration), f"source {source_id} stream {stream_id}.durationUs", 1)
            if stream_duration > duration:
                raise ValueError(f"source {source_id} stream {stream_id} exceeds source duration")
            if stream["kind"] == "video":
                integer(stream.get("width"), f"source {source_id} stream {stream_id}.width", 1)
                integer(stream.get("height"), f"source {source_id} stream {stream_id}.height", 1)
                checked_streams[stream_id] = {**stream, "durationUs": stream_duration,
                                              "frameRate": rational(stream.get("frameRate"), f"source {source_id} stream {stream_id}.frameRate")}
                continue
            integer(stream.get("sampleRate", 48_000), f"source {source_id} stream {stream_id}.sampleRate", 1)
            integer(stream.get("channels", 1), f"source {source_id} stream {stream_id}.channels", 1)
            checked_streams[stream_id] = {**stream, "durationUs": stream_duration}
        checked[source_id] = {**source, "durationUs": duration, "streams": checked_streams}
    return checked
