# Video Production

Local narrated-video skill: reviewed narration, measured scene audio/timestamps, voiceover-to-visual asset planning, approved execution playbooks, editable Remotion scenes, Studio feedback, MP4, and exact final-frame PNG. Storyboards describe audience experience; implementation-plan.md specifies execution. Original animation and code visuals remain available alongside supplied media.

For new work, follow [collaborative production](references/collaborative-production.md): transcript → audio → timestamps → narration approval; creative/asset planning → user asset handoff → refined-plan approval; one scene at a time → user Studio review → final master/export approval. Copy templates at the relevant stage. V2 production-state.json retains scoped approvals and file snapshots; execution-plan.json maps exact words to timed actions and acceptance criteria. Scaffold and generated npm exports enforce recorded prerequisites. Explicit --legacy-workflow supports existing v1/no-state projects or engineering fixtures, not bypassing new-production gates. Quality, rights and playback still require review.

Start with [SKILL.md](SKILL.md) for workflow and [the pipeline reference](references/video-production-pipeline.md) for executable commands and contracts. [Voice guidance](references/kokoro-voices.md) describes selection and compatibility.

Optional [whiteboard production](references/whiteboard-production.md) adds original SVG doodles, draw-on animation, camera framing, and chart helpers through `--visual-style whiteboard`. [Long-form production](references/long-form-production.md) covers chapters and asset continuity; [data explainers](references/data-explainers.md) includes a tested illustrative calculation helper. Supplied voice recordings can enter the same pipeline through `06_import_narration.py`. These support production work; the starter art is not a finished professional illustration library.

Prerequisites: uv, Python 3.11+, current supported Node/npm, ffmpeg/ffprobe, and phonemizer requirements for the selected language. Create/reuse a dedicated environment with uv venv and execute Python with uv run as shown in the pipeline reference; JavaScript dependencies belong to the generated project.

New projects separate visual scenes from narration/captions, with fades/slides/wipes, explicit holds, and boundary previews. Existing complete-scene projects retain their renderer. See [transitions](references/transitions.md) for edit plans/migration, [engagement direction](references/engagement-direction.md) for promise-to-payoff storytelling, [platform composition](references/platform-composition.md) for horizontal/vertical staging, [audio direction](references/audio-direction.md) for mix/captions, and [creative review](references/creative-review.md) for review bundles and measured iteration.

From the target workspace:
```bash
bash .agents/skills/video-production/scripts/04_setup_assets.sh .
```
The compatible runtime models total roughly 354 MB and are shared under .video_production_assets/kokoro/. Setup repairs invalid cached model downloads; it does not supply creative media. User images, B-roll, videos, and sound effects elsewhere under .video_production_assets/ are optional creative resources. Original animation and motion graphics are available even with no media. Detailed generation and verification commands live in the pipeline reference.
