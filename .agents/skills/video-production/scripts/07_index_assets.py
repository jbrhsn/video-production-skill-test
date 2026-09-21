#!/usr/bin/env python3
"""Create a non-destructive technical inventory of a creative asset library.

Curated meaning, provenance, and rights belong in ``library.json``. This script
only reports files and inspectable technical facts, and never overwrites it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


IGNORED_DIRS = {"kokoro", "whisper", "__pycache__", ".DS_Store"}
IGNORED_FILES = {"library.json", "inventory.json", "inventory.example.json", "inventory.generated.json", "README.md"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".aif", ".aiff"}


def parse_png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as image:
        header = image.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def parse_jpeg_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as image:
        if image.read(2) != b"\xff\xd8":
            return None
        while True:
            marker = image.read(1)
            while marker == b"\xff":
                marker = image.read(1)
            if not marker:
                return None
            marker_value = marker[0]
            if marker_value in {0xD8, 0xD9}:
                continue
            length_bytes = image.read(2)
            if len(length_bytes) != 2:
                return None
            length = int.from_bytes(length_bytes, "big")
            if length < 2:
                return None
            if 0xC0 <= marker_value <= 0xC3 or 0xC5 <= marker_value <= 0xC7 or 0xC9 <= marker_value <= 0xCB or 0xCD <= marker_value <= 0xCF:
                data = image.read(5)
                if len(data) != 5:
                    return None
                return int.from_bytes(data[3:5], "big"), int.from_bytes(data[1:3], "big")
            image.seek(length - 2, 1)


def parse_svg_size(path: Path) -> tuple[str | None, str | None]:
    source = path.read_text(encoding="utf-8", errors="ignore")[:8192]
    match = re.search(r"<svg\\b[^>]*", source, re.IGNORECASE)
    if not match:
        return None, None
    tag = match.group(0)
    width = re.search(r'\\bwidth=["\']([^"\']+)', tag)
    height = re.search(r'\\bheight=["\']([^"\']+)', tag)
    view_box = re.search(r'\\bviewBox=["\']([^"\']+)', tag, re.IGNORECASE)
    if view_box and (not width or not height):
        parts = view_box.group(1).replace(",", " ").split()
        if len(parts) == 4:
            return parts[2], parts[3]
    return (width.group(1) if width else None, height.group(1) if height else None)


def ffprobe(path: Path) -> dict[str, Any] | None:
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(path),
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        return json.loads(completed.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def kind_for(path: Path) -> str:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return "image"
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return "video"
    if path.suffix.lower() in AUDIO_EXTENSIONS:
        return "audio"
    return "other"


def inspect(path: Path, assets_dir: Path) -> dict[str, Any]:
    relative = path.relative_to(assets_dir).as_posix()
    entry: dict[str, Any] = {
        "path": relative,
        "kind": kind_for(path),
        "file_size_bytes": path.stat().st_size,
    }
    extension = path.suffix.lower()
    if extension == ".png":
        size = parse_png_size(path)
        if size:
            entry["dimensions_px"] = {"width": size[0], "height": size[1]}
    elif extension in {".jpg", ".jpeg"}:
        size = parse_jpeg_size(path)
        if size:
            entry["dimensions_px"] = {"width": size[0], "height": size[1]}
    elif extension == ".svg":
        width, height = parse_svg_size(path)
        if width or height:
            entry["dimensions"] = {"width": width, "height": height}
    elif entry["kind"] in {"video", "audio"}:
        probe = ffprobe(path)
        if probe:
            entry["probe"] = probe
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Index creative media without changing curated library metadata.")
    parser.add_argument("--assets-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="Defaults to ASSETS_DIR/inventory.generated.json")
    args = parser.parse_args()
    assets_dir = args.assets_dir.resolve()
    if not assets_dir.is_dir():
        parser.error(f"Asset directory does not exist: {assets_dir}")
    output = args.out.resolve() if args.out else assets_dir / "inventory.generated.json"
    if output == assets_dir / "library.json":
        parser.error("Refusing to overwrite curated library.json")

    assets: list[dict[str, Any]] = []
    for candidate in sorted(assets_dir.rglob("*")):
        if not candidate.is_file() or candidate.name in IGNORED_FILES:
            continue
        if any(part in IGNORED_DIRS for part in candidate.relative_to(assets_dir).parts):
            continue
        assets.append(inspect(candidate, assets_dir))

    report = {
        "schema_version": "1.0",
        "generated_by": "video-production/scripts/07_index_assets.py",
        "asset_root": str(assets_dir),
        "asset_count": len(assets),
        "assets": assets,
        "notice": "Technical discovery only. Confirm provenance, rights, and creative fitness in library.json before output use.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(assets)} creative files to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
