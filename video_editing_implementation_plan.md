# Recorded-video editing track: implementation plan

Status: baseline recorded-edit track implemented in `.agents/skills/video-production` on 2026-09-22. The contract, ingest, compiler, Remotion scaffold/renderer, v3 review guards, draft review support, tests, and documentation described below are present. Automated audio-correlation sync, OCR discovery, cursor tracking, and NLE interchange remain future extensions; the implemented path accepts reviewed manual evidence for those decisions.

This plan extends the local `.agents/skills/video-production` skill. It incorporates the user's clarification that parallel screen and talking-head recordings are the main format, including recordings approximately 20 minutes long. It supersedes the earlier recommendation to prioritize sequential footage. The original brainstorming document remains at [video_editing_workflow.md](video_editing_workflow.md).

## 1. Confirmed scope and working assumptions

### Confirmed requirements

- Edit supplied recordings; preserve the original media and recorded performance.
- Support talking-head-only, screen-only, parallel screen plus talking head, and sequential combinations.
- Treat parallel recordings as the primary use case. Similar durations do not establish synchronized starts or matching device clocks.
- During demonstrations, give the screen most of the composition and place the presenter in a corner.
- During theory, enlarge the presenter and move the screen into a smaller corner panel, with purposeful animated movement between arrangements.
- Support long recordings, multiple app/monitor views inside a screen recording, and content-driven output length.
- Retain the existing skill's collaborative review approach, with durable decisions and feedback.

### Proposed defaults, adjustable per project

- One active presenter track and one active screen track at a time; files may contain camera output captured through recording software.
- Separate source files are available for independently repositioning both views. A flattened recording is also accepted, with limitations described below.
- Start with horizontal 1920 × 1080 output at 30 fps when the user does not specify a format. Preserve native source dimensions and timestamps in the manifest. Other integer output rates and aspect ratios remain configurable.
- Use the cleanest approved voice stream as primary audio; do not automatically mix duplicate microphones.
- Normal-speed chronological editing is the first release. Synchronization correction is supported; creative speed ramps and extensive rearrangement are deferred.
- Music and SFX default to none until the project plan chooses them. Animation does not automatically trigger a sound.
- Use a single project root, defaulting to `WORKSPACE/videos/<slug>/`; honor an explicitly selected path. Keep Remotion at that root to reuse existing path conventions. Shared environments and model caches stay under the workspace.
- Keep the first release local. OCR and other optional detectors report their availability; their absence does not prevent manually reviewed editing.

### Clarifications resolved by intake rather than blocking implementation

For each production, establish whether media is independent tracks or a flattened composite, which audio stream carries narration, whether separate voiceover exists, target format, languages, useful source intervals, and sensitive-content policy. These fields become part of the source/brief contract, rather than questions repeated at each gate.

## 2. Expected viewing behavior

The editor changes emphasis while both streams continue on the shared clock. A layout change must not restart, pause, duplicate, or resynchronize either stream.

| Layout state | Presenter | Screen | Intended use |
|---|---|---|---|
| `screen-focus` | Corner panel, preserving face framing | Large, readable screen viewport | Demonstrating an action or examining output |
| `presenter-focus` | Large primary panel | Smaller corner context panel | Explaining theory while no essential screen action needs attention |
| `balanced` | Substantial panel | Substantial panel | Explaining a relationship while both views matter |
| `presenter-only` | Primary view | Absent | Talking-head-only source or approved screen omission |
| `screen-only` | Absent | Primary view | No usable presenter coverage or intentionally full-screen demonstration |

Design each project’s actual rectangles, crop policy, caption area, corners, and focal positions in `design-system.json`. A state name alone does not establish a complete design.

For an initial 16:9 treatment, propose a presenter panel around 22–28% of canvas width during demonstrations and a screen context panel around 25–32% during theory. These are audition ranges, not fixed requirements. Screen context panels need not make all UI text readable; any detail the viewer must read must be promoted or annotated.

Layout transition behavior:

1. Anchor each emphasis change to a checked word, observed action, or explicitly reviewed source time.
2. Animate position, size, border radius, and focal crop continuously over a proposed 12–24 frames at 30 fps, calibrated in the pilot.
3. Keep stable media identities while changing geometry. Define z-order and overlap behavior so the shrinking view remains visible where intended.
4. Prevent panels from covering the active UI region or caption area. Choose alternate corners in the plan; avoid autonomous corner hopping during playback.
5. Distinguish panel enlargement from an additional digital punch-in. Preserve presenter headroom; do not stretch either recording.
6. When theory narration overlaps meaningful screen activity, preserve a readable screen or use a balanced layout. Transcript labels alone cannot select the layout.
7. Return to screen focus before the next important interaction. Retain sufficient reading time on completed results.

No layout change is required at a fixed time interval. A static screen can be appropriate while the explanation requires it.

## 3. Existing implementation and required changes

Paths in this table are relative to `.agents/skills/video-production/`.

| Existing component | Observed behavior | Planned treatment |
|---|---|---|
| `SKILL.md` and `references/collaborative-production.md` | New productions follow narration-first gates | Route explicitly between generated production and recorded editing; document editing-specific gates |
| `scripts/06_import_narration.py` | One contiguous trim per scene; first audio stream; mono 24 kHz conversion | Preserve existing behavior; add a separate recording ingest/mix path with explicit stream selection |
| `scripts/02_timestamps.py` | Scene WAV transcription; exports word/start/end; rejects longer no-word clips | Reuse transcription logic behind a recorded-source adapter that allows verified nonspeech ranges and retains available recognition evidence |
| `scripts/timeline.py` | Scene spans derive from narration duration; visual transitions do not shorten speech | Keep v2 compiler; add recorded timeline compiler with source mappings, shared cuts, and independent layout events |
| `scripts/workflow_v2.py` | Nonempty word coverage, fixed approval scopes, ordered scenes, fixed snapshot paths | Keep v2 validation; introduce explicit v3 recorded-edit validation and dependency-aware snapshots |
| `scripts/production.py`, `scripts/09_check_production.py` | Accept v2 only | Dispatch by version and track; reject unknown combinations |
| `scripts/03_scaffold.py` | Requires narration metadata and visual-only v2 marker | Add a recorded-edit branch before narration-specific checks; reuse safe-write behavior and package generation |
| `assets/Timeline.tsx` | Mounts speech once per scene; visual components own graphics | Keep v2 template; add a footage master that owns source playback, audio, captions, and continuous layout |
| `scripts/05_review_bundle.py` | Review renders require final render readiness | Add purpose-specific, bounded draft review support for recorded projects |
| `assets/production-export.cjs` | Guards master/hero export; reads compiled last frame | Add recorded-contract dispatch and draft-purpose guard; preserve v2 defaults |
| Existing captions, design tokens, asset manifest, audio QC | Useful shared infrastructure | Reuse after adapting inputs and retaining relevant validation |

The local scaffold currently pins Remotion packages to `4.0.526`. Implement against the installed/pinned version first. Any dependency upgrade requires a concrete compatibility reason and a separate regression check.

## 4. Architecture and timing contract

### 4.1 Shared clock and non-destructive edits

Use four explicitly named time domains:

1. **Source presentation time:** original stream timestamps, time base, start timestamp, and presentation orientation.
2. **Session time:** an uncut common reference clock for recordings representing the same session.
3. **Edited master time:** retained session intervals concatenated in approved order, with explicit sequential placements where necessary.
4. **Composition frames and audio samples:** deterministic render coordinates derived from the edited master.

Store authoring times as integer microseconds with an explicit origin. Preserve rational original frame rates/time bases in manifests. Convert into integer output frames once in the compiler, using a documented rounding policy; do not accumulate `ceil()` independently for hundreds of short cuts.

For an initial chronological edit, quantize cumulative output boundaries to the nearest frame and derive each segment duration by subtracting adjacent boundaries. Reject a segment that becomes empty. Record the resulting timing deltas. Audio sample placement derives from the same compiled boundaries, with residual adjustments at approved quiet boundaries. The master must not drift because each cut accumulated an extra fraction of a frame.

Example: retain session `[0, 60)` seconds and `[65, 120)` seconds. The second interval starts at output second 60. A screen action and spoken word at session second 70 both occur at output second 65. If the screen file started recording 0.42 seconds before the session reference, its source lookup is session time plus 0.42 seconds. The sign convention is explicit and tested.

The master duration follows retained footage intervals, including intentional silence. It is not the end time of the final word. Talking-head-only productions use the same mapping with no screen track.

### 4.2 Synchronization model

- Establish the reference clock from the approved primary recording/audio, with an explicit session zero.
- Store corresponding observations as `(sessionUs, sourceUs)` pairs, evidence, confidence, and review status. A valid common event is required; equal file length or unrelated gestures are insufficient.
- Use embedded same-container stream timing when applicable. Otherwise use shared audio correlation, visible/audible common markers, or user-specified anchors. Correlation confidence must reflect ambiguity and available common signal.
- Inspect start, middle, end, and discontinuities; for a 20-minute recording, begin with approximately five-minute checkpoints and add checkpoints where evidence indicates drift or gaps.
- Fit constant offset when supported. Otherwise use monotonic piecewise affine mapping within continuous recording sections. Split at stops, dropped stretches, or source discontinuities; do not interpolate across missing content.
- Store fit residuals and uncertainty, not merely a binary synchronized flag. Proposed warning tolerance is one output frame at checked anchors, subject to actual anchor precision. Lip synchronization still requires playback review.
- Do not extrapolate beyond confirmed usable coverage without a recorded decision.
- Compile derivative video aligned to the session clock for drift-corrected sections where required. Preserve original sources, mappings, conversion commands, and section boundaries. The compiler remains authoritative; the derivative is a replaceable rendering aid.
- Keep primary audio unaltered by secondary-camera corrections. If a separate voiceover was not recorded concurrently, plan explicit action-to-speech alignment; do not describe that as microphone drift correction.

A source gap produces an explicit coverage decision: cut the interval from all linked tracks, use an available single-view layout, or use an approved substitute/freeze. Never silently loop or hold a missing track.

### 4.3 Cut semantics

- A normal cut removes the same session interval from all linked visual tracks and primary audio.
- Screen activity, complete instructions, results, breathing, and cut audibility inform proposals. Detection never silently changes the edit decision list.
- Separate transcript spelling corrections from edits to spoken content. Text correction cannot create an unspoken word.
- Keep stable word IDs tied to original audio. Derive output word occurrences through the approved edit mapping; do not rerun recognition for every scene split.
- Reject cuts through word interiors unless manually resolved from actual audio. Use listening and waveform evidence to assess joins; timestamps alone do not establish phoneme boundaries.
- Preserve necessary silent actions and result-reading intervals. Verified nonspeech segments can have no captions and action-anchored beats.
- Default to linked hard cuts. If needed, use short audio edge fades that preserve intelligibility; crossfades require actual handles and may not overlap spoken syllables accidentally.
- J/L cuts, creative speed changes, and repeated/reordered source ranges are deferred. The schema uses stable clip IDs so these can be added without redefining source identity.

## 5. Project artifacts and authority

Use one project root and one `production-state.json`. Do not introduce a competing `state.json` or manually synchronized feedback database. A readable feedback report may be generated from state history.

Create files only as their stage becomes relevant. Raw sources, analysis media, working copies, and caches are excluded from Git; plans, source manifests, review decisions, and authored code remain versionable. Source filenames and paths are preserved as provenance without logging detected secret values.

| Artifact | Authority and required fields |
|---|---|
| `brief.md` | Audience, source relationships, target formats, audio choice, scope, project preferences |
| `source/manifest.json` | Stable source ID, relative staged path/original locator, content hash, role, streams, codecs, native size, rotation, time bases, start times, duration, frame-rate evidence, audio channels/rate |
| `source/derivatives.json` | Original IDs, hashes, normalization/alignment parameters, tool versions, output hashes, exact time mapping, valid coverage |
| `sync/map.json` | Session IDs, reference source/stream, paired anchors, continuous sections, fit parameters, gaps, uncertainty, decisions |
| `transcript/source-words.json` | Word ID, source/stream, original interval, text, recognition evidence when available, correction history |
| `analysis/observations.json` | Source switches, content classifications, activity/cursor candidates, observed actions, evidence intervals and review status |
| `analysis/cut-proposals.json` | Proposed ranges, rationale, linked word/action evidence, confidence, dispositions |
| `source/sensitive-regions.json` | Source ID, source interval, oriented source-coordinate geometry/keyframes, category, disposition; no plaintext secret values |
| `cut-plan.json` | Authoritative retained clips and sequence; stable clip ID, session ID, retained session interval, linked tracks, audio selection, optional approved coverage exception |
| `storyboard.json` | Directorial intent and scene references to retained clip IDs; no competing timing table |
| `design-system.json` | Existing tokens plus recorded-layout presets, safe areas, panel/crop/focal-point rules, motion defaults |
| `execution-plan.json` | Recorded-contract beats, speech/action/time anchors, layout events, annotation events, masks, implementation/acceptance notes |
| `edit-plan.json` | Recorded-contract sound decisions, mix targets, joins and explicit holds; no second set of source cuts |
| `asset-plan.md`, `asset-manifest.json` | Existing roles: requests, decisions, accepted assets, provenance and inspection |
| `implementation-plan.md` | Production-specific playbook referencing canonical plans, scene order, pilot target, review checkpoints |
| `production-state.json` | v3 recorded track, phases, revisions, pending review targets, snapshots, scoped decisions and feedback history |
| `src/timeline-data.json` | Generated clips, source lookups, frames, sample placements, scene boundaries, layout/mask/sound events, captions and total frames |
| `review/` | Contact sheets, bounded playback previews, sync/cut/layout/mask reports with exact input snapshots |
| `out/` | Master, final-frame PNG, subtitles, measured QC; optional distinct thumbnail |

Media directories: preserve raw files under `source/raw/`; use `cache/` for replaceable analysis/proxy files; stage renderable media under `public/media/`. Render references use stable IDs resolved to local paths. Portability checks verify all needed media is present. Editable delivery does not automatically authorize publishing raw sources or unmasked review artifacts.

### Proposed minimal authoring example

```json
{
  "version": 1,
  "track": "recorded-edit",
  "clips": [
    {
      "id": "clip-001",
      "sessionId": "session-main",
      "sessionRangeUs": [0, 60000000],
      "tracks": {"screen": "screen-01", "presenter": "presenter-01"},
      "primaryAudio": {"sourceId": "presenter-01", "streamIndex": 1}
    },
    {
      "id": "clip-002",
      "sessionId": "session-main",
      "sessionRangeUs": [65000000, 120000000],
      "tracks": {"screen": "screen-01", "presenter": "presenter-01"},
      "primaryAudio": {"sourceId": "presenter-01", "streamIndex": 1}
    }
  ]
}
```

Here stream index 1 is illustrative; ingest must discover the actual stream. The document’s version is its own schema version, distinct from production-state v3. Destination frames are generated and never hand-maintained alongside the source decisions.

Layout events reference a clip occurrence plus an anchor. For example, `layout-theory-01` can reference checked word ID `word-0142` in `clip-002`, target `presenter-focus`, a duration in microseconds, and an explicit corner choice. Deleting its anchor creates an unresolved event requiring replanning; the compiler must not attach it to an arbitrary nearby word.

## 6. Ingest, transcription, and inspection

### Ingest

1. Probe all relevant streams and verify decodability across the recording, not only the header. Record truncated/unsupported intervals as errors or bounded coverage problems.
2. Determine independent versus flattened inputs and audio ownership. If a presenter is already burned into a screen capture, classify that layout explicitly; do not create a duplicate presenter by assumption.
3. Inspect actual timestamps for variable frame rate and discontinuities. CFR normalization is a proposed working-copy strategy, with preserved real-time duration and source mapping.
4. Preserve native resolution and aspect ratio. Generate lower-resolution proxies for interactive review when useful, retaining equivalent duration, timestamp origin, orientation, and crop geometry.
5. Extract full-quality selected audio for mixing and a separate transcription copy. Proposed mix workspace is 48 kHz PCM; do not inherit mono 24 kHz transcription conversion as the only master audio.
6. Cache by source hash, parameters, and tool version. Write outputs atomically; failed operations cannot leave a successful manifest referring to partial files.

### Transcript and edits

Transcribe the selected primary voice track once per continuous section. Preserve available word probabilities/segment evidence without presenting them as calibrated correctness scores. Verify jargon, commands, product names, and mixed-language passages against audio. Mark unresolved terms and timing uncertainty explicitly.

Generate silence/filler candidates, then associate them with screen activity. A silence interval containing meaningful work is retained by default. Present the proposed cut in a short playable before/after context so the user can judge delivery. Do not require a new transcription pass for every layout change.

### Screen analysis and sensitive content

Use sampled frames and denser candidate-event windows to support classification and layout planning. Frame-diff detection yields candidates; it does not prove that an application switch occurred. Keep manual source-switch/action annotations fully supported.

OCR-assisted sensitive detection is optional automation over an explicit review process. Record scan intervals, sampling density, detector availability and limitations. A sampled pass cannot claim absence of single-frame exposure. Use expanded windows or full-frame examination in flagged intervals and record the remaining review coverage.

Cursor highlights initially use manually confirmed action times and coordinates, or supplied cursor metadata. Automatic tracking and click inference are enhancements; unavailable tracking must not produce invented click events.

## 7. Rendering and animated layout implementation

Add proposed templates under `assets/recorded/`:

- `RecordedTimeline.tsx`: owns compiled master time and retained clip scheduling.
- `FootageStage.tsx`: composes screen/presenter layers and their continuous geometry.
- `FootageLayer.tsx`: resolves approved derivatives, source trims, source-space crop and mask operations; visual source audio is muted.
- `LayoutTransition.ts`: pure functions resolving panel geometry, focal points, easing, z-order and clipping for a master frame.
- `SourceMask.tsx`: applies solid/blur/graphic mask strategies in source coordinates and time, before the panel transform.
- `RecordedAudio.tsx`: owns selected primary voice, optional system sound, sound cues, gain envelopes and approved cut smoothing.

Reuse or adapt `WordCaptions.tsx` through an input adapter. Captions receive compiled master time and remapped word occurrences; they do not reset when a layout changes.

Keep both video components mounted throughout a continuous retained clip while their containers animate. Layout events update geometry rather than replacing the underlying clip or changing its React identity. Splitting at actual edits and synchronization-section boundaries is valid, with exact contiguous source mapping where appropriate.

Use `@remotion/media` video/audio APIs supported by the pinned version. Verify trim units, source frame selection, mute behavior, playback correction, and preview/render parity in the initial spike. FFmpeg normalization and alignment can provide deterministic working media where direct playback mapping is unreliable.

Scene code owns annotations and specific creative additions. The master owns footage playback across scene boundaries. Provide master-context `SceneNReview`, `BoundaryN`, and `VideoFull` compositions that resolve the same source frames and mix at the same master timestamps. A scene boundary alone must not restart a full-length recording.

Each layout variant can have independent geometry while using the same cut decisions. Additional aspect ratios require their own layout/mask/caption review; they are not simple crops of an approved master.

### Flattened-media limitation

A flattened source may allow cropping and enlarging an existing presenter box, at reduced quality, while retaining the composite as the screen layer. It does not provide hidden screen pixels or an independent high-resolution presenter. Detect duplicate burned-in presenter views, missing underlying UI, and inadequate crop resolution during intake. Request separate recordings only when the desired result cannot be achieved acceptably; otherwise record an approved constrained treatment.

## 8. Masking and audio correctness

### Masks

- Geometry is relative to the oriented source image, with explicit units and transform order.
- Keyframes are evaluated using the source time actually displayed, including source mapping and approved freezes.
- Apply masks before layout scaling, screen zoom, and rounded viewport clipping. An enlarged screen must enlarge its protection consistently.
- Opaque coverage is the initial default for secrets. Blur strength is a reviewed alternative rather than a guarantee of unreadability.
- Include temporal padding appropriate to the observed entrance/exit and conservative spatial margins. Review moving regions through their full tracked interval.
- Validate planned coverage at every rendered output frame of known flagged intervals where feasible. This proves geometric coverage of known regions, not completeness of sensitive-content discovery.
- Mask any reused frame or thumbnail derived from a flagged source range. A source reused elsewhere retains its sensitive-region references.

### Audio

- Select one primary voice stream per clip; duplicate embedded voice streams remain muted.
- Keep system audio separately selectable when available. If voice and system audio are already mixed, record the inability to independently rebalance them without additional processing.
- Keep audio continuity through layout changes. Panel size cannot alter gain or mute state.
- Review cuts for clipped words, breaths, clicks, and room-tone changes. Avoid asserting that a mathematically smooth fade sounds natural.
- Plan mix adjustments before final playback review. Material changes after review reopen audio/master review.
- Reuse `10_audio_qc.py` against the project's documented loudness/peak targets. Measurement is evidence alongside listening.

## 9. Review state, preview permissions, and change propagation

Introduce `production-state.json` version 3 with `track: recorded-edit`. Leave existing v2 projects on their current contract; do not translate old approvals into a different scope.

Proposed phases: `intake`, `source-review`, `edit-review`, `planning`, `plan-review`, `implementation`, `scene-review`, `final-review`, `delivery`.

| Review | Concrete target | What approval permits |
|---|---|---|
| Source review | Brief, source roles, primary audio, usable coverage, synchronization evidence and initial sensitive-content inventory | Prepare a cut proposal using accepted source relationships |
| Rough-cut review | Corrected transcript, cut decisions with playback context, scene/chapter map, unresolved findings | Plan the approved retained material |
| Refined-plan review | Layout/storyboard, exact emphasis events, masks, assets, mix, implementation steps, pilot and scene order | Scaffold and implement the agreed pilot |
| Pilot review | Representative master slice with synchronized video, an edit, layout swap, captions, and a mask if applicable | Continue implementation in the recorded review order |
| Scene/chapter review | Bounded master slices and join context | Advance the approved scope; batching only when explicitly delegated |
| Master review | Full playback using intended final mix, output framing and caption behavior | Export the reviewed master and related deliverables |
| Delivery acceptance | Rendered master and QC evidence | Record final completion; does not authorize external publication |

Source-review approval records detection evidence and outstanding items; it is not final masking sign-off. Refined-plan approval requires a concrete treatment for each known retained sensitive region. Final sign-off refers to the actual rendered output and its hash.

Editing scenes may use stable string IDs internally; map them to human-facing `SceneN` compositions in the compiled output. Define `reviewOrder` explicitly so an interior pilot does not require fake approvals for earlier chapters. Preserve sequential review for the remaining scenes unless the user delegates a batch.

### Draft preview rendering

Add a draft-only readiness operation that validates inputs and the current review target without requiring approval of the artifact being created for review. It permits local bounded review media, labels it as draft, writes only under `review/`, and records its input snapshot and coverage. An unresolved sync/mask issue is shown in the review report; it cannot pass final export readiness.

Draft preflight checks differ by stage: a rough-cut preview requires accepted source relationships and a valid candidate cut plan; a pilot preview requires the approved refined plan and implemented slice. It cannot accept arbitrary output paths or claim final approval. Draft review media stays local and may contain sensitive material awaiting disposition. Production review instructions govern use of this mode; the mode does not grant permission to upload anything.

### Invalidation rules

- Source replacement/hash change invalidates dependent mappings, analysis and reviews.
- Sync changes invalidate derived clips, affected caption/action mappings, masks, layouts and reviews using those intervals.
- Cut changes rebuild the master, captions, downstream placements and review windows. Locally unchanged scenes may retain content evidence, but shifted joins/global sound and master approval require re-review.
- Mask changes reopen all occurrences of the affected source regions and affected master outputs.
- Shared layout or renderer changes reopen every composition that uses the changed helper.
- A local annotation change reopens its scene and affected joins; it does not automatically invalidate unrelated source analysis.
- Subtitles, hero images, previews and thumbnails record the compilation revision they derive from.

Implement snapshot dependency manifests rather than hashing every large file repeatedly at every gate. Cache source content hashes only with a validated file-identity policy; rehash changed files and reverify authoritative sources before final export. Snapshot approval remains tied to exact reviewed inputs, never merely a matching revision label.

## 10. Skill and script organization

Keep the skill entrypoint short: shared purpose and constraints, then a track selector. Generated productions follow the existing narration-first references; recorded editing follows the new reference. A recorded project does not initialize Kokoro unless newly generated narration is explicitly requested.

Proposed new references:

- `references/recorded-video-editing.md`: production stages, intake, layout direction, reviews, fallback decisions.
- `references/recorded-timeline-contract.md`: source/session/output time, schemas, synchronization, cuts, rendering ownership and validation.

Proposed executable modules and entrypoints:

| New path under `scripts/` | Responsibility |
|---|---|
| `recorded_contract.py` | Schema validation and canonical IDs/units |
| `recorded_ingest.py` | Probe/decode reports, immutable staging, audio extraction, derivatives/proxies |
| `recorded_sync.py` | Anchor observations, fit, coverage, drift report and aligned derivatives |
| `recorded_analysis.py` | Transcription adapter, cut candidates, contact sheets, optional detector adapters |
| `recorded_timeline.py` | Compile cut/sync/layout/mask/audio/caption decisions into one master schedule |
| `recorded_workflow.py` | v3 phases, readiness, review targets, dependency snapshots and invalidation |
| `recorded_qc.py` | Source mapping, coverage, captions, mask geometry, render reconciliation and reports |

Expose subcommands only where they support an actual stage; avoid a large collection of numbered scripts whose names prescribe execution order. Reuse existing utilities where they are stable, rather than duplicating FFmpeg execution, JSON errors or file checks.

Extend the existing scaffold, review bundle, preflight dispatcher and export guard to call these modules. Copy all needed validation modules into generated projects, as the current export guard does, and record their contract/tool versions. Existing authored projects are never refreshed automatically.

## 11. Implementation units and dependencies

All unit paths are proposed changes under the local skill unless identified as fixtures. Units describe implementation work; this planning request does not execute them.

### U1 — Prove parallel playback and animated emphasis

**Dependencies:** none; use isolated fixtures and the pinned Remotion version.

Create a short synthetic presenter/screen pair with readable timecodes and common audio/visual markers. Include a known offset, one linked cut, a screen-focus → presenter-focus → screen-focus sequence, and a silent action. Build the smallest master that demonstrates continuous playback while both viewports animate.

**Evidence:** decoded source timecodes and audio markers agree before/after cuts and during animation; each voice is mounted once; draft playback and render agree. Record whether direct trim/playback mapping works or aligned derivatives are needed. This is an engineering fixture, not a creative user approval gate.

### U2 — Define recorded schemas and version dispatch

**Dependencies:** U1 findings.

Implement `recorded_contract.py`, minimal artifact templates, v3 dispatch in `production.py` and `09_check_production.py`, and validation of time domains, source coverage, stable IDs and unknown fields. Keep v2 handling intact. Include schema examples for parallel, solo, sequential, gaps and nonspeech intervals.

**Evidence:** well-formed examples validate; wrong time domains, absent streams, empty clips and unknown contract combinations fail with actionable diagnostics. Existing v2 contract tests retain their behavior.

### U3 — Ingest, source identity, proxies and synchronization

**Dependencies:** U2.

Implement `recorded_ingest.py` and `recorded_sync.py`. Support explicit audio selection, rational source rates, VFR, stream start offsets, manual anchors, candidate audio correlation, piecewise mappings, gaps and derivative provenance. Keep raw files unchanged.

**Evidence:** known offset/drift fixtures recover the mapping within documented uncertainty; a discontinuity is not interpolated through; derived duration and mapping are reconciled; interrupted writes cannot create valid partial assets. Unsupported sources yield bounded actionable errors.

### U4 — Transcript, inspection, and reviewable cut proposals

**Dependencies:** U3.

Implement source-level transcription with stable words, corrections, candidate cuts, activity annotations, sensitive-region registry and contact sheets. Initial detection can be manual-assisted. Define before/after review intervals and their source references here; the playable cut-preview renderer is implemented in U7 using U5's mapping.

**Evidence:** retained silent actions survive; transcript corrections preserve source identities; a technical-term correction does not fabricate timing; detected candidates remain proposals until disposition. Detector absence and analysis coverage are visible.

### U5 — Compile the authoritative edited timeline

**Dependencies:** U2–U4.

Implement `recorded_timeline.py`: linked cuts, sequential placements, source/sync mapping, cumulative frame quantization, sample placement, remapped captions, scenes, layout/mask/action events, sound anchors and total duration. Compile the same inputs deterministically. Preview and final render consume this output.

**Evidence:** the worked two-interval example maps correctly; many short edits do not accumulate rounding drift; out-of-range media and deleted anchors fail; no-word segments compile; every interval’s source provenance can be traced.

### U6 — Build reusable layouts, masks, audio and scaffold integration

**Dependencies:** U1, U5.

Add the proposed recorded templates and the recorded branch in `03_scaffold.py`. Implement layout interpolation, source-aware masks, manual screen annotations, focal crops, captions and selected audio. Generate master/context review compositions. Preserve authored files on refresh.

**Evidence:** both views continue through repeated focus swaps; UI/captions remain clear at planned checkpoints; masked areas stay covered through scaling and movement; missing coverage uses an approved fallback; visual tracks never duplicate narration.

### U7 — Implement review scopes, pilot order, draft guards and invalidation

**Dependencies:** U2, U5–U6.

Implement `recorded_workflow.py`, source/edit/plan/scene/master/delivery decisions, explicit pilot order, dependency snapshots and change propagation. Extend `05_review_bundle.py` and `production-export.cjs` to distinguish draft review from final export. Finish the rough-cut preview path.

**Evidence:** a draft can be created for a pending review without final approval; final export still fails on unresolved or stale prerequisites; an interior pilot works without invented earlier approvals; source, sync, cut, mask and shared-helper edits invalidate the correct dependent targets. Bundled project guards run independently of the installed skill directory.

### U8 — Long-recording performance and output QC

**Dependencies:** U3, U5–U7.

Implement `recorded_qc.py`, caption sidecars, final-frame export, manifest reconciliation, proxy/full-quality selection, and resumable analysis keyed to dependencies. Measure a two-track 20-minute synthetic or consented fixture with representative source dimensions and codec.

**Evidence:** start/middle/end synchronization and late source seeking remain correct; render failure/resume does not use stale output; memory, disk usage, analysis time and render time are reported with hardware/settings. Validate full-quality mask and text readability separately from proxy previews. No fixed performance promise before measurement.

### U9 — Integrate skill instructions and validate realistic use

**Dependencies:** U1–U8.

Update `SKILL.md` description/routing, shared collaboration/pipeline references, the new recorded references and meaningful fixtures/tests. Reconcile the brainstorming workflow’s broad sync requirement, duplicate state files, nearest-checkpoint rule, blanket word anchors, and excessive gate splitting with this contract.

**Evidence:** an agent following the skill routes the four supported formats correctly, skips TTS setup for recorded footage, stops at concrete production reviews, and handles missing audio, flattened inputs, uncertain sync and nonspeech intervals without inventing evidence. Run the skill validator and existing production regressions. Forward behavioral evaluation may use an independent agent only when separately authorized or applicable instructions allow it.

Dependency sequence: U1 → U2 → U3 → U4 → U5 → U6 → U7 → U8 → U9. U4 establishes review inputs; U7 supplies their playable previews after the shared compiler and renderer exist. There is no authorization to spawn parallel agents implied by this sequence.

## 12. Verification and release criteria

Use behavior-based fixtures with known timing/geometry; do not use tests that merely match document wording or generated filenames.

| Case | Required evidence |
|---|---|
| Parallel tracks with offset | Common marker matches at output start, middle and end |
| Gradual drift and recording gap | Fit is accurate within evidence precision; gap is explicit; no interpolation across it |
| VFR and mixed 29.97/30/60 fps sources | Presentation time preserved; deterministic output mapping; no growing A/V offset |
| Hundreds of short cuts | Final duration matches compiled cumulative boundaries; captions/actions stay aligned |
| Theory/demo focus swaps | No clip restart, freeze, dropped audio, duplicate voice, unwanted aspect distortion or caption overlap |
| Talking-head-only/screen-only | No absent-layer assumptions; correct audio and captions; meaningful nonspeech permitted |
| Sequential combination | Correct ordering and explicit audio handoff; no artificial simultaneous-sync prerequisite |
| Moving sensitive region during zoom | Known region fully covered over its output interval, including entry/exit and reused frames |
| Flattened source | Limits reported; no invented independent footage or hidden screen recovery |
| Stale source/cut/mask/shared helper | Correct review dependencies become stale; final export is rejected until resolved |
| Twenty-minute dual-track project | Correct late seeking and final duration; measured memory/disk/runtime; playback review of representative joins and whole master |
| Existing generated production | v2 schemas, scaffold and guard behavior remain compatible |

Current regression commands, to run during implementation with the existing dedicated environment:

```sh
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_pipeline.py
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_extensions.py
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_production.py
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/test_workflow_v2.py
```

`WORKSPACE` and `SKILL` above are path placeholders, not literal commands ready to paste. Add proposed `test_recorded_timeline.py`, `test_recorded_workflow.py`, and focused media integration fixtures when implementation exists. Generated projects also run `npm run typecheck` and authorized bounded render checks. Synthetic fixtures should use FFmpeg-generated counters/markers; real private recordings are not checked into the test suite.

Release requires the primary parallel workflow and all three fallback formats to work end to end, v2 compatibility checks to pass, stale approvals to block export, and a representative long-duration media run. Automated checks do not establish pacing, delivery quality, or complete sensitive-content discovery; record actual listening/playback/user review separately.

## 13. Risks, unknowns, and decision points

| Factor | Impact | Resolution / work affected |
|---|---|---|
| Separate versus flattened recordings | Determines independent layout quality | Intake plus U1/U3; flattened limitations are explicit |
| Silent screen track without common marker | Automatic sync may be impossible | Manual source/session anchors; blocks affected parallel intervals, not all project analysis |
| Voiceover recorded separately from actions | Alignment is an editorial task | Map speech/actions explicitly; no false drift model |
| Burned-in captions or existing presenter overlay | Can duplicate captions/presenter or hide UI | Inspect sources; choose constrained treatment or request independent material |
| Codec, HDR/color, orientation and timestamp differences | Can break decode, color consistency or geometry | U3 normalization policy with visual inspection; preserve metadata and originals |
| Mixed languages and technical jargon | Transcript/caption accuracy | Explicit language/model choice and correction review; automatic language quality is not guaranteed |
| Clipped/noisy or mixed audio | Limits cleanup and independent balancing | Audition original and optional processed copy; report irrecoverable defects |
| Moving sensitive regions and brief flashes | Detection/tracking completeness uncertain | Manual-assisted registry, coverage reports, conservative masking and final review |
| Hardware, storage and source resolution | Controls 20-minute feasibility and throughput | U8 benchmark; proxy/caching policy and available-space checks |
| Exact animation style and corner choice | Affects readability and visual quality | Refined plan and representative pilot; adjustable tokens rather than hardcoded style |
| Full NLE project interchange | Different delivery scope | Initial deliverable is editable Remotion plus source mapping, not an invented Premiere/Resolve project |

No missing preference blocks writing schemas or the synthetic U1 spike. Actual representative recordings are required before claiming real-world sync, visual quality, transcription or performance validation. Dependency/model downloads may need network access; reuse the existing workspace environment and caches and install only the dependencies required for recorded editing.

## 14. Compatibility, delivery, and rollback

- Add v3 recorded projects without migrating existing v2 projects or their approvals.
- Keep track/version checks explicit. A project marker identifies recorded footage versus generated visual-only scenes.
- Keep raw media immutable. Deleting failed derived outputs must never delete originals or authored plans.
- Record tool/schema versions in derivatives and compiled manifests. If a renderer/library change alters source selection, regenerate affected media and reopen impacted reviews.
- New project scaffolds bundle their guards and needed dependencies. Existing projects keep their saved helpers until an explicit, reviewed refresh.
- If a release regression affects recorded editing, disable that route for new work while preserving v2 behavior and existing project artifacts; do not silently fall back to unsynchronized footage.
- Deliver the master MP4, exact last-frame PNG, final-cut SRT (optional VTT), editable Remotion project, required media/provenance, and QC report. A designed thumbnail is a separate optional deliverable.
- Drafts, outputs and subtitles record the input revision/hash. Final mask sign-off records who reviewed which rendered artifact and when. Publishing/uploading remains separate authorization.

## 15. Evidence and next implementation action

This document was prepared from the supplied workflow, the user's parallel-layout clarification, local skill references, and direct inspection of the current importer, timestamp extractor, timeline renderer/compiler, scaffold, review bundle and state/export guards. Implementation now includes the v3 recorded contract and a real synthetic parallel-footage smoke render. The smoke test verified a linked cut, focus transition, source mask, captions schedule, selected audio, guarded MP4 export, 330 decoded video frames at 640 × 360, and the exact final-frame PNG. It does not establish creative quality or performance on private 20-minute sources.

Current primary documentation consulted for implementation constraints:

- [Remotion Video](https://www.remotion.dev/docs/media/video): footage embedding, trims, playback, buffering and failure behavior; verify against the project's pinned package before implementation.
- [Remotion Audio](https://www.remotion.dev/docs/media/audio): independent audio rendering controls.
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html): timestamp, frame-rate, audio and media processing primitives.
- [FFmpeg command documentation](https://ffmpeg.org/ffmpeg.html): stream selection and CFR/VFR behavior.

The next executable unit is U1: prove continuous synchronized parallel playback, a linked cut, and an animated screen/presenter emphasis swap using a short isolated fixture. Its outcome determines the detailed playback/derivative strategy before the remaining integration work.
