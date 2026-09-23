# Runtime, model cache, and library preflight

Use `uv` for every top-level Python command. Prefer `WORKSPACE/.venv/bin/python`; accept the existing `WORKSPACE/.venv-video-production/bin/python` only as a migration fallback. If `uv` is unavailable, run that selected project-local interpreter directly and report the fallback. Do not silently choose global Python.

Do not pass ad hoc Python through `python -c`, stdin, or a heredoc. Reuse an existing skill script first. Put a temporary reusable script at `WORKSPACE/.video_production_tmp/scripts/<purpose>.py`; promote generally useful scripts into `SKILL/scripts/` with tests.

Before generated narration or transcription, verify the required models in the workspace cache:

```bash
uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/model_cache.py \
  --workspace-root WORKSPACE --require kokoro --require whisper:base --ensure
```

Model files always live below `WORKSPACE/.video_production_assets/kokoro` or `whisper`. The cache manager hashes existing files, downloads missing/corrupt files to a same-directory temporary file, verifies its checksum, then atomically replaces the target. It never uses a home-directory cache. Require only models the route needs; record `not-required` for silent/non-speech work.

After routing and before the creative plan, refresh/inspect the creative inventory and record focused searches tied to actual beats:

```bash
uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/review_asset_inventory.py \
  --assets-dir WORKSPACE/.video_production_assets --route faceless-standard \
  --query s01-b01="focus distraction desk" --out PROJECT/analysis/asset-library-review.json
```

The review is discovery evidence, not selection approval. Inspect shortlisted assets, confirm usable rights, and record selected, rejected, or no-fit dispositions before plan approval.
