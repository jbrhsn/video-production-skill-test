---
name: video-production
description: Produce or edit Remotion videos, including generated explainers and supplied screen recordings, talking-head footage, or synchronized combinations, with captions, review previews, MP4, and a final-frame PNG.
---

# Video Production

Deliver an editable Remotion project, MP4, and hero PNG from the exact last composition frame. Preserve the source's message, evidence, qualifications, voice, and supplied recordings. Speech synthesis and transcription run locally after dependency/model downloads.

## Choose the production track

- For a video created from a script, generated/original visuals, or scene narration, use the version-2 generated-production workflow below and read [collaborative production](references/collaborative-production.md).
- For editing supplied screen recordings, talking-head footage, or synchronized parallel/sequential combinations, use production-state version 3 and read [recorded-video editing](references/recorded-video-editing.md) plus its [timeline contract](references/recorded-timeline-contract.md). Do not force recorded footage through narration-duration scenes or run speech synthesis unless new narration is requested.

Both tracks preserve concrete review gates, durable feedback, guarded final exports, immutable source media, and local editable output. Do not migrate approvals between track versions.

## Required sequential gates

For the generated-production track, read [collaborative production](references/collaborative-production.md) before starting. New generated productions default to v2 state and sequential user review. At each gate, present the concrete review target, end the turn, and wait. Do not create next-stage artifacts while waiting. “Proceed” approves only the stage just presented; explicit delegation is scoped.

1. Write transcript → generate/import scene audio → create/check timestamps. Present the narration package and STOP for approval before creative planning. An extra transcript-only gate is optional if requested.
2. After approval, create creative direction, storyboard, design system and beat-level asset requests. Ask for external assets/choices and STOP; do not silently switch to code-only visuals to avoid the handoff.
3. Inspect submissions, resolve alternatives, and finalize timed execution/playbook files. Present the refined plan and STOP for approval before scaffold or JSX.
4. Implement only the active scene and typecheck. Ask the user to run `npm run studio`, specifying SceneN and frame checkpoints. STOP for feedback; record and apply it until approved before implementing the next scene. Start Studio yourself only if requested.
5. After all scenes, review joins and VideoFull in Studio. STOP for export approval, then render scene exports, master and final PNG.

Run `09_check_production.py` at the applicable track gates. Generated productions use plan/implement/scene/render with version-2 state; recorded edits add source/edit/delivery gates with version-3 state. Raw CLI exports must not bypass pending review. Read the relevant track reference for snapshot-based approvals and engineering test exceptions.

## Scope and review

Honor the user's requested folder, duration, aspect ratio, and existing approvals. Default to 20–45 seconds, 4–8 scenes, 30 fps, vertical 1080 × 1920 if unspecified. Estimate narration at about 2.5 words/second; use measured audio durations for production.

For multi-minute explainers or a reference with a sustained argument, read [long-form production](references/long-form-production.md). The short defaults are not limits. Plan chapters and visual beats, maintain recurring identities and a shared asset inventory, and validate a representative sequence before scaling production. For reference matching, distinguish inspected frames/captions from actual motion and listening review; never infer production methods or sound quality from stills.

Read [engagement direction](references/engagement-direction.md) before scripting: define the audience's situation, opening promise, intermediate discoveries, and final takeaway. Use the principles as editorial guidance, not guaranteed psychology or retention outcomes. For platform/aspect-ratio choices or adaptations, read [platform composition](references/platform-composition.md). Horizontal YouTube needs deliberate spatial staging and pacing; vertical versions need their own readable composition. Re-stage rather than merely crop.

Use asset-plan.md for exact spoken-beat coverage, layer roles, filenames, prompts, provenance and visible action. Required execution-plan.json holds checked word/frame ranges, real layer references, before/action/after states, ordered coding steps and observable acceptance. implementation-plan.md supplies the reviewed design system and construction playbook. Whole-scene summaries do not satisfy the beat contract. Preserve actual user feedback and scoped approvals in production-state.json.

If the user explicitly delegates choices or requests an autonomous test, choose reasonable defaults and proceed within that scope; record delegation when using production state. Do not impose collaborative approval pauses on engineering tests. A separate storyboard-JSON approval is unnecessary when it implements an approved direction. Publishing or uploading requires separate authorization.

For debugging or improving this skill, reproduce the failure, repair the relevant scripts/instructions, and validate with isolated fixtures and a real smoke test when feasible. Do not apply creative approval gates to engineering tests. Preserve existing authored work.

## Preflight and assets

Read [the pipeline reference](references/video-production-pipeline.md) before running scripts or writing scene code. Resolve script paths relative to this skill, never the caller's working directory. Check uv, Node/npm, ffmpeg/ffprobe, and the selected phonemizer's system requirements. Use lean-coder if available for implementation, but the pipeline must not depend on a separately installed skill.

Choose the workspace root explicitly: nearest containing Git root (including worktree .git files), otherwise the user-designated workspace. A globally installed skill's directory is not the target workspace. Create or reuse a dedicated environment with `uv venv`; run every Python script with `uv run` using that environment as described in the pipeline reference. Do not use system Python or bare pip.

Inventory reusable creative media under WORKSPACE/.video_production_assets and project submissions under PROJECT/assets/. Read [asset library](references/asset-library.md) for intake, filename confirmation, prompts, source/licensing and AI disclosure, and inspection. Before preparing a storyboard, search any available curated inventory with topic and visual-beat terms and inspect suitable candidates. List only selected real assets in the storyboard; planned filenames belong in `asset-plan.md`. Candidate search informs art direction without forcing reuse. Keep kokoro/ and whisper/ model caches separate from creative media. Missing media never limits the work to text slides: plan original animation, diagrams, illustrated action, or spatial metaphors in code where suitable. When an approved required asset is unavailable or unsuitable, ask the user to choose an alternative, omission, or redesign unless already delegated; update dependent scenes and transitions before declaring readiness.

When using Kokoro, run scripts/04_setup_assets.sh with that workspace root if its models are absent or invalid; it does not download creative media. Supplied narration needs no Kokoro setup. Run authorized setup directly; request environment escalation only if necessary. Downloads are roughly 354 MB total. The compatible model and bundled voice archive come from the kokoro-onnx release, not the onnx-community Transformers/JS layout. A successful exit or file existence alone is not evidence of valid model contents.

Add .video_production_assets/, node_modules/, and output/cache paths to the appropriate .gitignore, preserving existing rules. Keep project source editable and versionable; do not ignore the entire project by default.

## Narration and timestamps

Write narration to PROJECT/transcript.txt, separating scenes with a line containing only ---. Complete audio/timestamps before the default narration-package approval gate; honor an earlier transcript review if requested.
For supplied recordings, use `scripts/06_import_narration.py` as described in [audio direction](references/audio-direction.md), then use the same timestamp and scaffold pipeline. Imported recordings do not require Kokoro models. Audition the chosen voice before generating a long script.
Read [audio direction](references/audio-direction.md) for phrasing, scene-to-scene cadence, optional mixing, and readable captions. Use supported voice controls and audition joins; do not invent speech-engine capabilities.
Use scripts/01_tts.py with --assets-dir WORKSPACE/.video_production_assets and --out-dir PROJECT/public/audio. Default voice: af_heart; see [voice guidance](references/kokoro-voices.md). Confirm every WAV is nonempty, finite, nonsilent, and matches metadata. Report measured scene durations.

Run scripts/02_timestamps.py sequentially for each WAV with --model base, --language en for English narration, and --model-dir WORKSPACE/.video_production_assets/whisper. Check words against the narration transcript; recognition is not forced alignment. Inspect and correct mistranscriptions without inventing timing, then present the narration package for approval. Short clips under 0.5 seconds produce an empty words array; empty captions for longer narration require investigation.

## Visual direction and composition

Read [visual direction](references/visual-direction.md) after narration approval. Recommend two treatments that fit the editorial job, then record the approved recipe and project-specific tokens in `design-system.json`. Professional process, editorial evidence, doodle, collage, flat character/object, screen tutorial, data/system, documentary hybrid, kinetic type and intentional dark are starting grammars—not mandatory layouts. `custom` requires equivalent concrete decisions. Do not let scaffold defaults select a dark background, or replace that habit with a universal beige style. Vary shot scale and staging while preserving coherent object behavior. Use a meaningful first frame and settled payoff. Keep the explanation understandable muted.

For doodle/whiteboard direction, read [whiteboard production](references/whiteboard-production.md). Scaffold with `--visual-style whiteboard` to copy an original SVG starter kit and reveal/camera/chart helpers. This is independent of aspect ratio; it supplies building blocks, not finished illustration or automatic storyboard rendering. For numerical comparisons, read [data explainers](references/data-explainers.md); generate chart values from explicit assumptions and tested calculations rather than hand-entering animated totals.

For a publishable project, consult current primary platform guidance and relevant examples where useful. Distinguish observed popularity from measured retention; do not promise virality. A functional smoke test needs no trend research.

Write PROJECT/storyboard.json as a scene-wise directorial brief using the pipeline reference. Describe what the audience sees and understands, the hook, payoff, visual atmosphere and action, background treatment, sound intent, and purposeful media usage. Do not specify element trees, coordinates, font sizes, fixed layouts, or animation keyframes here. Write enough to inspire execution without dictating its construction. Asset references are optional and must identify real inspected files when selected; explicitly allow original code visuals when no media fits.

After narration-package approval, map every spoken line to beats in asset-plan.md, including BG/midground/foreground and the action explaining the idea. Allow unused layers, reuse, and named code visuals; do not impose one shot per sentence. Request movable parts/cutouts/recordings according to the action, not an opaque landscape illustration for every layer. Register accepted selected visual/audio media in `asset-manifest.json` with stable IDs, staged paths, provenance, rights and inspection. After asset review, complete implementation-plan.md and execution-plan.json: word/frame ranges, named visual/sound events, design system, initial/action/result, geometry/anchors, masks, easing, continuity, coding steps and observable acceptance. Do not defer timing or construction to implementation. Consolidate existing scene-design.md. Master timing remains in metadata/edit plans/generated config; narration uses ceil(duration_s * fps), holds extend spans, and final PNG is TOTAL_FRAMES - 1.

Read [transitions](references/transitions.md) before composing scene joins. Choose transitions by the relationship between ideas: cuts, fades, directional slides, masks, or authored shared-object/camera continuity. Favor a coherent vocabulary over an effect quota. Visual scenes separate from narration/captions; visual overlap must not overlap voices or advance captions. Version-2 edit plans anchor music/SFX to checked words, named execution events or timeline boundaries. Missing transition entries mean cuts, not a requirement to animate every boundary.

For generated productions, run scripts/03_scaffold.py after refined-plan approval with the approved storyboard, narration metadata, edit plan and `--design-system PROJECT/design-system.json`; choose the profile. It requires v2 state and validated execution/design/asset contracts. Scaffold resolves sound anchors into the master clock and checks selected source duration. It creates placeholders and guarded exports, not permission to implement all scenes. Run scene preflight and author only active SceneN.tsx. Compare each planned action to actual code and Studio checkpoints; a fade or image pan does not satisfy a promised transformation. Return material unplanned choices to planning. Existing structural files cause safe refusal; inspect before `--refresh-generated`, which preserves authored scenes/helpers. Recorded edits use `11_scaffold_recorded.py` and the recorded contract instead.

Stage selected media in PROJECT/public/media with traceable source paths. Combine footage or imagery with animation where useful; choose crops and motion around the subject, and avoid stretching or unintentional looping. Mute source-video audio unless deliberately used. Decide music, ambience and SFX during planning—even when each is intentionally `none`. Tie selected effects to the same named events used by visual code; specify source trims, envelopes, ducking intent and listening acceptance. Control peaks and keep narration intelligible. Never claim generated graphics are real footage or invent assets that are not available. See the pipeline reference for media implementation and review guidance.

Use frame-driven animation, deterministic randomness, and local assets. In new visual-only scenes, use contentFrame for normal action and rawContentFrame for deliberate transition handles; the master owns narration and captions on the speech clock. The included WordCaptions groups phrases by punctuation, pauses, and a width heuristic with optional word highlighting; inspect real font bounds. @remotion/captions contains utilities, not a ready-made Captions React component. Other caption styles require implementation and preview verification. Do not suppress TypeScript errors to make templates appear valid.

## Verification and delivery

Read [creative review](references/creative-review.md). Run npm run typecheck and review isolated SceneN plus `SceneNReview`, the bounded master-context composition with music/SFX at their original timeline positions. Review BoundaryN and VideoFull before export. Inspect opening, dense and final frames for readability, clipping, missing elements and caption timing. Check whether visuals demonstrate the idea, each beat adds understanding and the payoff fulfills the hook. Check sound-event alignment, source edits, ducking, safe areas and voice clarity. Review muted, audio-only and combined playback; metadata/stills do not prove audible synchronization. Record feedback, revisions and actual user approvals durably in production-state.json; implemented feedback is not automatically approved. Reopen affected reviews when inputs change. scripts/05_review_bundle.py prepares commands/report; `--render` checks recorded export approval when state exists, then renders. Honor a user's requested pause before testing or rendering.

After approval, render scene/boundary exports, the full master composition, and exact final-frame PNG. Do not concatenate isolated scene files to assemble the deliverable; render VideoFull to preserve its overlaps and mix. Check audio/video streams, dimensions, fps, duration, and the final frame using ffprobe and decoded frames. Compare with compiled TOTAL_FRAMES / fps, including explicit holds; narration quantization contributes less than one frame per scene beyond summed WAV duration. Check each narration mounts once and survives visual transitions intact. Run `scripts/10_audio_qc.py` on an authorized rendered mix and report its integrated loudness/true peak against the project's documented target; measurement is not mastering, listening or approval. Material post-render audio changes require playback review. When authorized analytics are available, map observations to master beats and propose controlled revisions; otherwise report editorial hypotheses, not measured retention gains.

Deliver links to MP4, PNG, editable project, dimensions/fps/duration, style/voice/captions, and verification results. Clearly distinguish a technical smoke test from a finished creative video. State any remaining blockers without claiming incomplete checks passed.
