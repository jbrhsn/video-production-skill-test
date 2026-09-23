#!/usr/bin/env python3
"""Scaffold a Remotion project from the canonical editorial timeline."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from editorial_timeline import compile_timeline
from qc_timeline import check_timeline


def package(version):
    return {"name": "ai-native-video-production", "private": True, "version": "1.0.0",
            "scripts": {"studio": "npx remotion studio src/index.ts", "typecheck": "tsc --noEmit",
                        "render": "node scripts/production-export.cjs render", "hero": "node scripts/production-export.cjs hero"},
            "dependencies": {"remotion": version, "@remotion/media": version, "@remotion/cli": version,
                             "react": "18.3.1", "react-dom": "18.3.1"},
            "devDependencies": {"typescript": "5.4.5", "@types/react": "18.3.1"}}


def root_tsx():
    return dedent('''\
        import React from "react";
        import {Composition} from "remotion";
        import dataJson from "./timeline-data.json";
        import {EditorialTimeline, EditorialTimelineData} from "./EditorialTimeline";
        const data = dataJson as unknown as EditorialTimelineData;
        const fps = data.fps.num / data.fps.den;
        const Full: React.FC = () => <EditorialTimeline data={data} />;
        const Safe: React.FC = () => <EditorialTimeline data={data} showSafeArea />;
        export const Root: React.FC = () => <>
          <Composition id="VideoFull" component={Full} durationInFrames={data.totalFrames}
            fps={fps} width={data.width} height={data.height} />
          <Composition id="SafeAreaReview" component={Safe} durationInFrames={data.totalFrames}
            fps={fps} width={data.width} height={data.height} />
        </>;
    ''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--timeline", default="editorial/timeline.json")
    parser.add_argument("--sources", default="source/manifest.json")
    parser.add_argument("--resolved-style")
    parser.add_argument("--remotion-version", default="4.0.526")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--refresh-generated", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"4\.0\.\d+", args.remotion_version):
        raise ValueError("Use an exact stable Remotion 4.0.x version")
    project = Path(args.project_dir).expanduser().resolve()
    timeline = json.loads((project / args.timeline).read_text(encoding="utf-8"))
    sources = json.loads((project / args.sources).read_text(encoding="utf-8"))
    compiled = compile_timeline(timeline, sources)
    report = check_timeline(compiled)
    if report["status"] != "pass":
        raise ValueError("Timeline QC must pass before scaffolding")
    generated = ["package.json", "tsconfig.json", "src/index.ts", "src/Root.tsx", "src/EditorialTimeline.tsx",
                 "src/WordCaptions.tsx", "src/EditorialVisuals.tsx", "src/design-tokens.ts", "src/timeline-data.json", "scripts/production-export.cjs"]
    conflicts = [name for name in generated if (project / name).exists()]
    if conflicts and not args.refresh_generated:
        raise ValueError(f"Refusing to overwrite {conflicts}; inspect first, then use --refresh-generated")
    assets = Path(__file__).parent.parent / "assets"
    def write(relative, content):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    style = {"colors": {"background": "#101418"}, "captions": {"fontFamily": "Arial", "text": "#fff",
             "background": "#111", "active": "#ffe066", "radius": 6, "fontScale": .038, "bottomInset": .12}}
    if args.resolved_style:
        resolved = json.loads((project / args.resolved_style).read_text(encoding="utf-8"))
        style.update(resolved.get("values", {}).get("designTokens", {}))
    write("package.json", json.dumps(package(args.remotion_version), indent=2) + "\n")
    write("tsconfig.json", json.dumps({"compilerOptions": {"target": "ES2020", "module": "ESNext", "moduleResolution": "bundler",
        "jsx": "react", "strict": True, "skipLibCheck": True, "resolveJsonModule": True, "esModuleInterop": True}, "include": ["src"]}, indent=2) + "\n")
    write("src/index.ts", 'import {registerRoot} from "remotion";\nimport {Root} from "./Root";\nregisterRoot(Root);\n')
    write("src/Root.tsx", root_tsx())
    write("src/EditorialTimeline.tsx", (assets / "EditorialTimeline.tsx").read_text())
    write("src/EditorialVisuals.tsx", (assets / "EditorialVisuals.tsx").read_text())
    write("src/WordCaptions.tsx", (assets / "WordCaptions.tsx").read_text())
    write("src/design-tokens.ts", "export const DESIGN_TOKENS = " + json.dumps(style, indent=2) + " as const;\n")
    write("src/timeline-data.json", json.dumps(compiled, indent=2) + "\n")
    write("scripts/production-export.cjs", (assets / "production-export-v1.cjs").read_text())
    write("scripts/production/export-config.json", json.dumps({"python": sys.executable,
        "project": "project.json", "state": "production-state.json"}, indent=2) + "\n")
    shutil.copy2(Path(__file__).parent / "qc_timeline.py", project / "scripts/production/qc_timeline.py")
    shutil.copy2(Path(__file__).parent / "qc_production.py", project / "scripts/production/qc_production.py")
    shutil.copy2(Path(__file__).parent / "run_qc.py", project / "scripts/production/run_qc.py")
    shutil.copy2(Path(__file__).parent / "contracts.py", project / "scripts/production/contracts.py")
    shutil.copy2(Path(__file__).parent / "production_workflow.py", project / "scripts/production/production_workflow.py")
    shutil.copy2(Path(__file__).parent / "asset_library.py", project / "scripts/production/asset_library.py")
    shutil.copy2(Path(__file__).parent / "check_production_v1.py", project / "scripts/production/check_production_v1.py")
    for folder in ("out", "qc"):
        (project / folder).mkdir(exist_ok=True)
    ignore = project / ".gitignore"
    lines = ignore.read_text().splitlines() if ignore.is_file() else []
    for rule in ("node_modules/", "out/", "cache/"):
        if rule not in lines:
            lines.append(rule)
    ignore.write_text("\n".join(lines) + "\n")
    if not args.skip_install:
        subprocess.run(["npm", "install"], cwd=project, check=True)
    print(f"Production project scaffolded: {len(compiled['clips'])} clips, {compiled['totalFrames']} frames")


if __name__ == "__main__":
    main()
