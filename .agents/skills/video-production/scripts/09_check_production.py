#!/usr/bin/env python3
"""Check recorded production readiness without modifying project files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from production import check_production
from workflow_v2 import snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--production-state", help="Explicit state path; otherwise PROJECT/production-state.json")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--stage", choices=("plan", "implement", "scene", "render"))
    action.add_argument("--snapshot", help="Print digest for narration, plan, scene:N, or video; does not approve anything")
    parser.add_argument("--scene", type=int, help="Current scene for --stage scene")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    try:
        if args.snapshot:
            import re
            if not re.fullmatch(r"narration|plan|video|scene:[1-9][0-9]*", args.snapshot):
                raise ValueError("Invalid snapshot scope")
            print(snapshot(project, args.snapshot))
            return
        source = project / "storyboard.json"
        if args.stage == "plan":
            source = project / "public/audio/metadata.json"
        timeline = project / "src/timeline-data.json"
        if args.stage == "render" and timeline.is_file():
            source = timeline
        data = json.loads(source.read_text(encoding="utf-8"))
        scenes = data["scenes"] if isinstance(data, dict) else data
        if not isinstance(scenes, list) or not scenes:
            raise ValueError("Scene source must contain a nonempty scenes array")
        ids = [scene["scene"] for scene in scenes]
        if any(type(value) is not int for value in ids) or ids != list(range(1, len(ids) + 1)):
            raise ValueError("Scene IDs must be consecutive integers starting at 1")
        check_production(project, args.stage, ids, args.production_state, required=True, scene=args.scene)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Recorded {args.stage} readiness passed. V2 snapshots detect covered file changes; visual/rights quality and playback still require review.")


if __name__ == "__main__":
    main()
