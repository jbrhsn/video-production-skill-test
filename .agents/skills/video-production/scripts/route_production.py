#!/usr/bin/env python3
"""Resolve the first-class production route from explicit project inputs."""
from __future__ import annotations

import argparse
import json

from contracts import AUTONOMY_MODES, ROUTES


def route(request):
    if not isinstance(request, dict) or set(request) != {"recordedMedia", "generatedNarration", "needsExplanation", "autonomy"}:
        raise ValueError("route request requires recordedMedia, generatedNarration, needsExplanation, and autonomy")
    if any(type(request[key]) is not bool for key in ("recordedMedia", "generatedNarration", "needsExplanation")):
        raise ValueError("route media and explanation fields must be boolean")
    if request["autonomy"] not in AUTONOMY_MODES:
        raise ValueError("unsupported autonomy mode")
    if request["recordedMedia"]:
        selected = "hybrid-editorial-edit" if request["needsExplanation"] else "recorded-edit"
    else:
        selected = "faceless-editorial" if request["needsExplanation"] else "faceless-standard"
    if selected not in ROUTES:
        raise AssertionError("route catalog is inconsistent")
    return {"route": selected, "autonomy": request["autonomy"], "rationale": {
        "recordedMedia": request["recordedMedia"], "generatedNarration": request["generatedNarration"],
        "needsExplanation": request["needsExplanation"]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="Route request JSON file")
    args = parser.parse_args()
    with open(args.request, encoding="utf-8") as stream:
        print(json.dumps(route(json.load(stream)), indent=2))


if __name__ == "__main__":
    main()
