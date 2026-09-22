#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Prepare review commands; execute local renders only with --render."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from production import check_production


def build_commands(data):
    samples = {0, data["totalFrames"] - 1}
    compositions = [f"Scene{s['scene']}" for s in data["scenes"]]
    compositions += [f"Scene{s['scene']}Review" for s in data["scenes"]]
    compositions += [f"Boundary{b['afterScene']}" for b in data["boundaries"]]
    compositions.append("VideoFull")
    base = ["npx", "--no-install", "remotion"]
    commands = [base + ["render", "src/index.ts", name, f"out/review/{name}.mp4",
                       "--codec=h264", "--pixel-format=yuv420p"] for name in compositions]
    for scene in data["scenes"]:
        samples.update((scene["start"], scene["start"] + scene["contentFrames"] // 2,
                        scene["start"] + scene["spanFrames"] - 1))
    for boundary in data["boundaries"]:
        start = boundary["frame"] - boundary["frames"] // 2
        samples.update((max(0, start - 1), boundary["frame"],
                        min(data["totalFrames"] - 1, start + boundary["frames"])))
    ordered = sorted(samples)
    for index, frame in enumerate(ordered):
        commands.append(base + ["still", "src/index.ts", "VideoFull",
                                f"out/review/frame-{index:04d}.png", f"--frame={frame}"])
    commands.append(["ffmpeg", "-y", "-framerate", "1", "-start_number", "0", "-i",
                     "out/review/frame-%04d.png", "-vf",
                     f"scale=320:-1,tile=3x{math.ceil(len(ordered) / 3)}:nb_frames={len(ordered)}",
                     "-frames:v", "1", "out/review/contact-sheet.png"])
    return commands, ordered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--production-state", help="State path; defaults to PROJECT/production-state.json when present.")
    parser.add_argument("--render", action="store_true", help="Execute planned renders and contact-sheet generation")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    marker = project / "src/timeline-contract.json"
    if not marker.exists() or json.loads(marker.read_text()) != {"version": 2, "sceneContract": "visual-only"}:
        raise ValueError("Review bundle requires the visual-only v2 production timeline")
    data = json.loads((project / "src/timeline-data.json").read_text())
    if args.render:
        check_production(project, "render", [scene["scene"] for scene in data["scenes"]], args.production_state)
    elif args.production_state and not Path(args.production_state).expanduser().is_file():
        raise ValueError(f"Missing production state: {args.production_state}")
    commands, frames = build_commands(data)
    output = project / "out/review"
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"status": "planned", "frames": frames, "commands": commands,
                "completedCommands": 0, "playbackReview": "not performed", "creativeReview": "not performed"}
    path = output / "manifest.json"
    def save():
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    save()
    report = output / "review.md"
    if report.exists():
        index = 1
        while (output / f"review-previous-{index}.md").exists():
            index += 1
        report.rename(output / f"review-previous-{index}.md")
    report.write_text(
        "# Review bundle\n\nSee manifest.json for actual command execution status. "
        "Files from earlier runs may exist; only the current manifest establishes what was rendered.\n\n"
        "Playback/listening and creative review: NOT PERFORMED by this helper.\n\n"
        "Durable user feedback and approvals belong in PROJECT/production-state.json; this generated report is not approval evidence. "
        "Prior reports are retained as review-previous-N.md.\n\n"
        "Record observations by master frame/time: opening promise and payoff; useful progression; "
        "visual explanation; boundary continuity; caption readability; voice/mix clarity; "
        "platform fit. For each issue, record evidence and a concrete correction.\n\n"
        "Contact sheet frames are listed in manifest order. SceneN is isolated visual/narration inspection. "
        "SceneNReview is the bounded master-timeline view with continuing music/effects; BoundaryN and "
        "VideoFull also preserve the master mix.\n")
    if args.render:
        manifest["status"] = "rendering"
        save()
        try:
            for command in commands:
                subprocess.run(command, cwd=project, check=True)
                manifest["completedCommands"] += 1
                save()
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                                    "-of", "json", "out/review/VideoFull.mp4"],
                                   cwd=project, check=True, capture_output=True, text=True)
            (output / "probe.json").write_text(probe.stdout)
            manifest["status"] = "rendered; metadata captured; playback and creative review pending"
        except (OSError, subprocess.CalledProcessError):
            manifest["status"] = "failed; partial outputs are not a completed review"
            raise
        finally:
            save()
    print(f"Review bundle: {output} ({manifest['status']})")


if __name__ == "__main__":
    main()
