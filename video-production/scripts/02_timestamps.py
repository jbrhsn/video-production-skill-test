#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openai-whisper>=20231117",
#   "soundfile>=0.12.1",
# ]
# ///
"""
02_timestamps.py — Whisper word-level timestamp extractor

Transcribes a single scene WAV file using OpenAI Whisper with
word_timestamps=True and writes a structured JSON file containing
word-level start/end times in seconds.

Usage:
    uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/02_timestamps.py \\
        --audio path/to/public/audio/scene-N.wav \\
        --model base \\
        --out path/to/public/audio/scene-N-timestamps.json

The output JSON is consumed by the Remotion scene components to drive
@remotion/captions word-highlight subtitle rendering.

Supported --model values: tiny, base, small, medium, large
Default: base  (best speed/quality balance for typical narration audio)

Required models are verified and cached under WORKSPACE/.video_production_assets/whisper.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import whisper
from model_cache import ensure


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract word-level timestamps from a voiceover WAV using Whisper.")
    p.add_argument("--audio", required=True, help="Path to the input WAV file (scene-N.wav).")
    p.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                   help="Whisper model size (default: base).")
    p.add_argument("--out", required=True, help="Path to write the output JSON file.")
    p.add_argument("--language", default=None,
                   help="Force a specific language code (e.g. 'en'). Auto-detected if omitted.")
    p.add_argument("--assets-dir", required=True, help="Path to WORKSPACE/.video_production_assets.")
    p.add_argument("--model-dir", default=None, help="Compatibility override; must equal ASSETS_DIR/whisper.")
    return p.parse_args()


def extract_words(result: dict) -> list[dict]:
    """Flatten word-level entries from all segments into a single list."""
    words: list[dict] = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            word_text = w.get("word", "").strip()
            if not word_text:
                continue
            words.append(
                {
                    "word": word_text,
                    "start": round(float(w["start"]), 4),
                    "end": round(float(w["end"]), 4),
                }
            )
    return words


def get_audio_duration(audio_path: Path) -> float:
    """Measure the complete WAV duration, including trailing silence."""
    import soundfile as sf
    return round(sf.info(str(audio_path)).duration, 4)


def main() -> None:
    args = parse_args()
    audio_path = Path(args.audio).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    assets_dir = Path(args.assets_dir).expanduser().resolve()

    if not audio_path.exists():
        print(f"ERROR: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    if assets_dir.name != ".video_production_assets":
        raise ValueError("--assets-dir must name WORKSPACE/.video_production_assets")
    model_dir = assets_dir / "whisper"
    if args.model_dir and Path(args.model_dir).expanduser().resolve() != model_dir:
        raise ValueError("--model-dir must equal WORKSPACE/.video_production_assets/whisper")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    duration_s = get_audio_duration(audio_path)
    if duration_s <= 0:
        raise ValueError("Audio has no samples")
    if duration_s >= 0.5:
        ensure(assets_dir, [f"whisper:{args.model}"], allow_download=True)
        print(f"Loading Whisper '{args.model}' from {model_dir}...")
    model = whisper.load_model(args.model, download_root=str(model_dir)) if duration_s >= 0.5 else None

    transcribe_kwargs: dict = {"word_timestamps": True, "fp16": False}
    if args.language:
        transcribe_kwargs["language"] = args.language

    print(f"Transcribing: {audio_path.name}")
    result = model.transcribe(str(audio_path), **transcribe_kwargs) if model else {"segments": []}

    words = extract_words(result)

    if duration_s >= 0.5 and not words:
        raise ValueError("Whisper produced no words; inspect narration before continuing")
    previous_start = 0.0
    for word in words:
        if not (previous_start <= word["start"] <= word["end"] <= duration_s):
            raise ValueError(f"Invalid word timing: {word}")
        previous_start = word["start"]

    # Derive scene name from the audio filename (e.g. "scene-2.wav" → "scene-2")
    scene_name = audio_path.stem  # filename without extension

    output = {
        "scene": scene_name,
        "audio_file": audio_path.name,
        "duration_s": round(duration_s, 4),
        "language": result.get("language", args.language or "unknown"),
        "words": words,
    }

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  → {len(words)} words extracted, {duration_s:.2f}s duration")
    print(f"  → Written to: {out_path}")


if __name__ == "__main__":
    main()
