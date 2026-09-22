# Recorded timeline contract

This is the technical contract for production-state v3 recorded edits.

## Time domains

- Source presentation time comes from each file's actual stream timestamps.
- Session time is the uncut shared clock for recordings of the same event.
- Edited master time concatenates approved retained session intervals.
- Output frames and audio samples derive from edited master time.

Store authored times as integer microseconds. Preserve source time bases and frame-rate evidence in `source/manifest.json`. A synchronization mapping contains monotonic continuous sections with paired session and source ranges. Split the mapping at stops, missing media and discontinuities; never interpolate across a gap. Equal durations or unrelated gestures are not sync anchors.

The approved `cut-plan.json` is the only source-cut authority. A normal clip removes the same session interval from all linked visual tracks and primary audio. `recorded_timeline.py` quantizes cumulative edited boundaries to output frames, then obtains segment durations from adjacent boundaries. This prevents repeated per-cut rounding from growing the master duration. Silent action intervals remain valid.

## Required artifacts

- `source/manifest.json`: source IDs, roles, immutable hashes, staged paths and probed stream properties.
- `sync/map.json`: reference source and continuous source/session mappings with confirmed or estimated status.
- `transcript/source-words.json`: stable words with session ranges; optional when no speech exists.
- `source/sensitive-regions.json`: findings without secret plaintext.
- `cut-plan.json`: ordered retained intervals, active visual tracks and selected primary audio.
- `execution-plan.json`: output settings, caption safe area, scenes/beats, clip coverage, layout events, annotations and mask geometry.
- `production-state.json`: v3 review decisions and input snapshots.
- `src/timeline-data.json`: generated schedule used by Studio and exports; never hand-edit it as a second authority.

Every execution scene covers one or more cut-plan clip IDs. Clips occur exactly once and in cut-plan order in the initial contract. New plans give every scene a treatment and nonempty beats. Each beat records `correctedTranscriptRangeUs` when dialogue drives timing or `timelineRangeUs` otherwise, plus editorial purpose, intended effect, primary-media role, authored-addition role, entry/development/exit progression, caption policy, and sound policy. Legacy v3 plans and the former evidence-oriented field names remain readable for compatibility; do not use those narrower names as defaults for new work.

In the bundled screen/presenter renderer, layout events use clip-local microseconds and target a supported state; optional `fromLayout` makes an opening transition's predecessor state explicit. Masks and annotations use clip-local time and normalized source coordinates `[x, y, width, height]`. An annotation also records `sourceFrame`, `sourceTimeUs`, and `invalidatedBy`; its active range must not cross that invalidation. Other editing structures require explicit role, layout, and rendering extensions. A source-to-output change invalidates dependent captions, events, masks, annotations and reviews.

## Commands

Run all Python scripts with the workspace's dedicated uv environment described in [video production pipeline](video-production-pipeline.md).

```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/12_ingest_recorded.py --project-dir PROJECT --intake PROJECT/source-intake.json
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/09_check_production.py --project-dir PROJECT --snapshot source
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python SKILL/scripts/11_scaffold_recorded.py --project-dir PROJECT
```

Use `09_check_production.py` with stages `source`, `edit`, `plan`, `implement`, `scene`, `render`, or `delivery`. Final render requires reviewed scenes and video approval. A bounded draft scene review passes `--stage scene --scene N --draft`; it never authorizes final export.

## Rendering ownership

The recorded master owns source playback, selected primary audio, captions, layout and source masks. Scene-specific authored additions may own callouts and graphics. Keep both parallel footage layers mounted through layout changes; split them only at real edit or synchronization-section boundaries. Visual source layers are muted, and the selected primary audio mounts once per compiled clip.

The included renderer uses contain framing so source-coordinate masks remain aligned inside letterboxing. Review focal crops and mask coverage in the actual project; more advanced crops must transform footage and masks together. Multiple aspect ratios require separate layouts and mask review.

## Scope boundaries

The initial contract supports normal-speed chronological retained ranges. J/L cuts, creative speed changes, reordered/repeated source intervals, automatic cursor tracking and NLE interchange require explicit schema and renderer extensions. Do not emulate them through undocumented offsets.
