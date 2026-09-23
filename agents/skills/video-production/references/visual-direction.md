# Visual direction recipes

Read after narration approval when choosing the creative direction. A recipe is a starting grammar, not a finished layout. Select one primary recipe and at most one compatible secondary treatment. Record the choice and project-specific tokens in `design-system.json`; do not let scaffold defaults choose the look.

First decide the editorial format (argument, process, tutorial, data explanation, story), then the treatment below. Recommend two suitable treatments with reasons at the creative handoff. Resolve the choice before the refined-plan gate. If the user delegated direction, record the selected treatment and rationale.

## Recipe selector

| Recipe ID | Use it for | Construction and motion | Starter palette: background / ink / primary / support | Common failure |
|---|---|---|---|---|
| `professional-process` | Workflows, decisions, operations and productivity | Documents, queues, work surfaces and systems; route objects, compare states and expose bottlenecks | `#F6F8FA` / `#172B4D` / `#2457C5` / `#087F8C` | A dashboard of generic cards instead of a changing process |
| `editorial-evidence` | Arguments, investigations and historical/contextual explanation | Maps, tested charts, quotations, document crops and footage; motivated cuts and annotations | `#F4F0E6` / `#242424` / `#B9382D` / `#2457A7` | Invented evidence or imitation of a publisher's identity |
| `doodle-whiteboard` | Mechanisms, relationships and approachable teaching | Original SVG paths and selective fills; draw the relationship, then hold it | `#FFFCF3` / `#263238` / `#2463A6` / `#C58A16` | Slow draw-on for every object or a raster wipe presented as drawing |
| `tactile-collage` | Abstract concepts and metaphor-led stories | Separate paper cutouts, texture and measured parallax; assemble or replace objects | `#F3E8D5` / `#342C29` / `#B84A36` / `#52735C` | Flat illustrations that cannot perform the promised action |
| `flat-character-story` | Human situations and cause/effect | Consistent shapes, poses and articulated parts; anticipation, action and consequence | `#EEF6FA` / `#203249` / `#D95645` / `#187D78` | Claiming full character animation from one image |
| `screen-tutorial` | Real product and software tasks | Supplied capture, stable zoom, cursor focus and callouts tied to exact steps | `#FFFFFF` / `#202A35` / `#2457D6` / `#147D64` | Fabricated UI, unreadable zooms or exposed private data |
| `data-systems` | Comparisons, flows and simulations | Labeled charts and stable identities; animate the quantity or relationship that changes | `#F8FAFC` / `#192B3A` / `#2166AC` / `#B65312` | Color without labels, units, sources or checked calculations |
| `documentary-hybrid` | Human context, environments and atmosphere | Real or clearly labeled illustrative footage with restrained graphic intervention | `#F2F0EB` / `#1F2528` / `#B77A22` / `#537D76` | Treating unavailable footage as if it exists or letting overlays fight it |
| `kinetic-type` | Short language-driven arguments and quotations | Typographic contrast and syntax; punctuation accents and spatial transformation | `#FFF8ED` / `#25202B` / `#70439A` / `#B94431` | Using text as the automatic substitute for explanatory visuals |
| `intentional-dark` | Night, technical or dramatic direction supported by topic, brand or footage | Controlled pools of contrast and restrained glow; preserve dark negative space | `#17212B` / `#F3F5F7` / `#65C7CF` / `#F2B95D` | Selecting dark because the template was dark |
| `custom` | A reviewed direction that does not fit the recipes | State all equivalent rules and prerequisites explicitly | Project-specific | Using `custom` to avoid making design decisions |

Starter palettes are original starting points, not automatically accessible text combinations. Verify actual text/background pairs. Use labels, shape or position as well as color for meaning. Dark is a valid deliberate choice; it is not the fallback.

## Required design-system decisions

Start from `assets/design-system.json.template`. Replace every placeholder before refined-plan approval. The machine-readable file is authoritative for tokens; `implementation-plan.md` explains their purpose without copying a competing token table.

- Recipe ID, rationale, asset burden and background/material strategy.
- Background, surface, ink, muted, primary, secondary, positive and warning colors.
- Local font families/fallbacks and title, body, data and caption roles.
- Stroke width, radius, shadow and texture conventions.
- Motion durations in frames, easing names, camera rule and transition vocabulary.
- Caption colors, background, active word, radius and font family.
- Explicit `avoid` list for this project.

Typography and local font files still need visual inspection. A token file does not load fonts or prove contrast.

## Beat direction

Every planned beat must answer: what is initially true, what visible action occurs, what is true afterward, and what new relationship the viewer can explain. Choose staging such as overview-to-detail, before/after, evidence crop, accumulation, comparison or relationship reveal. Vary shot scale and composition when the argument benefits; do not repeat a title plus rounded panels for every sentence.

Use consistent object behavior. For character/object motion, identify preparation, contact and settle events when they matter. For complex artwork, keep motion simple enough to read. Ambient motion may support atmosphere, but image drift is not explanatory action.

Example: for “too many ideas create a bottleneck,” show distinct notes entering a constrained opening, accumulating, and then being filtered. The same action can use work cards, doodled notes or paper cutouts. A machine image plus a fade does not implement the explanation.

## Sound character

Define whether music and effects are present or intentionally absent. Recipe suggestions are not quotas: workplace clicks, editorial paper marks, doodle pencil cues, collage placement, character contacts, tutorial clicks and typographic punctuation should occur only on meaningful events. See `audio-direction.md` for event anchors, rights, mixing and listening review.

## Review

At the first scene review, check the chosen recipe against actual frames and playback: background choice, contrast, hierarchy, recurring object identity, layout variation, meaningful transformation, caption clearance, motion behavior and sound character. If the implementation exposes a material direction choice, update the reviewed plan before coding further.
