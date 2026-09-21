#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
03_scaffold.py — Remotion project scaffolder for video-production

Initializes or explicitly refreshes a Remotion project directory from a storyboard.json.
Creates all structural files (package.json, tsconfig.json, src/config.ts,
src/index.ts, src/Root.tsx, scene stubs) and updates the project .gitignore.
Runs npm install at the end.

Usage:
    uv run 03_scaffold.py \\
        --project-dir path/to/remotion-infographic \\
        --fps 30 \\
        --width 1080 \\
        --height 1920 \\
        --storyboard path/to/storyboard.json

Re-running is safe: it will NOT overwrite existing scene TSX files
(those contain real agent-authored composition code). With --refresh-generated it replaces
package.json, tsconfig.json, src/config.ts, src/index.ts, and src/Root.tsx
if they already exist — these are generated from storyboard data.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from timeline import compile_timeline
from production import check_production


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scaffold a Remotion project from a storyboard.json.")
    p.add_argument("--project-dir", required=True, help="Path to the remotion project directory (created if absent).")
    p.add_argument("--storyboard", required=True, help="Path to directorial storyboard.json (or legacy combined storyboard).")
    p.add_argument("--audio-metadata", help="TTS metadata.json; derives timing independently from creative direction.")
    p.add_argument("--production-state", help="State path; defaults to PROJECT/production-state.json when present.")
    p.add_argument("--legacy-workflow", action="store_true", help="Explicit compatibility/test path for absent or v1 state; never bypasses v2 gates.")
    p.add_argument("--edit-plan", help="Version 1 transition/hold/audio plan; requires visual-only scenes.")
    p.add_argument("--profile", choices=("vertical", "youtube-horizontal"), default="vertical")
    p.add_argument("--visual-style", choices=("custom", "whiteboard"), default="custom",
                   help="Optional visual helper kit; independent of aspect ratio. Preserves existing helpers.")
    p.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30).")
    p.add_argument("--width", type=int, help="Override profile width in pixels.")
    p.add_argument("--height", type=int, help="Override profile height in pixels.")
    p.add_argument("--remotion-version", default="4.0.526", help="Remotion package version to pin (default: 4.0.526).")
    p.add_argument("--skip-install", action="store_true", help="Skip npm install (useful for dry-run inspection).")
    p.add_argument("--refresh-generated", action="store_true", help="Explicitly replace generated structural files; preserves scenes.")
    return p.parse_args()


# ---------------------------------------------------------------------------
# File content generators
# ---------------------------------------------------------------------------

def make_package_json(version: str, total_frames: int, guarded: bool = False) -> str:
    last_frame = max(0, total_frames - 1)
    data = {
        "name": "video-production",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "studio": "npx remotion studio src/index.ts",
            "typecheck": "tsc --noEmit",
            "render": "node scripts/production-export.cjs render" if guarded else "npx remotion render src/index.ts VideoFull out/video.mp4 --codec=h264 --pixel-format=yuv420p",
            "hero": "node scripts/production-export.cjs hero" if guarded else f"npx remotion still src/index.ts VideoFull out/video-hero.png --frame={last_frame}",
        },
        "dependencies": {
            "remotion": version,
            "@remotion/media": version,
            "@remotion/cli": version,
            "react": "18.3.1",
            "react-dom": "18.3.1",
        },
        "devDependencies": {
            "typescript": "5.4.5",
            "@types/react": "18.3.1",
        },
    }
    return json.dumps(data, indent=2)


def make_tsconfig() -> str:
    data = {
        "compilerOptions": {
            "target": "ES2020",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "jsx": "react",
            "strict": True,
            "skipLibCheck": True,
            "resolveJsonModule": True,
            "esModuleInterop": True,
            "outDir": "dist",
        },
        "include": ["src"],
    }
    return json.dumps(data, indent=2)


def make_config_ts(fps: int, width: int, height: int, scenes: list[dict]) -> str:
    scenes_ts = json.dumps(
        [
            {
                "id": f"Scene{s['scene']}",
                "durationFrames": s["duration_frames"],
                "audioFile": f"audio/{s['audio_file']}",
                "timestampsFile": f"audio/{s['timestamps_file']}",
                "title": s.get("title", f"Scene {s['scene']}"),
            }
            for s in scenes
        ],
        indent=2,
    )
    total = sum(s["duration_frames"] for s in scenes)
    return dedent(f"""\
        // src/config.ts
        // Auto-generated by 03_scaffold.py — re-run scaffold to refresh after storyboard changes.

        export const VIDEO_CONFIG = {{
          fps: {fps},
          width: {width},
          height: {height},
        }} as const;

        export interface SceneConfig {{
          id: string;
          durationFrames: number;
          audioFile: string;
          timestampsFile: string;
          title: string;
        }}

        export const SCENES: SceneConfig[] = {scenes_ts};

        export const TOTAL_FRAMES = SCENES.reduce((sum, s) => sum + s.durationFrames, 0);
        export const LAST_FRAME = TOTAL_FRAMES - 1;
    """)


def make_index_ts() -> str:
    return dedent("""\
        import { registerRoot } from "remotion";
        import { Root } from "./Root";
        registerRoot(Root);
    """)


def make_root_tsx(scenes: list[dict]) -> str:
    imports = "\n".join(
        f'import {{ Scene{s["scene"]} }} from "./scenes/Scene{s["scene"]}";' for s in scenes
    )
    series_sequences = "\n".join(
        f'      <Series.Sequence durationInFrames={{SCENES[{i}].durationFrames}}>\n'
        f'        <Scene{s["scene"]} />\n'
        f'      </Series.Sequence>'
        for i, s in enumerate(scenes)
    )
    scene_compositions = "\n".join(
        f'    <Composition\n'
        f'      id="Scene{s["scene"]}"\n'
        f'      component={{Scene{s["scene"]}}}\n'
        f'      durationInFrames={{SCENES[{i}].durationFrames}}\n'
        f'      fps={{VIDEO_CONFIG.fps}}\n'
        f'      width={{VIDEO_CONFIG.width}}\n'
        f'      height={{VIDEO_CONFIG.height}}\n'
        f'    />'
        for i, s in enumerate(scenes)
    )
    return dedent(f"""\
        import React from "react";
        import {{ Composition, Series }} from "remotion";
        import {{ VIDEO_CONFIG, SCENES, TOTAL_FRAMES }} from "./config";
        {imports}

        const VideoFull: React.FC = () => (
          <Series>
        {series_sequences}
          </Series>
        );

        export const Root: React.FC = () => (
          <>
            {{/* Master composition — full merged video */}}
            <Composition
              id="VideoFull"
              component={{VideoFull}}
              durationInFrames={{TOTAL_FRAMES}}
              fps={{VIDEO_CONFIG.fps}}
              width={{VIDEO_CONFIG.width}}
              height={{VIDEO_CONFIG.height}}
            />
            {{/* Per-scene compositions for isolated preview rendering */}}
        {scene_compositions}
          </>
        );
    """)


def make_scene_stub(scene: dict, visual_only: bool = False) -> str:
    n = scene["scene"]
    name = "VisualScene.tsx.template" if visual_only else "Scene.tsx.template"
    template = (Path(__file__).parent.parent / "assets" / name).read_text()
    values = {
        "__SCENE__": str(n),
        "__TITLE__": json.dumps(scene.get("title", f"Scene {n}")),
        "__AUDIO__": json.dumps("audio/" + scene["audio_file"]),
        "__TIMESTAMPS__": json.dumps("../../public/audio/" + scene["timestamps_file"]),
    }
    for key, value in values.items():
        template = template.replace(key, value)
    return template


def make_visual_root(scenes: list[dict]) -> str:
    imports = "\n".join(
        f'import {{Scene{s["scene"]}}} from "./scenes/Scene{s["scene"]}";\n'
        f'import words{s["scene"]} from "../public/audio/{s["timestamps_file"]}";'
        for s in scenes)
    entries = ",\n".join(
        f'  {{Visual: Scene{s["scene"]}, audioFile: {json.dumps("audio/" + s["audio_file"])}, words: words{s["scene"]}.words}}'
        for s in scenes)
    return dedent(f'''\
        import React from "react";
        import {{Composition}} from "remotion";
        import {{VIDEO_CONFIG}} from "./config";
        import timelineData from "./timeline-data.json";
        import {{Timeline, TimelineSlice, ScenePreview, SceneEntry, TimelineData}} from "./Timeline";
        {imports}
        const data: TimelineData = timelineData;
        const entries: SceneEntry[] = [
        {entries}
        ];
        const Full: React.FC = () => <Timeline data={{data}} entries={{entries}} />;
        const SafeArea: React.FC = () => <Timeline data={{data}} entries={{entries}} showSafeArea />;
        const previews = data.scenes.map((_, index) => {{
          const Preview: React.FC = () => <ScenePreview data={{data}} entries={{entries}} index={{index}} />;
          return Preview;
        }});
        const boundaries = data.boundaries.map(boundary => {{
          const Preview: React.FC = () => <TimelineSlice data={{data}} entries={{entries}} start={{boundary.previewStart}} />;
          return Preview;
        }});
        export const Root: React.FC = () => <>
          <Composition id="VideoFull" component={{Full}} durationInFrames={{data.totalFrames}} {{...VIDEO_CONFIG}} />
          <Composition id="SafeAreaReview" component={{SafeArea}} durationInFrames={{data.totalFrames}} {{...VIDEO_CONFIG}} />
          {{data.scenes.map((scene, index) => <Composition key={{scene.scene}} id={{`Scene${{scene.scene}}`}}
            component={{previews[index]}}
            durationInFrames={{scene.spanFrames}} {{...VIDEO_CONFIG}} />)}}
          {{data.boundaries.map((boundary, index) => <Composition key={{boundary.afterScene}} id={{`Boundary${{boundary.afterScene}}`}}
            component={{boundaries[index]}}
            durationInFrames={{boundary.previewFrames}} {{...VIDEO_CONFIG}} />)}}
        </>;
    ''')


# ---------------------------------------------------------------------------
# Gitignore helper
# ---------------------------------------------------------------------------

def update_gitignore(project_dir: Path) -> None:
    """Keep generated caches ignored without modifying an unrelated ancestor."""
    gi = project_dir / ".gitignore"
    existing = gi.read_text() if gi.exists() else ""
    missing = [rule for rule in ("node_modules/", "out/") if rule not in existing.splitlines()]
    if missing:
        gi.write_text(existing.rstrip() + "\n" + "\n".join(missing) + "\n")


def resolve_scenes(storyboard: list[dict], metadata: dict | None, fps: int) -> list[dict]:
    """Join creative scene IDs with measured audio, leaving visual prose unconstrained."""
    if not isinstance(storyboard, list) or not storyboard:
        raise ValueError("Storyboard must be a non-empty array")
    for i, scene in enumerate(storyboard, 1):
        if not isinstance(scene, dict) or type(scene.get("scene")) is not int or scene["scene"] != i:
            raise ValueError("Scenes must be consecutive integers starting at 1")
    if metadata is None:
        validate_storyboard(storyboard, fps)
        return storyboard
    audio_scenes = metadata.get("scenes") if isinstance(metadata, dict) else None
    if not isinstance(audio_scenes, list) or len(audio_scenes) != len(storyboard):
        raise ValueError("Audio metadata must match storyboard scene count")
    resolved = []
    for scene, audio in zip(storyboard, audio_scenes):
        if (not isinstance(audio, dict) or type(audio.get("scene")) is not int
                or audio["scene"] != scene["scene"]):
            raise ValueError("Audio metadata scene IDs must match storyboard order")
        duration = audio.get("duration_s")
        filename = audio.get("file")
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
            raise ValueError("Audio duration_s must be finite and positive")
        if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.wav", filename):
            raise ValueError("Audio file must be a simple WAV filename")
        resolved.append({
            "scene": scene["scene"],
            "title": scene.get("title", f"Scene {scene['scene']}"),
            "duration_s": duration,
            "duration_frames": math.ceil(duration * fps),
            "audio_file": filename,
            "timestamps_file": audio.get("timestamps_file", Path(filename).stem + "-timestamps.json"),
        })
    validate_storyboard(resolved, fps)
    return resolved


def validate_storyboard(scenes: list[dict], fps: int) -> None:
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Storyboard must be a non-empty array")
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {i} must be an object")
        if type(scene.get("scene")) is not int or scene["scene"] != i:
            raise ValueError("Scenes must be consecutive integers starting at 1")
        duration = scene.get("duration_s")
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Scene {i}: duration_s must be finite and positive")
        frames = scene.get("duration_frames")
        if type(frames) is not int or frames != math.ceil(duration * fps):
            raise ValueError(f"Scene {i}: duration_frames must equal ceil(duration_s * fps)")
        hold = scene.get("hold_frames", 0)
        if type(hold) is not int or not 0 <= hold < frames:
            raise ValueError(f"Scene {i}: hold_frames must be within scene duration")
        for key in ("audio_file", "timestamps_file"):
            value = scene.get(key, "")
            suffix = "wav" if key == "audio_file" else "json"
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\." + suffix, value):
                raise ValueError(f"Scene {i}: {key} must be a simple asset filename")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    default_width, default_height = (1920, 1080) if args.profile == "youtube-horizontal" else (1080, 1920)
    args.width = default_width if args.width is None else args.width
    args.height = default_height if args.height is None else args.height
    project_dir = Path(args.project_dir).expanduser().resolve()
    storyboard_path = Path(args.storyboard).expanduser().resolve()

    if not storyboard_path.exists():
        print(f"ERROR: storyboard.json not found: {storyboard_path}", file=sys.stderr)
        sys.exit(1)

    storyboard: list[dict] = json.loads(storyboard_path.read_text(encoding="utf-8"))
    if not storyboard:
        print("ERROR: storyboard.json is empty.", file=sys.stderr)
        sys.exit(1)

    if min(args.fps, args.width, args.height) <= 0 or args.width % 2 or args.height % 2:
        raise ValueError("fps must be positive; dimensions must be positive and even for H.264")
    if not re.fullmatch(r"4\.0\.\d+", args.remotion_version):
        raise ValueError("Use an exact stable Remotion 4.0.x version")
    metadata = json.loads(Path(args.audio_metadata).expanduser().read_text(encoding="utf-8")) if args.audio_metadata else None
    storyboard = resolve_scenes(storyboard, metadata, args.fps)
    state = check_production(project_dir, "implement", [scene["scene"] for scene in storyboard], args.production_state,
                             required=not args.legacy_workflow)
    if state and state["version"] == 1 and not args.legacy_workflow:
        raise ValueError("V1 production state requires explicit --legacy-workflow; new productions use v2")
    if state and state["version"] == 2:
        from workflow_v2 import read, validate_execution
        execution = validate_execution(project_dir, [scene["scene"] for scene in storyboard])
        if execution["fps"] != args.fps:
            raise ValueError("Scaffold fps differs from the approved execution plan")
        if metadata != read(project_dir / "public/audio/metadata.json"):
            raise ValueError("Use the approved public/audio/metadata.json for scaffolding")
        if json.loads(storyboard_path.read_text()) != read(project_dir / "storyboard.json"):
            raise ValueError("Use the approved project storyboard")
        if not args.edit_plan or json.loads(Path(args.edit_plan).read_text()) != read(project_dir / "edit-plan.json"):
            raise ValueError("Pass the approved project --edit-plan")
    marker = project_dir / "src" / "timeline-contract.json"
    existing_scenes = list((project_dir / "src" / "scenes").glob("Scene*.tsx"))
    visual_only = marker.exists() or not existing_scenes
    if marker.exists() and json.loads(marker.read_text()) != {"version": 1, "sceneContract": "visual-only"}:
        raise ValueError("Unknown timeline contract; migrate explicitly before refresh")
    if args.edit_plan and not visual_only:
        raise ValueError("Existing scenes own audio/captions. Extract visual-only scenes and migrate explicitly before using --edit-plan")
    plan = json.loads(Path(args.edit_plan).expanduser().read_text()) if args.edit_plan else None
    # Preserve the previous edit decisions on structural refresh unless replaced explicitly.
    saved_plan = project_dir / "src" / "edit-plan.json"
    if visual_only and plan is None and saved_plan.exists():
        plan = json.loads(saved_plan.read_text())
    safe = {"top": .08, "right": .08, "bottom": .12, "left": .08} if args.width > args.height else {"top": .08, "right": .12, "bottom": .18, "left": .08}
    if plan is None:
        plan = {"version": 1, "safeArea": safe}
    elif isinstance(plan, dict) and "safeArea" not in plan:
        plan = {**plan, "safeArea": safe}
    timeline = compile_timeline(storyboard, args.fps, plan) if visual_only else None
    if timeline:
        for cue in timeline["audio"]:
            if not (project_dir / "public" / cue["src"]).is_file():
                raise ValueError(f"Missing selected audio asset: public/{cue['src']}")
    generated = ["package.json", "tsconfig.json", "src/config.ts", "src/index.ts", "src/Root.tsx"]
    if state:
        generated += ["scripts/production-export.cjs", "scripts/production/export-config.json"]
    if visual_only:
        generated += ["src/timeline-data.json", "src/timeline-contract.json", "src/edit-plan.json"]
    conflicts = [name for name in generated if (project_dir / name).exists()]
    if conflicts and not args.refresh_generated:
        raise ValueError(f"Refusing to overwrite {conflicts}; inspect first, then use --refresh-generated if intended")

    total_frames = timeline["totalFrames"] if timeline else sum(s["duration_frames"] for s in storyboard)
    print(f"Scaffolding Remotion project at: {project_dir}")
    print(f"  {len(storyboard)} scene(s), {total_frames} total frames @ {args.fps} fps")

    # Create directory tree
    (project_dir / "src" / "scenes").mkdir(parents=True, exist_ok=True)
    (project_dir / "public" / "audio").mkdir(parents=True, exist_ok=True)
    (project_dir / "out" / "scenes").mkdir(parents=True, exist_ok=True)

    # Write generated files (always overwrite)
    def write(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        print(f"  Wrote: {path.relative_to(project_dir)}")

    write(project_dir / "package.json", make_package_json(args.remotion_version, total_frames, guarded=state is not None))
    if state:
        guards = project_dir / "scripts/production"
        guards.mkdir(parents=True, exist_ok=True)
        for name in ("09_check_production.py", "production.py", "workflow_v2.py"):
            write(guards / name, (Path(__file__).parent / name).read_text())
        write(project_dir / "scripts/production-export.cjs", (Path(__file__).parent.parent / "assets/production-export.cjs").read_text())
        state_path = str(Path(args.production_state).expanduser().resolve()) if args.production_state else str(project_dir / "production-state.json")
        write(guards / "export-config.json", json.dumps({"python": sys.executable, "state": state_path, "lastFrame": total_frames - 1}))
    write(project_dir / "tsconfig.json", make_tsconfig())
    config = make_config_ts(args.fps, args.width, args.height, storyboard)
    if timeline:
        config = 'import timeline from "./timeline-data.json";\n' + config.replace(
            "SCENES.reduce((sum, s) => sum + s.durationFrames, 0)", "timeline.totalFrames")
        write(project_dir / "src" / "timeline-data.json", json.dumps(timeline, indent=2))
        write(marker, json.dumps({"version": 1, "sceneContract": "visual-only"}, indent=2))
        write(saved_plan, json.dumps(plan, indent=2))
        helper = project_dir / "src" / "Timeline.tsx"
        if not helper.exists():
            write(helper, (Path(__file__).parent.parent / "assets" / "Timeline.tsx").read_text())
    write(project_dir / "src" / "config.ts", config)
    write(project_dir / "src" / "index.ts", make_index_ts())
    write(project_dir / "src" / "Root.tsx", make_visual_root(storyboard) if visual_only else make_root_tsx(storyboard))

    # Write scene stubs — only for files that do not yet exist
    for scene in storyboard:
        n = scene["scene"]
        scene_path = project_dir / "src" / "scenes" / f"Scene{n}.tsx"
        if scene_path.exists():
            print(f"  Skipped (already exists): src/scenes/Scene{n}.tsx")
        else:
            write(scene_path, make_scene_stub(scene, visual_only=visual_only))

    caption_path = project_dir / "src" / "WordCaptions.tsx"
    if not caption_path.exists():
        write(caption_path, (Path(__file__).parent.parent / "assets" / "WordCaptions.tsx").read_text())

    if args.visual_style == "whiteboard":
        visuals = project_dir / "src" / "visuals"
        visuals.mkdir(exist_ok=True)
        for name in ("Whiteboard.tsx", "DoodleAssets.tsx"):
            target = visuals / name
            if not target.exists():
                write(target, (Path(__file__).parent.parent / "assets" / name).read_text())

    # Update .gitignore
    update_gitignore(project_dir)

    # npm install
    if args.skip_install:
        print("Skipping npm install (--skip-install).")
    else:
        pkg_manager = "npm"
        print(f"\nRunning {pkg_manager} install in {project_dir}...")
        result = subprocess.run([pkg_manager, "install"], cwd=project_dir, check=False)
        if result.returncode != 0:
            print(f"ERROR: {pkg_manager} install failed with code {result.returncode}.", file=sys.stderr)
            sys.exit(result.returncode)
        print(f"{pkg_manager} install completed successfully.")

    print(f"\nScaffold complete. Project ready at: {project_dir}")
    print("Next step: implement SceneN.tsx from the approved playbook (or delegated direction), then review in Studio.")


def _which(cmd: str) -> bool:
    """Return True if `cmd` is on PATH."""
    import shutil
    return shutil.which(cmd) is not None


if __name__ == "__main__":
    main()
