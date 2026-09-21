# Whiteboard and illustrated explainers

Use only when the user's reference or chosen direction calls for this style. `--profile` selects aspect ratio; `--visual-style whiteboard` copies `src/visuals/Whiteboard.tsx` and `src/visuals/DoodleAssets.tsx`. Existing authored copies are preserved, including on structural refresh. Other visual styles remain unconstrained.

## Art direction

Start with a warm white background, dark rounded strokes, generous empty space, and a few semantic accent colors. Choose project-specific proportions and a consistent drawing vocabulary. Use readable sans-serif typography for labels; do not rely on generated-image lettering. Paper texture is optional and must remain subtle. The included kit is deliberately simple original vector art, not a professionally illustrated character library or a copy of a reference creator's artwork.

`DoodleAsset` includes person (neutral/happy/worried, standing/pointing/walking), house, apartment, coin, key, document, clock, and arrow. It accepts a palette and draw progress. Compose cityscapes, money groups, and comparisons from these, and author additional paths or acquire/generate illustrations where the kit lacks narrative specificity. Raster image generation can help establish richer illustrations when available; inspect consistency and use layered assets for independent movement. A flattened image supports crops/fades/masks, not authentic per-stroke drawing or character rigging.

## Frame-driven helpers

`DrawPath` reveals an SVG path by normalized stroke length. `DoodleAsset` staggers those paths and then fades fills, avoiding fully visible fills before outlines. `WhiteboardStage` sets a 1920 × 1080 logical SVG coordinate system with a camera viewBox; its letterboxing preserves aspect ratio. Re-stage for vertical, or supply a matching logical canvas size. `LineChart` accepts numeric series, explicit domains, and draw progress. Labels, units, legends, source notes, and assumption qualifiers belong in the scene.

Example inside a visual-only scene, with the master retaining narration and captions:

```tsx
import React from 'react';
import {WhiteboardStage, progress} from '../visuals/Whiteboard';
import {DoodleAsset} from '../visuals/DoodleAssets';

// Inside SceneN, use contentFrame and fps from its existing props.
const reveal = progress(contentFrame, 0, fps * 1.2);
const visual = <WhiteboardStage>
  <g transform="translate(180 180) scale(3)">
    <DoodleAsset kind="house" progress={reveal} />
  </g>
  <g transform="translate(1100 180) scale(3)">
    <DoodleAsset kind="person" pose="pointing" mood="happy"
      progress={progress(contentFrame, fps, fps)} />
  </g>
</WhiteboardStage>;
```

Animate camera coordinates with the same frame-driven progress; keep a stable camera while viewers read dense data. SVG path order is draw order. To synchronize a pen/hand cursor, derive its position from the same path geometry/progress; the kit does not include automatic hand tracking. An arbitrary sweeping hand over a whole image is a wipe effect and should be described as such.

## Composition and review

Use drawing to establish a new relationship, then allow it to settle. Avoid drawing every repeated object slowly. Use cuts or grouped reveals for familiar material, and reserve detailed draw-on action for the concept it explains. Keep equations and numerical comparisons readable while narration interprets them. Provide enough caption space within the actual master composition.

Review an early, middle, and settled reveal frame; confirm no shape appears before its reveal, no text is erased prematurely, and fills do not obscure strokes. Inspect consecutive frames/playback for pacing and joins. Compare recurring character colors/proportions and dense charts across chapters. If the result needs richer illustration, report that gap and improve the asset source rather than claiming the starter kit matches a reference's finish.
