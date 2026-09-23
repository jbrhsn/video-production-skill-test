#!/usr/bin/env python3
"""Verify rendered schedule duration, source-frame mapping, tone onset, and hero frame."""
from __future__ import annotations

import argparse, hashlib, json, math, subprocess
from pathlib import Path


def command(args): return subprocess.run(args, check=True, capture_output=True).stdout
def raw_frame(path, frame, width, height): return command(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"select=eq(n\\,{frame})", "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
def pixel_error(left, right): return sum(abs(a - b) for a, b in zip(left, right)) / len(left)
def tone_energy(path, start, frequency, sample_rate=48_000):
    raw = command(["ffmpeg", "-v", "error", "-ss", str(start), "-t", "0.25", "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "-"])
    import array
    values = array.array("f"); values.frombytes(raw); omega = 2 * math.pi * frequency / sample_rate
    real = sum(value * math.cos(omega * index) for index, value in enumerate(values)); imaginary = sum(value * math.sin(omega * index) for index, value in enumerate(values))
    return real * real + imaginary * imaginary


def qualify(source, output, hero, expected_frames, width, height):
    probe = json.loads(command(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,nb_frames,duration,r_frame_rate,width,height", "-of", "json", str(output)]))
    video = next(row for row in probe["streams"] if row["codec_type"] == "video")
    if int(video["nb_frames"]) != expected_frames or video["width"] != width or video["height"] != height: raise ValueError("rendered video does not match compiled frame geometry")
    # The fixture's J-cut begins output frame 48 from source frame 60.
    output_frame = raw_frame(output, 48, width, height); source_frame = raw_frame(source, 60, width, height)
    if pixel_error(output_frame, source_frame) > 12: raise ValueError("J-cut picture does not land on declared source PTS")
    hero_raw = command(["ffmpeg", "-v", "error", "-i", str(hero), "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    last_raw = raw_frame(output, expected_frames - 1, width, height)
    # H.264 necessarily changes decoded pixels slightly; a direct still must
    # nonetheless match the final encoded frame within that codec tolerance.
    if pixel_error(hero_raw, last_raw) > 12: raise ValueError("hero is not the exact final rendered frame")
    before_440, before_880 = tone_energy(output, .2, 440), tone_energy(output, .2, 880)
    after_440, after_880 = tone_energy(output, 1.15, 440), tone_energy(output, 1.15, 880)
    if before_440 <= before_880 or after_880 <= after_440: raise ValueError("J-cut audio onset does not match declared source tone")
    return {"schema": "renderer-qualification", "version": 1, "status": "pass", "videoFrames": expected_frames, "jCut": {"audioFrame": 30, "pictureFrame": 48, "sourcePictureFrame": 60}, "checks": ["source-frame", "tone-onset", "hero-final-frame"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--source", required=True); parser.add_argument("--output", required=True); parser.add_argument("--hero", required=True); parser.add_argument("--frames", type=int, required=True); parser.add_argument("--width", type=int, required=True); parser.add_argument("--height", type=int, required=True); parser.add_argument("--out", required=True); args = parser.parse_args()
    report = qualify(args.source, args.output, args.hero, args.frames, args.width, args.height); Path(args.out).write_text(json.dumps(report, indent=2) + "\n"); print(json.dumps(report))

if __name__ == "__main__": main()
