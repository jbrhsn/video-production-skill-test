#!/usr/bin/env python3
"""Verify or atomically cache runtime models in a workspace video-assets directory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path


MANIFEST = Path(__file__).parent.parent / "assets" / "model-assets.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def requirements(manifest: dict, requirement: str) -> list[tuple[str, str, dict]]:
    if requirement == "kokoro":
        return [("kokoro", name, item) for name, item in manifest["kokoro"].items()]
    family, separator, name = requirement.partition(":")
    if family != "whisper" or not separator or name not in manifest["whisper"]:
        raise ValueError(f"Unknown model requirement: {requirement}")
    return [(family, name, manifest[family][name])]


def cache_path(assets_dir: Path, family: str, item: dict) -> Path:
    return assets_dir / family / item["filename"]


def inspect(assets_dir: Path, family: str, name: str, item: dict) -> dict:
    target = cache_path(assets_dir, family, item)
    valid = target.is_file() and digest(target) == item["sha256"]
    return {"family": family, "name": name, "path": str(target), "status": "cached" if valid else "missing-or-invalid",
            "sha256": item["sha256"]}


def download(target: Path, item: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=".download.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as output, urllib.request.urlopen(item["url"], timeout=60) as source:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)
        if digest(temporary) != item["sha256"]:
            raise ValueError(f"Checksum mismatch while downloading {target.name}")
        os.replace(temporary, target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def ensure(assets_dir: Path, requested: list[str], allow_download: bool) -> list[dict]:
    manifest = load_manifest()
    rows = []
    for requirement in requested:
        for family, name, item in requirements(manifest, requirement):
            row = inspect(assets_dir, family, name, item)
            if row["status"] != "cached" and allow_download:
                download(cache_path(assets_dir, family, item), item)
                row = inspect(assets_dir, family, name, item)
                row["status"] = "downloaded"
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--require", action="append", required=True, help="kokoro or whisper:<model>")
    parser.add_argument("--ensure", action="store_true", help="Download missing/corrupt required files into the workspace cache.")
    parser.add_argument("--out", type=Path, help="Optional JSON status output.")
    args = parser.parse_args()
    workspace = args.workspace_root.expanduser().resolve()
    if not workspace.is_dir():
        parser.error(f"Workspace root does not exist: {workspace}")
    assets_dir = workspace / ".video_production_assets"
    rows = ensure(assets_dir, args.require, args.ensure)
    result = {"schema": "video-production-model-cache", "version": 1, "workspace": str(workspace),
              "assetsDir": str(assets_dir), "requirements": args.require, "models": rows}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if any(row["status"] == "missing-or-invalid" for row in rows):
        raise SystemExit("Required model assets are missing or invalid; rerun with --ensure.")


if __name__ == "__main__":
    main()
