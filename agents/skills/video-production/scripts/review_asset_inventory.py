#!/usr/bin/env python3
"""Record route-aware creative-library discovery before video creative planning."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROUTES = {
    "faceless-standard": ("images", "brand", "fonts", "audio/music", "audio/sfx"),
    "faceless-editorial": ("images", "footage", "references", "brand", "fonts", "audio/music", "audio/sfx"),
    "recorded-edit": ("brand", "fonts", "audio/music", "audio/sfx", "images", "footage"),
    "hybrid-editorial-edit": ("images", "footage", "references", "brand", "fonts", "audio/music", "audio/sfx"),
}
STOP = {"a", "an", "and", "for", "from", "in", "of", "on", "or", "the", "to", "with"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(value: object) -> set[str]:
    return {item for item in re.findall(r"[a-z0-9]+", json.dumps(value).lower()) if item not in STOP}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-dir", required=True, type=Path)
    parser.add_argument("--route", required=True, choices=sorted(ROUTES))
    parser.add_argument("--query", action="append", required=True, help="BEAT_ID=topic/visual-beat")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    assets = args.assets_dir.expanduser().resolve()
    library_path = assets / "library.json"
    if not library_path.is_file():
        parser.error(f"Missing curated asset library: {library_path}")
    library = json.loads(library_path.read_text(encoding="utf-8"))
    queries = []
    for raw in args.query:
        beat, separator, query = raw.partition("=")
        if not separator or not beat.strip() or not query.strip():
            parser.error("--query must be BEAT_ID=query text")
        terms = tokens(query)
        candidates = []
        for asset in library.get("assets", []):
            if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
                continue
            matched = sorted(terms & tokens(asset))
            if matched:
                candidates.append({"id": asset.get("id"), "path": asset["path"],
                                   "rightsStatus": asset.get("rights", {}).get("status", "unknown"),
                                   "matchedTerms": matched})
        candidates.sort(key=lambda row: (-len(row["matchedTerms"]), str(row["id"])))
        queries.append({"beatId": beat, "query": query, "candidates": candidates})
    inventories = {"library.json": sha256(library_path)}
    generated = assets / "inventory.generated.json"
    if generated.is_file():
        inventories["inventory.generated.json"] = sha256(generated)
    result = {"schema": "video-production-asset-library-review", "version": 1, "route": args.route,
              "assetsDir": str(assets), "collections": list(ROUTES[args.route]), "inventoryDigests": inventories,
              "queries": queries, "dispositions": [],
              "notice": "Candidates are not selections. Record inspection, rights, and a selected/rejected/no-fit disposition before plan approval."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote asset-library review for {len(queries)} beat(s): {args.out}")


if __name__ == "__main__":
    main()
