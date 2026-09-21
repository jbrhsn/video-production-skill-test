# Collaborative production

Use for new user-reviewed productions. Keep an explicitly delegated autonomous production or engineering smoke test autonomous within its authorized scope. Existing projects can adopt these artifacts without migrating their renderer. Never repeat an approval already supplied for the current revision.

## Sequence and handoffs

1. Define audience, purpose, and promise; write and review `transcript.txt`. Generate or import one WAV per scene and check word timestamps against the transcript. Detailed visual planning follows measured audio. A later narration edit requires affected audio, timestamps, timing, and review to be updated.
2. Create `storyboard.json` for the visual argument. Copy the skill's `assets/asset-plan.md.template` into `PROJECT/asset-plan.md`; map every spoken line to a beat, layer roles, and visible action. Start the direction/design sections of `implementation-plan.md` from its template. Do not create JSX yet.
3. Collect requested visuals in `PROJECT/assets/`. Review the actual files using [asset library](asset-library.md). Resolve missing or unsuitable dependencies with the user. Complete independent planning before asking for a consolidated set of missing choices. Record accepted assets and source-to-`public/media/` mappings.
4. Finish the implementation playbook using the inspected assets and measured narration; prepare `edit-plan.json`. Present the specific plan revision for approval. Record approval or explicit delegation in `production-state.json`; silence is not approval. All required assets must be accepted, or their omission/replacement approved, before declaring readiness.
5. Scaffold/reuse the Remotion project and implement the approved playbook. Typecheck and start `npm run studio`; provide its actual local URL, composition IDs, and scene/frame checkpoints. Implement scenes in manageable batches and invite review of each scene; offer batch review when preferred.
6. Record feedback, apply changes, and review affected `SceneN`, `BoundaryN`, and `VideoFull` compositions. Update the playbook to describe the current intended result. Ask for final approval of the current project revision when requested changes are resolved.
7. After approval, render scene exports and boundary checks, then `VideoFull` and its exact final-frame PNG. Inspect the exported result. The master is the final assembly: do not concatenate isolated scene exports, which omit cross-scene visual handles and global audio.

User requests to pause before rendering apply to video/still exports; Studio playback and typechecking are normal implementation work unless the user also pauses those. Do not require exported previews before Studio review. Delegated tests may render their fixtures without creative approval gates. Direct CLI renders are still available; these are workflow controls, not an access-control system.

## The execution playbook

`implementation-plan.md` owns execution decisions. Reuse or consolidate an existing `scene-design.md` rather than maintaining competing specifications. Include a plan revision, input references, profile, dimensions/fps, and the approved visual treatment. A line may span several beats; several lines may share a shot. Beat IDs remain stable through revisions.

Set shared palette/semantic colors, typography, caption treatment and safe areas, lighting, character identity, compositing/layer order, motion vocabulary, and audio balance. Choose these for the project's story; do not inherit a previous video's design automatically.

For each scene specify:

- Scene/beat IDs, exact transcript phrases and checked timestamp word-index ranges, measured speech duration, and speech-local frame intervals. Use start-inclusive/end-exclusive intervals; document rounding for word-to-frame boundaries. Scene duration remains `ceil(duration_s * fps)`.
- Actual asset IDs and staged paths, geometry/code visuals, crops/trims, anchors, scale/position, masks, layer order, and independently moving parts.
- Ordered actions with frame intervals, initial/final states, easing, reveals, pauses, and what each action helps the viewer understand. Include settled reading time.
- On-screen text, caption clearance, sound cues, and embedded video-audio decisions.
- Scene entry/exit states and continuity into the next scene; specify transition-handle use of `contentFrame` and `rawContentFrame`.
- Files/components and ordered implementation steps, expected results, and exact review checkpoints. Do not copy complete TSX implementations into the plan.

Keep supported joins, holds, safe areas, and cues in `edit-plan.json`. The compiled timeline remains authoritative for master starts and total frames. Keep the directorial storyboard free of coordinates/keyframes; they belong in the playbook. Routine technical fixes may proceed; unresolved material changes to subjects, metaphors, narration, pacing, or transitions must update the plan and return to the relevant user review.

## Durable state and feedback

Copy `assets/production-state.json.template` to the project. It starts unapproved. This file records decisions; helpers read it but never invent approvals or rewrite feedback. Markdown remains the authority for asset requests/provenance; JSON is the authority for workflow state. Do not duplicate the curated asset inventory in JSON merely for convenience.

Version 1 fields:

| Field | Meaning |
|---|---|
| `version` | `1` |
| `mode` | `collaborative` or explicitly delegated `autonomous` |
| `phase` | `narration`, `planning`, `assets`, `implementation`, `review`, or `delivery` |
| `planRevision` | Nonempty ID; increment when plan, narration/timing, design, or required assets change |
| `projectRevision` | Nonempty ID; increment on implementation changes, including shared helpers/media |
| `assetsReadyRevision` | Plan revision whose required assets were inspected and accepted; initially `null` |
| `approvals` | Append decision records with `scope` (`plan`/`video`), `revision`, `decision` (`approved`/`changes-requested`/`delegated`), `date`, and actual user `evidence` |
| `scenes` | Entries with integer `scene`, `revision` (project revision), and `status`: `pending`, `in-review`, `changes-requested`, `approved` |
| `feedback` | Entries with unique `id`, `scope`, `request`, `status`, and append-only `history`; optional scene/beat/composition/location/timebase, interpretation, files, resolution, supersedes |

Use feedback statuses `open`, `implemented`, `resolved`, `deferred`, or `superseded`. Each history event has `date` and `note`; retain the user's wording and the agent's applied changes distinctly. `resolved` requires user confirmation or relevant existing delegation recorded in `resolution`; `deferred` requires the user's agreement there; `superseded` requires a `supersededBy` reference to the replacing feedback ID, without cycles. `implemented` does not mean user-approved. Feedback may identify a local frame, master frame, or timestamp; always specify its timebase.

Approval example (illustrative only, never copy as a real approval):

```json
{"scope":"plan","revision":"plan-2","decision":"approved","date":"YYYY-MM-DD","evidence":"The user's actual approval of plan-2"}
```

In autonomous mode, `delegated` decisions need the user's actual authorization and apply to the named scope/revision. A mode flag by itself authorizes nothing. The latest decision for a scope/revision wins. Record renewed/revoked approval as a new entry, preserving previous decisions. Helpers cannot establish that a recorded user statement is genuine.

## Revision discipline

Before implementing feedback, read state and the current playbook. Increment project revision for changes; reopen affected scene reviews and adjacent boundaries. Unaffected scene approvals can carry forward only after explicitly checking that their content and dependencies remain unchanged and recording that determination in feedback history. Shared style or audio changes require wider review. Review boundaries and the master before recording overall video approval.

Narration changes invalidate affected captions and speech durations plus downstream master positions and joins. Increment plan revision, clear `assetsReadyRevision` until dependencies are rechecked, and obtain the relevant plan approval. Recompile the timeline. An asset substitution likewise revises the plan; a transition change reopens its neighboring scene reviews. Record superseded decisions instead of deleting history.

The checker compares recorded revisions; it does **not** hash files or automatically detect edits. The agent must maintain revisions and review dependencies whenever files change. Report this limitation rather than treating a green preflight as proof that assets, timing, rights, playback, or creative quality were verified.

## Preflight

Run through the pipeline's uv environment:

```bash
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python \
  SKILL/scripts/09_check_production.py --project-dir PROJECT --stage implement
uv run --no-project --python WORKSPACE/.venv-video-production/bin/python python \
  SKILL/scripts/09_check_production.py --project-dir PROJECT --stage render
```

The standalone checker requires state. Scaffold and review helpers discover `PROJECT/production-state.json` automatically or accept `--production-state PATH`; absent state retains legacy behavior. An explicitly supplied nonexistent path fails. Implementation checks required planning files, asset readiness for the current plan, and its approval. Rendering additionally checks current video approval, complete scene coverage/revision, and unresolved feedback. The standalone checker uses compiled timeline scene IDs for rendering, falling back to storyboard IDs for legacy projects without that file. Explicit current video delegation can replace per-scene user approval, but does not waive unresolved feedback or asset readiness. Preparing review commands without `--render` remains possible before approval.
