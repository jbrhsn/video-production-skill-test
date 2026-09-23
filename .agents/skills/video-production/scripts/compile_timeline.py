#!/usr/bin/env python3
"""Compile a canonical editorial timeline into a deterministic render schedule."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_timeline import compile_timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    timeline = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    compiled = compile_timeline(timeline, sources)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
    print(f"Compiled {len(compiled['clips'])} clips to {compiled['totalFrames']} frames -> {output}")


if __name__ == "__main__":
    main()
