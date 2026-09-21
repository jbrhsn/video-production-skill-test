# Sequential collaborative production

This is the default for new videos. Read current state and the last user decision before acting. A generic request to create a video authorizes work through the next gate. End the turn at each gate and wait; do not write next-stage artifacts while waiting. Explicit delegation applies only to its stated scope. Engineering fixtures may use the documented legacy/test path.

## Stages and stops

| Stage | Permitted work | Required handoff and stop |
|---|---|---|
| Narration | Source/audience/promise, transcript, then scene audio, then checked timestamps | Present transcript, WAV links, measured durations, timestamp checks and unresolved pronunciation issues. Ask approval of this narration package. STOP before storyboard, asset requests, visual planning or JSX. |
| Creative planning | After narration approval, create visual argument, storyboard, design system and beat-level asset catalog | Present direction and exact external filenames/prompts/part requirements. Ask for assets and choices. STOP for required submissions. Code-only treatment needs an explicit user decision here; never eliminate assets just to keep moving. |
| Refined plan | Inspect supplied files, resolve replacements/omissions, stage accepted media, finalize timed execution plan and playbook | Present the complete revised plan. STOP for approval of this revision before scaffold or code. |
| Active scene | Scaffold once; implement only active scene and necessary helpers; typecheck and verify planned actions | Give the project directory and `npm run studio`, SceneN, local frame checkpoints, and review questions. Ask the user to run Studio. STOP for feedback/approval before the next scene or export. Start Studio yourself only if requested. |
| Scene revision | Preserve feedback, revise scene and affected plan/state, typecheck | Return to the same scene review until approved. Advance one scene at a time unless batching was explicitly requested. |
| Final review | After all scene approvals, review joins and VideoFull in Studio | STOP for approval to export the reviewed master. |
| Export | Render scene/boundary files as needed, VideoFull and final PNG | Check streams, timing and decoded final frame. Material corrections reopen review. |

“Proceed” in response to a narration review approves narration only. Clarify ambiguous scope; never invent approval wording or retroactively mark scenes reviewed. Do not require an extra transcript-only gate unless requested: the default is transcript → audio → timestamps → narration-package approval. Voice auditions/corrections can happen within that stage.

## Artifact responsibilities

- `transcript.txt`, `public/audio/`: narration package. Check recognition against speech/transcript; never invent timing.
- `storyboard.json`: directorial intent; real inspected selected files only.
- `asset-plan.md`: exact spoken phrase/word coverage, BG/midground/foreground roles, filenames or code references, visible action, prompts, provenance, inspection, and user asset decisions.
- `execution-plan.json`: authoritative beat timing and before/action/after states, implementation steps, layer paths, observable acceptance; schema below.
- `implementation-plan.md`: reviewed design system and construction playbook. Reference execution beat IDs/timing; do not maintain competing time tables.
- `edit-plan.json`: existing mechanical joins/holds/safe-area/audio schema. Compiled timeline remains the master clock.
- `production-state.json`: v2 phases/revisions, active scene, scoped approvals, persistent feedback. Helpers never approve anything.

Copy templates only at their stage. Empty future documents do not establish readiness. Consolidate existing scene-design.md rather than maintaining competing execution specifications.

## Executable beats

A scene/audio file can contain many shots. Do not replace line-to-action mapping with “Model 2, 52 seconds” or undefined “5A–5D.” Cover every checked timestamp word with a concrete beat. Several actions may share a phrase; several lines may share a deliberate sustained shot. No arbitrary cut/motion quota.

execution-plan.json contains `version: 1`, positive integer `fps`, and consecutive `scenes` with `scene` and nonempty `beats`:

| Field | Contract |
|---|---|
| id | Stable ID, unique within scene |
| words | Zero-based [start, end) word indices in checked timestamps |
| quote | Exact timestamp words for that range, joined with spaces |
| frames | Speech-local [start, end); default floor(first start × fps), ceil(last end × fps) |
| timingReason | Required for deviation from word anchors; explain anticipation/reading time/hold |
| layers | bg, mid, fg arrays of actual public/media/... paths or named code:... visuals; empty arrays allowed |
| initial / action / result | Concrete object states and transformation |
| steps | Ordered coding instructions: files/components, geometry/anchors, timing/easing, masks, caption clearance and sound as relevant |
| acceptance | Observable outcome and frame checkpoints proving the planned explanation occurs |

Set crops/trims, sizes, independent parts, depth order, entry/exit continuity, and all material construction choices before coding. “Make a chart” is incomplete: specify which relationship changes and how the viewer sees it. Do not defer timing to the implementer. The validator catches missing coverage/ranges/files and placeholder fields; agent review must reject vague instructions and meaningless timingReason text.

## Motion-capable asset review

Request a background plate, transparent isolated object, separate moving part, alternate pose, recording, code geometry, or complete shot according to the planned operation. Do not request every asset as an opaque 16:9 illustration. A flattened workflow diagram cannot provide independently animated nodes merely by fading in.

Inspect actual alpha, crop margins, resolution at composition scale, perspective/lighting, text/artifacts and ability to perform the intended action. List defects and their effects. Record user acceptance of exceptions; never automatically call defects intentional style. Preserve accepted originals unless edits are authorized. Missing provenance remains unresolved rather than automatically “user-authorized.”

For each scene, record a beat acceptance checklist in feedback/history: planned action, implementation location, Studio frame interval, observed result, unresolved issue. A machine picture plus a fade does not implement “outputs accumulate and jam.” Image drift is not articulated motion. CHART/MAP labels do not demonstrate relationships. Check narration alignment and whether long holds remain useful. Share design tokens/helpers without imposing identical headline-and-panels layouts. Check early value, concrete examples, and a payoff that fulfills the promise.

## Version 2 state

Start from assets/production-state.json.template:
- version: 2; mode: collaborative (autonomous only under explicit scope-specific delegation).
- phase: narration, planning, assets, plan-review, implementation, scene-review, final-review, delivery.
- narrationRevision, planRevision, projectRevision: nonempty revision IDs.
- activeScene: null before implementation, positive scene ID during work.
- assetsReadyRevision: null until required dependencies or user-approved substitutes are inspected; then current plan revision.
- scenes: scene ID, that scene's own revision, status pending/in-review/changes-requested/approved.
- approvals: append-only scope narration/plan/scene:N/video, revision, decision approved/changes-requested/delegated, date, actual user evidence, explicit reviewTarget, snapshot.
- feedback: unique id, scope, original request, status, dated history events (date/note), scene/beat/frame/timebase where relevant. Status open/implemented/resolved/deferred/superseded. Resolved/deferred requires confirmation/delegation in resolution; superseded requires acyclic supersededBy. Implemented is not approved.

At each handoff compute the snapshot and retain it with the pending review target. Record that exact snapshot when the user approves. Never recompute after changing reviewed files and attach the old approval. Helpers print hashes only:

```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python \
  SKILL/scripts/09_check_production.py --project-dir PROJECT --snapshot narration
```

Snapshot scopes:
- narration: transcript and public/audio files.
- plan: narration plus storyboard, asset/playbook/execution/edit plans, source assets and staged media.
- scene:N: plan plus that scene, shared src, package/lock/TypeScript configuration and public files.
- video: plan plus all src/config/public files.

Changed covered inputs invalidate approvals even if revision IDs were not bumped. Shared-code changes conservatively invalidate earlier scenes; keep scene-specific work in SceneN.tsx to avoid needless re-review. Reopen affected joins/master for timing, media or shared changes. Scene revisions are independent; do not reset unaffected scenes when another changes. Never migrate old approvals into v2 without establishing their scope and reviewed inputs.

Snapshots compare covered files; they do not authenticate user statements, prove visual quality, or cover every external toolchain/dependency. Keep assets and imports local. Preserve feedback and superseded decisions across sessions.

## Preflight and exports

Run 09_check_production.py with:
- --stage plan after narration approval (phase planning/assets/plan-review).
- --stage implement before scaffold (phase implementation or later).
- --stage scene --scene N before active-scene edits (phase implementation/scene-review).
- --stage render before export (phase final-review/delivery).

Scene N requires prior scenes approved; set activeScene. Checks reject stale/missing prerequisite approvals and invalid phases. Direct Markdown/JSX edits are not intercepted: the agent must run preflight and obey the stop instructions.

03_scaffold.py requires state by default, validates v2 plan timing/inputs, and installs guarded npm render/hero commands. It creates later scene placeholders but authoring remains limited to the active scene. Export guards bundle Python checks locally and invoke them with uv before Remotion. Missing state blocks guarded exports too. After moving a project, set VIDEO_PRODUCTION_PYTHON to its dedicated interpreter; the standard state path remains project-local.

Review-bundle renders also check readiness. Raw Remotion CLI and Studio export buttons can bypass helpers; never use them to evade review. These are workflow controls, not a security boundary against arbitrary edits.

V1/no-state projects require explicit --legacy-workflow at scaffold; fixtures may use it. It never bypasses v2 gates. Existing authored projects are not automatically refreshed or migrated. Fresh user productions use v2. Autonomous v2 work still records scoped delegation and snapshots for each gate, including scenes; a mode flag alone grants nothing.
