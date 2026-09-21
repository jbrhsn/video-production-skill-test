# Reusable asset library

Use `WORKSPACE/.video_production_assets/` as a durable, creative-media library. It is not a project's `public/media/` directory: only selected, inspected files are copied into a project, with their source and purpose recorded in the project manifest/storyboard.

The supplied layout separates images, footage, music, sound effects, fonts, brand material, and reference-only media. Keep `kokoro/` and `whisper/` as runtime caches only. Never catalogue model files as creative assets.

Every output-eligible asset needs a stable ID, workspace-relative path, kind, useful tags, source/provider, a rights status, usage basis, attribution requirements, and expiry limits. Use one of these rights statuses:

- `cleared`: licensed or otherwise documented for the intended output.
- `user-owned`: the user confirms they control the asset and its intended use.
- `unknown`: unavailable for published output until its source and rights are verified.
- `reference-only`: study material; never render it into an output.

Do not mistake an asset's presence in the workspace for permission to publish it. Existing user-provided files start as `unknown` unless the user has supplied a rights basis.

`WORKSPACE/.video_production_assets/inventory.example.json` provides copyable entries and provider examples for images, footage, music, sound effects, fonts, brand assets, and reference study. It is a discovery aid, not a downloadable stock catalog or blanket license. Use the exact item page and its current license/terms; providers can apply different terms to individual assets.

## Intake and indexing

Name files descriptively with lowercase hyphens, retain the original where possible, and inspect media before selection. Add human judgment to `library.json` and collection-specific inventories. Then generate a technical report:

```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python \
  SKILL/scripts/07_index_assets.py --assets-dir WORKSPACE/.video_production_assets
```

The report is `inventory.generated.json`, which can be regenerated at any time. The indexer excludes model caches and deliberately refuses to overwrite curated `library.json`. It reads PNG/JPEG/SVG dimensions directly and uses `ffprobe` for audio/video when present. It does not determine image transparency, copyright status, visual quality, or actual usage rights.

## Candidate search before storyboarding

Before preparing a storyboard, read `library.json`, collection inventories, and run a small number of topic/visual-beat searches:

```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python \
  SKILL/scripts/08_search_assets.py --assets-dir WORKSPACE/.video_production_assets \
  --query "focus distraction desk" --include-unusable
```

The command performs transparent token matching against curated metadata and collection details. `--include-unusable` makes `unknown` and `reference-only` entries visible for review; it does not make them usable. Inspect shortlisted files, confirm project-specific rights, and mention only real, suitable selected assets in the storyboard. When no asset is appropriate, proceed with original code visuals or acquire/generate media under the user's authorization. Inventory scarcity must not shrink the narrative, dictate a visual style, or turn the video into generic text slides.

## Selecting media for a project

For every selected asset, record the asset ID, original workspace path, project copy path, scene/beat role, crop or trim, audio decision for source video, rights status, and required attribution. Inspect it in the intended composition and validate it at delivery. Reference-study media remains separate even when it strongly influences the art direction.
