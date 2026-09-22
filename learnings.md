# Video-production skill learnings — recorded-screen edit

Project evidence: `dataops_agent_demo/remotion-edit` (2026-09-22)

This memo records observed workflow failures and durable practices from rebuilding a narrated screen recording as a Remotion presentation edit. It is not a substitute for the skill documentation; it identifies additions and stronger enforcement points that would prevent the same failures.

## What worked

- Treating the supplied recording as **evidence**, not as the whole visual treatment, produced a clearer instructional format. The live screen can move between `screen-focus` for reading and a left-side `balanced` evidence panel while a separate right-side presentation layer explains the narration.
- Keeping the immutable MP4 intact while mounting it as chronological `Sequence` clips is the correct recorded-edit model. The primary audio is mounted once per compiled clip at the same source offset; physical pre-cutting is neither necessary nor desirable.
- Word/source-time anchors made visual and sound actions defensible. Examples in this project include the Scene 1 failure treatment at source 38.94 s / local frame 1093, Scene 2's "Logs" beat at local frame 169, and Scene 3's root-cause accent at local frame 708.
- Individual stills are valuable for placement evaluation. They caught overlay drift and verified the revised canvas and joins without violating the user’s instruction not to render scene videos before final review.

## Failures observed and their causes

### 1. The plan and rendered implementation disagreed on the background

The approved `design-system.json` specified a light slate presentation canvas (`#F3F6FA`), but `RecordedTimeline.tsx` set both the master and each clip to dark `#080B14`. The result was a pitch-black void around the evidence screen, despite the plan calling for a light presentation surface.

**Learning:** a design token is not implemented merely because it exists in `design-system.json`. The review checklist should compare every global visual token actually used by the master and layer containers against the approved design system. This needs an explicit background/canvas checkpoint at frame 0 and during every balanced layout.

**Applied correction:** the master and clip canvases now use warm cream `#F7F0E5`; evidence cards use white and a restrained blue-grey shadow. Black pillar bars that remain inside the browser image are baked into the supplied recording and must not be mistaken for the composition background.

### 2. Global-coordinate overlays drifted across a scrolling UI

An earlier failure highlight obscured the pipeline name after the Teams content scrolled. The problem was not just an incorrect x/y value: a normalized source coordinate applies only while the target occupies that source position. Once the UI scrolls, an old anchor is invalid.

**Learning:** every UI-bound annotation requires:

- an inspected source frame at its activation point;
- normalized source geometry tied to the transformed media bounds, not output-canvas coordinates;
- a start/end range that excludes scroll or layout changes unless a separately verified anchor is supplied;
- preceding and following frame checks (at least 15 frames each side);
- a label-free outline when the label might conceal the exact source text being proved.

The project’s final Scene 1 `FailureAnchor` begins only after the verified scroll completion and frames the `Failed Pipeline / bronze_cil01` evidence rather than placing a card over it.

### 3. Legacy overlays remained mounted after a redesign

Replacing `SceneOverlay.tsx` conceptually was insufficient: an older globally mounted overlay layer continued to render alongside the new scene presentation. Its stale headers/cards/SFX conflicted with the redesigned footage and could appear at unrelated frames.

**Learning:** after an overlay-system rewrite, search imports and render sites—not just component files. Explicitly verify that legacy layers are unmounted and that their associated effects are removed or scoped. Render stills at every former legacy-event frame to prove absence.

### 4. Scene joins were technically contiguous but visually abrupt

The compiled clips were already chronological and audio-correct, but Scene 2 and Scene 3 began directly in a balanced layout while the preceding scenes ended in `screen-focus`. This made the camera/layout state jump at the clip boundary.

**Learning:** for contiguous screen recordings, a scene boundary must carry both source continuity and layout continuity. The incoming scene's opening layout event may need to interpolate from the outgoing scene’s settled layout rather than appear at its target layout on frame 0. Use the preplanned opening event duration as a camera handoff only when that motion supports the next spoken idea.

**Applied correction:** the Scene 1→2 and Scene 2→3 joins use their existing 20–21-frame layout handles to ease from screen focus into the new balanced explanation. No transition SFX was added because the narration did not establish a separate event worth accenting.

### 5. Isolated scene review does not prove a join

`SceneNReview` shows a bounded master slice for one scene, but the project initially had no `BoundaryN` compositions. This made it too easy to approve a scene without hearing/seeing the immediate preceding and following context.

**Learning:** recorded-edit scaffolding should create `Boundary1…Boundary(n-1)` by default. Each should be a short master-clock slice around the true join (for example, 1 second before and 2 seconds after), retaining the original source position, captions, audio, and effects. Boundary review is mandatory after shared layout, timing, caption, source, or transition changes.

## Voiceover, captions, animation, and SFX

- Recorded narration remains primary. Do not add a visual beat, panel row, zoom, or SFX because it looks energetic; add it only when it explains a spoken concept or a visible source action.
- Store each event as a named visual/action beat with a source word/time or an approved timeline boundary. Avoid comments such as “around here”; include source time, local frame, and the reason for the beat.
- A presentation row should enter on the corresponding spoken concept, not on scene start. For example, Scene 2’s manual-work rows align to the spoken sequence Logs → issue → documentation → DataOps Agent assistance.
- SFX must share the same named event as the visual action, be quiet enough to preserve speech, and have a listening acceptance criterion. A deterministic frame anchor proves intended timing, but does **not** prove audible synchronization, intelligibility, ducking, or mix quality.
- Do not automatically attach a whoosh to a transition. A silent camera handoff is preferable when narration continues continuously and no new semantic event occurs.
- Captions are part of the timing system. Check that moving evidence/panels leave the approved caption safe area clear at each entry, focus swap, and boundary.

## Review and verification workflow

1. Before implementation, inspect and save source stills for every proposed UI annotation, source scroll, focus crop, and layout handoff.
2. Encode the scene’s background, layout states, transitions, visual beats, SFX policy, and caption-safe area in the plan. Do not defer them to JSX.
3. Implement only the authorized scene. Keep screen evidence, presentation graphics, captions, source audio, and SFX as separate layers with clear ownership.
4. Run `npm run typecheck` and inspect stills at the opening, every named event, dense/overlap moment, source scroll, and both sides of a changed join. Still rendering is acceptable for placement analysis when scene-video rendering has been deferred.
5. Ask the user to review with `npm run studio`; do not render scene videos or the master before the final authorized phase. Provide exact compositions and frames, including `SceneNReview` and `BoundaryN`.
6. Review muted, audio-only, and combined playback in Studio. Stills and metadata cannot prove motion continuity, voice/SFX alignment, or intelligibility.
7. Record feedback as `open` → `implemented` → `resolved` only after user confirmation. “Implemented” is not approval.
8. Shared source, caption, master-layout, background, or transition code changes invalidate relevant prior scene snapshots. Reopen the affected scene(s) and boundaries rather than attaching an old approval to changed files.

## Suggested skill/scaffold improvements

- Add a recorded-edit preflight that rejects or warns when the master/clip background colors disagree with `design-system.json`’s background token.
- Extend the recorded execution schema with an optional explicit `fromLayout` (or `entryLayout`) on opening layout events. The compiler can then preserve predecessor-to-successor camera continuity without relying on component-specific inference.
- Generate `BoundaryN` review compositions in the recorded scaffold by default, with documented master-context ranges.
- Add a legacy-layer audit to the scene-review checklist: imported legacy overlays, mounted render sites, old SFX branches, and sampled former event frames.
- Add an annotation contract template: source frame file, source time, normalized target rectangle, active frame range, scroll/layout invalidation condition, and nearby-frame evidence.
- Make the review bundle list exact event frames and adjacent frames for each annotation, layout swap, and sound cue, rather than only generic scene checkpoints.
- Add explicit “no generic transition SFX” language to recorded-edit transition guidance, alongside a required narration/visible-action justification for every cue.
- Report the difference between composition background and baked-in recording letterboxing in the visual-review report so reviewers know which layer can be corrected.

## Current project status when these learnings were recorded

- Scene 1’s visual approval was reopened after the shared canvas and boundary-review changes.
- Scenes 2 and 3 remain pending user Studio review.
- Individual frame checks and TypeScript/readiness checks passed; no scene videos were rendered in this phase.
- Audible synchronization and final creative quality remain pending Studio playback and user confirmation.
