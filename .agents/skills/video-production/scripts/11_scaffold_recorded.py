#!/usr/bin/env python3
"""Scaffold a guarded Remotion project for an approved recorded-edit v3 plan."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from production import check_production
from recorded_timeline import compile_project


def package(version):
    return {"name": "recorded-video-edit", "version": "1.0.0", "private": True,
            "scripts": {"studio": "npx remotion studio src/index.ts", "typecheck": "tsc --noEmit",
                        "render": "node scripts/production-export.cjs render",
                        "hero": "node scripts/production-export.cjs hero"},
            "dependencies": {"remotion": version, "@remotion/media": version, "@remotion/cli": version,
                             "react": "18.3.1", "react-dom": "18.3.1"},
            "devDependencies": {"typescript": "5.4.5", "@types/react": "18.3.1"}}


def root_tsx():
    return dedent('''\
        import React from "react";
        import {Composition} from "remotion";
        import dataJson from "./timeline-data.json";
        import {RecordedTimeline, RecordedTimelineData} from "./RecordedTimeline";
        const data: RecordedTimelineData = dataJson as unknown as RecordedTimelineData;
        const Full: React.FC = () => <RecordedTimeline data={data} />;
        const Safe: React.FC = () => <RecordedTimeline data={data} showSafeArea />;
        const reviews = data.scenes.map(scene => {
          const Review: React.FC = () => <RecordedTimeline data={data} masterStart={scene.startFrame} />;
          return Review;
        });
        export const Root: React.FC = () => <>
          <Composition id="VideoFull" component={Full} durationInFrames={data.totalFrames}
            fps={data.fps} width={data.width} height={data.height} />
          <Composition id="SafeAreaReview" component={Safe} durationInFrames={data.totalFrames}
            fps={data.fps} width={data.width} height={data.height} />
          {data.scenes.map((scene, index) => <Composition key={scene.id} id={`Scene${scene.scene}Review`}
            component={reviews[index]} durationInFrames={scene.durationFrames}
            fps={data.fps} width={data.width} height={data.height} />)}
        </>;
    ''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--production-state")
    parser.add_argument("--remotion-version", default="4.0.526")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--refresh-generated", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"4\.0\.\d+", args.remotion_version):
        raise ValueError("Use an exact stable Remotion 4.0.x version")
    project = Path(args.project_dir).expanduser().resolve()
    check_production(project, "implement", state_path=args.production_state)
    timeline = compile_project(project)
    generated = ["package.json", "tsconfig.json", "src/index.ts", "src/Root.tsx",
                 "src/RecordedTimeline.tsx", "src/WordCaptions.tsx", "src/timeline-data.json",
                 "src/timeline-contract.json", "scripts/production-export.cjs"]
    conflicts = [name for name in generated if (project / name).exists()]
    if conflicts and not args.refresh_generated:
        raise ValueError(f"Refusing to overwrite {conflicts}; inspect first, then use --refresh-generated")
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "scripts/production").mkdir(parents=True, exist_ok=True)
    (project / "out").mkdir(exist_ok=True)
    assets = Path(__file__).parent.parent / "assets"
    def write(relative, content):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    write("package.json", json.dumps(package(args.remotion_version), indent=2) + "\n")
    write("tsconfig.json", json.dumps({"compilerOptions": {"target": "ES2020", "module": "ESNext",
        "moduleResolution": "bundler", "jsx": "react", "strict": True, "skipLibCheck": True,
        "resolveJsonModule": True, "esModuleInterop": True}, "include": ["src"]}, indent=2) + "\n")
    write("src/index.ts", 'import {registerRoot} from "remotion";\nimport {Root} from "./Root";\nregisterRoot(Root);\n')
    write("src/Root.tsx", root_tsx())
    write("src/RecordedTimeline.tsx", (assets / "recorded/RecordedTimeline.tsx").read_text())
    write("src/WordCaptions.tsx", (assets / "WordCaptions.tsx").read_text())
    design = json.loads((project / "design-system.json").read_text())
    write("src/design-tokens.ts", "export const DESIGN_TOKENS = " + json.dumps(design, indent=2) + " as const;\n")
    write("src/timeline-data.json", json.dumps(timeline, indent=2) + "\n")
    write("src/timeline-contract.json", json.dumps({"version": 3, "track": "recorded-edit"}, indent=2) + "\n")
    write("scripts/production-export.cjs", (assets / "production-export.cjs").read_text())
    state_value = str(Path(args.production_state).expanduser().resolve()) if args.production_state else "production-state.json"
    write("scripts/production/export-config.json", json.dumps({"python": sys.executable, "state": state_value}, indent=2) + "\n")
    for name in ("09_check_production.py", "production.py", "workflow_v2.py", "recorded_contract.py",
                 "recorded_timeline.py", "recorded_workflow.py"):
        shutil.copy2(Path(__file__).parent / name, project / "scripts/production" / name)
    ignore = project / ".gitignore"
    lines = ignore.read_text().splitlines() if ignore.is_file() else []
    for rule in ("node_modules/", "out/", "cache/"):
        if rule not in lines: lines.append(rule)
    ignore.write_text("\n".join(lines) + "\n")
    if not args.skip_install:
        subprocess.run(["npm", "install"], cwd=project, check=True)
    print(f"Recorded project scaffolded: {len(timeline['clips'])} clips, {timeline['totalFrames']} frames")


if __name__ == "__main__":
    main()
