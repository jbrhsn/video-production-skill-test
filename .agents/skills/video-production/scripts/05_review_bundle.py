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


def build_commands(data, output_root="out/review", only_scene=None):
    recorded = data.get("version") == 3 and data.get("track") == "recorded-edit"
    selected_scenes = [s for s in data["scenes"] if only_scene is None or s["scene"] == only_scene]
    if not selected_scenes:
        raise ValueError("Requested scene is absent from the compiled timeline")
    if only_scene is None:
        samples = {0, data["totalFrames"] - 1}
    else:
        row = selected_scenes[0]
        start = row["startFrame"] if recorded else row["start"]
        duration = row["durationFrames"] if recorded else row["spanFrames"]
        samples = {start, start + duration - 1}
    compositions = ([] if recorded else [f"Scene{s['scene']}" for s in selected_scenes])
    compositions += [f"Scene{s['scene']}Review" for s in selected_scenes]
    compositions += ([] if recorded else [f"Boundary{b['afterScene']}" for b in data["boundaries"]])
    if only_scene is None:
        compositions.append("VideoFull")
    base = ["npx", "--no-install", "remotion"]
    commands = [base + ["render", "src/index.ts", name, f"{output_root}/{name}.mp4",
                       "--codec=h264", "--pixel-format=yuv420p"] for name in compositions]
    for scene in selected_scenes:
        if recorded:
            samples.update((scene["startFrame"], scene["startFrame"] + scene["durationFrames"] // 2,
                            scene["startFrame"] + scene["durationFrames"] - 1))
        else:
            samples.update((scene["start"], scene["start"] + scene["contentFrames"] // 2,
                            scene["start"] + scene["spanFrames"] - 1))
    for boundary in data.get("boundaries", []):
        start = boundary["frame"] - boundary["frames"] // 2
        samples.update((max(0, start - 1), boundary["frame"],
                        min(data["totalFrames"] - 1, start + boundary["frames"])))
    ordered = sorted(samples)
    for index, frame in enumerate(ordered):
        commands.append(base + ["still", "src/index.ts", "VideoFull",
                                f"{output_root}/frame-{index:04d}.png", f"--frame={frame}"])
    commands.append(["ffmpeg", "-y", "-framerate", "1", "-start_number", "0", "-i",
                     f"{output_root}/frame-%04d.png", "-vf",
                     f"scale=320:-1,tile=3x{math.ceil(len(ordered) / 3)}:nb_frames={len(ordered)}",
                     "-frames:v", "1", f"{output_root}/contact-sheet.png"])
    return commands, ordered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--production-state", help="State path; defaults to PROJECT/production-state.json when present.")
    parser.add_argument("--render", action="store_true", help="Execute planned renders and contact-sheet generation")
    parser.add_argument("--draft", action="store_true", help="Render a pending recorded scene review, never a final export")
    parser.add_argument("--scene", type=int, help="Active scene for --draft")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    marker = project / "src/timeline-contract.json"
    contract = json.loads(marker.read_text()) if marker.exists() else None
    if contract not in ({"version": 2, "sceneContract": "visual-only"}, {"version": 3, "track": "recorded-edit"}):
        raise ValueError("Review bundle requires a supported production timeline")
    data = json.loads((project / "src/timeline-data.json").read_text())
    if args.draft and contract.get("version") != 3:
        raise ValueError("--draft applies only to recorded-edit projects")
    if args.draft and not args.scene:
        raise ValueError("--draft requires --scene")
    if args.render:
        stage = "scene" if args.draft else "render"
        check_production(project, stage, [scene["scene"] for scene in data["scenes"]], args.production_state,
                         scene=args.scene, draft=args.draft)
    elif args.production_state and not Path(args.production_state).expanduser().is_file():
        raise ValueError(f"Missing production state: {args.production_state}")
    output = project / "review" if args.draft else project / "out/review"
    output_relative = "review" if args.draft else "out/review"
    commands, frames = build_commands(data, output_relative, args.scene if args.draft else None)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"status": "planned", "purpose": "draft-scene-review" if args.draft else "final-master-review",
                "frames": frames, "commands": commands,
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
    recorded = contract.get("version") == 3
    context_note = ("SceneNReview is a bounded slice of the recorded master with synchronized footage, selected audio, captions and layout. "
                    if recorded else
                    "SceneN is isolated visual/narration inspection. SceneNReview is the bounded master-timeline view with continuing music/effects; "
                    "BoundaryN and VideoFull also preserve the master mix. ")
    report.write_text(
        "# Review bundle\n\nSee manifest.json for actual command execution status. "
        "Files from earlier runs may exist; only the current manifest establishes what was rendered.\n\n"
        "Playback/listening and creative review: NOT PERFORMED by this helper.\n\n"
        "Durable user feedback and approvals belong in PROJECT/production-state.json; this generated report is not approval evidence. "
        "Prior reports are retained as review-previous-N.md.\n\n"
        "Record observations by master frame/time: opening promise and payoff; useful progression; "
        "visual explanation; boundary continuity; caption readability; voice/mix clarity; "
        "platform fit. For each issue, record evidence and a concrete correction.\n\n"
        "Contact sheet frames are listed in manifest order. " + context_note + "\n")
    if args.render:
        manifest["status"] = "rendering"
        save()
        try:
            for command in commands:
                subprocess.run(command, cwd=project, check=True)
                manifest["completedCommands"] += 1
                save()
            probe_target = f"review/Scene{args.scene}Review.mp4" if args.draft else "out/review/VideoFull.mp4"
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                                    "-of", "json", probe_target],
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
