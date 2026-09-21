# Video Production

Local narrated-video skill: directorial storyboards, original animation and motion graphics, optional local footage/images/sound effects, Kokoro speech, Whisper word timestamps, editable Remotion scenes, MP4, and exact final-frame PNG. Storyboards describe audience experience; optional scene-design.md handles project-specific execution choices.

Start with [SKILL.md](SKILL.md) for workflow and [the pipeline reference](references/video-production-pipeline.md) for executable commands and contracts. [Voice guidance](references/kokoro-voices.md) describes selection and compatibility.

Prerequisites: uv, Python 3.11+, current supported Node/npm, ffmpeg/ffprobe, and phonemizer requirements for the selected language. Create/reuse a dedicated environment with uv venv and execute Python with uv run as shown in the pipeline reference; JavaScript dependencies belong to the generated project.

New projects separate visual scenes from narration/captions, with fades/slides/wipes, explicit holds, and boundary previews. Existing complete-scene projects retain their renderer. See [transitions](references/transitions.md) for edit plans/migration, [engagement direction](references/engagement-direction.md) for promise-to-payoff storytelling, [platform composition](references/platform-composition.md) for horizontal/vertical staging, [audio direction](references/audio-direction.md) for mix/captions, and [creative review](references/creative-review.md) for review bundles and measured iteration.

From the target workspace:
```bash
bash .agents/skills/video-production/scripts/04_setup_assets.sh .
```
The compatible runtime models total roughly 354 MB and are shared under .video_production_assets/kokoro/. Setup repairs invalid cached model downloads; it does not supply creative media. User images, B-roll, videos, and sound effects elsewhere under .video_production_assets/ are optional creative resources. Original animation and motion graphics are available even with no media. Detailed generation and verification commands live in the pipeline reference.
