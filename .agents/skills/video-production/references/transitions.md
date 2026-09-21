# Scene continuity and transitions

Read when planning joins or implementing the visual-only timeline. Scene-by-scene authoring remains supported; the master gives those scenes a continuous visual and audio context.

## Choose by relationship

| Join | Use when | Implementation |
|---|---|---|
| Cut | Contrast, emphasis, or continuous action already provides the connection | `cut`, zero frames |
| Fade | A change in context benefits from a brief dissolve | `fade`; incoming opaque scene fades over outgoing scene |
| Slide | Spatial movement or a next step should feel directional | `slide`; both scenes move together |
| Wipe | Reveal an answer or cross a meaningful boundary | `wipe`; a directional clipping mask reveals incoming scene |
| Shared object / match cut | The same idea changes context | Author matching object identity, position, scale, color, and velocity in the scenes |
| Camera move / shape morph | Move between overview and detail or transform a meaningful object | Author a shared visual layer or coordinated scene handles; do not declare an unsupported edit-plan kind |

Use a coherent subset for each project. Start around 8–18 frames at 30 fps when appropriate, then adjust to the action; this is an editorial starting point, not a mandated speed. Do not add a whoosh automatically. A deliberate cut is valid. Transition direction describes travel: a left slide moves both scenes left; a left wipe reveals incoming content from the right edge toward the left.

In collaborative production, settle joins in the approved implementation playbook/edit plan and review BoundaryN plus VideoFull in Studio. An asset substitution, timing change, or edited join reopens affected neighboring reviews; record decisions and revision changes using [collaborative production](collaborative-production.md). Render the final master directly rather than concatenating isolated scene exports.

## Edit plan v1

Pass `--edit-plan PROJECT/edit-plan.json` to the scaffold. An example for at least two scenes:

```json
{
  "version": 1,
  "transitions": [
    {"afterScene": 1, "kind": "slide", "frames": 12, "direction": "left", "easing": "smooth"}
  ],
  "holds": [{"afterScene": 2, "frames": 12}],
  "safeArea": {"top": 0.08, "right": 0.12, "bottom": 0.18, "left": 0.08},
  "audio": []
}
```

Scene numbers are 1-based; transitions reference distinct interior boundaries. Omitted joins are cuts. `kind` is cut/fade/slide/wipe; `direction` is left/right/up/down; `easing` is linear/smooth. Smooth is deterministic smoothstep. Non-cut transitions require at least two frames; cut requires zero. Holds are nonnegative integer frames appended after measured narration, including an optional final hold. Safe-area values are fractional insets, adjustable per placement. Unknown fields fail rather than silently hiding misspellings.

`scripts/timeline.py` compiles the plan once into `src/timeline-data.json`. Master, boundary previews, and hero duration use that output. `src/edit-plan.json` saves the input choices for refresh; pass a new empty version-1 plan to deliberately reset them. Changing fps requires revisiting all frame-based edit decisions.

Narration content length is `ceil(duration_s * fps)`. Holds extend its scene span and shift later starts. A D-frame visual transition around narration boundary B spans `[B - floor(D/2), B + ceil(D/2))`; only visuals overlap. Two 90-frame speech segments and a 12-frame transition still total 180 frames, with narration at 0 and 90, and visuals overlapping on frames 84–95. Added holds change that total explicitly. The compiler rejects transition windows that consume a scene's stable interval.

## Authoring contract

New `SceneN.tsx` components accept `VisualSceneProps`; they own visuals only. The master owns narration, caption timing, and optional audio cues. Every narration WAV mounts once on its content span. Captions appear above the visual transitions on the speech clock. Use a full opaque scene background for fades; transparency can expose the prior scene. Do not hide the basic explanation behind a transition.

Use `contentFrame` for ordinary scene animation: it clamps to the first/last content frame during transition handles or holds. `rawContentFrame` can be negative before narration and exceed the content duration afterward; use it deliberately for coordinated entrances, exits, or shared-object animation. `durationFrames` is the content length, not the full master length. Do not use an unadjusted `useCurrentFrame()` inside a visual to time narration; it starts at the visual handle. If a local media clip mounts before narration, explicitly trim, delay, or freeze it so pre-roll does not unintentionally advance its action or reveal the answer. Keep embedded source-video audio muted unless deliberately moved into the mix.

The included renderer uses frame-driven opacity, transforms, and clip paths; it does not require an extra transition package. For advanced presentations, Remotion's [TransitionSeries](https://www.remotion.dev/docs/transitions/transitionseries) is an option: pin `@remotion/transitions` to the project's exact Remotion version and account for its overlap duration. Do not wrap the existing complete speech-owning scenes in overlapping sequences. Replacing the primitive renderer must preserve the compiled narration and caption schedule.

## Legacy projects and previews

Existing scene files without `src/timeline-contract.json` retain the old complete-scene renderer. An edit plan is rejected for that contract. `--refresh-generated` preserves authored scenes, `WordCaptions.tsx`, and `Timeline.tsx`; it is not an automatic migration. To migrate, work in a separate copy, extract audio/captions from each scene, adopt visual props, ensure the updated caption/helper interfaces exist, then write `{"version":1,"sceneContract":"visual-only"}` to the marker before refresh. Check every scene; a marker alone cannot prove that audio was removed.

`SceneN` compositions show isolated visuals plus their speech/captions and holds. They omit global music/effects. `BoundaryN` compositions are slices of the actual master, including neighboring visuals, captions, and the mix. `SafeAreaReview` adds adjustable inset guides. Review joins in playback for black gaps, motion discontinuity, object duplication, text collisions, voice overlap, and chopped words. Exact frame/stream checks cannot replace listening.
