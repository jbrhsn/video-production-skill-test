#!/usr/bin/env python3
"""Create an immutable, inspectable derivative record for a selected asset."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def probe(path: Path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,pix_fmt:format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout); streams = data.get("streams", [])
    video = next((row for row in streams if row.get("codec_type") == "video"), None)
    return {"durationSeconds": float(data.get("format", {}).get("duration", 0)), "width": video.get("width") if video else None, "height": video.get("height") if video else None, "pixelFormat": video.get("pix_fmt") if video else None, "alpha": bool(video and "a" in (video.get("pix_fmt") or ""))}


def process(input_path: Path, output_path: Path, recipe: dict, provenance: dict, rights: dict):
    if not input_path.is_file() or output_path.is_absolute() and not output_path.parent.exists():
        raise ValueError("input must exist and output parent must exist")
    if not isinstance(recipe, dict) or not isinstance(provenance, dict) or not isinstance(rights, dict):
        raise ValueError("recipe, provenance, and rights must be objects")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # A copy is itself a deterministic derivative. Transforming media is explicit
    # only when callers provide a supported ffmpeg argument list.
    ffmpeg_args = recipe.get("ffmpegArgs")
    if ffmpeg_args is None:
        shutil.copy2(input_path, output_path)
    elif isinstance(ffmpeg_args, list) and all(isinstance(arg, str) for arg in ffmpeg_args):
        subprocess.run(["ffmpeg", "-y", "-i", str(input_path), *ffmpeg_args, str(output_path)], check=True)
    else:
        raise ValueError("recipe.ffmpegArgs must be a string list when supplied")
    return {"schema": "processed-asset", "version": 1, "id": f"asset:{digest(output_path)[:16]}", "input": {"path": str(input_path), "sha256": digest(input_path)}, "output": {"path": str(output_path), "sha256": digest(output_path), "inspection": probe(output_path)}, "recipe": recipe, "provenance": provenance, "rights": rights}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True); parser.add_argument("--output", required=True); parser.add_argument("--recipe", required=True); parser.add_argument("--provenance", required=True); parser.add_argument("--rights", required=True); parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    record = process(Path(args.input), Path(args.output), json.loads(args.recipe), json.loads(args.provenance), json.loads(args.rights))
    manifest = Path(args.manifest); manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Processed {record['id']} -> {manifest}")


if __name__ == "__main__": main()
