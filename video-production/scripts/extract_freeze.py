#!/usr/bin/env python3
"""Extract a source-coordinate still asset required by a canonical freeze clip."""
from __future__ import annotations

import argparse, subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--input", required=True); parser.add_argument("--source-us", type=int, required=True); parser.add_argument("--output", required=True); args = parser.parse_args()
    if args.source_us < 0: parser.error("source-us must be nonnegative")
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-ss", f"{args.source_us / 1_000_000:.6f}", "-i", args.input, "-frames:v", "1", str(out)], check=True)
    print(out)

if __name__ == "__main__": main()
