# Recorded-video editing

Read this reference when the user supplies footage or recorded audio. The editorial workflow applies to interviews, demonstrations, presentations, multicamera material, performances, observational footage, B-roll, montage, and mixed sources. The bundled v3 renderer specifically implements chronological single-source or synchronized screen/presenter layouts. When another source structure is required, retain the workflow and review gates but extend the source roles, cut contract, and renderer explicitly; do not relabel unrelated footage as `screen` or `presenter` merely to satisfy the starter schema.

## Route and outcome

Use production-state version 3 with `track: recorded-edit` when its timeline contract fits. Do not run Kokoro or the narration-first pipeline unless the user separately requests generated narration. Preserve raw sources and build edits through explicit time mappings; never trim originals in place. Deliver an editable Remotion project, reviewed MP4, final-frame PNG, and final-cut captions when requested or required.

Read [recorded timeline contract](recorded-timeline-contract.md) before ingest, synchronization, cut planning, scaffolding or source-backed JSX. Read the shared [audio direction](audio-direction.md), [platform composition](platform-composition.md), [transitions](transitions.md), and [creative review](creative-review.md) only when their subject applies.

## Required gates

1. **Source review.** Ingest and probe sources, establish roles and primary audio, inspect decodability, create synchronization evidence where tracks overlap, and record initial sensitive-content findings. Present the concrete source/sync report and stop for approval. Similar duration does not prove synchronization.
2. **Rough-cut and content review.** Transcribe speech when present and correct terminology, omissions, and speaker intent against the source without inventing speech. For non-speech work, map meaningful action, musical structure, ambience, or performance beats instead. Propose non-destructive cuts and derive a scene/beat map. Each beat records checked timing, editorial purpose, primary-media role, intended audience effect, and continuity needs. Present playable before/after context plus any corrected transcript and scene map. Stop for approval of cut decisions.
3. **Creative-plan review.** Inspect the source evidence appropriate to the proposed edit: stills and motion windows for reframes, annotations, masks, action continuity, sync points, performance moments, or handoffs. Define the editorial intent, visual grammar, shot-scale variation, primary-media role, authored additions, motion vocabulary, captions when applicable, transition relationships, and sound policy. Create the storyboard, asset plan, design system, exact timeline events, execution plan, and representative pilot target. Each beat includes entry/development/exit progression plus caption and sound policy. Detect unintentional staging repetition, but allow repetition when it serves rhythm, format, identity, or meaning. Stop for approval before scaffold or authored JSX.
4. **Pilot and scene review.** Scaffold once. Implement the approved representative scene first when reviewOrder says so, including a focus swap and the riskiest applicable sync/mask behavior. Typecheck and provide `npm run studio`, SceneNReview and master-frame checkpoints. Stop for feedback. Continue in recorded reviewOrder, one scene at a time unless batching was delegated.
5. **Master and export review.** Review the full composition, audio, captions, joins, masks and late-recording synchronization in Studio. Stop for export approval. Render the reviewed master, exact last-frame PNG and captions; run technical and audio QC. Delivery acceptance does not authorize external publishing.

Engineering fixtures and skill tests do not require creative review gates. Draft review renders are allowed only through the guarded draft path and stay under `review/`; they do not satisfy final export approval.

## Built-in screen/presenter layout mode

The following applies only when using the bundled synchronized screen/presenter renderer. Plan explicit layout states: `screen-focus`, `presenter-focus`, `balanced`, `screen-only`, or `presenter-only`. Layout changes resize and move stable media layers on the same compiled clock. They must not restart, pause, duplicate or independently seek a parallel recording.

For a chronological recording, preserve layout continuity as well as source continuity. An opening layout event may declare `fromLayout` to interpolate from the predecessor's settled camera state instead of jumping at scene frame 0. Use this handoff only when it supports the incoming spoken idea. A continuous narration boundary does not justify a generic whoosh; every cue needs a named narration or visible-action reason and a listening acceptance criterion.

Use screen focus for actions and results that need to be read. Use presenter focus for theory when the screen remains useful context. Use balanced framing when both carry meaning. Choose panel corners around the actual UI and caption safe area. Return focus before an important interaction, and allow enough time to inspect results. Do not add focus swaps at a fixed interval.

If only a flattened composite exists, cropping can enlarge visible regions but cannot restore hidden screen pixels or an independent high-resolution presenter. Record and review that limitation rather than pretending the sources are separable.

## Source-bound annotations, when used

For interfaces, documents, objects, people, or regions tracked by source geometry, every annotation identifies an inspected source frame and time, a normalized rectangle in source-media coordinates, a clip-local active range, the visual change that invalidates it, and a nearby-frame check. Transform it with the same media geometry. End or re-anchor it when the target moves, the shot changes, or the geometry becomes stale. Avoid covering the subject the annotation is meant to identify.

Treat baked-in bars inside footage separately from the composition canvas. The approved design-system background must drive the master and clip containers. When captions are present, use design-system `fontScale`, padding/radius, and `bottomInset`, with the execution safe area authoritative for collision checks.

## Review evidence and limitations

Contact sheets support composition and candidate discovery. They do not establish continuous masking, exact cursor timing, lip sync, cut audibility, delivery quality or pacing. Inspect short playback windows for event timing and the actual combined playback for synchronization. OCR, frame differences and audio correlation produce candidates with recorded coverage and confidence; they never prove absence of sensitive content or authorize a cut.

The scaffold creates `SceneNReview` and `BoundaryN` master-clock slices. Review every affected boundary after shared source, caption, background, master-layout, timing, or transition changes. After replacing an overlay system, search imports, mounted render sites, and old SFX branches, then inspect former event frames; deleting or rewriting one component does not prove the legacy layer is gone.

Each known retained sensitive region needs a source-time range, source-coordinate geometry, disposition and rendering treatment. Apply protection with the same source transform used by the footage and check it at full output resolution. Final sign-off identifies the rendered artifact reviewed; it does not claim that an automated scan found every possible disclosure.
