---
name: video-production
description: Create faceless, recorded, or hybrid editorial Remotion videos through deterministic source, editorial, style, timeline, quality, review, and delivery artifacts.
---

# AI-native video production

Build an editable Remotion project, master MP4, exact final-frame PNG, captions when requested, source/provenance manifest, and QC evidence. The system converts editorial decisions into inspectable artifacts. It does not claim that a successful render proves creative quality, factual correctness, rights, privacy, or listening review.

## Run Python, model caches, and asset discovery consistently

Use `uv run` with the workspace-local `.venv` for every top-level Python program. The legacy `.venv-video-production` is a temporary compatibility fallback. Never use inline Python; store reusable ad hoc scripts in `WORKSPACE/.video_production_tmp/scripts/`. Before loading Kokoro or Whisper, run `scripts/model_cache.py` so required files are checksum-verified in `WORKSPACE/.video_production_assets`; missing files are atomically cached there and never in a home-directory cache. After routing and before creative planning, record a route- and beat-aware inventory review with `scripts/review_asset_inventory.py`. Read [runtime preflight](references/runtime-preflight.md).

## Route the production before planning

Use `scripts/route_production.py` to select one route from explicit inputs. Store the result in `project.json`, validated by `scripts/contracts.py`.

| Route | Use when | Primary clock |
|---|---|---|
| `faceless-standard` | New narration needs designed/original visuals | Measured narration |
| `faceless-editorial` | New narration benefits from layered evidence, collage, maps, data, or documents | Measured narration |
| `recorded-edit` | Recorded media carries the story | Selected dialogue/source timeline |
| `hybrid-editorial-edit` | Recorded media needs generated explanations during speech | Selected dialogue/source timeline |

Choose `guided`, `producer`, or `autonomous` execution deliberately. Guided production requires review of source/narration, editorial thesis, style and asset plan, pilot/scene, master, and export. Producer mode requires creative direction, rough master, and export review. Autonomous mode requires explicit delegated scope, enabled detectors, bounded repair policy, and a complete evidence report. Publishing, external purchasing, and account actions always need separate authorization.

## Keep three sources of truth

1. **Source truth:** immutable originals, stream properties, hashes, derivatives, rights/provenance, transcript evidence, and source-coordinate tracking.
2. **Editorial intent:** route, edit thesis, selected style, beat map, accepted timeline, visual events, asset plan, sound plan, and review decisions.
3. **Render state:** compiled schedule, previews, QC findings, output probes, and delivery artifacts.

Never replace source truth with renderer output or use a compiled timeline as an editable editorial plan.

## Canonical artifacts

New projects use these versioned artifacts. Refer to them by paths declared in `project.json`; do not maintain competing editable copies.

```text
project.json
source/manifest.json
analysis/editorial-analysis.json
editorial/timeline.json
editorial/visual-events.json
style/resolved-style.json
assets/manifest.json
timeline/render.json
qc/report.json
production-state.json
delivery/
```

`source/manifest.json` uses source-manifest v3. It records each stream separately, including source video frame rate and audio layout, and never forces B-roll, cameras, audio, or generated media into a screen/presenter role. `editorial/timeline.json` uses editorial-timeline v2: independent audio, video, generated graphics, music, and effect tracks with source/stream trims, occurrence IDs, constant positive playback rates, explicit freeze stills, z-order, and master positions. Repeated source ranges are separate clip occurrences. Captions follow primary dialogue occurrences, not picture cuts.

Compile only with:

```bash
uv run --python WORKSPACE/.venv/bin/python python \
  SKILL/scripts/compile_timeline.py \
  --timeline PROJECT/editorial/timeline.json \
  --sources PROJECT/source/manifest.json --visual-events PROJECT/editorial/visual-events.json \
  --out PROJECT/timeline/render.json
```

The compiler rejects unbounded trims, ambiguous stream bindings, overlapping primary dialogue, and clocks it cannot represent. It quantizes the master schedule once and produces the final total frame count. The final PNG uses `totalFrames - 1`.

## Editorial intelligence and hybrid explanation

Analyze speech and media before editing. Record measured signals separately from judgments: silence, sentence boundaries, repeated phrases, speakers, source changes, and low-confidence regions are evidence; hook value, emotional peaks, likely removals, and explanation opportunities are candidates for a producer or delegated agent to decide.

When the source cannot explain an abstract relationship, plan a visual event. Every event names its dialogue occurrence, master frame range, editorial purpose, presentation mode, background/midground/foreground assets or code visuals, visible sequence, acceptance check, and exact source re-entry. Generated scenes do not restart or duplicate speech, create unplanned time, or detach captions from dialogue.

Read [editorial intelligence](references/editorial-intelligence.md), [hybrid editing](references/hybrid-editorial-editing.md), and [visual-event contract](references/visual-event-contract.md) before using these paths.

## Styles are production grammars

Resolve format, energy, visual language, platform, brand rules, and project overrides into one `resolved-style` artifact. The profile governs editorial pace ranges, visual and layer grammar, caption behavior, motion, sound policy, and QA defaults. It is not a list of colors and transitions.

Use `scripts/style_profile.py` with the supplied catalog as the first library. Record the resolved digest and field provenance. Brand restrictions remain constraints; an override needs an explicit recorded exception. Read [style system](references/style-system.md).

## Asset, motion, sound, and QA discipline

Use inspected assets with source, rights basis, transformation lineage, and intended beat role. Stage only selected media. Keep independent parts separate when the planned action needs articulated motion. For each meaningful beat, define initial state, visible action, settled result, caption policy, sound policy, and observable acceptance.

Run deterministic QC after compiling and after rendering affected windows. `scripts/qc_production.py` aggregates timeline checks with explicitly instrumented render observations; unavailable or partial detector coverage is reported, never passed silently. `bounded_repair()` only queues enabled mechanical fixes and produces a repair record. Findings include rule, severity, master range, evidence, and coverage. Passing QC means only the checks actually run passed.

Review meaningful event windows, joins, source annotations, muted playback, audio-only playback, combined playback, and the master. Record actual user feedback and scoped approvals in `production-state.json`; implementation is not approval. Read [visual and motion QC](references/visual-motion-qc.md), [editorial collage](references/editorial-collage.md), and [creative review](references/creative-review.md).

## Verification while developing this skill

Engineering fixtures do not require creative review gates. Run all Python code through the dedicated uv environment, then run the relevant contract, compiler, renderer, and fixture tests:

```bash
uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/test_editorial_timeline.py
uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/test_production_system.py
uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/test_follow_on_system.py
```

Use a short numbered-video and tone fixture to prove source PTS, picture/audio offsets, playback rate, captions, and final-frame behavior before claiming a renderer supports an edit operation. Unit tests do not establish playback continuity, mix quality, editorial usefulness, or production readiness.
