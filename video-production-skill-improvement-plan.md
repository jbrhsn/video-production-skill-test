# Video Production Skill — Improvement Plan

**Base skill:** `jbrhsn/video-production-skill-test/.agents/skills/video-production`  
**Goal:** Evolve the existing skill from a strong, deterministic AI video-production framework into a flexible AI-native production system capable of:
- premium faceless video creation,
- sophisticated recorded-video editing,
- hybrid recorded + generated editorial storytelling,
- reusable style systems,
- higher autonomy,
- stronger machine-verifiable quality control,
- and scalable long-form / short-form production.

---

# 1. Executive Summary

The current skill already has a strong foundation:

1. Two clear production tracks:
   - **Narration-led / faceless creation**
   - **Recorded-media-led editing**
2. A shared creative core:
   - editorial intent,
   - beat planning,
   - creative direction,
   - storyboard,
   - design system,
   - asset plan,
   - execution plan,
   - Remotion implementation,
   - scene review,
   - master review,
   - guarded export.
3. Deterministic timing and frame-aware execution.
4. Non-destructive recorded-media handling.
5. Good asset provenance and rights discipline.
6. Strong review / approval concepts.
7. Clear separation between creative planning and renderer implementation.
8. A useful “initial state → action → result” philosophy for meaningful animation.
9. Explicit acknowledgement of limitations instead of pretending automated QC proves creative quality.

The next version should **not replace this architecture**.

The improvement strategy should be:

> **Preserve the deterministic production contract, then widen the system’s creative vocabulary, editorial intelligence, autonomy, reusable style grammar, and automated verification.**

The end-state should support four first-class modes:

```text
1. FACELESS STANDARD
   Narration + generated/designed visuals

2. FACELESS EDITORIAL
   Narration + rich layered editorial / collage / documentary motion

3. AI RECORDED EDITING
   Talking head / interview / podcast / tutorial / screen recording

4. HYBRID EDITORIAL EDITING
   Recorded footage
   + AI editorial decisions
   + generated explainer scenes
   + charts/maps/documents/cutouts
   + motion graphics
   + return to original footage
```

The fourth mode is strategically important.

It moves the system from:

> “AI that cuts footage”

to:

> **“AI that understands what the speaker is explaining, decides when the source footage is insufficient, creates an explanatory visual sequence, animates it against the speech clock, and returns naturally to the source.”**

---

# 2. Product Vision

The skill should behave less like a collection of scripts and more like a small AI production studio.

The desired production model is:

```text
Brief / Source Media
        ↓
Production Router
        ↓
Editorial Understanding
        ↓
Creative Strategy
        ↓
Style Grammar
        ↓
Timing + Asset + Edit Plan
        ↓
Deterministic Timeline
        ↓
Implementation
        ↓
Automated QA
        ↓
Human Review where required
        ↓
Final MP4 + Editable Source + Evidence
```

The skill should optimize for five properties:

### 2.1 Intentional
Every cut, motion, visual, sound cue, or generated asset should have a reason.

### 2.2 Deterministic
Creative decisions should become explicit artifacts that can be inspected, revised, and reproduced.

### 2.3 Editable
The project source remains useful after the AI completes its pass.

### 2.4 Scalable
The same system should support one premium documentary or twenty social clips.

### 2.5 Honest
Automated checks should certify only what they can actually verify.

---

# 3. Guiding Design Principles

## 3.1 Do not collapse creative planning into prompting

Bad:

```text
“Make Scene 4 engaging.”
```

Better:

```text
Narration:
“Three countries suddenly joined the alliance.”

Intent:
Show expansion of membership.

Initial:
Base map with existing members.

Action:
Country A highlights.
Country B highlights 5 frames later.
Country C highlights 5 frames later.
Connection paths grow.

Result:
New alliance footprint is visible.

Acceptance:
Viewer can understand the expansion without narration.
```

The existing skill already moves in this direction. The improvement plan should deepen it.

---

## 3.2 The narration or source media remains the master clock

Generated video:

```text
script
→ narration
→ measured speech
→ word / phrase timing
→ visual timing
```

Recorded editing:

```text
source media
→ source timeline
→ sync map
→ transcript / events
→ cut plan
→ master timeline
```

Hybrid editing:

```text
source timeline
→ editorial decision
→ generated explanatory sequence
→ duration bound to source speech
→ re-entry to source footage
```

---

## 3.3 Styles must be production grammars, not themes

A style is not:

```text
font = bold
color = red
transition = zoom
```

A style should influence:

- editorial structure,
- hook structure,
- average shot duration,
- visual density,
- cut density,
- text density,
- caption behavior,
- camera grammar,
- motion grammar,
- B-roll behavior,
- chart behavior,
- asset treatment,
- sound design,
- transition family,
- QC thresholds.

---

## 3.4 Human review should be proportional to production risk

A premium corporate video should not use the same approval cadence as twenty daily shorts.

The skill therefore needs explicit autonomy modes.

---

# 4. Target Architecture

```text
                          VIDEO PRODUCTION SKILL
                                   │
                        ┌──────────┴───────────┐
                        │                      │
                 CREATION ROUTER         EDITING ROUTER
                        │                      │
              ┌─────────┴───────┐       ┌─────┴────────────┐
              │                 │       │                  │
       Faceless Standard   Editorial   Recorded Edit   Hybrid Editorial
              │                 │       │                  │
              └──────────────┬──┴───────┴──────────────────┘
                             │
                   SHARED CREATIVE CORE
                             │
                 Editorial / Audience Intent
                             │
                       Style Profile
                             │
                        Beat / Edit Map
                             │
                      Creative Direction
                             │
                         Storyboard
                             │
                      Asset / Media Plan
                             │
                      Execution Timeline
                             │
                   Remotion / Media Renderer
                             │
                    Machine Verification
                             │
                       Human Review
                             │
                         Delivery
```

---

# 5. Improvement Priority Overview

The five highest-value architectural improvements are:

| Priority | Improvement | Primary value |
|---|---|---|
| P0 | Rich recorded-video timeline | Expands real editing capability |
| P0 | Editorial intelligence layer | Makes automatic editing meaningfully smarter |
| P0 | Hybrid editorial visual storytelling | Differentiates the product from ordinary AI editors |
| P1 | Composable style system | Repeatability, brand consistency, creative breadth |
| P1 | Automated visual/motion QA | Safe autonomy and fewer bad exports |
| P1 | Autonomy modes | Supports both premium review and high-volume production |
| P2 | Reusable visual language / component library | Faster production and consistency |
| P2 | Better speech alignment / audio system | Stronger sync and polish |
| P2 | Long-form resilience | Reliable multi-scene and multi-hour workflows |
| P3 | NLE interchange / ecosystem compatibility | Professional handoff and adoption |

---

# 6. Phase 0 — Preserve and Formalize the Existing Core

## Intent

Before adding capabilities, freeze the current good architectural behavior into explicit interfaces so later improvements do not degrade determinism.

## Why

The existing skill’s value comes from its production discipline. Adding many new features without stable contracts could turn the system into an inconsistent prompt-driven pipeline.

## Implementation

### Step 0.1 — Define canonical production entities

Create explicit schemas for:

```text
Project
Track
Source
Narration
Transcript
Beat
Scene
EditDecision
VisualEvent
Asset
AudioEvent
StyleProfile
Timeline
ReviewState
QCResult
Delivery
```

### Step 0.2 — Version every important contract

Examples:

```text
timeline-contract-v2
style-profile-v1
visual-event-v1
editorial-analysis-v1
review-state-v2
qc-report-v2
```

### Step 0.3 — Separate three categories of state

```text
SOURCE TRUTH
What actually exists.

EDITORIAL INTENT
What should happen.

RENDER STATE
What the implementation produced.
```

Never let renderer output become the only source of truth.

### Step 0.4 — Add migration rules

Older projects should remain readable.

### Value

- prevents feature creep from weakening the core,
- makes tests possible,
- supports future renderer changes,
- simplifies agent reasoning,
- makes project state resumable.

---

# 7. Phase 1 — Rich Recorded-Video Timeline

## Intent

Turn the recorded-media path from a disciplined but narrow chronological editor into a real AI editorial timeline.

## Current limitation being addressed

The recorded workflow is strongest around:
- immutable sources,
- synchronization,
- retained source ranges,
- deterministic source/session/master mapping.

But advanced editorial structures need a richer contract.

## Target capabilities

Add:

1. J-cuts
2. L-cuts
3. audio-only edits
4. video-only edits
5. source interval reordering
6. repeated source intervals
7. speed changes
8. freeze frames
9. multicam switching
10. cutaway / B-roll lanes
11. music lanes
12. sound-effect lanes
13. overlay lanes
14. nested sequences
15. tracked punch-ins
16. variable reframing
17. source replacement
18. reaction inserts
19. transition handles
20. clip-level filters / transforms

## Proposed timeline representation

```yaml
sequence:
  id: master
  fps: 30

tracks:
  - id: dialogue
    type: audio

  - id: camera-a
    type: video

  - id: camera-b
    type: video

  - id: broll
    type: video_overlay

  - id: graphics
    type: generated_visual

  - id: music
    type: audio

  - id: sfx
    type: audio

clips:
  - id: clip-001
    source_id: presenter-a
    source_in: 12.420
    source_out: 18.110
    timeline_in: 0
    playback_rate: 1.0

  - id: broll-003
    source_id: product-screen
    source_in: 42.000
    source_out: 46.000
    timeline_in: 3.2
    layer: broll
```

## J/L cut example

```yaml
edit:
  picture:
    next_clip_starts: 45.0
  audio:
    next_clip_starts: 44.4
```

## Step-by-step implementation

### Step 1.1
Extend the recorded timeline schema without breaking source-coordinate truth.

### Step 1.2
Create a compiler:

```text
editorial timeline
→ deterministic render timeline
```

### Step 1.3
Add overlap validation.

### Step 1.4
Add source-bound validation.

### Step 1.5
Add audio continuity handling.

### Step 1.6
Add test fixtures for:
- J-cut,
- L-cut,
- reordered segment,
- repeated segment,
- multicam switch,
- freeze frame,
- speed-up,
- B-roll overlay.

### Step 1.7
Add timeline visualization for review.

## Value

This is the highest-impact improvement for the AI-edit track.

It unlocks:
- interviews,
- podcasts,
- cinematic testimonials,
- course editing,
- multicam,
- YouTube long-form,
- social repurposing,
- product demos.

---

# 8. Phase 2 — Editorial Intelligence Layer

## Intent

Give the agent structured editorial evidence before asking it to make cuts.

## Why

A raw transcript is insufficient.

A good editor notices:
- pauses,
- retakes,
- repeated phrases,
- emotional emphasis,
- topic boundaries,
- screen events,
- reaction moments,
- weak takes,
- sentence completion,
- interruptions,
- context dependencies.

The agent should receive these as explicit signals.

## New artifact

```text
analysis/editorial-analysis.json
```

## Suggested signals

### Speech
- silence
- filler word
- restart
- repeated phrase
- sentence boundary
- incomplete sentence
- high emphasis
- low confidence ASR
- speaker change

### Video
- scene change
- face present
- screen state change
- cursor activity
- slide change
- camera change
- low-motion region
- high-motion region

### Editorial
- likely hook
- key claim
- supporting example
- tangent
- repeated idea
- story beat
- emotional peak
- strong quote
- context dependency
- call-to-action

## Example

```yaml
events:
  - time: 14.4
    type: silence
    duration: 2.8
    confidence: 0.98

  - time: 31.1
    type: repeated_take
    related_to: 26.8

  - time: 68.0
    type: topic_transition
    label: pricing

  - time: 102.4
    type: emphasis
    transcript: "This changed everything."

  - time: 184.8
    type: screen_state_change
    region: browser-main
```

## Step-by-step implementation

### Step 2.1 — Speech segmentation
Generate sentence- and phrase-level chunks.

### Step 2.2 — Pause analysis
Classify:
- natural pause,
- dead air,
- dramatic pause,
- technical wait.

### Step 2.3 — Repetition and retake detection
Use semantic similarity and local transcript patterns.

### Step 2.4 — Speaker analysis
Support active-speaker decisions.

### Step 2.5 — Video-state analysis
Extract scene and UI state changes.

### Step 2.6 — Editorial candidate scoring
Do **not** directly delete material.
Generate candidates such as:

```text
candidate_remove
candidate_keep
candidate_highlight
candidate_broll
candidate_generated_visual
```

### Step 2.7 — Let the editorial agent decide
Analysis informs the editor; it does not replace editorial judgment.

## Value

- dramatically faster first cuts,
- lower token usage on long recordings,
- better long-form scalability,
- better podcast/short extraction,
- stronger tutorial editing,
- less brittle prompt reasoning.

---

# 9. Phase 3 — Hybrid Editorial Visual Storytelling

## Intent

Allow recorded videos to temporarily become rich faceless explainer sequences when the spoken idea needs visual explanation.

## Strategic value

This is the feature most likely to make the skill feel qualitatively different from ordinary AI editors.

Typical AI editor:

```text
speaker
→ captions
→ zoom
→ B-roll
```

Target system:

```text
speaker makes important claim
→ understand concept
→ choose visual explanation
→ construct layered editorial scene
→ animate it against speech
→ transition back to speaker
```

---

## 9.1 Add Visual Story Events

New canonical entity:

```yaml
visual_event:
  id: market-expansion
  source:
    transcript_range:
      start_word: 182
      end_word: 205

  purpose:
    explain geographic expansion

  presentation:
    mode: full_screen_editorial

  layers:
    background:
      - paper-map

    midground:
      - country-a
      - country-b
      - country-c

    foreground:
      - expansion-arrows
      - metric-label

  sequence:
    - reveal_map
    - highlight_country_a
    - stagger_country_b
    - stagger_country_c
    - draw_connection_lines
    - reveal_metric

  reentry:
    return_to: presenter
    method: motion_match
```

---

## 9.2 Visual replacement modes

Allow the agent to choose among:

```text
A. presenter only
B. presenter + overlay
C. split-screen explanation
D. picture-in-picture
E. full-screen generated visual
F. chart takeover
G. map takeover
H. document / screenshot sequence
I. archival / B-roll montage
J. return to presenter
```

---

## 9.3 Trigger rules

Generated explanation should be considered when the speech contains:

- abstract relationship,
- geographic explanation,
- historical sequence,
- numeric comparison,
- system architecture,
- process,
- timeline,
- causal chain,
- before/after,
- quote/document evidence,
- concept difficult to understand from facecam alone.

## Avoid generated takeover when:

- facial emotion is important,
- audience needs personal trust,
- reaction is the story,
- visual would add no explanatory value,
- source footage already shows the concept clearly.

## Value

- increases explanatory power,
- creates a premium editorial aesthetic,
- differentiates the product,
- reduces generic B-roll dependency,
- enables documentary-style recorded videos.

---

# 10. Phase 4 — Editorial Collage / Documentary Motion Style

## Intent

Create a first-class layered editorial visual language inspired by modern magazine/documentary explainers without copying any creator’s exact work.

## Visual DNA

```text
layered cutouts
editorial typography
paper / grain texture
halftone treatment
maps
documents
archival imagery
charts
marker strokes
limited accent palette
foreground / midground / background separation
```

## Core production rule

Every meaningful narration beat must receive:

1. meaning,
2. visual intent,
3. layer plan,
4. asset plan,
5. animation intent,
6. acceptance criteria.

## Script-to-visual plan

```text
Narration
↓
Meaning
↓
Visual metaphor / evidence
↓
Layers
↓
Motion sequence
↓
Transition
↓
QC criterion
```

## Required layer model

```text
BACKGROUND
Persistent world / texture / environment

MIDGROUND
Context and supporting evidence

FOREGROUND
Current narrative focus
```

## Asset-processing pipeline

```text
source asset
→ background removal where needed
→ clean crop
→ desaturation
→ contrast normalization
→ optional halftone
→ grain / paper treatment
→ optional accent mask
→ transparent export
→ provenance record
```

## Motion rules

Every motion should answer:

```text
WHAT changes?
WHY?
WHEN relative to the narration?
WHAT must the viewer notice?
WHAT state remains afterward?
```

## Anti-patterns

Do not default to:
- generic fade-in,
- random scale pulses,
- constant text cards,
- meaningless drifting images,
- arbitrary wipe transitions,
- excessive zooms,
- flattening independently animated objects into one bitmap.

## Value

- premium faceless output,
- reusable visual identity,
- strong hybrid-video capability,
- supports documentary, business, history, technology and data content.

---

# 11. Phase 5 — Composable Style System

## Intent

Replace vague style prompts with deterministic, machine-readable production grammars.

## Style dimensions

A final style should be composable from:

```text
FORMAT
+
ENERGY
+
VISUAL LANGUAGE
+
PLATFORM
+
BRAND PROFILE
```

Example:

```text
Podcast
+ Fast
+ Editorial
+ YouTube Shorts
+ Brand X
```

or:

```text
Explainer
+ Calm
+ Minimal
+ LinkedIn
+ Brand Y
```

---

# 12. Faceless Production Style Catalog

## 12.1 Premium Documentary

**Best for:** history, economics, biographies, business stories, deep dives.

### Instructions
- Start with consequence, contradiction, or unanswered question.
- Prefer archival imagery, maps, documents, restrained text.
- Use controlled camera movement.
- Typical beat duration: 3–6 seconds.
- Allow visual pauses.
- Use music to support chapter progression.
- Avoid meme treatment and constant text animation.
- Use chapter-level transitions.

### Value
Credibility, emotional weight, long-form watchability.

---

## 12.2 Modern YouTube Explainer

**Best for:** tech, science, business, education.

### Instructions
- Narration controls the timeline.
- Every major concept requires visual explanation.
- Mix diagrams, charts, screenshots, icons, selective B-roll.
- Visual change approximately every 2–4 seconds.
- Use persistent visual metaphors.
- Avoid full-screen text except for major structural moments.

### Value
Balanced retention and comprehension.

---

## 12.3 High-Energy Viral Short

**Best for:** Shorts, Reels, TikTok.

### Instructions
- Core hook within 1–2 seconds.
- No greeting unless functionally necessary.
- 0.5–2 second micro-beats.
- Strong keyword captions.
- Pattern interrupt around every 5–8 seconds.
- Use hard cuts more than decorative transitions.
- End on payoff, reveal, loop, or CTA.

### Value
High information density and mobile-native pacing.

---

## 12.4 Minimal Product Story

**Best for:** SaaS, launches, products, premium brand content.

### Instructions
- One idea per shot.
- Strong negative space.
- Product-first framing.
- Minimal copy.
- Smooth physical easing.
- Avoid decorative clutter.
- Motion directs attention toward product functionality.

### Value
Premium perceived quality and clear product communication.

---

## 12.5 Whiteboard / Visual Thinking

**Best for:** frameworks, teaching, mental models.

### Instructions
- Build the idea progressively.
- Maintain persistent spatial relationships.
- Reveal labels/arrows in narration order.
- Use zooms only for logical movement across the canvas.
- Avoid random sketch animation.

### Value
Strong comprehension for abstract subjects.

---

## 12.6 Data Storytelling

**Best for:** finance, research, economics, analytics.

### Instructions
- Numeric claims must bind to validated data.
- Render chart and narration from the same computed dataset.
- Highlight one relationship at a time.
- Preserve units / axes when needed.
- Avoid misleading scale changes.
- Use motion to explain, not decorate.

### Value
Trust, analytical clarity, factual consistency.

---

## 12.7 Editorial Newsroom

**Best for:** industry updates, current affairs, research recaps.

### Instructions
- Begin with what changed and why it matters.
- Use headlines, source cards, timelines, documents, maps.
- Distinguish fact, reported claim, and analysis.
- Show source/date where temporally relevant.
- Use restrained transitions.

### Value
Fast, source-aware explanatory reporting.

---

## 12.8 Cinematic Story

**Best for:** case studies, emotional brand stories.

### Instructions
- Optimize emotional progression, not visual density.
- Use establishing shots, details, symbolic imagery.
- Allow 4–8 second shots where appropriate.
- Use ambient sound and music transitions.
- Motivate transitions through sound, shape, motion, or theme.

### Value
Emotional impact and brand storytelling.

---

## 12.9 Isometric / System Animation

**Best for:** cloud, infrastructure, workflows, security, systems.

### Instructions
- Maintain stable spatial positions.
- Objects retain identity.
- Animate requests/data/money/processes through system paths.
- Show cause → movement → consequence.
- Avoid teleportation without narrative reason.

### Value
Excellent comprehension of system behavior.

---

## 12.10 Social Infographic

**Best for:** comparisons, quick lists, statistics.

### Instructions
- One message per composition.
- Bold numeric hierarchy.
- Reusable layout grammar.
- Vertical-safe defaults.
- Keep captions away from important graphic zones.
- Use fast but consistent transitions.

### Value
Repeatable high-volume educational social content.

---

# 13. Recorded Editing Style Catalog

## 13.1 Clean Professional Talking Head

### Instructions
- Remove obvious errors and excessive dead air.
- Preserve human speech rhythm.
- Prefer invisible cuts.
- Use subtle punch-ins to hide edits or emphasize important moments.
- Restrained lower-thirds.
- B-roll only when it adds information.
- Dialogue is always audio priority.

### Value
Professional founder, coaching, business, educational videos.

---

## 13.2 High-Retention Talking Head

### Instructions
- Aggressive dead-air compression.
- Tight sentence-boundary cuts.
- More frequent crop changes.
- Keyword caption emphasis.
- Use relevant graphics, screenshots, B-roll, memes selectively.
- Pattern interrupts should not destroy comprehension.
- Never cut inside syllables.

### Value
Social-first retention.

---

## 13.3 Podcast → Viral Clips

### Instructions
- Find self-contained ideas.
- Start at compelling claim, not chronological start.
- Remove context dependencies where possible.
- Reframe speakers vertically.
- Active-speaker crop switching.
- Strong readable captions.
- Optional top headline.

### Value
Efficient long-form repurposing.

---

## 13.4 Long-Form Podcast Editorial

### Instructions
- Preserve authenticity.
- Remove technical issues, major repetition, excessive silence.
- Keep meaningful pauses.
- J/L cuts where useful.
- Cut for reactions and speaker relevance.
- Add topic cards at real topic transitions.
- Preserve room-tone continuity.

### Value
Natural but polished long-form conversation.

---

## 13.5 Screen-Recording Tutorial

### Instructions
- Screen is primary information source.
- Detect cursor/action region.
- Zoom to important UI areas.
- Remove loading and unnecessary navigation.
- Presenter appears when socially useful.
- Callouts identify controls.
- Captions must not obscure UI.
- Hold/freeze source when explanation needs extra time.

### Value
Much stronger software and coding tutorials.

---

## 13.6 Course / Educational Lecture

### Instructions
- Optimize comprehension over edit speed.
- Remove errors and tangents.
- Keep explanatory pauses.
- Use chapter headers, definitions, diagrams, recap points.
- Avoid hyperactive viral editing.

### Value
Better learning outcomes.

---

## 13.7 Cinematic Interview

### Instructions
- Preserve emotional pauses.
- Keep meaningful reactions.
- Use B-roll to cover edits and deepen context.
- Longer shot durations.
- Maintain eye-line continuity.
- Consistent grade / crop behavior.
- Music supports emotional transitions.

### Value
Premium testimonials and documentaries.

---

## 13.8 Product Demo / Launch Edit

### Instructions
- Structure problem → action → result.
- Compress setup.
- Track UI interactions.
- Use clean callouts and zooms.
- Alternate presenter and product based on information ownership.
- Add before/after comparison.
- Avoid irrelevant stock footage.

### Value
Clearer product value and stronger conversion content.

---

## 13.9 Gaming / Reaction Edit

### Instructions
- Detect high-emotion moments.
- Compress low-information gameplay.
- Enlarge facecam at reaction peaks.
- Replay or freeze only when it improves the moment.
- Preserve enough gameplay continuity to understand the event.
- Memes should be selective.

### Value
Entertainment pacing without incoherence.

---

## 13.10 Executive / Corporate Edit

### Instructions
- Prioritize clarity and credibility.
- Remove mistakes and excessive pauses.
- Preserve professional cadence.
- Clean titles, charts, lower-thirds.
- No meme editing.
- Minimal punch-ins.
- Verify names and numbers used in overlays.

### Value
Safe enterprise and leadership content.

---

# 14. Style Profile Schema

Each style should be machine-readable.

Example:

```yaml
style_id: editorial-youtube

format: explainer
energy: balanced-fast
visual_language: editorial-collage

editing:
  cut_density: medium_high
  preserve_emotional_pauses: context_dependent

visuals:
  layers_required: true
  halftone: strong
  document_usage: high
  maps: allowed
  charts: allowed
  text_density: medium

motion:
  pace: medium_fast
  stagger_elements: true
  generic_fades: discouraged
  semantic_motion_required: true

captions:
  enabled: true
  mode: phrase
  emphasis: keywords
  max_lines: 2

audio:
  dialogue_priority: highest
  music: moderate
  impact_sfx: selective

qc:
  safe_area_required: true
  static_visual_warning_sec: 6
  cut_inside_word: forbidden
```

## Value

Style becomes a repeatable operating contract instead of subjective prompt text.

---

# 15. Phase 6 — Reusable Visual Language System

## Intent

Build a reusable creative library above the raw asset library.

## Add reusable primitives

### Typography
- headline
- data number
- quote
- source citation
- chapter
- label
- annotation

### Motion
- reveal
- stagger
- push
- track
- underline
- draw path
- count-up
- morph
- mask wipe
- shared-object transition

### Scene grammars
- comparison
- timeline
- process
- system diagram
- metric reveal
- before/after
- quote evidence
- map explanation
- document analysis
- hierarchy
- cause/effect
- ranked list

### Caption grammars
- documentary
- clean
- social keyword
- tutorial
- corporate

### Camera grammars
- static
- slow push
- focus move
- tracking crop
- punch-in
- map navigation
- document detail

## Value

- faster production,
- less visual reinvention,
- stronger brand consistency,
- better quality at scale.

---

# 16. Phase 7 — Three Autonomy Modes

## Intent

Allow the same skill to serve high-touch premium projects and automated volume production.

---

## 16.1 Guided Mode

### Approval points
- script / edit thesis
- style direction
- asset plan
- each major scene or sequence
- master
- export

### Best for
- premium brand video,
- high-stakes corporate content,
- complex factual production.

---

## 16.2 Producer Mode

### Approval points
- creative direction
- rough master
- final export

### Agent autonomy
- selects assets,
- builds scenes,
- resolves ordinary implementation decisions,
- fixes minor QC issues.

### Best for
- normal YouTube production,
- professional internal teams.

---

## 16.3 Autonomous Mode

### Workflow
- agent completes production,
- applies automated QA,
- self-repairs within bounded retry budget,
- delivers master + QC report.

### Best for
- social clips,
- routine product updates,
- template-driven production.

## Critical rule

Autonomous mode does not remove production evidence.

It increases machine-verification requirements.

## Value

One skill can serve both quality-sensitive and high-volume workflows.

---

# 17. Phase 8 — Automated Visual and Motion QA

## Intent

Expand the current strong QC philosophy into machine-checkable visual behavior.

## Add checks for

### Layout
- clipped text
- safe-area violations
- overlapping labels
- caption/graphic collision
- cropped face
- important UI hidden

### Asset quality
- missing asset
- placeholder asset
- low resolution
- unexpected alpha
- wrong aspect
- failed asset load

### Motion
- unexpectedly frozen composition
- planned event did not visibly occur
- abrupt jump
- transition discontinuity
- animation ends in incorrect state
- repeated frames
- off-screen animation

### Timeline
- audio/video duration mismatch
- subtitle drift
- visual event outside speech range
- invalid cut handles
- source overrun

### Recorded video
- flash frame
- accidental black frame
- repeated source frame after cut
- large crop jump
- speaker crop off face

## QC output

```text
Scene 04
✓ duration correct
✓ audio present
✓ source bounds valid
✓ captions inside safe area
✓ all planned assets loaded
⚠ title overlaps diagram for 11 frames
⚠ no meaningful visual change for 6.8 sec
✗ planned “queue-full” event not detected
```

## Repair loop

```text
render
→ detect issue
→ classify repairability
→ auto-fix bounded issues
→ re-render affected range
→ re-check
```

## Never claim

- static contact sheet proves motion quality,
- stream presence proves audio quality,
- visual presence proves factual correctness,
- automated scan proves privacy,
- automated pass proves artistic quality.

## Value

Safe autonomous operation and fewer embarrassing exports.

---

# 18. Phase 9 — Better Speech Alignment and Audio Production

## Intent

Improve timing precision and final polish.

## Improvements

### 18.1 Forced alignment where practical
Use actual narration audio and transcript to refine word timing.

### 18.2 Confidence-aware timing
Mark uncertain word ranges.

### 18.3 Phrase timing
Not every visual event needs word-level precision.

Support:

```text
word
phrase
sentence
beat
scene
```

### 18.4 Richer voice direction
Allow:
- pace,
- emphasis,
- pause,
- emotional intent,
- pronunciation notes.

### 18.5 Mastering pipeline
Add:
- dialogue leveling,
- noise reduction policy,
- EQ preset,
- de-essing where available,
- music ducking,
- loudness normalization,
- true-peak guard.

## Value

Tighter motion sync, better perceived production quality, more natural narration.

---

# 19. Phase 10 — Long-Form Resilience

## Intent

Make large projects resumable and cheap to revise.

## Improvements

### Scene-local rendering
Only rerender changed scenes.

### Scene-local narration
Cache TTS at scene / paragraph granularity.

### Asset caching
Content-hash reusable transformations.

### Incremental QC
Only rerun affected checks.

### Chapter-level manifests
Allow a two-hour project to be reasoned about chapter by chapter.

### Checkpointing

```text
research complete
editorial plan complete
assets complete
chapter 1 rendered
chapter 2 rendered
...
master assembled
```

## Value

- lower compute,
- faster revisions,
- less catastrophic failure,
- practical long-form production.

---

# 20. Phase 11 — Multicam and Speaker-Aware Editing

## Intent

Make interviews and podcasts a first-class use case.

## Add

- speaker diarization,
- face-to-speaker association,
- active speaker confidence,
- reaction-shot candidates,
- wide / closeup strategy,
- multicam source groups.

## Editing rules

Do not switch cameras mechanically.

Switch because:
- speaker changes,
- reaction matters,
- sentence emphasis,
- visual reset needed,
- technical continuity requires it.

## Value

More natural podcast/interview edits.

---

# 21. Phase 12 — Smart Reframing and Tracking

## Intent

Improve vertical repurposing and screen/tutorial editing.

## Support

- face tracking,
- active-speaker crop,
- cursor tracking,
- UI-region tracking,
- object tracking,
- source-coordinate annotations,
- vertical safe framing.

## Rule

Store tracking in source coordinates.

Do not hard-code generated output coordinates as source truth.

## Value

High-quality 16:9 → 9:16 conversion and better tutorial clarity.

---

# 22. Phase 13 — B-Roll and Supporting-Media Intelligence

## Intent

Move beyond random stock insertion.

## B-roll selection should answer

```text
What claim is being supported?
Is evidence required?
Is explanation required?
Is emotional texture required?
Does source footage already show it?
```

## B-roll types

- evidentiary
- explanatory
- contextual
- emotional
- temporal bridge
- continuity cover
- pattern interrupt

## Reject

- generic office footage for arbitrary business narration,
- unrelated city drone footage,
- visually attractive but semantically irrelevant material.

## Value

More meaningful visuals and less “AI stock-footage syndrome.”

---

# 23. Phase 14 — Brand Profiles

## Intent

Make repeat production visually consistent for channels and companies.

## Brand profile should include

```text
logos
colors
font stack
caption grammar
lower thirds
chart styles
icon style
illustration treatment
transition family
motion easing
logo usage rules
safe areas
intro/outro policy
music policy
prohibited treatments
```

## Value

Channel consistency, faster repeat work, brand safety.

---

# 24. Phase 15 — NLE Interchange

## Intent

Make the AI skill useful inside professional editing workflows.

## Export targets to consider

- OTIO
- FCPXML
- EDL where compatible
- timeline JSON
- subtitle files
- marker files
- source manifest

## Important

Remotion remains an editable delivery format for programmatic scenes.

NLE interchange is an additional professional handoff route.

## Value

Editors can continue work in established tools rather than being locked into one renderer.

---

# 25. Production Router

Add a first step that decides the production track.

Example:

```yaml
production_route:
  source_type: recorded_talking_head
  target_platform: youtube
  requested_style: editorial-youtube
  route: hybrid_editorial_edit
  autonomy: producer
```

## Router decision questions

1. Is recorded media present?
2. Does source footage contain the main visual information?
3. Does the content require generated explanation?
4. Is narration being created from scratch?
5. Is the output short-form or long-form?
6. Is this brand-sensitive?
7. What level of review is required?

---

# 26. Proposed Project Structure

```text
project/
├── source/
│   ├── originals/
│   ├── manifests/
│   └── sync/
│
├── analysis/
│   ├── transcript.json
│   ├── editorial-analysis.json
│   ├── speaker-analysis.json
│   └── visual-analysis.json
│
├── editorial/
│   ├── thesis.md
│   ├── cut-plan.json
│   ├── beat-map.json
│   ├── visual-events.json
│   └── story-structure.md
│
├── style/
│   ├── profile.yaml
│   ├── brand.yaml
│   └── resolved-style.json
│
├── assets/
│   ├── source/
│   ├── processed/
│   ├── generated/
│   └── manifest.json
│
├── audio/
│   ├── narration/
│   ├── music/
│   ├── sfx/
│   └── mix/
│
├── timeline/
│   ├── editorial.json
│   ├── compiled.json
│   └── markers.json
│
├── remotion/
│   └── ...
│
├── renders/
│   ├── previews/
│   ├── scenes/
│   └── master/
│
├── qc/
│   ├── visual.json
│   ├── audio.json
│   ├── timeline.json
│   └── master-report.md
│
└── delivery/
    ├── final.mp4
    ├── poster.png
    ├── subtitles.srt
    └── source-package/
```

---

# 27. Recommended Reference Files to Add

```text
references/
├── production-routing.md
├── style-system.md
├── faceless-style-catalog.md
├── editing-style-catalog.md
├── editorial-collage.md
├── hybrid-editorial-editing.md
├── editorial-intelligence.md
├── advanced-recorded-timeline.md
├── multicam-editing.md
├── smart-reframing.md
├── broll-intelligence.md
├── visual-event-contract.md
├── autonomy-modes.md
├── visual-motion-qc.md
├── brand-profiles.md
└── long-form-resilience.md
```

---

# 28. Recommended Scripts / Modules to Add

Names are illustrative.

```text
scripts/
├── analyze_editorial.py
├── detect_repetitions.py
├── detect_pauses.py
├── detect_speakers.py
├── detect_screen_events.py
├── compile_timeline.py
├── track_faces.py
├── track_cursor.py
├── generate_visual_events.py
├── process_editorial_asset.py
├── resolve_style_profile.py
├── validate_style_profile.py
├── qc_layout.py
├── qc_motion.py
├── qc_timeline.py
├── qc_captions.py
├── qc_source_bounds.py
├── export_otio.py
└── build_review_timeline.py
```

---

# 29. Implementation Sequence

## Milestone 1 — Foundation
1. Freeze current contracts.
2. Add schema versioning.
3. Add production router.
4. Add style profile schema.
5. Add autonomy mode schema.

**Outcome:** new architecture without changing rendering behavior.

---

## Milestone 2 — Style System
1. Implement composable style dimensions.
2. Add 10 faceless styles.
3. Add 10 editing styles.
4. Add brand profile.
5. Build reusable motion / typography primitives.

**Outcome:** much greater creative variety with repeatability.

---

## Milestone 3 — Recorded Timeline v2
1. Track/lane system.
2. Audio/video decoupling.
3. J/L cuts.
4. reordered/repeated intervals.
5. speed/freeze.
6. B-roll and overlay tracks.
7. multicam foundation.

**Outcome:** serious recorded-video editing capability.

---

## Milestone 4 — Editorial Intelligence
1. Transcript event analysis.
2. silence / pause classification.
3. repetition detection.
4. topic boundaries.
5. speaker analysis.
6. video-state changes.
7. highlight / removal candidates.

**Outcome:** much better automatic first edits.

---

## Milestone 5 — Editorial Collage
1. Add three-layer scene grammar.
2. Add asset-processing pipeline.
3. Add editorial motion primitives.
4. Add visual-event contract.
5. Add editorial style variants.

**Outcome:** premium faceless documentary/explainer capability.

---

## Milestone 6 — Hybrid Editorial Editing
1. Detect visual explanation opportunities.
2. Decide source vs overlay vs full takeover.
3. Generate visual event.
4. build assets.
5. animate to source speech.
6. return to source smoothly.

**Outcome:** differentiated AI visual storyteller.

---

## Milestone 7 — QA Expansion
1. Layout checks.
2. caption collision.
3. missing assets.
4. frozen motion.
5. event presence.
6. source-bound checks.
7. cut discontinuities.
8. bounded auto-repair.

**Outcome:** safer autonomy.

---

## Milestone 8 — Advanced Recorded Editing
1. multicam,
2. active-speaker cuts,
3. reaction strategy,
4. tracked reframing,
5. screen/cursor tracking,
6. vertical repurposing.

**Outcome:** podcast/tutorial/editor workflows become first-class.

---

## Milestone 9 — Long-Form + Professional Handoff
1. scene/chapter cache,
2. resumability,
3. incremental QC,
4. OTIO / FCPXML exploration,
5. richer review timeline.

**Outcome:** production-team adoption.

---

# 30. Success Metrics

Avoid using vague “looks better” as the only metric.

## Reliability
- percentage of exports without technical failure,
- duration mismatch rate,
- missing asset rate,
- invalid source-bound rate.

## Edit efficiency
- percentage of first-pass cuts retained by reviewer,
- manual correction count,
- time spent on structural corrections.

## Visual execution
- planned visual events successfully rendered,
- caption collision rate,
- unintended static-duration rate.

## Style consistency
- violations against brand profile,
- inconsistent caption grammar,
- inconsistent motion primitive usage.

## Hybrid storytelling
- percentage of generated visual takeovers judged useful,
- percentage removed as unnecessary,
- explanation events aligned correctly to speech.

## Autonomy
- number of issues repaired automatically,
- number of issues requiring human intervention,
- false-positive QC rate.

---

# 31. Testing Strategy

Every new capability should have deterministic fixtures.

## Faceless tests
- data explainer,
- documentary,
- short-form,
- whiteboard,
- editorial collage.

## Recorded tests
- talking head,
- two-person podcast,
- screen tutorial,
- product demo,
- multicam interview.

## Hybrid tests
- presenter + map explanation,
- presenter + chart,
- presenter + document evidence,
- presenter + system diagram.

## QA tests
Intentionally introduce:
- clipped text,
- missing asset,
- black frame,
- caption overlap,
- broken timeline,
- excessive freeze,
- incorrect source bounds.

The test should prove the QC system catches the correct issue.

---

# 32. What Not to Change

The following principles from the base skill should remain:

1. **Immutable source handling**
2. **Source-coordinate truth**
3. **Explicit sync maps**
4. **Narration / source timing as master clock**
5. **Deterministic frames**
6. **Asset provenance**
7. **Rights status**
8. **Creative plan before implementation**
9. **Scene-level reviewability**
10. **Guarded export**
11. **Editable project delivery**
12. **Honest QC boundaries**

These are not overhead.

They are the reason the system can become more autonomous without becoming unreliable.

---

# 33. Final Recommended Product Position

After these improvements, the skill should be positioned internally as:

> **An AI-native video production operating system that can create videos from scratch, professionally edit recorded media, and dynamically synthesize explanatory visual sequences when the story requires them.**

Its competitive advantage should not be:

> “It can use Remotion.”

It should be:

> **It converts editorial intent into deterministic, inspectable, editable production artifacts—and can reason across script, speech, footage, graphics, data, assets, timing, sound, style, and quality control as one production system.**

---

# 34. Recommended Priority if Only Five Improvements Can Be Built

If resources are limited, implement in this order:

## 1. Rich recorded-video timeline
**Intent:** remove the largest structural limitation.  
**Value:** dramatically widens edit types.

## 2. Editorial intelligence
**Intent:** understand footage before cutting it.  
**Value:** stronger first edits and long-form scalability.

## 3. Hybrid editorial visual storytelling
**Intent:** create explanation when source footage is insufficient.  
**Value:** major product differentiation.

## 4. Composable style profiles + reusable visual grammar
**Intent:** replace vague style prompting with deterministic production language.  
**Value:** creative breadth, brand consistency, faster output.

## 5. Automated visual / motion QA
**Intent:** verify more than “the file rendered.”  
**Value:** safe autonomy and fewer production mistakes.

---

# 35. North-Star Workflow

The final system should be able to receive:

> “Here is a 20-minute founder recording. Turn it into an 8-minute YouTube video. Use a modern editorial documentary style. Keep the founder visible when emotion or credibility matters, but create maps, charts, screenshots, document sequences, and layered editorial animations when they make the explanation clearer. Keep the pacing intelligent rather than hyperactive. Deliver a final MP4 plus editable source and a QC report.”

And execute:

```text
Ingest sources
↓
Hash + probe + sync
↓
Transcribe
↓
Analyze editorial events
↓
Build edit thesis
↓
Choose style profile
↓
Create rough cut
↓
Identify explanation gaps
↓
Create Visual Story Events
↓
Plan assets and rights
↓
Generate/process assets
↓
Build layered editorial scenes
↓
Compile source + generated timeline
↓
Add captions / music / SFX
↓
Render
↓
Run layout / motion / timing / audio QC
↓
Auto-repair bounded issues
↓
Review according to autonomy mode
↓
Export final MP4
↓
Deliver Remotion/editable source
↓
Deliver QC + provenance report
```

That is the target state.

It retains the strongest ideas from the current skill while extending it from a disciplined video-generation workflow into a broader **AI production and editing system**.
