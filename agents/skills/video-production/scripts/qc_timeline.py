"""Deterministic timeline checks with explicit coverage and evidence."""
from __future__ import annotations


def check_timeline(render_timeline):
    findings = []
    clips = render_timeline.get("clips", [])
    total = render_timeline.get("totalFrames")
    if type(total) is not int or total < 1:
        return {"schema": "qc-result", "version": 1, "status": "error", "coverage": ["render-timeline"],
                "findings": [{"rule": "timeline.valid", "severity": "error", "message": "Invalid totalFrames"}]}
    tracks = {track["id"]: track for track in render_timeline.get("tracks", [])}
    by_track = {}
    for clip in clips:
        start, duration = clip.get("startFrame"), clip.get("durationFrames")
        if type(start) is not int or type(duration) is not int or start < 0 or duration < 1 or start + duration > total:
            findings.append({"rule": "timeline.bounds", "severity": "error", "clipId": clip.get("id"),
                             "message": "Clip is outside the compiled master"})
            continue
        by_track.setdefault(clip.get("trackId"), []).append(clip)
    for track_id, rows in by_track.items():
        track = tracks.get(track_id, {})
        if track.get("allowOverlap"):
            continue
        rows.sort(key=lambda row: row["startFrame"])
        for previous, current in zip(rows, rows[1:]):
            if current["startFrame"] < previous["startFrame"] + previous["durationFrames"]:
                findings.append({"rule": "timeline.overlap", "severity": "error", "trackId": track_id,
                                 "message": "Non-overlapping track contains overlapping clips"})
    for caption in render_timeline.get("captions", []):
        if not (isinstance(caption.get("start"), (int, float)) and isinstance(caption.get("end"), (int, float))
                and 0 <= caption["start"] < caption["end"] <= total * render_timeline["fps"]["den"] / render_timeline["fps"]["num"]):
            findings.append({"rule": "captions.bounds", "severity": "error", "captionId": caption.get("id"),
                             "message": "Caption lies outside the master"})
    status = "fail" if any(item["severity"] == "error" for item in findings) else "pass"
    return {"schema": "qc-result", "version": 1, "status": status,
            "coverage": ["timeline bounds", "non-overlap", "caption bounds"], "findings": findings}
