# Video production pipeline

## Paths and commands

SKILL means this skill directory; WORKSPACE is the explicit target repository/workspace; PROJECT is the user's selected video project. Run commands with real, quoted paths. Never infer WORKSPACE from the installation path of this skill.

Create a dedicated environment once (reuse it on later runs). In these examples replace SKILL, WORKSPACE, and PROJECT with actual paths; quote paths containing spaces.

For a new generated production, follow [collaborative production](collaborative-production.md): transcript -> scene audio -> checked timestamps -> narration-package approval -> creative/asset planning and asset-request handoff -> inspected assets and approved refined playbook -> one scene at a time with Studio approval -> master review and export approval. Copy the state/asset/playbook/execution templates from SKILL/assets only at their applicable stage, without overwriting authored files. Use PROJECT/assets for submitted files; selected files are staged into public/media. The commands below are pipeline steps, not permission to skip those reviews.

For supplied screen/talking-head footage, follow [recorded-video editing](recorded-video-editing.md) and [the recorded timeline contract](recorded-timeline-contract.md). Ingest with `12_ingest_recorded.py`, use v3 source/edit/plan reviews, and scaffold with `11_scaffold_recorded.py`. Both tracks use the dedicated uv environment and guarded final exports.

```bash
uv venv --python 3.11 WORKSPACE/.venv-video-production
uv pip install --python WORKSPACE/.venv-video-production/bin/python 'kokoro-onnx>=0.4.0' 'soundfile>=0.12.1' 'numpy>=1.26' 'openai-whisper>=20231117'
bash SKILL/scripts/04_setup_assets.sh WORKSPACE
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/01_tts.py --text PROJECT/transcript.txt --voice af_heart --assets-dir WORKSPACE/.video_production_assets --out-dir PROJECT/public/audio
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/02_timestamps.py --audio PROJECT/public/audio/scene-1.wav --model base --language en --model-dir WORKSPACE/.video_production_assets/whisper --out PROJECT/public/audio/scene-1-timestamps.json
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/03_scaffold.py --project-dir PROJECT --storyboard PROJECT/storyboard.json --audio-metadata PROJECT/public/audio/metadata.json --edit-plan PROJECT/edit-plan.json --design-system PROJECT/design-system.json --fps 30 --width 1080 --height 1920
```

Use the environment's Scripts/python.exe on Windows. Add .venv-video-production/ to workspace ignores. All Python execution, including tests and ad hoc checks, goes through `uv run` with this interpreter. The explicit `python SCRIPT` form uses the created venv instead of letting inline script metadata select a separate ephemeral environment. Inline dependency metadata remains available for standalone users. For scaffold-only work no ML dependencies are needed.

For horizontal YouTube use `--profile youtube-horizontal` without explicit dimensions; vertical is the default profile. Width/height flags override profile dimensions. New collaborative work passes approved edit and design-system files. Version-2 edit plans resolve transitions, holds and event-anchored sound; see [transition contracts](transitions.md) and [audio direction](audio-direction.md). Stage and register selected sound assets before scaffolding. Revisit frame-based edit choices whenever fps changes.

Add `--visual-style whiteboard` for the optional original vector/reveal/chart helpers in `src/visuals/`; see [whiteboard production](whiteboard-production.md). This copies helpers and preserves authored copies; it does not generate finished scenes or change aspect ratio. Multi-minute work uses [long-form production](long-form-production.md). Recorded speech can replace synthesis through `06_import_narration.py`; see [audio direction](audio-direction.md). Both sources feed the same measured WAV metadata contract.

Run timestamp extraction for every scene, sequentially. Whisper needs ffmpeg. Model downloads require network access once; cached synthesis/transcription run locally. Use workspace-local caches or normal environment escalation when required.

## Compatible Kokoro assets

The [kokoro-onnx upstream setup](https://github.com/thewh1teagle/kokoro-onnx) links the [model-files-v1.0 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0):
- kokoro-v1.0.onnx: 325532387 bytes.
- voices-v1.0.bin: 28214398 bytes; NumPy archive, not a single raw voice array.

Setup checks exact release sizes, downloads to a temporary sibling, fails on HTTP errors, and replaces a cached invalid file only after a successful complete download. Interrupted/failed transfers never become valid cache entries. Release sizes are truncation checks, not cryptographic verification; upstream publishes no digest for these assets. TTS verifies the voice archive and loads the model through ONNX Runtime. Do not substitute the onnx-community model/individual voices without checking runtime compatibility.

## Audio and timestamp contracts

transcript.txt uses a standalone --- line between scenes. Inline dashes are narration. Empty sections are skipped; wholly empty input fails.

01_tts.py writes scene-N.wav (24 kHz mono float WAV, peak normalized to -1 dBFS) and metadata.json:
```json
{"voice":"af_heart","lang":"en-us","generated_at":"ISO-8601 UTC","scenes":[{"scene":1,"file":"scene-1.wav","duration_s":4.23,"text":"Narration."}]}
```
Invalid assets, unavailable voice IDs, empty/silent/non-finite synthesis, or unexpected sample rates fail. Treat failed generation as incomplete; do not consume old metadata from an earlier run.

02_timestamps.py writes:
```json
{"scene":"scene-1","audio_file":"scene-1.wav","duration_s":4.23,"language":"en","words":[{"word":"Narration.","start":0.1,"end":0.9}]}
```
Times are seconds relative to the WAV, with four decimal places. Duration comes from the audio file, not the last recognized word. Clips under 0.5 seconds skip model loading and return empty words; longer speech yielding no words fails. --model-dir controls model cache location. Compare recognized words with the approved narration.

## Directorial storyboard and technical timing

A nonempty array with consecutive integer scene IDs starting at 1:
```json
[
  {
    "scene": 1,
    "title": "Attention has a direction",
    "direction": {
      "audience_sees": "A restless swarm of signals resolves into one purposeful movement.",
      "hook": "An apparently chaotic scene suddenly becomes easy to follow.",
      "value": "Motion can guide attention and reveal meaning.",
      "visual_approach": "Expressive object animation with a tactile, spacious atmosphere; let the transformation carry the explanation.",
      "background": "An environment that feels busy at first, then recedes as the important action becomes clear.",
      "sound": "If a suitable local effect exists, use a restrained accent at the reveal; otherwise let narration carry it.",
      "assets": [],
      "progression": "Move from distraction to focus, then leave time for the insight to register."
    }
  }
]
```

Only scene IDs are mechanical identifiers. Direction fields are prompts for useful decisions, not a closed vocabulary: combine or extend them as the story needs. Describe the intended audience experience; do not prescribe JSX trees, coordinates, font sizes, layout IDs, or per-element keyframes. Do not force every scene into hook/body/CTA or every video into this example's aesthetic. Narration lives in transcript.txt and audio metadata.

When media is selected, assets entries identify an actual workspace-relative source path, its narrative purpose, and intended usage in plain language (for example, how a B-roll action relates to the explanation). Empty assets means an intentional original-visual treatment, not an incomplete scene. Background and sound direction can describe absence or restraint. Never list nonexistent files as selected assets.

Pass --audio-metadata to join TTS metadata with storyboard scene IDs. The scaffold requires matching scene counts/IDs and derives duration_frames = ceil(duration_s * fps), audio_file from metadata's file, and timestamps_file from that filename's stem plus -timestamps.json. An optional timestamps_file in an audio metadata scene supports custom filenames. It does not parse or render directorial prose. Existing combined technical storyboards still work without --audio-metadata for compatibility.

Master timing belongs in metadata/edit plans/generated config. In collaborative production, asset-plan.md maps spoken lines to beats, BG/midground/foreground assets, prompts, exact filenames, and meaningful visual actions. After asset review, implementation-plan.md settles shot beats, design system, framing, crops/trims, speech-local frame actions, caption placement, sound, file/component steps, and review checkpoints. Consolidate or reference an existing scene-design.md; keep one execution authority. Autonomous tests may use a compact plan. In-content visual holds do not extend audio duration. Explicit edit-plan holds append frames after narration and shift later starts. Legacy hold_frames stays within duration_frames and does not extend the master. Useful optional direction fields are viewer_question, new_understanding, payoff, and continuity_to_next; see [engagement direction](engagement-direction.md).

## Creative media and motion

Inventory images, B-roll, video, and sound effects recursively under WORKSPACE/.video_production_assets. Exclude runtime models under kokoro/ and whisper/. For reusable libraries, follow [asset-library.md](asset-library.md): `library.json` retains IDs, provenance, rights and creative notes, while `07_index_assets.py` generates a non-destructive technical report. Before storyboard preparation, use `08_search_assets.py` with terms from the topic and planned visual beats; it reads the curated JSON rather than guessing from filenames. Inspect shortlisted files and rights before selecting them. No matching or cleared file is a valid result: retain the planned scope and use original code visuals or newly authorized media instead. Check images visually; use ffprobe for clip dimensions, duration, frame rate, and audio streams, then inspect representative frames or playback. Select assets based on narrative fit. Existing source assets stay intact; copy only chosen media to PROJECT/public/media and record their source and role in the storyboard or scene-design.md.

Also inspect PROJECT/assets submissions and record their exact names, generation prompts/provenance or source/licensing evidence, actual properties, acceptance, and public/media destinations in asset-plan.md. Search an existing library when available; its absence does not block planning. Requests may name files before they exist, but selected storyboard asset references must identify real inspected files. Resolve missing required assets through user-approved alternatives, omission, or redesign (unless delegated), updating transitions and the execution plan. Original code visuals require no external file.

Compose each scene around its action or insight. Without supplied media, use original SVG/React illustration, diagrams that transform, particles, procedural environments, object/character motion, simulated interactions, and camera-like staging as appropriate. With media, consider live-action footage with tracked-looking callouts, image parallax, collage, masks, or graphic overlays. These are examples, not required ingredients. Do not use repetitive text cards as the fallback for an empty asset folder. Asset availability does not gate animation or motion graphics.

Use Remotion local-media primitives with staticFile paths, frame-driven transforms, and scene-local sequences. Verify APIs against the installed version when implementing footage trims or advanced effects. Define deliberate crops, trim ranges, and playback speeds; ensure source duration covers the shot, and loop only when intentional. Mute embedded clip audio unless selected for the mix. Cue effects to meaningful actions, fade edges where needed, and balance the mix under narration without clipping. If no suitable sound effect exists, omit it or deliberately synthesize one within available capabilities; do not reference a missing file. External asset acquisition or generation uses available tools within the user's authorization.

## Scaffold and captions

03_scaffold.py pins Remotion, @remotion/cli, and @remotion/media to the same published version (currently 4.0.526), React 18.3.1, TypeScript 5.4.5. Package publication has been verified; generated-project compatibility must still be checked by typechecking and rendering. --remotion-version accepts another exact 4.0.x version; verify compatibility before changing. npm install creates a lockfile. --skip-install supports offline structural tests.

Generated files: package.json, tsconfig.json, src/config.ts, src/index.ts, src/Root.tsx, src/WordCaptions.tsx, and scene components. New visual-only projects also get src/timeline-contract.json, src/edit-plan.json, src/timeline-data.json, src/design-tokens.ts, and src/Timeline.tsx. Assets in public/audio must exist before typechecking. The storyboard's filenames are honored. The compiled timeline is the single authority for starts, spans, sound anchors, overlaps, review slices and total length. `src/design-tokens.ts` is derived from approved `design-system.json`; do not edit it as a second authority.

The default refuses to overwrite structural files; --refresh-generated explicitly replaces them. Existing scenes, WordCaptions.tsx, and Timeline.tsx are preserved and may need manual updates. Saved src/edit-plan.json choices are reused unless --edit-plan supplies a replacement. The script only adds node_modules/ and out/ ignores inside PROJECT; the caller manages workspace model ignores.

03_scaffold.py requires version-2 production-state.json (or --production-state PATH), narration/plan approvals, asset readiness, accepted asset manifest, approved design system and a valid execution plan matching the approved inputs/fps. Run 09_check_production.py with --stage plan, implement, scene --scene N, or render at the respective gate. Use --snapshot narration|plan|scene:N|video to retain the reviewed input digest. Snapshot changes invalidate approvals; quality/rights review remains manual. See [collaborative production](collaborative-production.md).

The local WordCaptions groups phrases using punctuation, pauses, word count, and a width-based character budget. It supports optional word highlighting and safe-area fractions, and hides captions in gaps. The heuristic is not font measurement; inspect actual text bounds. Existing projects preserve their authored caption component. See [Remotion caption utilities](https://www.remotion.dev/docs/captions/) for advanced layouts; do not import a nonexistent Captions component.

Visual-only scenes receive contentFrame, rawContentFrame, durationFrames, fps, width, and height. contentFrame clamps at content endpoints during handles/holds; rawContentFrame allows authored pre/post action. The master mounts @remotion/media Audio and captions once per narration segment, independent of visual overlap. Captions receive speech-local time = frame / fps. Sound cues have separate gain/fade/duck envelopes; see [audio direction](audio-direction.md). No CSS transitions or wall-clock animation. JSON imports use resolveJsonModule; no @ts-expect-error is needed.

## Rendering and checks

During collaborative implementation, typecheck the active scene and ask the user to run `npm run studio` from PROJECT. Provide isolated SceneN and master-context SceneNReview frame checkpoints, record feedback, and wait for approval before the next scene. Start Studio yourself only if requested. Obtain final master/export approval before video/still exports. Record all feedback and approval history in production-state.json. Scripts never infer that a successful render means approval. The following export commands apply after the relevant approval or explicit delegation.

From PROJECT:
```bash
npm run typecheck
npx remotion render src/index.ts Scene1 out/scenes/scene-1-preview.mp4 --codec=h264 --pixel-format=yuv420p
npm run render
npm run hero
ffprobe -v error -show_streams -show_format -of json out/video.mp4
```
Repeat preview rendering for each SceneN, SceneNReview and BoundaryN composition. VideoFull uses the compiled timeline. SafeAreaReview adds inset guides. BoundaryN and SceneNReview slice the actual master including its mix; SceneN isolates speech/visuals without global music/effects.

Render the deliverable from VideoFull, not by concatenating isolated SceneN files. Scene files are separate exports; they lack master overlap and global mix. State-bearing scaffold projects have guarded npm render/hero commands, bundling the Python checker locally and invoking it through uv before Remotion. Missing state blocks these exports. Direct Remotion CLI or Studio export buttons are not intercepted and must not be used to bypass pending review.

TOTAL_FRAMES = sum(contentFrames + explicit hold frames); visual overlap does not shorten speech or the total. LAST_FRAME = TOTAL_FRAMES - 1. Regenerate timing/config/hero commands after edit changes. Compare output duration to TOTAL_FRAMES / fps, allowing container/audio encoder rounding. Narration quantization adds less than one frame per scene; explicit holds are additional intentional duration.

Inspect opening, dense middle, transitions, and last decoded video frame; compare hero content with the latter allowing H.264 compression differences. Check audio presence and nonzero samples, caption alignment, readability, contrast, safe areas, asset loading, and final settled takeaway. Report still inspection separately from playback listening.

## Regression tests

Prepare a review bundle with `uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/05_review_bundle.py --project-dir PROJECT`. It writes commands and a pending-review report, preserving prior reports as review-previous-N.md. Add `--render` to require current recorded export readiness, then execute scene/boundary/full renders and stills, make a contact sheet, and capture ffprobe metadata. --production-state PATH selects explicit state. The manifest records completion or partial failure, never claiming listening or creative review occurred. The helper never modifies production-state.json. See [creative review](creative-review.md) for editorial checks and optional analytics-based iteration. Honor any requested pause before testing/rendering.

Run from the workspace:
```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_pipeline.py
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_extensions.py
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_production.py
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_workflow_v2.py
```
Tests use temporary directories and mock external synthesis/transcription where appropriate. A real integration smoke test should additionally run download, TTS, timestamps, npm install/typecheck, and a small MP4/hero render under the requested test folder. Unit tests alone do not establish end-to-end media quality.

For the optional TypeScript integration test in `test_extensions.py`, set `VIDEO_PRODUCTION_NODE_MODULES` to an existing generated project's absolute `node_modules` path. It checks a single-scene whiteboard project with empty transition/caption arrays using those installed dependencies; without that variable the check is reported skipped. The other extension tests run actual ffmpeg recording conversion and validate calculation identities.
