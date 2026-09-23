#!/usr/bin/env python3
"""Export the explicit, safely representable subset of the compiled timeline."""
from __future__ import annotations

import json


def export_manifest(render_timeline, source_manifest, captions):
    unsupported = [clip["id"] for clip in render_timeline.get("clips", []) if clip.get("kind") == "generated" or clip.get("freezeFrameUs") is not None]
    markers = [{"name": marker.get("name", marker.get("id", "marker")), "frame": marker.get("frame")} for marker in render_timeline.get("markers", []) if isinstance(marker, dict)]
    return {"schema": "production-interchange", "version": 1, "timeline": render_timeline, "sources": source_manifest, "captions": captions, "markers": markers, "fidelity": {"native": ["source-trims", "tracks", "constant-positive-rate", "markers", "captions"], "baked": unsupported, "unsupported": ["rate-ramps", "reverse", "nested-sequences"]}}


def srt(captions):
    def stamp(value):
        ms = round(value * 1000); hours, ms = divmod(ms, 3_600_000); minutes, ms = divmod(ms, 60_000); seconds, ms = divmod(ms, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"
    return "\n\n".join(f"{index}\n{stamp(row['start'])} --> {stamp(row['end'])}\n{row['word']}" for index, row in enumerate(captions, 1)) + ("\n" if captions else "")
