---
name: video-production
description: Produce or revise narrated Remotion videos for horizontal YouTube and vertical short-form, including long-form explainers and illustrated whiteboard videos, with original motion graphics, local or recorded narration, captions, review previews, MP4, and a final-frame PNG.
---

# Video Production

Deliver an editable Remotion project, narrated MP4, and hero PNG from the exact last composition frame. Preserve the source's message, evidence, qualifications, and voice. Speech synthesis and transcription run locally after dependency/model downloads.

## Scope and review

Honor the user's requested folder, duration, aspect ratio, and existing approvals. Default to 20–45 seconds, 4–8 scenes, 30 fps, vertical 1080 × 1920 if unspecified. Estimate narration at about 2.5 words/second; use measured audio durations for production.

For multi-minute explainers or a reference with a sustained argument, read [long-form production](references/long-form-production.md). The short defaults are not limits. Plan chapters and visual beats, maintain recurring identities and a shared asset inventory, and validate a representative sequence before scaling production. For reference matching, distinguish inspected frames/captions from actual motion and listening review; never infer production methods or sound quality from stills.

Read [engagement direction](references/engagement-direction.md) before scripting: define the audience's situation, opening promise, intermediate discoveries, and final takeaway. Use the principles as editorial guidance, not guaranteed psychology or retention outcomes. For platform/aspect-ratio choices or adaptations, read [platform composition](references/platform-composition.md). Horizontal YouTube needs deliberate spatial staging and pacing; vertical versions need their own readable composition. Re-stage rather than merely crop.

For a new creative project, present the full transcript and a compact proposed visual direction together for review before synthesis. If the user delegates choices or requests an autonomous test, choose reasonable defaults and proceed. Do not repeat approvals already given. Render all scene previews before asking for review as a batch; offer individual review if requested. A separate storyboard-JSON approval is unnecessary when it implements an approved direction. Publishing or uploading requires separate authorization.

For debugging or improving this skill, reproduce the failure, repair the relevant scripts/instructions, and validate with isolated fixtures and a real smoke test when feasible. Do not apply creative approval gates to engineering tests. Preserve existing authored work.

## Preflight and assets

Read [the pipeline reference](references/video-production-pipeline.md) before running scripts or writing scene code. Resolve script paths relative to this skill, never the caller's working directory. Check uv, Node/npm, ffmpeg/ffprobe, and the selected phonemizer's system requirements. Use lean-coder if available for implementation, but the pipeline must not depend on a separately installed skill.

Choose the workspace root explicitly: nearest containing Git root (including worktree .git files), otherwise the user-designated workspace. A globally installed skill's directory is not the target workspace. Create or reuse a dedicated environment with `uv venv`; run every Python script with `uv run` using that environment as described in the pipeline reference. Do not use system Python or bare pip.

Inventory creative media under WORKSPACE/.video_production_assets: images, B-roll, videos, and sound effects. Inspect relevant images, sample footage, and check media durations before selecting them. Existing kokoro/ and whisper/ subdirectories are runtime model caches, not creative media. Keep them separate from the creative inventory. Missing media never limits the work to text slides: create original animation, motion graphics, diagrams, illustrated action, or spatial visual metaphors in code. Use media when it strengthens the explanation, not to fill an asset quota.

When using Kokoro, run scripts/04_setup_assets.sh with that workspace root if its models are absent or invalid; it does not download creative media. Supplied narration needs no Kokoro setup. Run authorized setup directly; request environment escalation only if necessary. Downloads are roughly 354 MB total. The compatible model and bundled voice archive come from the kokoro-onnx release, not the onnx-community Transformers/JS layout. A successful exit or file existence alone is not evidence of valid model contents.

Add .video_production_assets/, node_modules/, and output/cache paths to the appropriate .gitignore, preserving existing rules. Keep project source editable and versionable; do not ignore the entire project by default.

## Narration and timestamps

Write the approved/delegated narration to PROJECT/transcript.txt, separating scenes with a line containing only ---.
For supplied recordings, use `scripts/06_import_narration.py` as described in [audio direction](references/audio-direction.md), then use the same timestamp and scaffold pipeline. Imported recordings do not require Kokoro models. Audition the chosen voice before generating a long script.
Read [audio direction](references/audio-direction.md) for phrasing, scene-to-scene cadence, optional mixing, and readable captions. Use supported voice controls and audition joins; do not invent speech-engine capabilities.
Use scripts/01_tts.py with --assets-dir WORKSPACE/.video_production_assets and --out-dir PROJECT/public/audio. Default voice: af_heart; see [voice guidance](references/kokoro-voices.md). Confirm every WAV is nonempty, finite, nonsilent, and matches metadata. Report measured scene durations.

Run scripts/02_timestamps.py sequentially for each WAV with --model base, --language en for English narration, and --model-dir WORKSPACE/.video_production_assets/whisper. Check words against the approved transcript; recognition is not forced alignment. Inspect and correct mistranscriptions without inventing timing. Short clips under 0.5 seconds produce an empty words array; empty captions for longer narration require investigation.

## Visual direction and composition

Choose a visual language for this audience, topic, and emotional arc. Possibilities include documentary footage with graphic interventions, illustrated storytelling, simulations, tactile collage, character/object animation, cinematic environments, and kinetic typography. These are possibilities, not a menu or mandatory formula. Motion graphics and original animation remain available with or without supplied media. Avoid inheriting the previous project's palette, card layout, pacing, or vibe by habit. Establish coherent art direction while varying shot scale, staging, and rhythm where the story benefits. Use a meaningful first frame and a settled final takeaway. Keep the explanation understandable muted.

For doodle/whiteboard direction, read [whiteboard production](references/whiteboard-production.md). Scaffold with `--visual-style whiteboard` to copy an original SVG starter kit and reveal/camera/chart helpers. This is independent of aspect ratio; it supplies building blocks, not finished illustration or automatic storyboard rendering. For numerical comparisons, read [data explainers](references/data-explainers.md); generate chart values from explicit assumptions and tested calculations rather than hand-entering animated totals.

For a publishable project, consult current primary platform guidance and relevant examples where useful. Distinguish observed popularity from measured retention; do not promise virality. A functional smoke test needs no trend research.

Write PROJECT/storyboard.json as a scene-wise directorial brief using the pipeline reference. Describe what the audience sees and understands, the hook, payoff, visual atmosphere and action, background treatment, sound intent, and purposeful media usage. Do not specify element trees, coordinates, font sizes, fixed layouts, or animation keyframes here. Write enough to inspire execution without dictating its construction. Asset references are optional and must identify real inspected files when selected; explicitly allow original code visuals when no media fits.

After the storyboard, optionally write PROJECT/scene-design.md for execution decisions that improve quality: composition, typography, palette, visual hierarchy, shot timing, masks, camera paths, media trims, sound levels, and caption safe areas. This is a revisable project-specific design pass, not a universal scene template or a second approval gate. Simple scenes can go straight to code. Keep mechanical timing in audio metadata/edit plans/generated config, separate from directorial intent. Narration uses ceil(duration_s * fps). Explicit edit-plan holds extend scene spans; the compiled timeline determines TOTAL_FRAMES and final PNG frame TOTAL_FRAMES - 1.

Read [transitions](references/transitions.md) before composing scene joins. Choose transitions by the relationship between ideas: cuts, fades, directional slides, masks, or authored shared-object/camera continuity. Favor a coherent vocabulary over an effect quota. New projects separate visual scenes from narration/captions; visual overlap must not overlap voices or advance captions. An optional version-1 edit plan controls joins, holds, safe areas, and sound cues. Missing transition entries mean cuts, not a requirement to animate every boundary.

Run scripts/03_scaffold.py with the storyboard and --audio-metadata PROJECT/public/audio/metadata.json; choose --profile youtube-horizontal or vertical and optionally --edit-plan PROJECT/edit-plan.json. Author src/scenes/SceneN.tsx to realize the direction; replace placeholders before delivery. The scaffold does not translate creative prose into a fixed layout. Existing structural files cause a safe refusal; inspect before using --refresh-generated. It preserves authored scenes, caption and timeline helpers. Existing complete-scene projects retain their renderer; migrating them to visual-only scenes is explicit. Legacy storyboards remain readable; do not reuse their element schema for new work.

Stage selected media in PROJECT/public/media with traceable source paths. Combine footage or imagery with animation where useful; choose crops and motion around the subject, and avoid stretching or unintentional looping. Mute source-video audio unless deliberately used. Place sound effects on meaningful actions, control peaks, and keep narration intelligible. Silence is a valid creative decision. Never claim generated graphics are real footage or invent assets that are not available. See the pipeline reference for media implementation and review guidance.

Use frame-driven animation, deterministic randomness, and local assets. In new visual-only scenes, use contentFrame for normal action and rawContentFrame for deliberate transition handles; the master owns narration and captions on the speech clock. The included WordCaptions groups phrases by punctuation, pauses, and a width heuristic with optional word highlighting; inspect real font bounds. @remotion/captions contains utilities, not a ready-made Captions React component. Other caption styles require implementation and preview verification. Do not suppress TypeScript errors to make templates appear valid.

## Verification and delivery

Read [creative review](references/creative-review.md). Run npm run typecheck, render scene and boundary previews, and inspect opening, dense, and final frames for readability, clipping, missing elements, and caption timing. Boundary previews use the actual master mix and visual overlap; isolated scenes cannot establish smooth joins. Check whether visuals demonstrate the idea, each beat adds understanding, and the payoff fulfills the hook. Check media crops, sound alignment, safe areas, and voice clarity. Review muted, audio-only, and combined playback when available; metadata/stills alone do not prove audible or synchronized playback. Apply revisions and rerender affected scenes and boundaries. scripts/05_review_bundle.py prepares commands/report; --render executes them. Honor a user's requested pause before testing or rendering.

Render the full composition and exact final-frame PNG. Check audio/video streams, dimensions, fps, duration, and the final frame using ffprobe and decoded frames. Compare with compiled TOTAL_FRAMES / fps, including explicit holds; narration quantization contributes less than one frame per scene beyond summed WAV duration. Check each narration mounts once and survives visual transitions intact. When authorized analytics are available, map observations to master beats and propose controlled revisions; otherwise report editorial hypotheses, not measured retention gains.

Deliver links to MP4, PNG, editable project, dimensions/fps/duration, style/voice/captions, and verification results. Clearly distinguish a technical smoke test from a finished creative video. State any remaining blockers without claiming incomplete checks passed.
