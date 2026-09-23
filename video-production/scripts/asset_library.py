"""Validation for route-aware workspace creative-library review evidence."""
from __future__ import annotations

import json
from pathlib import Path


ROUTES = {"faceless-standard", "faceless-editorial", "recorded-edit", "hybrid-editorial-edit"}
OUTCOMES = {"selected", "rejected", "reference-only", "no-fit"}


def validate_review(path: Path, allowed_routes: set[str] | None = None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "video-production-asset-library-review" or data.get("version") != 1:
        raise ValueError("Asset-library review requires schema video-production-asset-library-review version 1")
    if data.get("route") not in ROUTES or (allowed_routes and data["route"] not in allowed_routes):
        raise ValueError("Asset-library review route does not match this production workflow")
    if not isinstance(data.get("collections"), list) or not data["collections"] or not all(isinstance(item, str) and item for item in data["collections"]):
        raise ValueError("Asset-library review requires checked collections")
    queries = data.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("Asset-library review requires one or more beat queries")
    beats = set()
    for query in queries:
        if not isinstance(query, dict) or not isinstance(query.get("beatId"), str) or not query["beatId"].strip() or not isinstance(query.get("query"), str) or not query["query"].strip() or not isinstance(query.get("candidates"), list):
            raise ValueError("Asset-library review query requires beatId, query, and candidates")
        if query["beatId"] in beats:
            raise ValueError("Asset-library review beat IDs must be unique")
        beats.add(query["beatId"])
    dispositions = data.get("dispositions")
    if not isinstance(dispositions, list):
        raise ValueError("Asset-library review requires dispositions")
    decided = set()
    for item in dispositions:
        if not isinstance(item, dict) or item.get("beatId") not in beats or item.get("outcome") not in OUTCOMES or not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError("Asset-library review disposition requires beatId, outcome, and reason")
        decided.add(item["beatId"])
    if decided != beats:
        raise ValueError("Every asset-library review query requires a selected, rejected, reference-only, or no-fit disposition")
    return data
