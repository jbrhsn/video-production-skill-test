# Recorded-video editing

Read this reference when the user supplies screen recordings, talking-head footage, or both. The main case is synchronized parallel recordings: the screen stays large during demonstrations and the presenter grows during theory while the screen moves into a context panel. Sequential and single-source edits use the same contracts with fewer active tracks.

## Route and outcome

Use production-state version 3 with `track: recorded-edit`. Do not run Kokoro or the narration-first pipeline unless the user separately requests generated narration. Preserve raw sources and build edits through time mappings; never trim originals in place. Deliver an editable Remotion project, reviewed MP4, final-frame PNG and final-cut captions when speech exists.

Read [recorded timeline contract](recorded-timeline-contract.md) before ingest, synchronization, cut planning, scaffolding or source-backed JSX. Read the shared [audio direction](audio-direction.md), [platform composition](platform-composition.md), [transitions](transitions.md), and [creative review](creative-review.md) only when their subject applies.

## Required gates

1. **Source review.** Ingest and probe sources, establish roles and primary audio, inspect decodability, create synchronization evidence where tracks overlap, and record initial sensitive-content findings. Present the concrete source/sync report and stop for approval. Similar duration does not prove synchronization.
2. **Rough-cut review.** Transcribe the primary voice where present, correct terminology without inventing speech, propose non-destructive cuts, retain meaningful silent screen actions, and present playable before/after context plus the scene map. Stop for approval of cut decisions.
3. **Refined-plan review.** Inspect contact sheets and relevant motion windows. Create the storyboard, project design system, exact layout events, masks, annotations, sound choices, execution plan and representative pilot target. Stop for approval before scaffold or authored JSX.
4. **Pilot and scene review.** Scaffold once. Implement the approved representative scene first when reviewOrder says so, including a focus swap and the riskiest applicable sync/mask behavior. Typecheck and provide `npm run studio`, SceneNReview and master-frame checkpoints. Stop for feedback. Continue in recorded reviewOrder, one scene at a time unless batching was delegated.
5. **Master and export review.** Review the full composition, audio, captions, joins, masks and late-recording synchronization in Studio. Stop for export approval. Render the reviewed master, exact last-frame PNG and captions; run technical and audio QC. Delivery acceptance does not authorize external publishing.

Engineering fixtures and skill tests do not require creative review gates. Draft review renders are allowed only through the guarded draft path and stay under `review/`; they do not satisfy final export approval.

## Visual direction for parallel footage

Plan explicit layout states: `screen-focus`, `presenter-focus`, `balanced`, `screen-only`, or `presenter-only`. Layout changes resize and move stable media layers on the same compiled clock. They must not restart, pause, duplicate or independently seek a parallel recording.

Use screen focus for actions and results that need to be read. Use presenter focus for theory when the screen remains useful context. Use balanced framing when both carry meaning. Choose panel corners around the actual UI and caption safe area. Return focus before an important interaction, and allow enough time to inspect results. Do not add focus swaps at a fixed interval.

If only a flattened composite exists, cropping can enlarge visible regions but cannot restore hidden screen pixels or an independent high-resolution presenter. Record and review that limitation rather than pretending the sources are separable.

## Review evidence and limitations

Contact sheets support composition and candidate discovery. They do not establish continuous masking, exact cursor timing, lip sync, cut audibility, delivery quality or pacing. Inspect short playback windows for event timing and the actual combined playback for synchronization. OCR, frame differences and audio correlation produce candidates with recorded coverage and confidence; they never prove absence of sensitive content or authorize a cut.

Each known retained sensitive region needs a source-time range, source-coordinate geometry, disposition and rendering treatment. Apply protection with the same source transform used by the footage and check it at full output resolution. Final sign-off identifies the rendered artifact reviewed; it does not claim that an automated scan found every possible disclosure.
