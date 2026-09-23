# Video production skill: implementation plan

Status: direct-overhaul foundation delivered and renderer-qualified. The deterministic canonical path is implemented; model-backed analysis, native NLE interchange, and render-observation instrumentation remain deliberately deferred until separately qualified.

Source: [video-production-skill-improvement-plan.md](video-production-skill-improvement-plan.md). Target: [.agents/skills/video-production](.agents/skills/video-production/SKILL.md). Prepared against the repository inspected on 2026-09-23.

## 1. Outcome and implementation strategy

Replace the former track-specific skill architecture with one AI-native production system supporting faceless standard, faceless editorial, recorded editing, and hybrid editorial editing. Preserve source truth, deterministic timing, editable delivery, asset provenance, scoped review, and guarded export throughout the expansion.

Implement the work as direct increments on the new contracts. Do not add migration adapters, compatibility shims, or new behavior to the former v2/v3 paths. Prove separate picture/dialogue scheduling with a real render early, then add editorial analysis, layered explanation, reusable styles, stronger QA, and advanced editing.

This document is the implementation ledger and remaining-work authority for the overhaul. The source improvement document remains the product vision. The implementation record below distinguishes delivered code, renderer-qualified behavior, and deferred work.

The foundation establishes the canonical route/project/source/timeline/style/event/QC/review artifacts. It schedules separate audio and video tracks, maps captions to dialogue occurrences, and blocks export when the current master lacks approval. The renderer qualification fixture proves a 600 ms J-cut against real media. The remaining work is limited to capabilities whose required detector, NLE, or production-scale evidence has not been obtained.

## 1A. Implementation record and follow-on boundary

The following code exists in the skill and is covered by the tests named here:

| Delivered capability | Implementation | Evidence |
|---|---|---|
| Direct route selection | `scripts/route_production.py` | `test_editorial_timeline.py` covers all four routes |
| Canonical project/source contracts | `scripts/contracts.py` | Contract validation exercised by new timeline/system fixtures |
| Independent editorial lanes | `scripts/editorial_timeline.py`, `scripts/compile_timeline.py` | 600 ms J-cut, repeat occurrence, overlap rejection, source-bounds tests |
| Deterministic caption mapping | `editorial_timeline.py` | Captions map to dialogue clips, including repeated source intervals |
| Remotion renderer/scaffold | `assets/EditorialTimeline.tsx`, `assets/EditorialVisuals.tsx`, `scripts/13_scaffold_production.py` | Scaffold integration and generated-project TypeScript typecheck |
| Real-media renderer qualification | `generate_renderer_fixture.py`, `qualify_renderer.py` | 78-frame Remotion MP4/PNG fixture: source frame 60 at output frame 48; audio J-cut at frame 30; last-frame still check within H.264 decode tolerance |
| Style grammar resolution | `assets/style-profiles.json`, `scripts/style_profile.py` | Twenty profiles; deterministic resolved digest and provenance test |
| Editorial evidence and decisions | `scripts/analyze_editorial.py`, `scripts/apply_editorial_decisions.py` | Silence, sentence, repetition, retake/context candidates, and explicit unavailable-detector result tests |
| Visual-story event rendering | `scripts/visual_events.py`, `EditorialVisuals.tsx` | Dialogue occurrence/re-entry validation and generated/event schedule test |
| Asset, source, audio, and delivery evidence | `probe_sources.py`, `process_asset.py`, `audio_production.py`, `export_interchange.py` | Source/derivative provenance, FFmpeg loudness evidence, canonical JSON/SRT handoff |
| QC, repair, tracking, and resume contracts | `qc_production.py`, `tracking.py`, `build_state.py` | Detector-coverage, bounded-repair, source-coordinate, and invalidation tests |
| Timeline QC and guarded export | `qc_timeline.py`, `run_qc.py`, `production_workflow.py`, `production-export-v1.cjs` | Bounds/caption findings and stale-master-approval test |

The following capabilities are deliberately adapter-gated and must not be represented as available until separately qualified: automatic forced alignment, diarization, face/cursor/UI detection, multicam selection, automatic reframing, and native OTIO/FCPXML import fidelity. The system records these as unavailable coverage rather than guessing. The delivered deterministic path includes real-media renderer qualification, source PTS/frame-rate probing, J-cut playback, positive-rate/freeze/generated lanes, the twenty-style catalog, visual primitives/events, asset lineage, evidence analysis, observation-aware QC, bounded repair records, source-coordinate tracking contracts, cache invalidation/resume state, SRT, and canonical interchange metadata.

## 2. Evidence from the current skill

Paths in this table are relative to `.agents/skills/video-production/`.

| Existing component | Observed behavior | Consequence for implementation |
|---|---|---|
| `SKILL.md`, `references/collaborative-production.md` | Generated production follows narration, asset/planning, active-scene, master, and export gates. | Carry the approval invariants into the canonical direct-overhaul policy. |
| `scripts/workflow_v2.py` | Validates state, snapshots, design system, accepted assets, and executable beats. | Retire it from the canonical route while carrying forward the useful snapshot and approval invariants. |
| `scripts/timeline.py` | Compiles the former generated edit-plan path. | It is retired from the canonical route; retain only as historical regression evidence. |
| `scripts/recorded_contract.py` | Source roles are screen/presenter/voice/system-audio; clips link screen/presenter tracks with primary audio over one session range. | A general timeline needs new source capabilities and independent track clips. B-roll must not be relabeled as a presenter. |
| `scripts/recorded_timeline.py` | Compiles clip boundaries cumulatively; derives source playback rate from sync sections; remaps each word to its first matching retained clip. | Repeated intervals need occurrence IDs and multiple caption mappings. Creative speed must remain distinct from sync correction. |
| `references/recorded-timeline-contract.md` | Supported production scope is normal-speed chronological retained ranges; J/L cuts, reorder/repeat and creative speed require extensions. | Incidental permissiveness in a validator is not support. Add explicit compiler, renderer, review, and test coverage. |
| `assets/recorded/RecordedTimeline.tsx` and recorded contract | Renderer contract centers on synchronized screen/presenter layouts, primary audio, masks, and source annotations. | Retire it from the canonical route; use it only as regression evidence for the former architecture. |
| `scripts/recorded_workflow.py` | v3 approval scopes include source/edit/plan/scene/video/delivery; snapshots use fixed artifact groups. | Every new editorial/style/tracking input must enter the correct approval dependency set. |
| `scripts/09_check_production.py`, `scripts/production.py` | Dispatch readiness by former state/track conventions. | Keep outside the canonical route; `check_production_v1.py` owns canonical readiness. |
| `scripts/03_scaffold.py`, `scripts/11_scaffold_recorded.py` | Scaffolds emit renderer/configuration plus copies of checker modules for project-local exports. | A new module must be packaged into generated projects, not merely importable from the installed skill. |
| `assets/production-export.cjs` | Runs the bundled readiness checker; renders `VideoFull`; hero uses `totalFrames - 1`. | Retain these guarantees and verify relocated projects with the bundled new checker. |
| `scripts/05_review_bundle.py` | Produces event-aware review artifacts and supports guarded recorded draft renders. | Extend for new timelines and QC without converting a render result into a human approval. |
| `scripts/10_audio_qc.py` | Measures an authorized mix against documented loudness/peak targets. | Add mastering separately; preserve measurement versus listening distinctions. |
| `scripts/07_index_assets.py`, `scripts/08_search_assets.py` | Technical inventory and curated token search already exist. | Extend asset selection and transformation lineage instead of creating another asset authority. |
| `assets/Whiteboard.tsx`, `assets/DoodleAssets.tsx`, `assets/WordCaptions.tsx` | Reusable drawing and caption helpers exist. Caption wrapping is heuristic. | Extend shared primitives and add actual rendered geometry checks where supported. |
| `references/long-form-production.md` | Chapters and continuity are documented; TTS is not a resumable scheduler. | Add content-based cache and scheduling behavior explicitly. |
| `scripts/test_*.py` | Five existing suites cover pipeline, extensions, production, v2, and recorded workflows; some tests use real media/tools. | Retain the suites and add targeted fixtures. Test execution and skips need recorded evidence. |

The canonical tests, legacy regression tests, generated-project TypeScript check, and a disposable real-media Remotion render were run during implementation. The fixture project is disposable; the existing horror project remains authored work and was not used as a fixture.

## 3. Scope, invariants, and assumptions

### Required invariants

1. Originals remain immutable. Derivatives retain source hash, recipe, tool version, and time/geometry mappings.
2. Narration or selected source dialogue owns speech timing. Generated explanation cannot silently stretch, restart, duplicate, or replace it.
3. Authored intent and source evidence remain separate from compiled schedules and rendered observations.
4. Every caption, source annotation, visual event, and audio event has an explicit time domain and traceable anchors.
5. Source/session gaps cannot be crossed through inferred synchronization. Unrelated B-roll does not require a fabricated session map.
6. Output frames and audio samples derive deterministically from one compiled master schedule.
7. Production autonomy reflects explicit user delegation. Choosing a style or receiving a passing QA report does not grant authority.
8. Export validates the current inputs and relevant evidence; raw renderer commands are not treated as enforcement boundaries.
9. The final image is exactly the last composition frame. The master retains full timeline context and mix.
10. Automated checks identify their coverage and limits. Unobserved behavior is `not_checked`, not a pass.

### Planning assumptions

- Keep Python and Remotion as the core implementation. Reuse the dedicated uv environment and the generated project's npm setup.
- Use the canonical project layout declared by `project.json`. Do not build compatibility paths for pre-overhaul project layouts.
- Use JSON for canonical machine artifacts. Human-authored YAML style profiles may be accepted later through a pinned parser that resolves to JSON.
- Keep optional speech, vision, alignment, and tracking models behind adapters. Core validation/scaffolding must not download ML models.
- Start the new renderer at the existing integer-fps boundary. Preserve rational source rates/time bases; add fractional output fps only after its renderer compatibility is demonstrated.
- Do not upgrade the currently pinned Remotion stack solely to implement the architecture. Evaluate an upgrade only when a bounded compatibility experiment establishes the need.
- Maintain guided production as the default. Implement producer/autonomous execution after their verification requirements work.
- Engineering fixtures are allowed to exercise production flows without creative approval pauses; fixture authorization must never become a normal export bypass.
- No publishing, remote asset purchase, external account integration, or hosted AI service is required by this plan.

## 4. Contract and artifact design

### 4.1 Version strategy

`project.json` v1 is the canonical project root. It names the production route, independent contract versions, artifact paths, renderer, and minimum compatible skill build. Do not treat all integers named `version` as one global version.

| Contract | Existing | Proposed evolution |
|---|---|---|
| Production state | `production-state` v1 | Route/policy-aware state with exact snapshots and decision evidence |
| Editorial timeline | `editorial-timeline` v2 | Canonical edit authority for all routes, including source and generated lanes |
| Source manifest | `source-manifest` v3 | Stream capabilities, source frame rate/audio layout, role tags, and derivative lineage |
| Execution plan | `execution-plan` v1 | Stable beat/event IDs and typed anchors |
| Editorial timeline | No general lane contract | `editorial-timeline` v2 |
| Compiled render timeline | Track-specific output | `render-timeline` v2 with source frame-rate and visual-event schedule |
| Style and brand | Design-system v1 | `resolved-style` v2, compiled into design tokens |
| Editorial evidence | Observations and cut-proposal artifacts | `editorial-analysis` v2 with explicit unavailable coverage |
| Visual events | Beat-local named events | `visual-story-events` v1 referencing beat-local events and timeline occurrences |
| QC | `qc-result` v1 | `qc-report` v2 aggregate with explicit detector coverage |

Write schema files under proposed `schemas/`, with valid/invalid examples under `tests/fixtures/contracts/`. Keep structural schema validation and semantic validation distinct. Cross-file references, source bounds, cycles, clock mapping, and approval freshness require code checks beyond JSON Schema.

Canonical entity coverage: Project, Track, Source, Narration, Transcript, Beat, Scene, EditDecision, VisualEvent, Asset, AudioEvent, StyleProfile, Timeline, ReviewState, QCResult, and Delivery. Entities can be nested in an owning artifact; they do not each require an independently editable file.

### 4.2 Authority and ownership

| Information | Authoritative input | Derived outputs |
|---|---|---|
| Original media, streams, timing evidence | Source manifest, immutable sources, sync maps | Proxies, thumbnails, waveforms, staged files |
| Corrected speech | Transcript with stable word IDs and source/narration time ranges | Phrase groups, captions, final-cut SRT/VTT |
| Edit choices | Editorial timeline plus accepted edit decisions | Render timeline, review windows, interchange |
| Story and behavior | Storyboard, beat/execution plan, visual events | Scene implementation and observable event checks |
| Style | Selected profile dimensions, brand, explicit project overrides | Resolved style, design system, TypeScript tokens |
| Selected asset suitability and provenance | Asset manifest and intake decisions | Search indexes and transformed assets |
| Permission and review | Production state with actual evidence/delegation | Readiness decisions, export authorization report |
| Observed result | Render/QC manifests tied to input and output hashes | Review report and delivery package |

Projects declare artifact paths in `project.json`. Avoid simultaneous editable copies such as both root and nested asset manifests; one canonical artifact owns each concern.

### 4.3 Time and identity contract

- Use half-open ranges `[start, end)` throughout.
- Keep source presentation timestamps, time-base fractions, stream start offsets, and rotation/geometry metadata from probing.
- Author recorded times in integer microseconds for compatibility. Use exact rational arithmetic internally for rates, source mappings, and cumulative boundaries.
- Quantize master boundaries once, using a documented tie rule and fixtures at rounding boundaries.
- Audio has sample-accurate trims and envelopes. Video frames must not become the only representation of audio edit points.
- A clip instance ID identifies an occurrence, independently of source ID and source range. Repeating a source interval creates a new instance.
- A caption instance references both its source word ID and selected dialogue clip instance. Repeated speech gets repeated captions; unused picture audio never creates captions.
- Anchors explicitly identify narration word/phrase, source range, clip instance, visual event, or master boundary. An anchor into repeated footage without an occurrence is ambiguous and fails validation.
- A freeze has a selected source PTS and explicit master duration. Zero playback rate is not used to encode a freeze.
- Store creative playback rate separately from source/session sync correction. Compile their composition explicitly, including pitch policy for audible speed changes.
- When an edit changes timing, recompile captions, events, reviews, and sound. Do not copy old master offsets into new artifacts.

### 4.4 General timeline

Proposed shape, illustrative rather than an already accepted schema:

```json
{
  "schema": "editorial-timeline",
  "version": 2,
  "sequence": {"id": "master", "fps": {"num": 30, "den": 1}},
  "tracks": [
    {"id": "dialogue", "kind": "audio", "role": "primary-dialogue"},
    {"id": "picture", "kind": "video", "role": "primary-picture"},
    {"id": "graphics", "kind": "generated", "role": "explanation"}
  ],
  "clips": [
    {
      "id": "dialogue-next-1",
      "trackId": "dialogue",
      "sourceId": "camera-b",
      "streamId": "audio-0",
      "sourceRangeUs": [12000000, 18000000],
      "timelineStartUs": 4400000,
      "playbackRate": {"num": 1, "den": 1}
    },
    {
      "id": "picture-next-1",
      "trackId": "picture",
      "sourceId": "camera-b",
      "streamId": "video-0",
      "sourceRangeUs": [12600000, 18000000],
      "timelineStartUs": 5000000,
      "playbackRate": {"num": 1, "den": 1}
    }
  ]
}
```

This fragment demonstrates a 600 ms J-cut: at the picture cut both audio and picture refer to source time 12.6 seconds. A complete fixture must also contain preceding coverage and an explicit end. The compiler must reject gaps or overlaps that violate the sequence's declared policy.

Tracks specify allowed overlap, compositing order, mix roles, and link groups. Primary dialogue overlap is rejected unless an intentional conversation/transition policy permits it. Picture overlap requires a supported transition or explicit layered composition. Nested sequences form an acyclic graph and carry time transforms. Source replacement retains the clip identity but changes source bindings and invalidates dependent geometry/timing evidence.

### 4.5 Review and autonomy

Production-state v4 records policy selection, explicit delegation scope, pending targets, immutable decision history, scene/sequence status, and snapshot dependencies. Keep user decisions, machine results, and agent choices as distinct record types.

| Mode | Required user reviews by default | Agent scope | Release prerequisite |
|---|---|---|---|
| Guided | Existing track-specific narration/source/edit, creative/assets, refined plan, scene/pilot, master/export gates | Work through current gate | Baseline compatibility and scoped snapshots |
| Producer | Creative direction, rough master, final export | Ordinary assets, scenes, and bounded corrections within delegated direction | Draft master path and mandatory QA available |
| Autonomous | Explicit initial delegation and its limits; additional input only for unresolved required choices | Local production and bounded repairs within that scope | Mandatory checks available, retry budget enforced, no unresolved blocking findings |

For guided mode, retain the current optional transcript-only review behavior; the vision document's simplified script gate does not add an extra mandatory gate. A change of mode does not rewrite earlier approvals or automatically authorize missing assets, purchases, publication, or a new narrative direction.

Proposed repair default: at most two attempts for one finding and six repair attempts per production job. Make budgets configurable in the delegated policy. Count no-progress attempts; stop with evidence when the budget or scope is exhausted. Missing required detectors cannot count as a successful autonomous run.

## 5. Delivery sequence and dependencies

| Work package | Outcome | Depends on | Suggested release |
|---|---|---|---|
| WP-00 | Baseline, fixtures, capability map | — | Foundation |
| WP-01 | Contracts, router, manifest, compatibility adapters | WP-00 | Foundation |
| WP-02 | Review policy, input dependencies, bundled export guard | WP-01 | Foundation |
| WP-03 | General timeline plus real J-cut slice | WP-01, WP-02 | Timeline preview |
| WP-04 | Full editing primitives, speed/freeze/nesting | WP-03 | Recorded editing |
| WP-05 | Composable styles, brand, reusable primitives | WP-01; WP-03 for recorded integration | Creative system |
| WP-06 | Editorial evidence and candidate edit decisions | WP-01, WP-03 | Editorial system |
| WP-07 | Collage processing, visual events, faceless editorial | WP-03, WP-05 | Creative system |
| WP-08 | Hybrid explanation and source re-entry | WP-04, WP-06, WP-07 | Hybrid preview |
| WP-09 | Visual, motion, caption and timeline QA | WP-03; expand with WP-04–08 | Verified production |
| WP-10 | Alignment, audio production and caption exports | WP-03; integrate WP-04 speed mappings | Audio system |
| WP-11 | Producer/autonomous orchestration and bounded repair | WP-02, WP-09, WP-10 and enabled-route tests | Verified production |
| WP-12 | Multicam, tracking, smart reframing, media selection | WP-04, WP-06, WP-09 | Advanced editing |
| WP-13 | Incremental production and long-form recovery | WP-02, WP-09, WP-10 | Long-form |
| WP-14 | NLE interchange and professional handoff | WP-04, WP-08; WP-12 for tracked edits | Interchange |
| WP-15 | Documentation integration and release qualification | All features included in a release | Every release/final |

WP-05 and WP-06 can proceed independently once their contracts are stable. Start QA instrumentation during WP-03 rather than waiting for WP-09. Add cache keys and dependency recording early; enable cache reuse only after WP-13 proves invalidation. Ship styles progressively: an editorial, tutorial, and minimal profile first, then the full requested catalog. This reconciles the source document's style-first milestone list with its higher priority for recorded timelines.

Do not assign calendar estimates until WP-00 establishes render cost and WP-03 retires the main media compatibility risks. Timeline playback, rendered geometry QA, tracking, and NLE fidelity have the greatest uncertainty.

## 6. Implementation work packages

All new paths in this section are proposed and relative to the skill root unless explicitly called project artifacts. Each package includes code, fixtures, relevant references/templates, and release notes for its behavior.

### WP-00 — Establish the baseline and integration fixtures

**Outcome:** a reproducible record of current behavior and known gaps.

1. Run the five existing suites through the dedicated uv environment. Record Python, Node, ffmpeg, Remotion, OS, tested revision, results, and skips.
2. Inspect fixture coverage for approvals, copied guard modules, narration quantization, source/session gaps, sync-rate correction, masks, and draft renders. Add only missing behavior checks needed for compatibility.
3. Build a synthetic fixture generator using local media tools: frame-numbered/color-coded clips, time labels, identifiable audio tones, silence, words with known anchors, and deliberate sync gaps. Include multiple stream rates and a VFR input.
4. Maintain small canonical fixtures for faceless, recorded, and hybrid routes plus projects with authored helpers. Use temporary project folders; preserve the horror project.
5. Add `references/capability-matrix.md` with implemented, experimental, unsupported, and dependency-required states.

**Acceptance:** baseline report identifies passing/failing/skipped checks without implying unavailable tests passed; both current production tracks have a reproducible small render fixture or an explicit environment blocker. Re-running fixture generation produces the same semantic source manifest even if container metadata is nondeterministic.

### WP-01 — Formalize contracts, routing, and migration

**Outcome:** explicit route selection and schema ownership for the canonical system.

1. Add `schemas/`, `scripts/contracts.py`, `scripts/project_manifest.py`, and `scripts/route_production.py`. Validate versions, IDs, ranges, references, capabilities, and paths.
2. Implement the four route choices using source presence, information carried by footage, requested explanation, platform/aspect, and delegated review scope. Emit route rationale and unresolved prerequisites. Fail unsupported combinations explicitly.
3. Deliver source-manifest v3 with stream capability separate from editorial role, source frame-rate/audio-layout evidence, derivative mapping, and provenance. Validate containment of local asset paths.
4. Define canonical artifact paths in `project.json`; reject ambiguous or incomplete project definitions at the boundary.
5. Define project layout references. Introduce only needed directories and ensure every artifact path is project-relative.
7. Add `references/production-routing.md` and `references/contract-versioning.md`; update intake templates only when this package is operational.

**Acceptance:** all four routes can be represented and validated; source audio alone and silent footage are handled deliberately; unknown versions fail; invalid project paths and duplicate IDs fail before compilation.

### WP-02 — Review policies and trustworthy export packaging

**Outcome:** new contracts have explicit review semantics and portable enforcement.

1. Implement `scripts/workflow_v4.py`, `scripts/review_policy.py`, and `scripts/dependency_graph.py`. Define readiness per route and mode. Initially enable guided mode; producer/autonomous policy parsing can precede execution support.
2. Keep `production.py` and `09_check_production.py` outside the canonical route; direct-overhaul projects use `check_production_v1.py` and canonical snapshots.
3. Hash selected transcript, timeline, style/brand, visual events, accepted assets, model-derived evidence used by decisions, source mappings, authored code, and relevant tool/config versions. Exclude generated QC reports from input hashes to avoid self-invalidating loops.
4. Keep conservative invalidation when dependencies are unknown. Narrow scene scope only after dependency evidence proves that shared code, assets, captions, and boundaries are accounted for.
5. Add a package manifest for all copied export-checker modules and schemas. Update both scaffolds and `assets/production-export.cjs` integration; test the bundled copy after the original skill directory is unavailable.
6. Preserve pending-review snapshots exactly. Treat implemented feedback separately from approval; record post-review changes and affected scopes.

**Acceptance:** source/style/timeline changes invalidate the right new approvals; changing shared source reopens affected joins/master; missing state, stale evidence, unsupported mode, and tampered dependencies block final export. Draft renders remain bounded and cannot be presented as final delivery. Legacy snapshots and guards remain compatible.

### WP-03 — General timeline and first rendered slice

**Outcome:** separate picture and dialogue lanes render deterministically with correct captions.

1. Add `scripts/editorial_timeline.py`, `scripts/timeline_compiler.py`, and a thin `scripts/compile_timeline.py` CLI. Keep the existing `timeline.py` name and implementation for legacy generated projects.
2. Implement lane/clip schemas, occurrence IDs, source/stream selection, master placement, bounds, intentional gaps, ordering, and explicit overlap policy.
3. Add a compatibility experiment for source PTS, audio trims, frame quantization, seeking, and playback rates using the pinned Remotion version. Use decoded numbered frames and tone onsets as evidence. If the renderer cannot reproduce a required mapping, propose a deterministic media derivative and retain its source mapping.
4. Add `assets/timeline/Timeline.tsx`, `MediaTrack.tsx`, and `AudioTrack.tsx`, plus a new scaffold entry point or explicit dispatch path. Keep muted visual playback and single ownership of dialogue.
5. Import a chronological v3 fixture; produce equivalent output. Then edit picture/dialogue timing to make a J-cut and L-cut with continuous lip sync on re-entry.
6. Compile caption occurrences from dialogue, and expose `SceneNReview`, boundary windows, full master, and exact hero frame.
7. Add `scripts/build_review_timeline.py` producing a local timeline report showing lanes, sources, trim ranges, edit points, and anchor mappings.

**Acceptance:** known 600 ms offset is 18 output frames at 30 fps; frame IDs and audio markers match compiled evidence; both legacy-equivalent and J/L-cut fixtures typecheck and render; no duplicate dialogue/captions; a bad source trim fails before render. Render bounds and total duration match the compiled master with documented container tolerance.

### WP-04 — Complete the richer editing contract

**Outcome:** explicit support for the advanced timeline operations in source-plan Phase 1.

1. Add reordered/repeated source ranges with unique instances; remap words and source annotations per instance.
2. Add audio-only/video-only edits, independent B-roll/cutaway lanes, music/SFX lanes, overlays, and explicit mix envelopes. Validate primary-audio ownership and intentional multi-speaker overlap.
3. Add constant positive creative speed, freeze frames, and pitch policy. Defer speed ramps/reverse playback unless separately designed; the requested speed-change capability is satisfied initially by constant-rate clips.
4. Add transition handles with source availability checks and explicit overlap semantics. Do not borrow unavailable frames silently.
5. Add nested sequences, flattening with reversible origin metadata, cycle detection, and configured depth/size limits.
6. Add manual multicam groups/switches, reaction inserts, source replacement, keyframed crop/transform, and a small declared filter set. Tracking-driven crops arrive in WP-12.
7. Split clips at synchronization discontinuities, compile any derivative map, and propagate edits into review and caption outputs.
8. Add `references/advanced-recorded-timeline.md` with supported operations, clock math, fixtures, limitations, and unsupported-operation errors.

**Acceptance:** each operation has a fixture proving visible/audible output and a relevant rejection case. Repeated dialogue repeats captions correctly; freeze does not freeze independent speech; nested source mapping survives flattening; replacing media invalidates prior mask/annotation evidence; speed preserves source bounds and selected audio policy.

### WP-05 — Styles, brand profiles, and reusable visual language

**Outcome:** reproducible production grammar with project-specific overrides and resolved tokens.

1. Add `scripts/resolve_style_profile.py`, `scripts/validate_style_profile.py`, `assets/styles/`, and brand/profile templates.
2. Define resolution order: base defaults → format → energy → visual language → platform → brand → explicit project override. Treat brand prohibitions and technical constraints as constraints requiring a recorded exception, not ordinary values erased by merge order.
3. Resolve editorial guidance, shot/cut density ranges, captions, camera/motion grammar, charts, media treatment, sound, and QC defaults. Store field provenance and a resolution digest.
4. For new projects, generate `design-system.json` and design tokens from resolved style. Move editable token choices into profile overrides. For legacy projects, preserve `design-system.json` as authority until explicit migration.
5. Add all ten faceless profiles: premium documentary, modern explainer, high-energy short, minimal product, whiteboard, data storytelling, newsroom, cinematic story, isometric/system, social infographic.
6. Add all ten recorded profiles: clean talking head, high-retention talking head, podcast clips, long-form podcast, screen tutorial, course/lecture, cinematic interview, product demo, gaming/reaction, executive/corporate.
7. Build proposed `assets/visuals/` primitives for typography, reveal/stagger/path/mask/count-up, camera movement, and captions. Reuse existing whiteboard helpers where practical.
8. Add comparison, timeline, process, system, metric, before/after, quote, map, document, hierarchy, cause/effect, and ranked-list scene grammars with data/geometry inputs and event IDs.
9. Document `style-system.md`, both style catalogs, and `brand-profiles.md`. Style pace ranges are editorial defaults/warnings, never automatic cut quotas or retention claims.

**Acceptance:** the same profile inputs resolve identically; conflicts are explained; all twenty profiles validate and declare actual prerequisites; representative editorial, tutorial, and minimal fixtures render distinct treatments from shared content. Brand typography/color/caption rules reach actual code. Changing a profile invalidates dependent render/review evidence.

### WP-06 — Editorial evidence and candidate decisions

**Outcome:** structured analysis supports an editor without changing source or silently applying cuts.

1. Add `scripts/analyze_editorial.py` as an orchestrator with adapters in proposed `scripts/editorial/`. Reuse existing observations/cut-proposal artifacts through an adapter.
2. Start with deterministic speech segmentation, silence detection, exact/local repeated phrases, and transcript boundaries. Record detector version, confidence, coverage, input hash, and source/session references.
3. Add optional semantic retake/topic/context analysis and screen-state/scene-change detectors. Unavailable detectors produce explicit `not_available` output.
4. Represent measured silence separately from editorial classification such as dramatic pause or technical wait. Keep emotional emphasis, hook usefulness, and topic inference labeled as judgments.
5. Generate candidate keep/remove/highlight/B-roll/generated-visual decisions with reasons, dependencies, alternatives, and surrounding playback context. A removal must account for incomplete sentences and references to earlier material.
6. Add self-contained clip candidates for podcast/social reuse, with context requirements and aspect-specific reframe needs.
7. Let an editor or authorized agent accept/reject candidates into the editorial timeline; persist that decision separately.
8. Add `references/editorial-intelligence.md` with source coverage, confidence, failure cases, and manual correction workflow.

**Acceptance:** a known retake is flagged, an intentionally repeated refrain is not automatically removed, a meaningful pause remains reviewable, and a context-dependent quote cannot become an approved standalone clip without resolution. Analysis reruns leave source and accepted timeline unchanged. Long recordings can be analyzed in bounded chunks with stable IDs.

### WP-07 — Editorial collage and visual-story events

**Outcome:** meaningful layered animation works for faceless production and supplies the hybrid building blocks.

1. Add the visual-event schema and `scripts/visual_events.py`. Each event names purpose, checked anchor, presentation mode, layer ownership, initial/action/result, named motion events, caption/sound policy, and observable acceptance.
2. Extend asset planning to background/midground/foreground roles without requiring all layers in every shot. Declare independent cutouts/parts needed by motion.
3. Add `scripts/process_editorial_asset.py` for deterministic crop, tonal treatment, optional halftone/grain, accent masks, and export. Background removal is an optional adapter with inspected output and a manual-mask fallback.
4. Preserve originals; cache derivative recipes by input hash and parameters. Register alpha, dimensions, crop margins, transform lineage, rights basis, and usable status in the existing asset system.
5. Add collage/map/document primitives to `assets/visuals/` using the resolved style and event clock. Render text and numerical evidence from authoritative data, not baked AI text.
6. Add `references/editorial-collage.md` and `references/visual-event-contract.md`. Clarify that stylistic motion does not prove the event's explanatory goal.

**Acceptance:** one fixture builds a map expansion, one reveals document evidence, and one compares computed values. Each has independent visible layer action, actual event frame checks, accepted assets, and a settled result. Flattened art that cannot perform the planned action fails asset readiness rather than receiving a generic pan.

### WP-08 — Hybrid editorial explanation

**Outcome:** source footage yields to a useful generated explanation and returns on the same speech clock.

1. Add `scripts/generate_visual_events.py` to validate and assemble proposed events from accepted editorial decisions. It may consume agent-authored choices; it must not pretend deterministic heuristics understand arbitrary semantics.
2. Support presenter-only, overlay, split, picture-in-picture, full generated scene, chart/map takeover, document sequence, archival montage, and source re-entry.
3. Require the takeover to identify a source dialogue clip occurrence and timing budget. If it needs more time, return a proposed edit/hold for review under the active policy.
4. Define re-entry state: source instance, PTS, camera/layout/crop, caption state, sound continuity, and transition handles. Keep dialogue mounted through the visual takeover.
5. Preserve face/performance when emotion, reaction, or credibility carries the story; record why generated explanation adds value when selected.
6. Add `references/hybrid-editorial-editing.md` and integrate both faceless and recorded creative references through the shared event contract.

**Acceptance:** presenter→map→presenter, chart, document, and system-diagram fixtures preserve speech and captions, re-enter at the correct source time, and include reviewed motion windows. A repeated phrase resolves to the requested occurrence. No audio restarts, caption duplication, or hidden duration expansion occurs.

### WP-09 — Visual, motion, caption, and timeline QA

**Outcome:** measurable findings with coverage, evidence, and honest uncertainty.

1. Introduce `scripts/qc/` modules for timeline, assets, layout, captions, motion, and recorded continuity; expose one `scripts/run_qc.py` entry point. Reuse existing duration/source/asset checks.
2. Define findings with rule ID, severity, scene/clip/event IDs, master range, expected/observed value, confidence, detector version, evidence paths, input/output hashes, and repair classification. Aggregate statuses are pass/fail/warning/not_checked/error.
3. Add renderer instrumentation for named layers/events and actual text/element bounds after fonts and media load. Compute clipping and caption collisions in output coordinates, including transforms and masks. Record coverage limits for arbitrary canvas, raster text, filters, and uninstrumented user components.
4. Add media load/placeholder/resolution/alpha checks and source-bound/transition-handle checks.
5. Compare rendered windows for black/flash frames, unexpected freezes, repeated frames, large crop jumps, off-screen action, and transition discontinuities. Account for declared holds, dark scenes, and intended cuts.
6. For planned event presence, combine instrumentation with before/during/after image evidence and event-specific expected changes. An emitted event marker alone cannot certify visible action; generic pixel change cannot certify meaning.
7. Use focused windows around events/joins plus declared sampling for discovery. Run every-frame geometry checks where claiming complete layout coverage; a sampled scan must report unsampled intervals.
8. Integrate findings into `05_review_bundle.py`, state readiness, and delivery reports. Calibrate thresholds against intentional negative fixtures and clean controls.
9. Add `references/visual-motion-qc.md` with detector limits and reviewer responsibilities.

**Acceptance:** injected text clipping, caption overlap, missing media, flash/black frame, invalid source bound, stalled event, and caption drift yield localized findings; clean controls and intentional still/dark shots avoid unjustified blocking errors. Reports distinguish measured geometry from inferred face/UI obstruction. Detector failure cannot produce a green report.

### WP-10 — Alignment, narration control, mixing, and captions

**Outcome:** accurate speech anchors and reproducible audio processing with observable limitations.

1. Add `scripts/align_speech.py` with backend interface, capability report, language support, confidence, and transcript/audio hashes. Select a local forced-alignment backend through a bounded experiment; retain existing Whisper recognition as an explicit fallback.
2. Keep corrected text authoritative; represent unaligned/uncertain spans. Build word, phrase, sentence, beat, and scene anchors without inventing precise timestamps.
3. Extend narration direction with pronunciation, pause, pace, emphasis, and emotional intent fields; compile only controls supported by the selected engine. Preserve unsupported intent as guidance or request supplied performance.
4. Add `scripts/mix_audio.py` and a recipe artifact for dialogue leveling, optional denoise/EQ/de-ess, music ducking, loudness normalization, and true-peak limiting. Feature-detect processors and record their versions.
5. Preserve source audio and produce versioned derivatives. Document filter latency, sample rates, trims, and how alignment remains valid. Re-align/recompile when processing changes timing.
6. Extend `10_audio_qc.py` integration to compare the authorized final mix with project targets and retain measurements. Listening remains separate evidence.
7. Add `scripts/export_captions.py` for SRT/VTT from the compiled dialogue occurrences and corrected transcript. Burned and sidecar captions share grouping/timing inputs.

**Acceptance:** alignment fixture reports uncertainty for a mismatched word; held/reordered/repeated/speed-adjusted speech maps correctly; mastering meets the fixture's declared target without clipping or duration drift; cuts remain intelligible on listening review; sidecar captions match the master and contain no removed dialogue. No universal platform loudness target is hard-coded.

### WP-11 — Producer and autonomous execution

**Outcome:** delegated workflows progress through evidence-based readiness and bounded repairs.

1. Enable the WP-02 policies only for capabilities whose required tests and QA are available. Add `scripts/production_runner.py` with resumable stage/job records.
2. Implement producer mode's concrete direction/rough-master/export review targets. Support draft master renders with explicit artifact status and location.
3. In autonomous mode, validate scope and capability prerequisites, execute stages, run mandatory checks, and deliver the output plus evidence and unresolved warnings.
4. Classify safe automatic repairs narrowly: approved-range text reflow/scale, caption placement adjustment, restaging a known accepted asset, or a measured level correction within recipe bounds. Changes to meaning, missing evidence, source identity, or narrative structure follow the delegated decision scope.
5. Record each repair's input hash, change, affected ranges, result, and retry cost. Re-run dependent checks; stop on no progress, oscillation, exhausted budget, or required unresolved user input.
6. Prevent repair logic from deleting findings or manufacturing user approvals. Delivery status must reflect incomplete work.
7. Add `references/autonomy-modes.md` and update sequential-gate instructions with explicit mode routing.

**Acceptance:** the same fixture observes the correct review policy in all three modes; autonomous execution repairs a caption collision within budget, fails transparently on an unrepairable required asset, and refuses stale evidence. A user's delegated scope persists across resume. Changing mode alone cannot authorize an export.

### WP-12 — Multicam, tracking, reframing, and supporting media

**Outcome:** podcasts, tutorials, and vertical adaptations use source-aware editorial choices.

1. Add optional diarization and face/speaker association adapters with confidence and manual corrections. Keep visible face IDs separate from speaker identity until association is supported.
2. Extend manual multicam support to active-speaker and reaction candidates, wide/close strategies, minimum dwell preferences, and meaningful pause preservation.
3. Add `scripts/track_sources.py` with face/object/cursor/UI adapters. Store tracks in source PTS and normalized coordinates, with gaps, occlusion, confidence, and invalidation ranges.
4. Compile tracking into crop and annotation transforms for each clip occurrence, playback rate, output aspect, and source rotation. Transform masks with the same geometry.
5. Create separate 16:9 and 9:16 layouts. Define fallback framing for missing/low-confidence tracks; do not interpolate through scene cuts or missing source coverage.
6. Extend asset search with the B-roll roles from the source plan: evidentiary, explanatory, contextual, emotional, bridge, continuity cover, and pattern interrupt. Return relevance/rights evidence and alternatives; attractive but unrelated media must not become a default.
7. Add `multicam-editing.md`, `smart-reframing.md`, and `broll-intelligence.md`.

**Acceptance:** two-speaker fixtures choose source-consistent crops, reaction inserts preserve context, face loss triggers a declared fallback, UI callouts stay anchored through a reframe, and known masked regions remain covered. Vertical output keeps the important face/UI and captions readable in inspected windows. Speaker switches are candidates, not unconditional cuts.

### WP-13 — Long-form recovery and incremental work

**Outcome:** revisions and interruptions reuse valid work without stale artifacts or lost approvals.

1. Add `scripts/cache.py`, `scripts/build_graph.py`, and chapter/job manifests. Keys include content, parameters, model/tool versions, style, source maps, fonts, and relevant renderer configuration.
2. Cache narration by stable scene/paragraph identity, alignment, asset processing, compiled schedules, review windows, and QC results. Atomic writes and completion markers distinguish reusable artifacts from partial output.
3. Build dependency-driven invalidation. A duration change moves downstream anchors; a shared style/helper change affects consumers and joins; changed dialogue invalidates corresponding captions and mix.
4. Preserve conservative approval invalidation even when computational cache reuse is narrower. A reused frame is not a reused approval unless its reviewed dependency set is unchanged.
5. Add chapter-level progress summaries and resumable failure handling. Detect incompatible tool versions and concurrent attempts writing the same cache entry.
6. Cache preview ranges first. For final acceleration, test chunked master rendering with required handles and a continuous audio mix; do not concatenate isolated scene exports. Retain full `VideoFull` render as the correctness fallback.
7. Add `references/long-form-resilience.md` and update existing long-form guidance.

**Acceptance:** interrupt/resume produces equivalent timeline/media content to an uninterrupted fixture; a single-scene text revision recomputes only justified work; a changed duration correctly invalidates downstream mappings; corrupt/incomplete caches are rejected. A long multi-chapter fixture records wall time, memory, cache reuse, and full-master versus chunked equivalence where chunking is enabled.

### WP-14 — Interchange and professional delivery

**Outcome:** editors receive a usable handoff with explicit conversion fidelity.

1. Add `scripts/export_interchange.py` with timeline JSON, source manifest, markers, and corrected captions as the baseline package.
2. Evaluate OTIO against a concrete consuming editor/version using a small fixture. Export supported cuts, rates, tracks, and source references through an adapter.
3. Evaluate FCPXML separately. Support EDL only for the subset it can represent; list omitted or flattened operations.
4. For generated scenes or unsupported effects, emit rendered media with handles and a link back to editable Remotion source. Preserve source/media relink information and transformation provenance.
5. Include a fidelity report distinguishing native, baked, approximated, and unsupported items. Fail or request a scoped fallback for required unsupported behavior instead of silently dropping it.
6. Package the MP4, exact final PNG, editable project, captions, QC/provenance report, source manifest, and interchange outputs requested by the user. Avoid absolute workstation paths where portable references suffice.

**Acceptance:** import a mixed-track fixture into the selected editor and compare trims, track offsets, duration, and markers; rendered generated media has declared handles; exported JSON round-trips stable identities. If a consuming editor is unavailable, interchange remains experimental and parser validation is reported separately from successful editor import.

### WP-15 — Documentation and release qualification

**Outcome:** the skill advertises only capabilities supported by its current implementation and evidence.

1. Update `SKILL.md` into a compact router: intake route, active policy, shared creative core, required references, verification, delivery. Link specialized details instead of embedding the full catalog.
2. Update README, pipeline, collaborative/recorded, asset/audio, visual, transitions, creative-review, long-form, platform, whiteboard, and data references wherever contracts or behavior changed.
3. Update templates and examples together with validators. Validate examples in CI or the release check command.
4. Publish a contract/capability matrix and migration guide. Explicitly label optional models, unsupported operations, experimental interchange, and QC coverage.
5. Qualify each released route with an end-to-end fixture, backward compatibility checks, guard portability, migration rehearsal, and delivery inspection.
6. Record tested revision, environment, fixture hashes, commands, results, skips, known limitations, and rollback instructions in `release-evidence.md` for that release.

**Acceptance:** no reference sends an agent to nonexistent functionality; generated projects work with their bundled validator; legacy fixtures still pass; each advertised mode has a complete example and accurate review instructions. Documentation does not treat proposed scripts or schemas as installed capabilities.

## 7. Verification matrix

These checks are planned. None is marked passed by this document.

| ID | Input/action | Expected observable result | Level / owner package |
|---|---|---|---|
| V-01 | Compile/render current generated v2 and recorded v3 fixtures | Existing clocks, captions, guard behavior, and authored files preserved | Regression/integration; WP-00/01 |
| V-02 | Migrate twice; introduce destination collisions and unknown versions | No overwrite/duplicate IDs; explicit errors; approval history retained without false freshness | Contract/migration; WP-01 |
| V-03 | Change style, transcript, source mapping, and shared helper after review | Relevant decisions become stale and final export is refused | Integration; WP-02 |
| V-04 | Copy generated project away from skill; remove a required bundled module | Complete bundle works; incomplete bundle fails before rendering | Packaging; WP-02 |
| V-05 | 600 ms J-cut, L-cut, and intentional overlapping conversation | Picture/audio relationship matches declared policy; captions follow chosen dialogue | Real media; WP-03/04 |
| V-06 | Reorder and repeat one source interval | Both occurrences render and receive correctly offset words/events | Compiler + render; WP-04 |
| V-07 | Rate change, freeze, VFR source, sync gap, insufficient transition handles | Correct source frames and audio timing, or specific rejection of unsupported/invalid mapping | Contract + media; WP-03/04 |
| V-08 | Nested sequence, cycle, source replacement | Flattened positions correct; cycles rejected; dependent evidence invalidated | Contract/integration; WP-04 |
| V-09 | Resolve same style twice; conflicting brand rule; render three treatments | Stable resolution and field provenance; explained conflict; visible style differences | Contract + visual; WP-05 |
| V-10 | Retake, refrain, emotional pause, context-dependent quote | Useful candidates with evidence; no automatic destructive cut | Editorial fixtures; WP-06 |
| V-11 | Map/chart/document/system takeover followed by presenter | Intended visual action; continuous speech; correct source re-entry | Playback + timing; WP-07/08 |
| V-12 | Inject clipping, overlap, missing asset, black flash, stale captions and absent event | Localized findings with correct severity and evidence | Detector negative tests; WP-09 |
| V-13 | Intentional dark/static shot and uninstrumented canvas | No unjustified failure; limitations/coverage explicitly reported | Detector controls; WP-09 |
| V-14 | Low-confidence alignment, audio processing, compiled SRT/VTT | Uncertainty preserved; measured mix target; captions align to actual master | Audio/media; WP-10 |
| V-15 | Guided/producer/autonomous runs; no-progress repair and missing detector | Correct gates and budget; incomplete evidence cannot pass | Workflow; WP-11 |
| V-16 | Speaker occlusion, source cut, vertical crop, moving mask/UI | Declared fallback; no interpolation across gaps; consistent source geometry | Tracking/playback; WP-12 |
| V-17 | Interrupt build; corrupt cache; alter one scene then shared style | Correct resume and invalidation; no stale outputs or approvals | Recovery/integration; WP-13 |
| V-18 | Import interchange into named editor; unsupported effect | Verified representable timing; explicit bake/limitation report | External integration; WP-14 |
| V-19 | Final render and hero across all released routes | Valid streams, dimensions/fps/duration, single intended speech mix, final PNG from last frame | End-to-end; WP-15 |

Use property-based or generated-case tests where they add value: rational time transformations, cumulative quantization, source bounds, nesting, occurrence mapping, and dependency invalidation. Keep expensive media tests small and deterministic. Human evaluation focuses on usefulness, pacing, intelligibility, and continuity; it is not replaced by schema validation.

### Existing execution commands

Run from the workspace root. These are existing test entry points, not claims that their dependencies are already installed:

```bash
uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_pipeline.py
uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_extensions.py
uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_production.py
uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_workflow_v2.py
uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_recorded_workflow.py
```

Inspect prerequisites before running real-media tests; record skips. `VIDEO_PRODUCTION_NODE_MODULES` can point the existing optional TypeScript extension test at a compatible installed project. Use dedicated fixture projects for `npm run typecheck` and guarded render checks.

Proposed new CLIs such as `compile_timeline.py`, `run_qc.py`, `production_runner.py`, and `export_interchange.py` do not exist yet. Their final flags and commands must be added to the pipeline reference only when implemented and tested.

## 8. Bounded technical investigations

| Question | Experiment | Required evidence / decision |
|---|---|---|
| Can the pinned renderer implement source PTS, rate, audio trims and independent tracks accurately? | Short numbered-video/tone fixture, VFR input, J/L cut and constant rate | Decoded frames/onsets versus compiled schedule; retain stack or specify derivative/upgrade path; blocks WP-03/04 release |
| Which local forced aligner is practical? | Same short clean/noisy/mismatched scripts on available hardware | Timing errors, uncertainty, model size, language support, license and runtime; select adapter for WP-10 |
| How much rendered geometry can be verified automatically? | Fonts, transformed DOM/SVG, clipping, canvas and image text fixtures | Measurable bounds and explicit unsupported coverage; determines WP-09 claims |
| Which diarization/tracking adapters are viable? | Two speakers, occlusion, screen cursor, noisy audio | Accuracy/coverage, resource use, manual fallback, model/license constraints; gates WP-12 automation |
| Can cached master chunks preserve joins and mix? | Render same fixture whole and in bounded chunks with handles | Decoded frame/audio equivalence and seam inspection; otherwise retain full-master rendering in WP-13 |
| What interchange is actually editable in the target NLE? | Small cut/rate/overlay/generated-scene fixture imported into a named editor/version | Import result and fidelity report; controls WP-14 supported subset |

Each investigation ends with a short decision record, measured evidence, limitations, and affected contracts. Check current official APIs/licenses when selecting external dependencies during implementation; this repository-based plan does not assume a specific unverified new library.

## 9. Direct rollout and rollback

1. **Foundation:** the canonical schemas, router, style/event/QC contracts, scaffold, and export guard are the active architecture.
2. **Renderer qualification:** prove the new renderer against numbered video/audio fixtures before enabling J/L cuts, speed changes, or source-bound graphics in production.
3. **Route qualification:** enable each production route after its timeline, planning, review, and final export tests pass. A feature exists only when schema, compiler, renderer, QA/review, docs, and fixtures agree.
4. **Guard refresh:** version the project-local checker bundle and display changed files before refreshing generated project files. Preserve authored scenes/helpers and refuse unrecognized local guard modifications until resolved.
5. **Rollback:** retain original sources, generated derivative recipes, and the prior skill release. New-format-only project edits do not need an automatic downgrade path; restore the prior project copy when rolling back.
6. **Default state:** the canonical contract remains the only path. Mark an individual route experimental until its own end-to-end fixture passes.

A release fails readiness if it loses source mapping, omits a bundled checker dependency, allows stale approvals, or reports unperformed QA as passed. Retain the failed evidence for diagnosis.

## 10. Metrics and release evidence

Collect denominators, fixture/project mix, environment, and comparable revisions. Establish baselines in WP-00; avoid unsupported percentage-improvement promises.

| Area | Measure | Collection point |
|---|---|---|
| Reliability | Failed exports / attempts; invalid source bounds; missing assets; timeline/output duration deltas | Compiler, render and delivery reports |
| Editing usefulness | Candidate cuts accepted/rejected; structural correction count; reviewer edit time | Editorial decisions/review log |
| Visual execution | Planned events observed, unverified events, caption collisions, unintended static spans | Event/QC reports |
| Style | Brand rule violations and unexplained overrides | Resolver and rendered review |
| Hybrid value | Takeovers retained, revised, or removed as unnecessary | Human review per event |
| Autonomy | Repairs attempted/succeeded, escalations, budget exhaustion, detector errors and false positives | Runner/QC evidence |
| Long-form cost | Wall time, peak memory, recomputed ranges, cache hit validity | Job/build manifest |
| Interchange | Native/baked/approximate/unsupported operations and import corrections | Handoff fidelity report |

Suggested release conditions for controlled fixtures: no unresolved blocking technical findings; all planned caption/source mappings accounted for; no stale review authorization; all required checks executed or the feature explicitly left experimental. Creative acceptance remains a recorded human judgment where the active policy requires it.

## 11. Coverage of the source improvement plan

The `WP-*` identifiers below are historical traceability labels from the original backlog. They are not active work packages; the implementation ledger and FO statuses in sections 1A and 12 govern current scope.

| Source phase or section | Implementation coverage |
|---|---|
| Phase 0: formalize core | WP-00, WP-01, WP-02 |
| Phase 1: rich recorded timeline | WP-03, WP-04; tracked punch-ins completed in WP-12 |
| Phase 2: editorial intelligence | WP-06 |
| Phase 3: hybrid visual storytelling | WP-07, WP-08 |
| Phase 4: editorial collage | WP-07 |
| Phase 5: composable styles; both ten-style catalogs | WP-05 |
| Phase 6: reusable visual language | WP-05, WP-07 |
| Phase 7: autonomy modes | Policy in WP-02; operational modes in WP-11 |
| Phase 8: automated visual/motion QA | WP-09; bounded repair in WP-11 |
| Phase 9: alignment/audio | WP-10 |
| Phase 10: long-form resilience | WP-13 |
| Phase 11: multicam/speakers | Manual foundation in WP-04; automated candidates in WP-12 |
| Phase 12: smart reframing/tracking | WP-12 |
| Phase 13: supporting-media intelligence | WP-06, WP-12; existing asset search retained |
| Phase 14: brand profiles | WP-05 |
| Phase 15: NLE interchange | WP-14 |
| Router and proposed project structure | WP-01; gradual adoption through manifest references |
| References/scripts and final positioning | WP-15 plus documentation in every package |
| Success metrics, tests, preserved principles | Sections 3, 7, 9, and 10 of this plan |

The north-star founder-recording workflow is the final integration scenario: ingest/sync → corrected speech/evidence → edit thesis and style → shortened timeline → explanation events → inspected assets → hybrid scenes → captions/mix → QA and scoped repair → policy review → final MP4, exact PNG, editable project, provenance/QC report. Use a consented recording when available; a synthetic substitute validates mechanics but cannot establish editorial usefulness on real conversation.

## 12. Follow-on execution sequence

The canonical foundation replaces the former first batch. Execute follow-on work in this order.

### FO-01 — Real-media renderer qualification — J-cut slice completed

**Delivered evidence:** `generate_renderer_fixture.py` creates the 30 fps test source; `qualify_renderer.py` passed against a rendered 78-frame MP4 and last-frame PNG. It proves source frame 60 at output frame 48, the audio J-cut at output frame 30, and last-frame PNG correspondence within H.264 decode tolerance. L-cut, repeated-dialogue playback, and copied-project export-guard playback still need their own real-media fixtures.

**Outcome:** prove that `EditorialTimeline.tsx` renders source time correctly, including independent picture/audio starts.

1. Add a fixture generator for numbered video frames and distinct audio tones, with known source PTS and short source ranges.
2. Scaffold a canonical project with `13_scaffold_production.py`, install the pinned Remotion dependencies in a disposable fixture directory, typecheck, render `VideoFull`, and render the final-frame PNG.
3. Add decoded-frame and audio-onset assertions for normal cuts, a 600 ms J-cut, a 600 ms L-cut, repeated dialogue, and a final-frame check.
4. Verify the bundled `production-export-v1.cjs` checks master approval and timeline QC from a copied project after the skill directory is unavailable.
5. Correct the timeline renderer if source time, trim math, caption clock, or `totalFrames - 1` differs from the compiled schedule.

**Acceptance:** the fixture proves source frame, audio onset, caption start, output duration, and exact final PNG against declared schedule values. No route may advertise J/L-cut support before this passes.

### FO-02 — Timeline and renderer — partially delivered

**Delivered:** independent source/generated lanes, audio-only/video-only scheduling, z-order, repeated occurrences, constant positive rates, pitch policy, transition-handle validation, and extracted-still freezes. **Deferred:** nested sequences/cycle checks, source replacement rendering, rate ramps/reverse, and operation-specific real-media fixtures beyond the J-cut.

**Outcome:** add the remaining high-value recorded-edit operations on the canonical lane model.

1. Add audio-only/video-only cuts, B-roll/overlay/music/SFX lanes, track z-order, and source replacement.
2. Add constant positive creative speed, explicit freeze frames, transition handles, reordered/repeated occurrences, and nested sequences with cycle detection.
3. Keep source/session synchronization correction separate from creative playback rate; declare pitch policy for audible speed changes.
4. Add per-operation validation fixtures and decoded render tests. Reject unsupported rate ramps, reverse playback, or unavailable transition handles until explicitly implemented.

**Acceptance:** each operation has one successful real-media fixture and one meaningful invalid-input fixture. Repeated speech yields repeated captions; freezes do not halt independent dialogue.

### FO-03 — Styles, assets, and reusable visual language — partially delivered

**Delivered:** all twenty JSON profiles, brand exceptions, deterministic resolution, an editorial primitive renderer, source probing, and immutable derivative records. **Deferred:** distinct rendered-style fixture evidence for three profiles and the full named primitive library/camera grammar.

**Outcome:** turn the starter style resolver into the full composable catalog and reusable visual library.

1. Add all ten faceless styles and ten recorded-edit styles from the product plan, each with editing, visual, motion, caption, audio, and QC policies.
2. Add brand profile validation, constraint/exception records, and generated design tokens.
3. Build original React primitives for typography, charts, maps, documents, comparisons, timelines, systems, quote evidence, paths, counters, masks, and camera rules.
4. Add a deterministic asset-processing pipeline with derivative recipe, input/output hash, alpha/dimension inspection, provenance, rights, and staged path.

**Acceptance:** each profile resolves deterministically; three representative styles render visibly distinct fixtures; a processed asset has a complete immutable lineage record.

### FO-04 — Hybrid visual events — partially delivered

**Delivered:** validated events compile into the render schedule and render generic presenter/overlay/split/PiP/map/chart/document/montage/full-screen event surfaces while dialogue/captions remain independent. **Deferred:** dedicated map, chart, document, and system frame-checkpoint fixtures plus source-return playback qualification.

**Outcome:** visual-story events become actual presenter/overlay/takeover/re-entry sequences.

1. Compile validated events into the render timeline with layer ownership and master-frame anchors.
2. Render presenter-only, overlay, split, picture-in-picture, map, chart, document, montage, and full-screen modes.
3. Keep primary dialogue/captions mounted once across an event; attach re-entry to the exact picture occurrence and source time.
4. Add map, chart, document, and system-diagram fixtures with frame checkpoints and source-return playback windows.

**Acceptance:** all fixture takeovers preserve dialogue/caption continuity and return to the declared source frame without adding duration.

### FO-05 — Editorial intelligence — partially delivered

**Delivered:** deterministic sentence/silence/pause/repetition/retake/context candidates and supplied speaker, scene, and UI evidence with coverage/gaps. `editorial-decisions` validates review records without mutating the timeline. **Deferred:** model adapters for semantic topics, speaker diarization, visual scene/UI detection, and manual-correction persistence.

**Outcome:** analysis supports more useful first cuts without making unreviewed editorial changes.

1. Add phrase/sentence segmentation, pause classification, semantic retake/topic/context candidates, speaker changes, source scene changes, screen/UI events, and confidence/coverage metadata.
2. Store detector inputs, versions, time domains, gaps, and manual corrections. Keep model-dependent detectors optional behind adapters.
3. Compile accepted candidates into timeline changes only through a documented decision record.

**Acceptance:** fixtures distinguish a retake from an intentional refrain, preserve a dramatic pause, flag context-dependent clip extraction, and produce explicit unavailable-detector results.

### FO-06 — Quality control and bounded repair — partially delivered

**Delivered:** aggregation of timeline findings and declared render observations, explicit unavailable/partial coverage, and bounded mechanical repair records. **Deferred:** renderer instrumentation plus concrete layout, flash, crop, visual-state, and caption-drift detectors; producer/autonomous repair execution remains blocked by those detectors.

**Outcome:** identify layout, media, motion, event, source, and audio risks with evidence and repair only bounded mechanical defects.

1. Instrument rendered elements to capture post-font bounds, transforms, asset load state, named event state, and output-frame ranges.
2. Add checks for clipping, safe areas, caption/graphic collisions, missing/low-resolution assets, source bounds, black/flash frames, freezes, crop jumps, caption drift, and expected event state changes.
3. Add report aggregation, detector coverage, false-positive controls for intentional dark/still shots, and bounded repair records.
4. Enable producer/autonomous execution only after required checks and repair limits are enforced.

**Acceptance:** injected defects produce localized findings; clean controls do not block; no detector error or uninstrumented region is reported as a pass.

### FO-07 — Speech, audio, tracking, and long-form operations — partially delivered

**Delivered:** SRT export, FFmpeg loudness evidence, source-coordinate tracking contract, content-hash invalidation, atomic state writes, and full-master-required resume state. **Deferred:** a selected forced aligner, mixing/mastering recipes, tracking model adapters, multicam/reframing, and interrupted-job integration qualification.

**Outcome:** make large recorded and hybrid projects accurate, resumable, and suitable for podcasts/tutorials.

1. Evaluate and add forced alignment, phrase confidence, narration direction, sidecar caption export, mixing recipes, loudness/true-peak measurement, and playback review evidence.
2. Add speaker/face/cursor/UI tracking in source coordinates, multicam decision candidates, vertical reframing, and source-bound annotations/masks.
3. Add chapter manifests, content-hash caches, atomic artifact writes, dependency invalidation, resume reports, and full-master correctness fallback.

**Acceptance:** alignment uncertainty is explicit; tracked geometry follows source transforms; interrupted jobs resume safely; changed duration invalidates downstream anchors and captions.

### FO-08 — Professional interchange and release qualification — partially delivered

**Delivered:** canonical interchange JSON, markers, source manifest, captions, and explicit native/baked/unsupported fidelity metadata. **Deferred:** OTIO/FCPXML exporters, named-NLE import testing, package assembly CLI, and end-to-end qualification for every route.

**Outcome:** deliver a reviewable, portable production package.

1. Export timeline JSON, markers, source manifest, corrected captions, and provenance/QC reports.
2. Evaluate OTIO and FCPXML against named consuming-editor versions; record native, baked, approximate, and unsupported operations.
3. Package source, master MP4, exact PNG, captions, render/QC evidence, and editable project. Run all route end-to-end fixtures before changing an experimental route to supported.

**Acceptance:** an imported fixture preserves declared trims/tracks/markers within documented fidelity, while unsupported operations are explicitly baked or rejected.
