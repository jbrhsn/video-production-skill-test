#!/usr/bin/env python3
"""Generate a tiny deterministic video/audio fixture for renderer qualification."""
from __future__ import annotations

import argparse, hashlib, json, subprocess
from pathlib import Path


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): value.update(chunk)
    return value.hexdigest()


def generate(root: Path):
    media = root / "public/media"; media.mkdir(parents=True, exist_ok=True); output = media / "numbered-tone.mp4"
    # testsrc2 changes every source frame. The 440Hz and 880Hz sections are
    # separated in source time, letting the rendered J-cut have a measured onset.
    audio = "sine=frequency=440:sample_rate=48000:duration=1[a];anullsrc=r=48000:cl=mono:d=1[b];sine=frequency=880:sample_rate=48000:duration=1[c];anullsrc=r=48000:cl=mono:d=1[d];[a][b][c][d]concat=n=4:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=4", "-filter_complex", audio, "-map", "0:v", "-map", "[out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(output)], check=True, capture_output=True)
    digest = sha256(output)
    manifest = {"schema": "source-manifest", "version": 3, "sources": [{"id": "fixture", "path": "public/media/numbered-tone.mp4", "sha256": digest, "durationUs": 4_000_000, "streams": [{"id": "video-0", "kind": "video", "durationUs": 4_000_000, "width": 640, "height": 360, "frameRate": {"num": 30, "den": 1}}, {"id": "audio-1", "kind": "audio", "durationUs": 4_000_000, "sampleRate": 48000, "channels": 1}], "roles": [], "provenance": {"fixture": "ffmpeg testsrc2 + 440Hz/880Hz tones", "sourcePts": 0}}]}
    timeline = {"schema": "editorial-timeline", "version": 2, "sequence": {"id": "fixture", "fps": {"num": 30, "den": 1}, "width": 640, "height": 360}, "tracks": [{"id": "dialogue", "kind": "audio", "role": "primary-dialogue"}, {"id": "picture", "kind": "video", "role": "primary-picture"}], "clips": [{"id": "audio-a", "trackId": "dialogue", "sourceId": "fixture", "streamId": "audio-1", "sourceRangeUs": [0, 1_000_000], "timelineStartUs": 0, "playbackRate": {"num": 1, "den": 1}}, {"id": "video-a", "trackId": "picture", "sourceId": "fixture", "streamId": "video-0", "sourceRangeUs": [0, 1_000_000], "timelineStartUs": 0, "playbackRate": {"num": 1, "den": 1}}, {"id": "audio-b", "trackId": "dialogue", "sourceId": "fixture", "streamId": "audio-1", "sourceRangeUs": [2_000_000, 3_000_000], "timelineStartUs": 1_000_000, "playbackRate": {"num": 1, "den": 1}}, {"id": "video-b", "trackId": "picture", "sourceId": "fixture", "streamId": "video-0", "sourceRangeUs": [2_000_000, 3_000_000], "timelineStartUs": 1_600_000, "playbackRate": {"num": 1, "den": 1}}], "dialogueWords": [{"id": "tone", "word": "tone", "sourceId": "fixture", "streamId": "audio-1", "sourceRangeUs": [2_000_000, 2_300_000]}]}
    (root / "source").mkdir(exist_ok=True); (root / "editorial").mkdir(exist_ok=True)
    (root / "source/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n"); (root / "editorial/timeline.json").write_text(json.dumps(timeline, indent=2) + "\n")
    return manifest, timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-dir", required=True); args = parser.parse_args(); generate(Path(args.project_dir)); print(f"Fixture created in {args.project_dir}")


if __name__ == "__main__": main()
