# Video production pipeline

`WORKSPACE` is the target repository and `PROJECT` is the video project. Run all Python through the workspace's dedicated uv environment. Use local, inspected media; keep model caches separate from creative assets.

## Project setup

Create the canonical project directories declared by `project.json`:

```text
PROJECT/
├── project.json
├── source/manifest.json
├── analysis/editorial-analysis.json
├── editorial/timeline.json
├── editorial/visual-events.json
├── style/resolved-style.json
├── assets/manifest.json
├── timeline/render.json
├── qc/report.json
├── production-state.json
└── delivery/
```

Create `project.json` with schema `video-production-project`, version `1`, a stable project ID, route, autonomy mode, and project-relative artifact paths. The project file declares where each artifact lives; do not create an alternative editable copy at another path.

## Route, source truth, and style

Resolve a route request before preparing an edit. The request contains `recordedMedia`, `generatedNarration`, `needsExplanation`, and `autonomy`.

```bash
uv run --python WORKSPACE/.venv/bin/python python \
  SKILL/scripts/route_production.py --request PROJECT/route-request.json
```

Probe each original, copy only a staged project-local source, compute a SHA-256 hash, and write source-manifest v3. Use `scripts/probe_sources.py` for FFprobe-backed stream facts. Each source lists stream IDs, stream kind, duration, video dimensions and rational source frame rate or audio layout. Keep source timestamps, source coordinate system, rights, and derivative lineage with the source evidence.

Resolve a style profile before implementation. Keep the resolver output with its digest and per-field provenance. The supplied profile catalog is `SKILL/assets/style-profiles.json`; use brand and project overrides to produce the project artifact.

## Editorial timeline

Write editorial-timeline v2 with independent tracks. A source clip binds one source stream to one track and declares source range, master start, and positive rational playback rate; a generated clip names its generator/payload and duration. A clip ID is an occurrence ID: reusing the same source region produces another clip ID. Freeze clips require an extracted still under `public/`, made with `scripts/extract_freeze.py`; they never rely on a renderer-specific implicit freeze.

Use a single non-overlapping `primary-dialogue` audio track. Picture, B-roll, graphics, music, and effects use separate tracks. Captions are derived from dialogue words matched to each selected dialogue occurrence. Picture cuts do not alter speech or captions.

Compile the edit:

```bash
uv run --python WORKSPACE/.venv/bin/python python \
  SKILL/scripts/compile_timeline.py \
  --timeline PROJECT/editorial/timeline.json \
  --sources PROJECT/source/manifest.json --visual-events PROJECT/editorial/visual-events.json \
  --out PROJECT/timeline/render.json
```

The compiler rejects unknown source streams, source bounds violations, invalid rate mappings, ambiguous field shapes, multiple dialogue tracks, and disallowed overlap. It quantizes output frames once from the master schedule. The render timeline is derived output and must never be hand-edited.

## Visual events and review

For an editorial or hybrid explanation, create visual-story-events v1. Each event binds its visual action to a selected dialogue clip occurrence and master frame range. Name concrete assets or code visuals for each layer and name a specific picture occurrence for re-entry. Source speech and captions continue across a generated takeover.

Review route-appropriate editorial decisions before irreversible delivery. A renderer or QC report does not create a user approval. Store user feedback, scoped delegation, pending review target, and actual decision evidence in `production-state.json`.

## Quality and delivery

Run the current deterministic schedule checks after compilation:

```bash
uv run --python WORKSPACE/.venv/bin/python python \
  SKILL/scripts/run_qc.py --timeline PROJECT/timeline/render.json --out PROJECT/qc/report.json
```

The report covers timeline bounds, non-overlap policy, caption bounds, and supplied render-observation coverage. Add observations only from an instrumented render; unavailable coverage is a warning rather than a pass. Use `scripts/qualify_renderer.py` against the disposable FFmpeg fixture before changing supported renderer behavior. Use `scripts/export_interchange.py` to deliver canonical handoff JSON and SRT; it labels generated/freeze operations as baked and unsupported rate ramps/reverse/nesting explicitly. Deliver the project source, MP4, final PNG, requested captions, source/provenance evidence, QC report, and interchange fidelity report.
