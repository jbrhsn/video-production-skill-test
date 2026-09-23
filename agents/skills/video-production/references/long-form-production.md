# Long-form explainers

Use for multi-minute narration and arguments that span chapters. Duration is an editorial choice, not a scaffold limit. Do not stretch a short-video template or require a cut every fixed number of seconds.

## Plan and prove the direction

Develop the script with a chapter outline: audience question, evidence or mechanism, illustrative example, and the understanding carried into the next chapter. Follow the normal transcript, measured-audio, asset, and implementation-plan sequence in [collaborative production](collaborative-production.md); do not introduce a second approval for the same choices.

Maintain a compact chapter overview in `implementation-plan.md` (or reference an existing `production-plan.md`). Include chapter IDs, scene IDs, purpose, measured duration, recurring people/objects, required asset IDs, and known production gaps. An initial 8–20-second visual beat is a useful estimate for a calm explainer, not a required scene length. One narration segment can contain several visual beats in scene code. The current scaffold requires one audio file per scene; it does not independently schedule arbitrarily many shots over a single full-length narration file.

Plan a representative opening/story beat, dense chart explanation, and transition. Implement and review these in the approved scene order; do not prebuild a representative batch before the required scene approvals. Verify visual style, character continuity, actual caption space, speech cadence, and sound. Use that sequence for the already-required preview review or proceed when choices are delegated. Do not promise a complete reference-quality video based on one successful still.

## Assets and division of work

Use `asset-plan.md` for requests, layer maps, prompts, provenance, inspection, and recurring asset IDs. If an existing large project has a structured `asset-manifest.json`, retain it as the asset authority and generate/reference its human-readable catalog rather than maintaining duplicate editable inventories. Keep reference-study media separate from assets licensed for the output. Generated or planned assets become selected storyboard assets only after they exist and have been inspected.

Maintain a small character/style sheet: silhouette, clothing colors, proportions, expressions, stroke/fill conventions, and recurring locations. Keep identities stable across new poses; use a small vocabulary of transitions and vary compositions rather than changing styles. Source exact labels, numbers, and formulas from data or text rendered in code.

The agent can research source material, draft narration, design diagrams, author animations, generate or acquire assets with available authorized tools, assemble sound, and render. The user supplies intent and unavailable private inputs; approves consequential assumptions, licensed purchases, voice/likeness use where applicable, and the final creative result. The user does not need to draw every asset or research every factual claim. Flag specific unavailable capabilities, such as complex character acting or a requested voice, instead of assigning all creative work to the user.

## Production and revisions

Organize the plan by chapter, but implement/review one active scene at a time unless the user explicitly delegates batch review. Reuse approved helpers and assets; create bespoke scenes where the explanation requires them. Keep numerical assumptions in a shared data file. Track each scene as planned, assets ready, authored, previewed, or reviewed; track problems by master timestamp and scene ID.

The current TTS helper regenerates its input scenes; it is not a resumable chapter scheduler. For a partial regeneration, synthesize to a scratch directory, map the new files to stable scene IDs, preserve unaffected originals, update measured metadata, and recompile timing. Changes in duration invalidate later master timestamps and sound cues. Review all affected joins, regenerate caption offsets and chapter markers, and rerender the master.

Use the compiled timeline to derive chapter timestamps after durations and holds are settled. Validate the representative sequence in Studio under the approved plan before scaling implementation; record feedback in production-state.json. Export review videos only after the user's applicable approval, or when delegated. Budget for many custom assets and iterative review; code rendering does not eliminate illustration effort.

## Final review

Check the argument across the full duration, not only isolated scenes: repeated setup, delayed payoff, unexplained charts, identity drift, repetitive visual staging, and abrupt voice joins. Check any references and assumptions on screen against source data. Inspect actual combined playback where available and separately record visual, listening, and technical checks. A contact sheet establishes coverage and style, not smooth motion or sound quality.
