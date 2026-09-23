# AI-native video production

This skill is a deterministic production system for four routes: faceless standard, faceless editorial, recorded editing, and hybrid editorial editing. It plans and compiles source media, dialogue, graphics, visual events, audio, style, review evidence, and quality findings into one editable Remotion delivery.

Start with [SKILL.md](SKILL.md). It defines the canonical project artifacts, routing, review policies, timeline ownership, style system, QC limits, and engineering verification.

The canonical implementation includes:

- A source-manifest v3 contract with stream-level source truth, source frame rates, audio layout, and provenance.
- An editorial-timeline v2 contract with independent source/generated lanes, clip occurrences, explicit source trims, positive rate mappings, freeze stills, z-order, markers, visual events, and dialogue-derived captions.
- A production router for the four first-class routes.
- Twenty resolved production grammars, brand restrictions/exceptions, and reusable editorial React primitives.
- Visual-story-event rendering for hybrid takeovers and source re-entry.
- Deterministic source probing, asset derivatives, editorial evidence, source-coordinate tracking, timeline/render-observation QC, bounded repair records, build invalidation, SRT, and timeline interchange.

Run `scripts/test_editorial_timeline.py`, `scripts/test_production_system.py`, and `scripts/test_follow_on_system.py` through the workspace uv environment. `generate_renderer_fixture.py` and `qualify_renderer.py` provide the real-media Remotion qualification; its generated fixture is intentionally disposable.
