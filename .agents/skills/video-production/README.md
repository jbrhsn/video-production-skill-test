# AI-native video production

This skill is a deterministic production system for four routes: faceless standard, faceless editorial, recorded editing, and hybrid editorial editing. It plans and compiles source media, dialogue, graphics, visual events, audio, style, review evidence, and quality findings into one editable Remotion delivery.

Start with [SKILL.md](SKILL.md). It defines the canonical project artifacts, routing, review policies, timeline ownership, style system, QC limits, and engineering verification.

The foundational implementation includes:

- A source-manifest v2 contract with stream-level source truth.
- An editorial-timeline v1 contract with independent audio/video lanes, clip occurrences, explicit source trims, rate mappings, and dialogue-derived captions.
- A production router for the four first-class routes.
- Resolved production grammars from reusable style and brand inputs.
- Visual-story-event contracts for hybrid takeovers and source re-entry.
- Deterministic timeline/caption QC with machine-readable findings.

Run `scripts/test_editorial_timeline.py` and `scripts/test_production_system.py` through the workspace uv environment to verify the foundation. The next implementation increments extend the same contracts into the Remotion renderer, media analysis, source tracking, audio processing, visual/motion checks, bounded repair, caching, and interchange.
