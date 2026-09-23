#!/usr/bin/env python3
"""Content-addressed job state for resumable, full-master-safe production work."""
from __future__ import annotations

import hashlib, json, os, tempfile
from pathlib import Path


def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(data, stream, indent=2); stream.write("\n"); name = stream.name
    os.replace(name, path)


def plan(chapters, inputs, previous=None):
    if not isinstance(chapters, list) or not all(isinstance(value, str) and value for value in chapters): raise ValueError("chapters must be nonempty IDs")
    current = digest(inputs); old = (previous or {}).get("inputDigest")
    rows = [{"id": chapter, "status": "cached" if old == current and (previous or {}).get("chapters", {}).get(chapter) == "complete" else "pending"} for chapter in chapters]
    return {"schema": "production-build-state", "version": 1, "inputDigest": current, "chapters": {row["id"]: row["status"] for row in rows}, "fullMasterRequired": True, "resume": {"invalidated": old is not None and old != current, "reason": "input digest changed" if old and old != current else None}}
