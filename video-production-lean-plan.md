# Video-production skill lean-down plan

## Objective

Reduce dead code and generated clutter in `.agents/skills/video-production` without changing any supported route, artifact contract, review gate, renderer behavior, quality check, asset workflow, or delivery feature.

This is intentionally a conservative plan. A file is included only when current code and test-discovery evidence show that it is generated, permanently skipped, or unreachable through the supported interfaces. Similar-looking implementations are retained when they serve different production contracts.

## Audit baseline

- Tracked skill source: 468,979 bytes.
- Full Python discovery run: 75 tests, 48 passed, 27 skipped, 0 failed.
- Of the 27 skips, 25 are explicitly marked obsolete and cannot contribute coverage. The remaining two are useful opt-in real-render smoke tests and must stay.
- Local `scripts/__pycache__/`: 32 ignored `.pyc` files, 458,852 bytes at audit time. `.gitignore` already excludes these files.
- The supported faceless scaffolder has no `--legacy-workflow` argument, requires the v2 production state and approved plan inputs, and explicitly rejects non-visual scene contracts.

## Safe removal plan

### 1. Remove generated Python bytecode from the skill working tree

Delete `.agents/skills/video-production/scripts/__pycache__/` as local cleanup. Do not add it to source control or package it with the skill. The files are interpreter-generated, already ignored, and regenerate automatically.

Expected result: about 459 KB removed from the current working copy, with no tracked diff and no behavioral change.

### 2. Remove tests that are permanently disabled as obsolete

Delete `.agents/skills/video-production/scripts/test_production.py`. Its only test class has a class-level `@unittest.skip` stating that obsolete v1 production-contract coverage was replaced by `test_workflow_v2.py`. This also makes its nested real-render test impossible to opt into, regardless of environment variables.

From `.agents/skills/video-production/scripts/test_pipeline.py`, remove:

- `test_directorial_cli_generates_measured_composition`
- `test_scaffold_rerun_preserves_authored_files`
- the complete skipped `TimelineTests` class
- imports and the `05_review_bundle.py` dynamic load used only by those removed tests

From `.agents/skills/video-production/scripts/test_extensions.py`, remove:

- `test_whiteboard_scaffold_and_refresh_preserve_art`
- `test_single_scene_whiteboard_typechecks_with_empty_boundaries`
- imports used only by those removed tests

These 25 tests currently execute no assertions. Their commands also target the removed `--legacy-workflow` interface. Keep all 48 currently executing tests and the two opt-in renderer smoke tests.

Expected result: test discovery drops from 75 tests / 27 skips to 51 tests / 2 intentional environment-gated skips. The migrated v2 whiteboard test raises executed coverage from 48 to 49 tests.

### 3. Remove unreachable v1/non-visual branches from the supported faceless scaffolder

Refactor `.agents/skills/video-production/scripts/03_scaffold.py` only along invariants already enforced by its CLI and validation:

- Remove `make_root_tsx()`, the old root generator that mounts scene-owned audio/visual compositions.
- Remove the `visual_only=False` path from `make_scene_stub()` and always use `VisualScene.tsx.template`.
- Remove the unguarded `render` and `hero` package-script alternatives from `make_package_json()`; successful v2 scaffolding always has a validated production state and guarded exports.
- Replace `state`, `timeline`, and `visual_only` conditionals whose alternate branches cannot follow successful validation with their supported v2 behavior.
- Preserve the explicit rejection of projects lacking the v2 visual-only timeline marker when authored scenes already exist. This failure guard protects old projects from accidental conversion and is not dead code.
- Preserve generated-file conflict checks, authored-scene preservation, structural refresh behavior, whiteboard helper installation, timeline compilation, captions, design tokens, export guards, and audio-source validation.

Delete `.agents/skills/video-production/assets/Scene.tsx.template` after the only unreachable reader is removed. Keep `VisualScene.tsx.template`.

This phase changes internal structure only. Do not remove or rename the `03_scaffold.py` CLI, its supported arguments, generated v2 files, or review/export gates.

### 4. Tighten tests around the retained behavior before accepting the refactor

Update active tests only where needed to call the simplified internal helpers. Ensure they assert these observable contracts:

- generated scenes remain visual-only and do not mount narration or captions;
- generated `package.json` always routes `render` and `hero` through `scripts/production-export.cjs`;
- the master timeline owns narration, captions, transitions, holds, and final-frame timing;
- existing authored scenes remain untouched during an approved structural refresh;
- projects with an incompatible/non-v2 scene contract fail before generated files are written;
- the optional whiteboard kit is still copied and preserved when selected.

Where obsolete tests contained a still-relevant assertion, migrate that assertion to a valid v2 fixture before deleting the old body. Do not retain a test merely to preserve historical v1 setup code.

## Explicitly retained

The following were investigated and are not removal candidates because deleting or merging them could reduce functionality or verification quality:

- `assets/production-export-v1.cjs`, `scripts/check_production_v1.py`, and `scripts/production_workflow.py`: despite their names, they are actively copied by `13_scaffold_production.py` for the canonical editorial-timeline route.
- `assets/production-export.cjs`: actively used by generated-v2 and recorded-edit scaffolds.
- `timeline.py` / `workflow_v2.py` and `editorial_timeline.py` / `production_workflow.py`: these support distinct timeline and production-state contracts.
- Recorded-edit templates and helpers: they provide the v3 recorded/hybrid route even where template filenames are not directly copied by every scaffolder.
- Reference documents, style profiles, visual helpers, QC tools, source/provenance tools, interchange tools, and calculation helpers: each supports an advertised production or quality capability; none is an exact duplicate.
- `README.md`: it is a concise package entry point outside agent execution and its removal would reduce usability.
- The two environment-gated real-render tests in `test_workflow_v2.py` and `test_recorded_workflow.py`: these are the only retained end-to-end render checks for their respective contracts.

Do not consolidate distinct contract implementations merely to reduce line count. Fewer files would not be leaner if it obscures ownership or couples independent routes.

## Verification gates

Apply the removals in small commits or patches and stop if any gate fails.

1. Run the three required skill suites:

   ```bash
   uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_editorial_timeline.py
   uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_production_system.py
   uv run --no-project --python .venv-video-production/bin/python python .agents/skills/video-production/scripts/test_follow_on_system.py
   ```

2. Run full discovery and require 51 discovered tests, 49 passes, and only the two documented environment-gated render skips:

   ```bash
   uv run --no-project --python .venv-video-production/bin/python python -m unittest discover \
     -s .agents/skills/video-production/scripts -p 'test_*.py' -v
   ```

3. Run valid `03_scaffold.py` v2 fixtures for custom and whiteboard styles with `--skip-install`; compare generated timeline data, package scripts, Root composition IDs, scene preservation, and export-guard files against the baseline.

4. Run the recorded-edit and canonical editorial scaffold tests to prove the retained similarly named export/check files were unaffected.

5. Run the renderer qualification fixture when Remotion dependencies are available. Verify source PTS mapping, audio/picture offsets, playback rate, caption timing, total frame count, and `totalFrames - 1` final-frame output.

6. Review the final diff for accidental changes to contracts, templates, references, style profiles, and production-state semantics. Recalculate tracked bytes and report actual savings; size reduction is secondary to preserving behavior.

## Acceptance criteria

- All four production routes remain available: `faceless-standard`, `faceless-editorial`, `recorded-edit`, and `hybrid-editorial-edit`.
- Guided, producer, and autonomous review semantics are unchanged.
- Canonical source, editorial, render, QC, review, and delivery artifacts are unchanged.
- No active test, opt-in renderer test, detector, guard, template, or documented workflow is removed.
- Full discovery has no obsolete skips and no new failures.
- The v2 faceless scaffold produces behaviorally equivalent generated projects from the same valid inputs.
- Any candidate that cannot satisfy these criteria is omitted from implementation.

## Execution record

Completed on 2026-09-23.

- Removed 587 lines of obsolete or unreachable code and added 56 lines of active v2 coverage, for a net reduction of 531 lines.
- Reduced the tracked skill from 468,979 to 437,398 bytes (31,581 bytes; 6.7%).
- Removed the ignored Python bytecode directory after verification.
- Verified the required editorial, production-system, and follow-on suites, plus full discovery: 51 tests run, 49 passed, and 2 intentional environment-gated renderer tests skipped.
