#!/usr/bin/env python3
"""Find transparent, token-based candidates in a curated video asset library.

This intentionally ranks recorded metadata rather than pretending to understand
uninspected media. A ranked candidate is still subject to visual and rights
review before it can appear in a storyboard or output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


STOP_WORDS = {"a", "an", "and", "for", "from", "in", "of", "on", "or", "the", "to", "with"}


def tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if token not in STOP_WORDS}


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def load_collection_details(assets_dir: Path, library: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for collection in library.get("collections", []):
        inventory = collection.get("inventory")
        if not isinstance(inventory, str):
            continue
        inventory_path = assets_dir / inventory
        if not inventory_path.is_file():
            continue
        try:
            document = json.loads(inventory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for asset in document.get("assets", []):
            if isinstance(asset, dict) and isinstance(asset.get("file_name"), str):
                details[asset["file_name"]] = asset
    return details


def main() -> int:
    parser = argparse.ArgumentParser(description="Search curated video-production library metadata.")
    parser.add_argument("--assets-dir", required=True, type=Path)
    parser.add_argument("--query", required=True, help="Topic, visual concept, or scene beat to match against metadata.")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--include-unusable", action="store_true", help="Include unknown and reference-only assets for planning review.")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    assets_dir = args.assets_dir.resolve()
    library_path = assets_dir / "library.json"
    if not library_path.is_file():
        parser.error(f"Missing curated library: {library_path}")
    try:
        library = json.loads(library_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        parser.error(f"Invalid library.json: {error}")
    query_terms = tokens(args.query)
    if not query_terms:
        parser.error("Query must contain at least one searchable word")

    details = load_collection_details(assets_dir, library)
    matches: list[dict[str, Any]] = []
    for asset in library.get("assets", []):
        if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
            continue
        status = asset.get("rights", {}).get("status", "unknown")
        if not args.include_unusable and status not in {"cleared", "user-owned"}:
            continue
        detail = details.get(Path(asset["path"]).name, {})
        metadata_terms = tokens(" ".join(strings(asset))) | tokens(" ".join(strings(detail)))
        matched = sorted(query_terms & metadata_terms)
        if not matched:
            continue
        matches.append({
            "id": asset.get("id"),
            "path": asset["path"],
            "rights_status": status,
            "score": len(matched),
            "matched_terms": matched,
            "output_notes": asset.get("output_notes") or asset.get("creative_notes"),
        })
    matches.sort(key=lambda item: (-item["score"], str(item["id"])))
    output = {
        "query": args.query,
        "query_terms": sorted(query_terms),
        "included_rights_statuses": ["cleared", "user-owned"] if not args.include_unusable else "all",
        "candidates": matches[:args.limit],
        "notice": "Candidates are metadata matches, not automatic selections. Inspect the actual media and confirm project-specific rights before listing it in a storyboard.",
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
