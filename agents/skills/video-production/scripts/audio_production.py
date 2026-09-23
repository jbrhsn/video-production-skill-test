#!/usr/bin/env python3
"""Measure a rendered mix and retain an honest, reproducible audio evidence record."""
from __future__ import annotations

import argparse, json, subprocess
from pathlib import Path

def measure(path):
    result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, check=False)
    return {"schema": "audio-measurement", "version": 1, "input": str(path), "tool": "ffmpeg ebur128", "returnCode": result.returncode, "rawEvidence": result.stderr[-8000:], "coverage": {"loudness": "measured" if result.returncode == 0 else "error", "listeningReview": "unavailable", "forcedAlignment": "unavailable"}}

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--input", required=True); parser.add_argument("--out", required=True); args = parser.parse_args()
    report = measure(args.input); Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    if report["coverage"]["loudness"] == "error": raise SystemExit(1)

if __name__ == "__main__": main()
