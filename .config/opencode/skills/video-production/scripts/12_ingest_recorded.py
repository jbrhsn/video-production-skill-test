#!/usr/bin/env python3
"""Stage immutable recorded sources and write their probed source manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                            check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--intake", required=True, help="JSON with sources [{id,path,role}]")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    intake_path = Path(args.intake).expanduser().resolve()
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    requests = intake.get("sources") if isinstance(intake, dict) else None
    if not isinstance(requests, list) or not requests:
        raise ValueError("intake requires nonempty sources")
    raw = project / "source/raw"
    media = project / "public/media"
    manifest_path = project / "source/manifest.json"
    if manifest_path.exists():
        raise ValueError("source/manifest.json already exists; ingest revisions into a new project or explicit take directory")
    raw.mkdir(parents=True, exist_ok=True)
    media.mkdir(parents=True, exist_ok=True)
    rows, seen = [], set()
    for request in requests:
        source_id, role = request.get("id"), request.get("role")
        if not isinstance(source_id, str) or not source_id or source_id in seen or role not in {"screen", "presenter", "voice", "system-audio"}:
            raise ValueError("sources require unique IDs and a supported role")
        seen.add(source_id)
        source = Path(request.get("path", "")).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"missing source: {source}")
        suffix = source.suffix.lower()
        raw_path = raw / f"{source_id}{suffix}"
        staged = media / f"{source_id}{suffix}"
        if raw_path.exists() or staged.exists():
            raise ValueError(f"refusing to overwrite staged source {source_id}")
        shutil.copy2(source, raw_path)
        shutil.copy2(raw_path, staged)
        info = probe(staged)
        duration = info.get("format", {}).get("duration")
        if duration is None or float(duration) <= 0:
            raise ValueError(f"{source_id}: positive probed duration required")
        video = next((stream for stream in info.get("streams", []) if stream.get("codec_type") == "video"), None)
        audio = [stream for stream in info.get("streams", []) if stream.get("codec_type") == "audio"]
        if role in ("screen", "presenter") and video is None:
            raise ValueError(f"{source_id}: {role} requires a video stream")
        rows.append({"id": source_id, "role": role, "stagedPath": f"public/media/{staged.name}",
                     "rawPath": f"source/raw/{raw_path.name}", "sha256": digest(raw_path),
                     "durationUs": round(float(duration) * 1_000_000),
                     "width": video.get("width") if video else None, "height": video.get("height") if video else None,
                     "codec": video.get("codec_name") if video else None,
                     "avgFrameRate": video.get("avg_frame_rate") if video else None,
                     "realFrameRate": video.get("r_frame_rate") if video else None,
                     "timeBase": video.get("time_base") if video else None,
                     "audioStreams": [{"index": stream.get("index"), "codec": stream.get("codec_name"),
                                       "sampleRate": stream.get("sample_rate"), "channels": stream.get("channels")}
                                      for stream in audio]})
    manifest_path.write_text(json.dumps({"version": 1, "track": "recorded-edit", "sources": rows}, indent=2) + "\n")
    print(f"Ingested {len(rows)} immutable source copies -> {manifest_path}")


if __name__ == "__main__":
    main()
