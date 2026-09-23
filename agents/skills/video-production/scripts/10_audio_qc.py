#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Measure an existing rendered mix; never renders, masters, or approves it."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path


def parse_loudnorm(stderr: str) -> dict:
    blocks = re.findall(r"\{[^{}]*\}", stderr, re.S)
    for block in reversed(blocks):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if "input_i" in data and "input_tp" in data:
            return data
    raise ValueError("ffmpeg did not return loudnorm JSON")


def measure(media: Path) -> dict:
    if not media.is_file() or not media.stat().st_size:
        raise ValueError(f"Missing or empty rendered media: {media}")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-select_streams", "a", "-show_entries", "stream=codec_name,channels,sample_rate",
                            "-of", "json", str(media)], check=True, capture_output=True, text=True)
    metadata = json.loads(probe.stdout)
    if not metadata.get("streams"):
        raise ValueError("Rendered media has no audio stream")
    loudness = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(media),
                               "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                              check=True, capture_output=True, text=True)
    stats = parse_loudnorm(loudness.stderr)
    result = {
        "media": str(media.resolve()),
        "durationSeconds": float(metadata["format"]["duration"]),
        "audioStream": metadata["streams"][0],
        "integratedLufs": float(stats["input_i"]),
        "loudnessRangeLu": float(stats["input_lra"]),
        "truePeakDbtp": float(stats["input_tp"]),
        "thresholdLufs": float(stats["input_thresh"]),
        "measurement": "ffmpeg loudnorm analysis; no mastering or listening performed"
    }
    if not all(math.isfinite(result[key]) for key in ("durationSeconds", "integratedLufs", "loudnessRangeLu", "truePeakDbtp")):
        raise ValueError("Non-finite audio measurement")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Existing rendered video or audio file")
    parser.add_argument("--out", required=True, help="JSON report path")
    parser.add_argument("--target-lufs", type=float)
    parser.add_argument("--tolerance-lufs", type=float, default=1)
    parser.add_argument("--max-true-peak-dbtp", type=float)
    args = parser.parse_args()
    if args.tolerance_lufs < 0 or not math.isfinite(args.tolerance_lufs):
        raise ValueError("Tolerance must be finite and nonnegative")
    report = measure(Path(args.input).expanduser().resolve())
    findings = []
    if args.target_lufs is not None:
        if not math.isfinite(args.target_lufs):
            raise ValueError("Target LUFS must be finite")
        delta = report["integratedLufs"] - args.target_lufs
        findings.append({"check": "integratedLoudness", "target": args.target_lufs,
                         "tolerance": args.tolerance_lufs, "measured": report["integratedLufs"],
                         "status": "within-target" if abs(delta) <= args.tolerance_lufs else "outside-target"})
    if args.max_true_peak_dbtp is not None:
        if not math.isfinite(args.max_true_peak_dbtp):
            raise ValueError("True-peak target must be finite")
        findings.append({"check": "truePeak", "maximum": args.max_true_peak_dbtp,
                         "measured": report["truePeakDbtp"],
                         "status": "within-limit" if report["truePeakDbtp"] <= args.max_true_peak_dbtp else "over-limit"})
    report["findings"] = findings
    report["listeningReview"] = "not performed"
    output = Path(args.out).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audio QC report: {output}")


if __name__ == "__main__":
    main()
