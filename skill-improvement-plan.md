# Video-production skill: visual direction and synchronized sound

Status: proposed implementation plan, not an approved skill revision.
Date: 2026-09-22. Scope: local `.agents/skills/video-production` only.

## 1. Recommendation

Incorporate the useful ideas from [workflow.md](workflow.md) into the existing gated pipeline. Do not replace its directories, state format, narration clock, or approval model.

The highest-value changes are concrete visual recipes, project-specific design tokens, audio cues anchored to the same events as visual actions, and scene previews that include the actual master mix. A different palette alone will not make a video feel intentionally directed: the visual must explain something through staging, evidence, or a meaningful change of state.

Interpret “work style” as professional/workplace/process explanations; include editorial explanation separately. These are selectable treatments, not claims that the skill already automatically generates every type. Code-driven 2D animation is practical; footage, richer character animation, and cinematic work depend on appropriate supplied/generated assets and review.

This evaluation inspected the workflow, skill instructions, relevant references, templates, timeline compiler/renderer, scaffold, and approval implementation. It is not a playback evaluation of the latest video or a controlled comparison of model sizes. The reported smaller-model behavior is plausible, but not experimentally established here.

## 2. Evidence: what exists and what is missing

Paths below are relative to `.agents/skills/video-production/`.

| Area | Current evidence | Targeted improvement |
|---|---|---|
| Sequential approvals | `SKILL.md`, `references/collaborative-production.md`, `scripts/workflow_v2.py` already enforce narration → assets → refined plan → active scene → master/export | Preserve; expand review contents, not gate count |
| Visual direction | Many possibilities are listed, but most lack recipes. Whiteboard has its own reference and helpers | Add selectable families, concrete tokens, staging/motion rules, examples, and limitations |
| Dark starting point | `assets/VisualScene.tsx.template` and legacy `Scene.tsx.template` use `#171717`; `Timeline.tsx` uses black underneath scenes | Replace new-project hardcoded theme inheritance with approved tokens; do not blindly change intentional black footage or authored projects |
| Beat-level execution | Execution plan already checks word coverage, frame ranges, layers, before/action/result and steps | Add named action events so sound and code share timing instead of interpreting prose independently |
| Sound playback | `scripts/timeline.py` supports music/effect cues, gain, fades and duck gain; `assets/Timeline.tsx` renders them | Extend existing edit plan rather than create a competing sound clock |
| Sound synchronization | Cues currently require absolute master `startFrame`; no beat/event link | Resolve stable scene/beat/event anchors after holds and narration durations compile |
| Scene review | `ScenePreview` explicitly passes `audio: []`; boundaries/master include cues | Add a master-context scene review composition, preserving isolated visual inspection |
| Mixing | Music ducks across narration segments; effects do not. No automatic looping/in-points; source coverage is not checked by scaffold | Add checked source trims, cue-specific envelopes, deliberate looping policy and media validation |
| Loudness | `01_tts.py` peak-normalizes; audio reference recommends manual full-mix measurement | Distinguish peak normalization from perceived loudness; automate measurement/reporting, not automatic creative approval |
| Asset rights | Existing asset plan/library guidance covers source, rights, disclosure and inspection | Make audio-specific metadata and attribution verifiable through an asset register |
| Revisions | Scoped approval snapshots already invalidate changed reviewed inputs | Include new design/asset contracts; no second approval system |
| Selective regeneration | Approval hashes exist, but narration helpers do not implement a per-scene content/settings cache | Useful follow-up, not prerequisite for style and sound improvements |

The scaffold defaults are a concrete source of bias, not proof that they explain every poor result. Flat compositions, generic icons, repeated panel layouts and decorative image drift also need explicit editorial review.

## 3. Research and its implications

These are design recommendations, not evidence of guaranteed retention or “human-made” detection outcomes.

- Motion should establish consistent behavior and communicate a sequence or cause/effect; complexity in the drawing need not imply complexity in its motion. Apply that principle to recipe-specific motion rather than a universal fade-and-slide pattern. [IBM animation guidance](https://www.ibm.com/design/language/animation/tips-and-techniques/)
- Staging, anticipation and follow-through offer a useful vocabulary for object action. Translate them into executable events such as prepare → contact → settle, not mandatory bounces on every label. [Adobe animation principles](https://www.adobe.com/creativecloud/animation/discover/principles-of-animation.html)
- Color must support legibility and meaning. Use explicit text/background pairs and labels or shapes alongside semantic colors. Check normal text against a 4.5:1 contrast target; that is a useful design check, not certification of an entire moving video. [IBM color guidance](https://www.ibm.com/design/language/color/), [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- Remotion supports frame-dependent audio gain and source trimming. Volume callbacks use audio-local frames, so timeline placement and source offsets must be handled explicitly. Check compatibility against the scaffold's pinned Remotion version before using current documentation examples. [Volume](https://www.remotion.dev/docs/audio/volume), [trimming](https://www.remotion.dev/docs/audio/trimming)
- FFmpeg can measure and normalize integrated loudness and true peak, including a two-pass approach. Measurement does not establish intelligibility or automatically produce a reviewed master. [FFmpeg loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm)
- Music/SFX licensing must be track-specific. YouTube's Audio Library distinguishes attribution requirements and warns that unrelated “royalty-free” sources are not covered by its assurances. Store the applicable license and required credit, not merely a download URL. [YouTube Audio Library guidance](https://support.google.com/youtube/answer/3376882?hl=en)

## 4. Proposed visual-direction library

Separate three decisions: editorial format, visual treatment, and motion vocabulary. An editorial explainer can combine real evidence with paper graphics; a workplace explanation can use doodles or a screen demonstration. Select one primary treatment and, when useful, a compatible secondary treatment. Do not randomly alternate styles per scene.

The palettes below are original proposed starting points, not copied brand palettes or prevalidated accessible combinations. Each lists background / ink / primary accent / supporting accent. Accent colors are not automatically suitable for small text.

| Family | Appropriate use and visual construction | Starting palette | Motion and sound character | Limits / avoid |
|---|---|---|---|---|
| Professional process / workplace | Decisions, operations, productivity; documents, queues, work surfaces, connected systems and concrete tasks | Porcelain `#F6F8FA` / `#172B4D` / blue `#2457C5` / teal `#087F8C` | Route objects, compare states, highlight bottlenecks; restrained clicks/physical placement | Not a dashboard of rounded cards; show the process changing |
| Editorial evidence explainer | Context, arguments, investigations; maps, charts, quotations, document crops and footage | Newsprint `#F4F0E6` / `#242424` / vermilion `#B9382D` / blue `#2457A7` | Purposeful cuts, annotation, crop-to-detail; sparse paper/marker accents | Verify evidence and provenance; do not invent archival imagery or copy a publisher's identity |
| Doodle / whiteboard | Teaching mechanisms, relationships, simple narratives; original SVG paths and selective fills | Paper `#FFFCF3` / charcoal `#263238` / blue `#2463A6` / ochre `#C58A16` | Draw a relationship, then hold it; occasional short pencil cues | No slow draw-on for everything; raster wipes are not genuine stroke animation |
| Tactile collage / cut-paper | Abstract concepts made concrete through metaphor; cutouts, paper planes, limited texture | Cream `#F3E8D5` / espresso `#342C29` / brick `#B84A36` / moss `#52735C` | Layered assembly, measured parallax, object replacement; paper/fabric accents | Requires separated pieces; texture and jitter must not reduce clarity |
| Flat 2D object / character story | Cause/effect, human situations, recurring motifs; consistent shapes, poses and articulated parts | Pale sky `#EEF6FA` / midnight `#203249` / coral `#D95645` / teal `#187D78` | Anticipation → action → consequence; selective contact/settle sounds | No promise of full character rigging from one image; no face/identity substitution without approval |
| Screen tutorial / product walkthrough | Actual software tasks; supplied capture, cursor action, magnification and callouts | White `#FFFFFF` / slate `#202A35` / blue `#2457D6` / green `#147D64` | Follow the task; stable zoom during reading; clicks only where meaningful | Preserve real UI colors; redact private data; fabricated UI must be identified as illustrative |
| Data / systems explanation | Comparisons, flows, simulations; labeled charts and consistent object identity | Mist `#F8FAFC` / navy `#192B3A` / blue `#2166AC` / orange `#B65312` | Animate the changing quantity or relationship; restrained or no SFX | Palette does not replace labels, units, sources or tested calculations |
| Documentary / cinematic hybrid | Human context, environments, atmosphere; real or clearly labeled illustrative footage with overlays | Warm white `#F2F0EB` / near-black `#1F2528` / amber `#B77A22` / sage `#537D76` | Motivated reframing and cuts, continuous ambience where useful | Footage owns much of the palette; asset-dependent, not automatically cinematic |
| Kinetic typographic essay | Language-driven short argument, quotation or punchline; typography carries the idea | Ivory `#FFF8ED` / ink `#25202B` / plum `#70439A` / rust `#B94431` | Emphasize contrast and syntax; occasional punctuation accents | Supporting format, not the automatic substitute for all explanatory visuals |

Retain an intentional dark option: graphite `#17212B`, paper ink `#F3F5F7`, cyan `#65C7CF`, amber `#F2B95D`. Use it when the selected direction, footage, reference or brand supports it. Do not ban dark backgrounds; remove their unexamined default status. Do not merely replace one universal dark theme with one universal beige theme.

### What every recipe must contain

1. Selection criteria, prerequisites and asset burden: code-native, mixed assets, or footage-dependent.
2. Background/material treatment, allowed color roles and verified text pairs.
3. Typography roles: title/body/data/captions, chosen local font files and fallback. Editorial serif headings are optional; doodles need readable labels, not compulsory handwriting fonts.
4. Stroke, corner, shadow, texture and depth conventions with numeric project tokens.
5. Staging patterns: overview → detail, before/after, evidence crop, accumulation, relationship reveal. Avoid a fixed layout repeated for every sentence.
6. Motion vocabulary: durations/easing selected at the project fps, entry/settle behavior, camera rules and supported transitions.
7. A worked beat showing narration, initial state, action, result, BG/mid/FG, sound event or intentional silence, and review checkpoints.
8. Common failure examples and concrete corrections; note when the assets cannot support the promised motion.

For example, “too many ideas cause a bottleneck” should show distinct notes entering a limited opening, accumulating, then being filtered. A machine illustration with a fade does not implement that explanation. The same action can use clean work cards, drawn notes, or cut-paper shapes without changing its meaning.

### Smaller-model execution support

After narration approval, recommend two suitable treatments with reasons, then resolve the selection within the existing creative/assets handoff. If choices were delegated, document the selected treatment and why. No detailed style artifact before the narration gate; earlier intake may record user constraints.

Add proposed `design-system.json` as the authoritative machine-readable token file. `implementation-plan.md` explains choices and references tokens; generated `src/design-tokens.ts` is derived, not a second source of truth. Include recipe ID, background strategy, colors, typography, stroke/depth, motion and caption tokens. Reject unknown recipe IDs unless an explicit custom direction is supplied. Do not silently choose a recipe during scaffold.

Keep instructions compact: a selector plus only the chosen recipe, rather than loading a large visual encyclopedia. Use the first approved scene to calibrate execution; an additional non-first pilot requires explicit delegation because current gates are sequential.

## 5. Sound planning as part of the same playbook

Make the sound decision mandatory, but not the presence of music: `music: none`, `sfx: none` is a valid deliberate design. For selected sound, specify its narrative job, asset, exact trigger, source trim, duration, envelope, and acceptance checkpoint before implementation.

### Proposed artifact responsibilities

- Keep `asset-plan.md` for human-facing requests, filenames, prompts and decisions. Add audio rows: role, character, duration, intended action, source/rights, attribution and review status.
- Add proposed `asset-manifest.json` as the authoritative verified media register for both visual and audio dependencies. Use stable IDs; distinguish AI disclosure from usage rights. Record source path, staged path, hash, type, technical metadata, license evidence/usage basis, attribution and inspection result. Markdown references IDs rather than maintaining competing status fields.
- Extend `execution-plan.json` to version 2 with named events within beats. Preserve existing words/frames and before/action/result structure. Each event has an ID and speech-local frame, plus an optional word anchor and documented offset. Examples: `contact`, `chart-threshold`, `settled`.
- Extend `edit-plan.json` to version 2 for anchored audio and mix settings. It is the sole editable cue specification. No independent `sound-plan.json` or manually maintained master cue table.
- Compiler outputs the resolved master cues into existing generated timeline data and a readable validation report with local/master timecodes. Generated outputs are never manually edited.
- Keep `production-state.json` as approval/feedback authority. An optional readable feedback report is derived, not a second editable log.

### Proposed cue contract

Each cue: stable `id`, `assetId`, role (`music`, `effect`, optional `ambience`), purpose, required/optional status, anchor, source in-point, duration or end anchor, base gain, fade-in/out, ducking policy, and listening acceptance. Use explicit units: frames for timeline placement/envelopes, seconds for source trim metadata; compile against composition fps. Gain fields use dB in v2, converted once to linear amplitude; retain v1 linear behavior unchanged.

Anchors support one unambiguous form at a time: execution event, checked word boundary, scene speech start/end, scene span end, transition boundary, or master start/end. Require a reason for offsets and absolute-frame exceptions. Use scene ID plus beat ID plus event ID because existing beat IDs need only be unique within a scene. Distinguish the end of speech from the end of an explicit hold.

Example: scene 2, beat `b03`, event `contact` occurs at speech-local frame 96. If scene 2's compiled narration starts at master frame 420, the click starts at frame 516. Adding a 12-frame hold before scene 2 moves it to 528 automatically. If the sound has a 0.08-second lead-in before the audible impact, trim that lead-in or record a deliberate offset; aligning a file's beginning alone does not align its audible event.

Visual code references the generated event frame, and sound references the same event ID. Do not copy frame 96 into multiple authored files. A compiler test can prove the mapping; only playback can establish the intended perceived synchronization.

### Mix behavior

- Narration remains continuous and single-mounted on its existing speech clock; visual overlap must not overlap voices.
- Start with the existing speech-segment ducking approach, adding explicit attack/release/duck amount. Avoid automatic word-gap pumping. SFX ducking is a deliberate per-cue choice, not universally required.
- Specify fades independently: a click should not inherit a music fade that removes its transient. Ambience/music can bridge scenes without restarting at each scene preview.
- Validate source duration against trim and playback length. No silent loop or truncation. Initially require an approved pre-edited longer file or explicit repeated segments; seamless loop/crossfade support is a later extension unless needed by a real project.
- Music selection describes emotional role, density, vocals allowed, and planned changes/silences; do not force every visual to the music beat or stretch approved narration to fit a track.
- Set a documented project loudness target and tolerance. A possible house starting point is −16 LUFS integrated ±1 LU with true peak ≤−1 dBTP, adjustable for destination and material; it is not a platform rule. Measure the final encoded output and listen. Short clips and silence can make integrated metrics unsuitable; report that instead of inventing a pass.
- Prefer adjusting the actual reviewed mix. If a separate mastering pass is necessary, preserve the source render, measure the new output, and have the user review material audible changes. No unreviewed master after final approval.

## 6. What to incorporate from workflow.md

| Proposal | Decision and reason |
|---|---|
| Brief, source permissions, voice/caption/music preferences | Adopt lightweight intake; ask for consequential missing choices, not every optional field |
| Full style guide before narration | Adapt: capture constraints early, finalize design after the existing narration approval |
| Extra script/style/execution gates | Optional on request; keep existing defaults and approve detailed execution with the refined plan |
| Voice audition and pronunciation map | Strengthen existing auditions; add overrides only through supported engine controls; do not invent speed/phoneme flags |
| Forced alignment | Evaluate as a later optional backend on actual hardware; preserve checked Whisper fallback and report uncertain timings honestly |
| Scene hashes and regeneration cache | Valuable follow-up; key on text, engine/model version, voice, actual supported settings and post-processing, not text alone |
| Fixed 0.3/0.5-second audio padding | Do not impose; preserve performance and use existing explicit holds where needed. Any waveform trim/pad precedes alignment |
| `round(sec × fps)` everywhere | Do not adopt; preserve floor starts / ceil ends and existing measured-duration quantization |
| No beat overlaps or gaps | Adapt: complete word coverage plus intentional visual coverage through pauses/holds. Layered actions can overlap |
| Placeholders so building is never blocked | Reject as default gate bypass; optional expressly approved prototyping only, with unresolved assets preventing publishable export |
| Transitions must fit audio padding | Do not adopt literally; existing independent visual handles permit overlaps without cutting speech |
| Pilot and per-scene feedback | Already present in substance; improve checkpoints and include full-mix context |
| Low-resolution/contact-sheet previews before approval | Optional user-authorized review exports would require a separate preview permission, not reuse delivery approval. Preserve Studio-first by default |
| Mix only at finalization | Move rough mix into planning and each scene review; finalization measures and verifies the already reviewed design |
| Automatic commits and additional state/feedback files | Do not adopt; retain current state and only commit when requested |
| Never read outside video directory | Adapt to bounded production writes plus permitted shared skill/model/media reads; existing shared caches remain usable |
| Agent cannot ever judge motion/audio | Replace categorical claim with accurate disclosure of tools and evidence actually inspected; user approval remains essential |
| Universal hardware/model limits | Do not hardcode; record actual environment and use configurable render concurrency/scale |
| Thumbnail instead of final-frame PNG | Keep exact final PNG; optional selected thumbnail is an additional deliverable |
| SRT, credits, release notes | Useful optional delivery features; rights/measurement summary should accompany selected audio even without expanded packaging |

## 7. Implementation sequence and acceptance

All items below are proposed. Preserve existing uncommitted changes and authored projects. Implement in the order shown; no new video production is authorized by this plan.

### A. Direction recipes and token-driven scaffold

Files: update `SKILL.md`, `references/whiteboard-production.md`, `references/creative-review.md`, `assets/implementation-plan.md.template`; add `references/visual-direction.md`, selected recipe examples and `assets/design-system.json.template`. Update `scripts/03_scaffold.py`, `assets/VisualScene.tsx.template`, `assets/Timeline.tsx`, and caption token integration in `assets/WordCaptions.tsx`.

Route to the chosen recipe, resolve tokens during refined planning, and generate scaffold theme from them. Do not add a generic finished-scene generator. Preserve legacy behavior when explicitly using the existing legacy path; never repaint existing JSX during refresh.

Acceptance: a light workplace fixture, paper doodle fixture and intentional dark fixture all use their selected backgrounds/text/caption tokens; unknown or missing required new tokens fail clearly. Local fonts and actual caption bounds are inspected. Existing scenes/helpers survive refresh. The dark recipe remains available by choice.

### B. Versioned media/event/cue contracts

Files: update execution/asset/playbook templates, `scripts/workflow_v2.py`, `scripts/09_check_production.py`, `scripts/timeline.py`; add proposed asset-manifest and edit-plan-v2 templates. Update `references/audio-direction.md`, `references/asset-library.md`, `references/collaborative-production.md` and pipeline schema documentation.

Implement validators and deterministic anchor resolution first. Derive local and master event maps, verify media duration/trim with ffprobe, and generate actionable errors identifying scene/beat/cue. Reject duplicate cue IDs, missing anchors/assets, unresolved required rights/status, nonfinite gains, out-of-range trims, unsupported schema versions and cues beyond timeline. Do not silently clip negative offsets.

Acceptance: inserting a hold moves every affected anchored cue exactly once; nonzero word starts and anticipation offsets resolve correctly; malformed inputs fail before scaffold. V1 fixtures compile identically. Plan reports distinguish machine errors, manual checks and unresolved user choices.

### C. Renderer and honest full-mix scene review

Files: `assets/Timeline.tsx`, `scripts/03_scaffold.py`, `scripts/05_review_bundle.py`, review references.

Render v2 trims and envelopes through the existing master timeline. Keep isolated `SceneN` for visual inspection; add `SceneNReview` as a bounded master slice containing the active scene and available context. Do not implement future scenes to populate a preview. Preserve music source position and envelopes when seeking into a slice. Use BoundaryN after adjacent scenes exist.

Acceptance: narration appears once; music continuing from a previous scene does not restart; an effect before/after a visual overlap plays at its original master time. Review-slice decoded audio matches the corresponding master interval within a documented codec tolerance. Test the pinned Remotion version, not only current docs. Hand off `npm run studio` with both visual and mix checkpoints and await approval.

### D. Measurement and approval integrity

Add proposed `scripts/10_audio_qc.py` to analyze an authorized rendered file and output machine-readable loudness/peak/duration findings plus a readable summary. Do not render or modify media implicitly. Integrate reporting with review/delivery helpers.

Extend snapshot coverage to design-system and asset-manifest files and any approved mix controls. Keep production state version 2 if its structure is unchanged; schema versions for execution/edit plans evolve independently. New projects require new contracts; existing versions remain supported explicitly. Do not automatically migrate approved projects or transfer approvals to different hashes. Report the impact before an opt-in migration.

Acceptance: changing a sound asset, anchor, trim, gain or design token invalidates affected approvals under the existing conservative snapshot model. Writing a QC report does not itself invalidate source approvals. Missing state still blocks delivery. Snapshot changes for migrated projects require renewed review, not synthesized approval.

### E. Behavioral evaluation and documentation reconciliation

Extend `scripts/test_pipeline.py`, `scripts/test_extensions.py`, `scripts/test_workflow_v2.py`; add focused cue/QC tests if separation improves clarity. Use synthetic sound fixtures so regression tests do not require copyrighted music or a generation provider.

Test two or more styles against the same short explanatory brief, and include an explicit dark brief to detect overcorrection. With smaller models if available, evaluate actual artifacts and handoffs: did the model use the chosen treatment, demonstrate the action, specify silence/sound, request missing audio and stop at gates? Record model/version and settings; do not label a stronger-model simulation a smaller-model test.

Independent review should check contrast, layout variation, concrete visual transformations, audio anchors, silence decisions and approval compliance. User playback assesses perceived synchronization, distraction, pacing and whether the result feels deliberately edited. No invented aesthetic score or quality guarantee.

Reconcile SKILL, pipeline, audio, creative-review, collaborative, whiteboard, transitions and long-form references so none tells the agent to add sound only after final review. Run existing regression tests, new unit/integration tests, skill validation, and an isolated real render smoke test when authorized/available. Technical success is not creative approval.

## 8. Deferred work and release boundary

Defer forced-alignment replacement, alternate TTS engines, voice cloning, sophisticated sidechain compression, automatic music generation, full character rigging, new directory layout, general preview-export permissions, and per-scene cache/dependency optimization. They have value but are not required to fix this iteration's concrete failures.

Minimum useful release: recipe selection + approved design tokens + event-anchored sound + source validation + full-mix scene review + QC evidence, without weakening existing gates. Start with the direction/token change, then complete one end-to-end synthetic sound example before expanding the recipe examples.

No skill implementation, project migration, rendering, music downloads or existing-video edits were performed as part of this planning task. Approval of this plan would authorize targeted skill implementation, not approval of a future video's creative choices or exports.
