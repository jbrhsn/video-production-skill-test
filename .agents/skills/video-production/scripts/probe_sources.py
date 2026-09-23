#!/usr/bin/env python3
"""Build a source-manifest v3 from FFprobe stream facts without changing media."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): value.update(chunk)
    return value.hexdigest()


def rational(text):
    numerator, denominator = text.split("/")
    return {"num": int(numerator), "den": int(denominator)}


def inspect(path, source_id, project_root):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], check=True, capture_output=True, text=True).stdout)
    streams = []
    for row in info["streams"]:
        if row.get("codec_type") not in {"audio", "video"}: continue
        duration = int(round(float(row.get("duration", info["format"].get("duration", 0))) * 1_000_000))
        stream = {"id": f"{row['codec_type']}-{row['index']}", "kind": row["codec_type"], "durationUs": duration}
        if row["codec_type"] == "video": stream.update({"width": row["width"], "height": row["height"], "frameRate": rational(row.get("avg_frame_rate", "30/1"))})
        else: stream.update({"sampleRate": int(row.get("sample_rate", 48000)), "channels": int(row.get("channels", 1))})
        streams.append(stream)
    duration = max((item["durationUs"] for item in streams), default=0)
    return {"id": source_id, "path": str(path.resolve().relative_to(project_root.resolve())), "sha256": sha256(path), "durationUs": duration, "streams": streams, "roles": [], "provenance": {"method": "ffprobe", "tool": "ffprobe"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-root", required=True); parser.add_argument("--source", action="append", required=True, metavar="ID=PATH"); parser.add_argument("--out", required=True); args = parser.parse_args()
    root = Path(args.project_root); entries = []
    for value in args.source:
        source_id, raw = value.split("=", 1); entries.append(inspect(Path(raw), source_id, root))
    Path(args.out).write_text(json.dumps({"schema": "source-manifest", "version": 3, "sources": entries}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
