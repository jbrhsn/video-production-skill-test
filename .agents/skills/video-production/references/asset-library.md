# Reusable asset library

## Project intake and asset planning

For a new collaborative production, use `PROJECT/assets/` for user submissions and `PROJECT/asset-plan.md` for requests and review. Start from the skill's `assets/asset-plan.md.template`. This project intake folder is separate from the reusable workspace library and runtime models. Stage only inspected selections into `PROJECT/public/media/`; preserve original files and trace the mapping.

Map every exact voiceover line to stable scene/beat IDs and checked timestamp references, with BG, midground, foreground, and visible action/new understanding. Reuse assets across rows. Allow `none` or `code:<name>`; layer counts and asset counts are not quality targets. Every external object needs an exact user-provided or user-confirmed filename. The agent may propose descriptive filenames; preserve existing names where practical. Requested filenames may be nonexistent in the asset plan, but never label them as inspected storyboard selections.

Give each asset one detail entry: ID, beats, role, filename, requested/supplied/accepted/needs-revision/omitted status, required format/resolution/transparency/crop space, pose/parts, perspective, lighting, clip length/trims, optional generation prompt, consistency references, provenance, rights/attribution, actual inspection, and staged path. Put prompts in these entries rather than overloading the line table. A prompt should specify the individual layer, subject/action, framing, shared visual style, lighting, background/alpha needs, margins, and exclusions. Generated transparency, dimensions, and identity consistency require inspection.

For downloaded assets, the user supplies source item URL, creator/provider, and licensing or permission information. Record evidence and attribution conditions, not a blanket “downloaded from the internet” clearance. For user-owned assets record their usage confirmation. For AI-generated assets record tool/model when known, prompt/reference provenance, and disclosure wording plus placement. Record generation provenance and usage basis separately; an AI-generated label does not itself establish rights. Missing evidence remains `unknown` until resolved.

For recurring characters, maintain a shared reference for proportions, clothing, palette, and poses. If a requested persona cannot be produced suitably, offer a faceless white mannequin, silhouette, original illustrated figure, or abstract metaphor with the same narrative role. Use the user's choice or existing delegation; do not silently substitute. This is an art-direction option, not an automatic rights or quality solution. Specify separate parts/poses for articulated action; a single cutout may not support the planned motion.

Inspect actual files for readability/resolution, transparency, style/lighting/perspective, crop margins, duration/audio, and ability to support the action. Return a consolidated decision table for missing/unsuitable required files: asset and beat, issue, recommended alternative/omission/redesign, effect on story and joins. Update the storyboard, asset plan, playbook, and affected edit-plan entries after resolution. Declare readiness only after required files are accepted or their removal/replacement approved. Code visuals have no external image dependency. See [collaborative production](collaborative-production.md) for phase and approval records.

## Workspace library

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

The command performs transparent token matching against curated metadata and collection details. `--include-unusable` makes `unknown` and `reference-only` entries visible for review; it does not make them usable. Inspect shortlisted files, confirm project-specific rights, and mention only real, suitable selected assets in the storyboard. When none fits, propose code visuals or acquisition/generation at the asset handoff and await the user's choice unless already explicitly delegated. Do not use a code-only fallback to bypass that gate. Inventory scarcity must not shrink the narrative, dictate style, or turn the video into generic text slides.

## Selecting media for a project

For every selected asset, record the asset ID, original workspace path, project copy path, scene/beat role, crop or trim, audio decision for source video, rights status, and required attribution. Inspect it in the intended composition and validate it at delivery. Reference-study media remains separate even when it strongly influences the art direction.
