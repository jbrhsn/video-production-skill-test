# Long-form explainers

Use for multi-minute narration and arguments that span chapters. Duration is an editorial choice, not a scaffold limit. Do not stretch a short-video template or require a cut every fixed number of seconds.

## Plan and prove the direction

Develop the script with a chapter outline: audience question, evidence or mechanism, illustrative example, and the understanding carried into the next chapter. Reuse the normal transcript/direction review; do not introduce a second approval for the same choices.

Maintain a compact `production-plan.md` alongside the storyboard. Include chapter IDs, scene IDs, purpose, approximate duration, recurring people/objects, required assets, and known production gaps. An initial 8–20-second visual beat is a useful estimate for a calm explainer, not a required scene length. One narration segment can contain several visual beats in scene code. The current scaffold requires one audio file per scene; it does not independently schedule arbitrarily many shots over a single full-length narration file.

Prepare a short representative sequence before producing every illustration: an opening/story beat, a dense chart explanation, and a transition with continuing narration. Verify visual style, character continuity, actual caption space, speech cadence, and sound. Use that sequence for the already-required preview review or proceed when choices are delegated. Do not promise a complete reference-quality video based on one successful still.

## Assets and division of work

Create `asset-manifest.json` when the asset count warrants it. Each entry records `id`, real source path or generation status, project path, role, creator/source URL, usage basis, and the scenes that reuse it. Keep reference-study media separate from assets licensed for the output. Generated or planned assets become selected storyboard assets only after they exist and have been inspected.

Maintain a small character/style sheet: silhouette, clothing colors, proportions, expressions, stroke/fill conventions, and recurring locations. Keep identities stable across new poses; use a small vocabulary of transitions and vary compositions rather than changing styles. Source exact labels, numbers, and formulas from data or text rendered in code.

The agent can research source material, draft narration, design diagrams, author animations, generate or acquire assets with available authorized tools, assemble sound, and render. The user supplies intent and unavailable private inputs; approves consequential assumptions, licensed purchases, voice/likeness use where applicable, and the final creative result. The user does not need to draw every asset or research every factual claim. Flag specific unavailable capabilities, such as complex character acting or a requested voice, instead of assigning all creative work to the user.

## Production and revisions

Produce in coherent chapter batches. Reuse approved helpers and assets; create bespoke scenes where the explanation requires them. Keep numerical assumptions in a shared data file. Track each scene as planned, assets ready, authored, previewed, or reviewed; track problems by master timestamp and scene ID.

The current TTS helper regenerates its input scenes; it is not a resumable chapter scheduler. For a partial regeneration, synthesize to a scratch directory, map the new files to stable scene IDs, preserve unaffected originals, update measured metadata, and recompile timing. Changes in duration invalidate later master timestamps and sound cues. Review all affected joins, regenerate caption offsets and chapter markers, and rerender the master.

Use the compiled timeline to derive chapter timestamps after durations and holds are settled. Keep review video renders at modest resolution until final export where useful. Budget for many custom assets and iterative review; code rendering does not eliminate illustration effort.

## Final review

Check the argument across the full duration, not only isolated scenes: repeated setup, delayed payoff, unexplained charts, identity drift, repetitive visual staging, and abrupt voice joins. Check any references and assumptions on screen against source data. Inspect actual combined playback where available and separately record visual, listening, and technical checks. A contact sheet establishes coverage and style, not smooth motion or sound quality.
