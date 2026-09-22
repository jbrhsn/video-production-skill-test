#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "kokoro-onnx>=0.4.0",
#   "soundfile>=0.12.1",
#   "numpy>=1.26",
# ]
# ///
"""
01_tts.py — Kokoro ONNX voiceover synthesizer

Splits transcript.txt on '---' scene separators, synthesizes each scene
using the Kokoro ONNX model, and writes one WAV per scene plus a
metadata.json summary into the output directory.

Usage:
    uv run 01_tts.py \\
        --text path/to/transcript.txt \\
        --voice af_heart \\
        --assets-dir path/to/.video_production_assets \\
        --out-dir path/to/remotion-infographic/public/audio

Requirements:
    .video_production_assets/kokoro/kokoro-v1.0.onnx
    .video_production_assets/kokoro/voices-v1.0.bin
    brew install espeak-ng   (macOS phoneme backend for Kokoro)
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

SAMPLE_RATE = 24_000  # Kokoro v1.0 native output sample rate


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Synthesize voiceover WAVs with Kokoro ONNX.")
    p.add_argument("--text", required=True, help="Path to transcript.txt with '---' scene separators.")
    p.add_argument("--voice", default="af_heart", help="Kokoro voice ID (default: af_heart).")
    p.add_argument("--assets-dir", required=True, help="Path to the .video_production_assets directory.")
    p.add_argument("--out-dir", required=True, help="Directory to write scene-N.wav and metadata.json.")
    p.add_argument("--lang", default="en-us", help="Language code for Kokoro (default: en-us).")
    return p.parse_args()


def check_assets(assets_dir: Path) -> tuple[Path, Path]:
    """Verify that the Kokoro model and voices files are present."""
    kokoro_dir = assets_dir / "kokoro"
    model_path = kokoro_dir / "kokoro-v1.0.onnx"
    voices_path = kokoro_dir / "voices-v1.0.bin"

    missing: list[str] = []
    if not model_path.is_file() or model_path.stat().st_size != 325532387:
        missing.append(str(model_path))
    if not voices_path.is_file() or voices_path.stat().st_size != 28214398:
        missing.append(str(voices_path))

    if missing:
        print("ERROR: Kokoro model assets missing or invalid:", file=sys.stderr)
        for m in missing:
            print(f"  Missing: {m}", file=sys.stderr)
        print(
            "\nRun the one-time setup script to download them:\n"
            f"  bash {Path(__file__).with_name('04_setup_assets.sh')} {assets_dir.parent}\n"
            f"\nExpected asset directory: {kokoro_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    with np.load(voices_path, allow_pickle=False) as voices:
        if not voices.files:
            raise ValueError("Voice archive is empty; rerun asset setup")
    return model_path, voices_path


def parse_transcript(text_path: Path) -> list[str]:
    """Split transcript on '---' separator lines; skip empty scenes."""
    raw = text_path.read_text(encoding="utf-8")
    scenes = [s.strip() for s in re.split(r"(?m)^\s*---\s*$", raw)]
    scenes = [s for s in scenes if s]  # drop empty segments
    if not scenes:
        print("ERROR: transcript.txt contains no non-empty scenes.", file=sys.stderr)
        sys.exit(1)
    return scenes


def normalize_audio(samples: np.ndarray) -> np.ndarray:
    """Peak-normalize to -1 dBFS to prevent clipping."""
    peak = np.max(np.abs(samples))
    if peak > 0:
        target = 10 ** (-1 / 20)  # -1 dBFS
        samples = samples * (target / peak)
    return samples


def synthesize_scene(
    kokoro: Kokoro,
    text: str,
    voice: str,
    lang: str,
    out_path: Path,
) -> float:
    """Synthesize a single scene and write to out_path. Returns duration in seconds."""
    samples, sr = kokoro.create(text, voice=voice, lang=lang)
    samples = np.array(samples, dtype=np.float32)

    if samples.size == 0 or not np.isfinite(samples).all() or not np.any(samples):
        raise ValueError(f"TTS produced empty, silent, or non-finite audio: {text[:60]!r}")
    if sr != SAMPLE_RATE:
        raise ValueError(f"Unexpected sample rate {sr}; expected {SAMPLE_RATE}")

    samples = normalize_audio(samples)
    sf.write(str(out_path), samples, SAMPLE_RATE, subtype="FLOAT")
    return len(samples) / SAMPLE_RATE


def main() -> None:
    args = parse_args()
    text_path = Path(args.text).expanduser().resolve()
    assets_dir = Path(args.assets_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not text_path.exists():
        print(f"ERROR: transcript file not found: {text_path}", file=sys.stderr)
        sys.exit(1)

    model_path, voices_path = check_assets(assets_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scenes = parse_transcript(text_path)
    with np.load(voices_path, allow_pickle=False) as voices:
        if args.voice not in voices.files:
            raise ValueError(f"Unknown voice {args.voice!r}. Available: {', '.join(voices.files)}")
    print(f"Loading Kokoro model from: {model_path}")
    kokoro = Kokoro(str(model_path), str(voices_path))
    print(f"Voice: {args.voice}  |  Language: {args.lang}  |  Scenes: {len(scenes)}")

    metadata_scenes: list[dict] = []

    for i, scene_text in enumerate(scenes, start=1):
        wav_name = f"scene-{i}.wav"
        wav_path = out_dir / wav_name
        print(f"  Synthesizing scene {i}/{len(scenes)}: {scene_text[:60]!r}...")
        duration_s = synthesize_scene(kokoro, scene_text, args.voice, args.lang, wav_path)
        print(f"    → {wav_name}  ({duration_s:.2f}s)")
        metadata_scenes.append(
            {
                "scene": i,
                "file": wav_name,
                "duration_s": round(duration_s, 4),
                "text": scene_text,
            }
        )

    metadata = {
        "voice": args.voice,
        "lang": args.lang,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scenes": metadata_scenes,
    }
    meta_path = out_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone. Wrote {len(scenes)} WAV file(s) and metadata.json to: {out_dir}")


if __name__ == "__main__":
    main()
