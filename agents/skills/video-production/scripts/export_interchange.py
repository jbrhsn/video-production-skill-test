#!/usr/bin/env python3
"""Write canonical timeline handoff JSON and corrected SRT sidecar captions."""
from __future__ import annotations

import argparse, json
from pathlib import Path
from interchange import export_manifest, srt

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--timeline", required=True); parser.add_argument("--sources", required=True); parser.add_argument("--out", required=True); parser.add_argument("--srt", required=True); args = parser.parse_args()
    timeline = json.loads(Path(args.timeline).read_text()); sources = json.loads(Path(args.sources).read_text())
    Path(args.out).write_text(json.dumps(export_manifest(timeline, sources, timeline.get("captions", [])), indent=2) + "\n")
    Path(args.srt).write_text(srt(timeline.get("captions", [])))

if __name__ == "__main__": main()
