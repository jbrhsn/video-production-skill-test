#!/usr/bin/env python3
"""Check generated or recorded production readiness without modifying project files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from production import check_production


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--production-state", help="Explicit state path; otherwise PROJECT/production-state.json")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--stage", choices=("source", "edit", "plan", "implement", "scene", "render", "delivery"))
    action.add_argument("--snapshot", help="Print a track-valid input digest; does not approve anything")
    parser.add_argument("--scene", type=int, help="Current scene for --stage scene")
    parser.add_argument("--draft", action="store_true", help="Validate a local recorded-edit review render, never final export")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    try:
        state_path = Path(args.production_state).expanduser().resolve() if args.production_state else project / "production-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        recorded = state.get("version") == 3 and state.get("track") == "recorded-edit"
        if args.snapshot:
            if recorded:
                from recorded_workflow import snapshot
            else:
                from workflow_v2 import snapshot
            print(snapshot(project, args.snapshot))
            return
        if recorded:
            check_production(project, args.stage, state_path=args.production_state, scene=args.scene, draft=args.draft)
            print(f"Recorded-edit {args.stage} readiness passed. Playback and creative review remain separate evidence.")
            return
        if args.stage in ("source", "edit", "delivery") or args.draft:
            raise ValueError("This stage/option applies only to recorded-edit v3 projects")
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
    print(f"Generated-production {args.stage} readiness passed. V2 snapshots detect covered file changes; visual/rights quality and playback still require review.")


if __name__ == "__main__":
    main()
