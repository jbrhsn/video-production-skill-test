# Video-production asset library

This is the workspace's reusable creative-media library. It is deliberately separate from any one Remotion project: projects copy only their selected, inspected assets into `public/media/` and record the source in their storyboard or asset manifest.

`kokoro/` and `whisper/` are runtime model caches, not creative assets. Do not add them to a project asset manifest.

## Where things go

| Folder | Put here | Do not put here |
| --- | --- | --- |
| `images/` | Illustration, photo, icon, texture, cutout | Source video or animated GIFs used as footage |
| `footage/` | B-roll, screen recordings, licensed clips | Music or stills |
| `audio/music/` | Music beds and stems | One-shot effects |
| `audio/sfx/` | Whooshes, clicks, ambience, hits | Narration takes |
| `fonts/` | Licensed font files and their license notes | Fonts with unclear redistribution terms |
| `brand/` | Approved logos, colors, lockups, lower-thirds | Unapproved platform logos or client files |
| `references/` | Mood boards and study-only material | Output-ready media without usage rights |

The four high-resolution sample images in `images/` form the first collection. Three visually read as transparent cutouts; the LIKE graphic uses a white canvas. Their detailed visual descriptions live in `images/inventory.json`; their searchable IDs, source status, and reuse rules live in `library.json`.

For copyable entries and discovery sources for every folder, see `inventory.example.json`. Those are examples of where to look, not an authorization to use every item from a provider.

## Add an asset

1. Put the original file in the appropriate folder using a descriptive, lowercase, hyphenated name: `person-presenting-side-profile.png`, not `IMG_4821.png`.
2. Add or update its entry in `library.json`. Record its source, creator or provider, license/permission basis, and any attribution or expiry requirement before it is eligible for output use.
3. For a visual asset, note subject, style, composition, text, and limitations in that collection's `inventory.json`. For footage, include duration, aspect ratio, usable action, and any audio restriction.
4. Run the library indexer to produce a fresh technical report. It never overwrites your curated `library.json`.

```bash
uv run --python .venv/bin/python python \
  .agents/skills/video-production/scripts/07_index_assets.py \
  --assets-dir .video_production_assets
```

`inventory.generated.json` is a disposable inspection report. `library.json` is the source of truth for human judgment, rights, and creative meaning.

## Find candidates before a storyboard

Before writing a video storyboard, search the curated metadata using words from the topic, audience problem, and visual beats. Include unreviewed material only to form a review shortlist:

```bash
uv run --python .venv/bin/python python \
  .agents/skills/video-production/scripts/08_search_assets.py \
  --assets-dir .video_production_assets \
  --query "creative thinking and ideas" --include-unusable
```

The result is a candidate list, not a command to use the highest-ranked asset. Inspect each candidate and its rights. Only `cleared` or `user-owned` assets may be selected for an output. If nothing fits, the video can use original motion graphics, illustration, footage acquired for that project, or no media at all.

## Before using an asset in a video

- Inspect it at its intended crop and scale. Transparent PNGs can still contain an opaque matte or edge halo.
- Confirm it supports the scene's idea rather than functioning as generic decoration.
- Confirm the license/permission status is `cleared` or `user-owned`. `unknown` and `reference-only` assets may not be used in an output.
- Copy the selected original into the project, then record the asset ID, source path, scene purpose, trim/crop, and attribution in the project's asset manifest.

Do not treat this library as a licensed stock subscription. The current sample images are marked `user-provided` with rights `unknown` until their origin is confirmed.

## Runtime model cache

`kokoro/` and `whisper/` are checksum-verified runtime caches. Before TTS or timestamps, run the skill cache manager with the workspace root and the model actually needed. It downloads missing/corrupt files atomically into this directory and never falls back to `~/.cache`:

```bash
uv run --python .venv/bin/python python \
  .agents/skills/video-production/scripts/model_cache.py \
  --workspace-root . --require kokoro --require whisper:base --ensure
```
