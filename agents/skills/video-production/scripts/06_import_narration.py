"""Import recordings or explicit trims into the existing scene-WAV metadata contract."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def validate_manifest(manifest, base):
    scenes = manifest.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Manifest requires nonempty scenes")
    normalized = []
    for index, item in enumerate(scenes, 1):
        if type(item.get("scene")) is not int or item["scene"] != index or not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError("Scenes require consecutive integer IDs and nonempty approved text")
        if not isinstance(item.get("source"), str) or not item["source"]:
            raise ValueError(f"Scene {index}: source path required")
        source = (base / item["source"]).resolve()
        if not source.is_file():
            raise ValueError(f"Missing recording: {source}")
        start = item.get("start_s", 0)
        end = item.get("end_s")
        if isinstance(start, bool) or not isinstance(start, (float, int)) or not math.isfinite(start) or start < 0:
            raise ValueError("start_s must be finite and nonnegative")
        if end is not None and (isinstance(end, bool) or not isinstance(end, (float, int)) or not math.isfinite(end) or end <= start):
            raise ValueError("end_s must be finite and greater than start_s")
        normalized.append({**item, "source": str(source), "start_s": start, "end_s": end})
    return normalized


def import_narration(manifest_path: Path, out_dir: Path):
    manifest = json.loads(manifest_path.read_text())
    scenes = validate_manifest(manifest, manifest_path.parent)
    # A new output directory makes failure atomic and keeps existing takes intact.
    if out_dir.exists():
        raise ValueError("Output already exists; import into a new directory, then select the reviewed take")
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".narration-", dir=out_dir.parent) as temp:
        staging = Path(temp) / "audio"
        staging.mkdir()
        rows = []
        for item in scenes:
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "json", item["source"]], check=True, capture_output=True, text=True)
            source_duration = float(json.loads(probe.stdout)["format"]["duration"])
            end = source_duration if item["end_s"] is None else item["end_s"]
            if not math.isfinite(source_duration) or item["start_s"] >= source_duration or end > source_duration + 0.001:
                raise ValueError("Trim lies outside the recording")
            filename = f"scene-{item['scene']}.wav"
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", item["source"],
                       "-ss", str(item["start_s"]), "-t", str(end - item["start_s"]),
                       "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "24000", "-c:a", "pcm_f32le", str(staging / filename)]
            subprocess.run(command, check=True, capture_output=True)
            samples, rate = sf.read(staging / filename)
            if samples.size == 0 or not np.isfinite(samples).all() or not np.any(samples):
                raise ValueError(f"Scene {item['scene']}: empty, nonfinite, or silent recording")
            duration = len(samples) / rate
            if abs(duration - (end - item["start_s"])) > 0.1:
                raise ValueError("Decoded duration differs from requested trim; inspect source timing")
            rows.append({"scene": item["scene"], "file": filename, "text": item["text"],
                         "duration_s": duration, "source": item["source"],
                         "start_s": item["start_s"], "end_s": end})
        (staging / "metadata.json").write_text(json.dumps({"voice": manifest.get("voice", "recorded"),
            "lang": manifest.get("lang", "en"), "scenes": rows}, indent=2) + "\n")
        staging.rename(out_dir)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    rows = import_narration(Path(args.manifest).resolve(), Path(args.out_dir).resolve())
    print(f"Imported {len(rows)} scenes, {sum(r['duration_s'] for r in rows):.3f}s. Run timestamp extraction next.")


if __name__ == "__main__":
    main()
