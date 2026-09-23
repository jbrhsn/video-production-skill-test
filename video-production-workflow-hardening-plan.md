# Video-production workflow hardening plan

## Objective

Update `.agents/skills/video-production` so every production route follows three enforceable workspace rules:

1. Agent-initiated Python programs run through `uv` and the repository-local virtual environment. Ad hoc Python is saved as a named script under a repository-root temporary script directory instead of being passed through `python -c`, stdin, or a shell heredoc. A clearly reported fallback is available when `uv` is absent.
2. A route uses Kokoro or Whisper only after the required model files have been verified in `WORKSPACE/.video_production_assets/{kokoro,whisper}`. Missing or corrupt files are downloaded atomically into that cache and never fall back to a home-directory cache.
3. Every video route reviews the workspace creative-asset inventory before its creative plan is approved, records route- and beat-relevant searches, and carries useful candidates or an explicit no-fit decision into project planning.

This plan preserves the four production routes, review gates, source/editorial/render separation, asset rights rules, and delivery contracts.

## Audit findings

### What already works

- `SKILL.md` and the principal references already show `uv run` for documented Python commands.
- The existing dedicated environment is project-local at `WORKSPACE/.venv-video-production`.
- Kokoro is already stored under `.video_production_assets/kokoro`; `01_tts.py` checks the two required byte sizes and `04_setup_assets.sh` downloads atomically enough to preserve an existing file after an HTTP failure.
- Whisper exposes `--model-dir`, and this workspace already contains valid `tiny.pt` and `base.pt` files in `.video_production_assets/whisper`.
- `07_index_assets.py`, `08_search_assets.py`, `library.json`, collection inventories, and `references/asset-library.md` already separate technical discovery, creative judgment, and rights eligibility.
- Current baseline: 51 tests pass with two intentional opt-in renderer skips.

### Gaps to close

- The Python execution rule is convention, not a single explicit invariant. Script docstrings still show short `uv run script.py` forms, executable shebangs invite direct execution, and no rule covers ad hoc analysis scripts.
- There is no repository-root temporary script convention or promotion path for a useful ad hoc script.
- The documented environment name and the requested conventional `.venv` name differ. Generated export configuration captures `sys.executable`, so an environment migration must update both scaffolders and preserve existing projects.
- `uv run --no-project` currently emits a warning because this repository has no Python project metadata. Environment/bootstrap behavior is not owned by one helper.
- Kokoro and Whisper have separate cache behavior. Kokoro fails with setup instructions when missing; Whisper defaults to `~/.cache/whisper` when `--model-dir` is omitted.
- Kokoro validation uses exact sizes rather than a versioned checksum manifest. Whisper relies on upstream checksum validation only when `load_model` is called.
- `04_setup_assets.sh` handles only Kokoro. There is no common command that reports required, cached, valid, downloaded, corrupt, or not-required status for both model families.
- Asset-library search is documented as a pre-storyboard action, but it is not represented in canonical artifacts and no readiness check proves it happened. Route-specific collection priorities and explicit no-fit decisions are absent.
- The three production-state implementations (`workflow_v2.py`, `recorded_workflow.py`, and `production_workflow.py`) do not include asset-library review evidence in their plan snapshots/readiness checks.

## Proposed decisions

### Runtime command contract

Use `WORKSPACE/.venv` as the new canonical environment and support the existing `WORKSPACE/.venv-video-production` as a read-only compatibility fallback during migration. Do not rename or delete an existing environment automatically.

The documented command form becomes:

```bash
uv run --python WORKSPACE/.venv/bin/python python SKILL/scripts/<script>.py ...
```

If `.venv` is absent but `.venv-video-production` exists, use the latter and emit one migration notice. If `uv` is missing, use the selected project-local interpreter directly and emit a fallback warning. If neither `uv` nor a usable local interpreter exists, stop with a bootstrap command; do not silently use a global Python with unknown dependencies.

This is an agent/workflow invocation rule. Python tests or helpers may use `sys.executable` for child processes after the top-level program has entered the selected environment.

Ad hoc Python belongs under proposed `WORKSPACE/.video_production_tmp/scripts/` with a descriptive stable filename. Reuse an existing repository or skill script first. Retain a useful scratch script for the production/session; promote generally reusable logic into `SKILL/scripts/` with tests. Add `.video_production_tmp/` and `.venv/` to the repository ignore rules.

### Model-cache contract

Add a versioned model manifest and one Python cache manager. The manifest records logical model ID, filename, URL, SHA-256, and optional size. The manager:

- accepts `--workspace-root`, repeated `--require kokoro|whisper:<model>`, and `--ensure`;
- resolves only `WORKSPACE/.video_production_assets/kokoro` and `.../whisper`;
- hashes an existing file before use;
- downloads to a same-directory temporary file, validates it, and atomically replaces only an invalid/missing target;
- leaves the old cache intact after download or validation failure;
- emits machine-readable status for project evidence and concise human output;
- never uses `~/.cache`, `XDG_CACHE_HOME`, or another implicit model location.

Route/stage selection should avoid unnecessary downloads:

| Workflow need | Required cache |
|---|---|
| Generated narration | Kokoro model and voice archive |
| Speech transcription/timestamps | Selected Whisper checkpoint, default `base` |
| Recorded edit with speech | Selected Whisper checkpoint |
| Silent/non-speech recorded edit | No speech model; record `not-required` |

`01_tts.py` and `02_timestamps.py` must share this resolver. `02_timestamps.py` should default to the workspace Whisper directory, not the home cache. Keep `04_setup_assets.sh` temporarily as a compatibility wrapper around the new manager, then deprecate it after callers and tests migrate.

### Asset-inventory review contract

Add proposed canonical artifact `analysis/asset-library-review.json`, referenced from `project.json` for new canonical projects and included by the legacy v2/v3 plan checks. It contains:

- schema/version, route, platform/aspect ratio, and project/video-type tags;
- workspace library path plus digests of `library.json`, collection inventories, and the generated technical inventory;
- checked collections and route-specific rationale;
- query IDs tied to editorial scene/beat IDs, query text, candidate IDs, rights status, and inspection status;
- disposition for every shortlisted candidate: `selected`, `rejected`, `reference-only`, or `no-fit`, with reason;
- selected project asset IDs or the planned code/generation/acquisition alternative;
- generation time and tool version, without claiming creative approval.

Collection priorities guide discovery without shrinking the narrative:

| Route | Inventory emphasis |
|---|---|
| `faceless-standard` | Images, brand, fonts, music/SFX; footage when the treatment benefits |
| `faceless-editorial` | Images, footage, references, brand, fonts, music/SFX, evidence-oriented metadata |
| `recorded-edit` | Brand, fonts, music/SFX, overlays/B-roll relevant to the cut; source media remains in the source manifest |
| `hybrid-editorial-edit` | Recorded-edit needs plus images/footage/reference material for each explanation event |

The review runs after routing and initial editorial analysis, before storyboard/creative-plan approval. Refresh the generated technical inventory when library contents changed, then run focused metadata searches derived from the actual topic and beats. A zero-result search is valid only when recorded as `no-fit` with the chosen alternative. Rights and visual inspection remain separate mandatory checks before selection.

## Implementation units

### VP-1 — Establish the runtime policy and workspace resolver

Affected paths:

- `.agents/skills/video-production/SKILL.md`
- proposed `.agents/skills/video-production/references/runtime-preflight.md`
- `.agents/skills/video-production/references/video-production-pipeline.md`
- Python command examples in other references and script docstrings
- `.gitignore`

Work:

- Put the short universal invariant and fallback order in `SKILL.md`; keep detailed commands and scratch-script lifecycle in `runtime-preflight.md`.
- Define workspace-root resolution and reject broad or ambiguous roots.
- Standardize examples on the resolved project-local interpreter.
- Document `.video_production_tmp/scripts/` and prohibit inline Python in agent-authored workflow commands.
- Add a migration note for `.venv-video-production`; existing generated projects remain runnable.

Acceptance evidence:

- Repository search finds no documented direct Python invocation, `python -c`, or Python heredoc in the skill workflow.
- Examples resolve from a workspace with `.venv`, a compatibility-only workspace, and a no-`uv` fallback fixture.
- Missing local environment fails with a specific bootstrap message rather than selecting global Python.

### VP-2 — Unify and harden model-cache management

Affected paths:

- proposed `assets/model-assets.json`
- proposed `scripts/model_cache.py`
- `scripts/01_tts.py`
- `scripts/02_timestamps.py`
- `scripts/04_setup_assets.sh`
- `references/audio-direction.md`
- `references/kokoro-voices.md`
- `.video_production_assets/README.md`
- `scripts/test_pipeline.py`

Work:

- Encode Kokoro and supported Whisper metadata in the manifest.
- Implement check-only and ensure/download modes with checksum verification and atomic replacement.
- Make TTS/timestamp entrypoints resolve the workspace cache before loading a model.
- Remove the Whisper home-cache default from code, output, and docs.
- Preserve the shell setup entrypoint as a wrapper for compatibility.

Acceptance evidence:

- Valid cached models cause zero network calls.
- Missing models download only into `.video_production_assets` and pass checksum verification before becoming visible.
- Corrupt cache, HTTP failure, checksum mismatch, interrupted temporary file, unsupported model ID, and unwritable cache all fail without destroying a previous valid file.
- `02_timestamps.py` cannot create or read `~/.cache/whisper` through an omitted argument.
- The current Kokoro pair and Whisper `tiny`/`base` fixtures validate against the manifest.

### VP-3 — Make inventory review route-aware and reproducible

Affected paths:

- proposed `scripts/review_asset_inventory.py`
- `scripts/07_index_assets.py`
- `scripts/08_search_assets.py`
- `references/asset-library.md`
- `references/production-routing.md`
- `references/collaborative-production.md`
- `references/recorded-video-editing.md`
- `assets/asset-plan.md.template`
- proposed `assets/asset-library-review.json.template`

Work:

- Compose the current index/search helpers rather than duplicate their matching logic.
- Accept route, platform, video-type tags, and repeatable beat/query inputs.
- Record collection coverage, inventory digests, candidates, dispositions, and alternatives.
- Add the review artifact to creative-planning handoffs and asset-plan references.
- Keep model directories excluded from creative indexing.

Acceptance evidence:

- Each of the four routes produces a valid review with the expected collection emphasis.
- Stale inventory digests are detected after a library file changes.
- Unknown/reference-only candidates remain visible only for review and cannot become output selections.
- An empty or unsuitable library requires an explicit `no-fit` alternative rather than silently collapsing to generic text slides.

### VP-4 — Enforce evidence in all production contracts

Affected paths:

- `scripts/contracts.py`
- `scripts/workflow_v2.py`
- `scripts/recorded_workflow.py`
- `scripts/production_workflow.py`
- `scripts/09_check_production.py` and `scripts/check_production_v1.py` as needed
- `assets/production-state.json.template`
- `assets/recorded/production-state.json.template`
- canonical project/scaffold templates and snapshot path sets

Work:

- Add schema validation for model-preflight evidence and asset-library review evidence.
- Require current asset review before the plan/implementation gate for all routes.
- Require only the route/stage-relevant model evidence; do not make Kokoro mandatory for a supplied-narration or silent edit.
- Include review artifacts and relevant digests in plan snapshots so changed library decisions invalidate the affected approval.
- Keep cache binaries outside project manifests and snapshots; snapshot the small verification record, not model files.

Acceptance evidence:

- Every route rejects implementation when required review evidence is absent, malformed, stale, or for another route.
- Non-speech recorded work passes with model status `not-required`.
- Changing a selected asset decision invalidates plan approval; adding an unrelated library file does not invalidate an already approved production unless its recorded review is refreshed.
- Existing projects without the new fields receive a clear migration error or compatibility path, never an accidental approval.

### VP-5 — Update scaffold/export integration

Affected paths:

- `scripts/03_scaffold.py`
- `scripts/11_scaffold_recorded.py`
- `scripts/13_scaffold_production.py`
- `assets/production-export.cjs`
- `assets/production-export-v1.cjs`

Work:

- Resolve the project-local interpreter consistently when scaffolding.
- Avoid permanently baking an obsolete absolute interpreter when a relocatable workspace-relative choice is available.
- Have guarded exports use the same `uv`/fallback policy and preserve current review checks.
- Preserve existing generated projects; require an explicit structural refresh to migrate generated configuration.

Acceptance evidence:

- New faceless, recorded, and canonical editorial scaffolds use the same runtime policy.
- Guarded render/hero commands still block before approval and work after approval.
- Moving a project within the same workspace does not force a home-cache or global-Python fallback.

### VP-6 — Regression, migration, and skill validation

Tests to add or extend:

- `test_pipeline.py`: runtime selection, model checks/download failures, Whisper cache location.
- `test_workflow_v2.py`: faceless asset-review readiness and snapshot invalidation.
- `test_recorded_workflow.py`: recorded/hybrid route coverage and no-model-needed case.
- `test_production_system.py`: canonical artifact/schema and route-specific requirements.
- `test_follow_on_system.py`: cache/report provenance and bounded failure behavior where applicable.

Verification commands:

```bash
uv run --python WORKSPACE/.venv/bin/python python -m unittest discover \
  -s SKILL/scripts -p 'test_*.py' -v

uv run --python WORKSPACE/.venv/bin/python python \
  /Users/jbrhsn/.codex/skills/.system/skill-creator/scripts/quick_validate.py SKILL
```

Also run fixture scaffolds for all four routes with installs disabled, inspect the generated export configuration, and run the existing optional real-render qualifications when their dependencies are available. Network tests use a local fake downloader/server; they must not fetch large real models in routine CI.

## Dependency order and rollout

Implement VP-1 and VP-2 first because later gates need stable runtime and cache evidence. VP-3 can proceed independently after its artifact schema is agreed. VP-4 depends on VP-2 and VP-3. VP-5 follows VP-1/VP-4. VP-6 closes each unit incrementally and then runs the complete matrix.

Roll out with one compatibility window:

1. Accept `.venv-video-production` while preferring `.venv`; emit migration guidance.
2. Generate the new evidence for existing active projects before their next plan/implementation check.
3. Do not move/delete model files or rewrite approvals automatically.
4. After all in-repository examples and generated projects use `.venv`, remove the legacy environment fallback in a separately reviewed change.

Rollback is code-only: retain the old shell wrapper and environment fallback until the new cache and readiness tests pass. The model cache and creative library remain durable data and must never be deleted by rollback.

## Open implementation choice

The only material naming decision is whether the canonical environment must literally be `WORKSPACE/.venv` or whether the existing `WORKSPACE/.venv-video-production` satisfies “a project-local `.venv`.” This plan recommends literal `.venv` plus a compatibility fallback because it matches the requested convention without breaking the current workspace. No other scope decision is needed before implementation.

## Definition of done

- All top-level workflow Python commands use `uv` with a repository-local environment, with the documented bounded fallback.
- No agent-authored inline Python is required; reusable scratch scripts have a stable root-temporary location and promotion path.
- Kokoro/Whisper never load or download from an implicit home cache.
- Required model files are checksum-verified and atomically cached under `.video_production_assets` before use.
- Every route records a current, route-aware creative-asset inventory review before implementation.
- Rights, inspection, and human creative approval remain distinct from search/ranking results.
- All current tests plus new failure-path and migration tests pass; the skill validator passes; optional renderer skips remain explicit.
