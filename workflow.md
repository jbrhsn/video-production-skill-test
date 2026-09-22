# Faceless Video Production Workflow (Agent-Agnostic)

Local-first pipeline: script → voice → timestamps → storyboard → beat map → code (Remotion) → render.
Every phase ends with a **user gate**. The agent never advances past a gate without explicit approval recorded in `state.json`.

---

## 0. Ground Rules (apply to every phase)

1. **Working Directory (WD)** = the folder of ONE video, e.g. `<workspace>/videos/<video-slug>/`. A workspace can hold many video folders; each is self-contained. Never read or write outside the active WD (except installed dependencies).
2. **Files are memory.** At the start of every session the agent reads `WD/state.json`, then the latest `WD/feedback.md`. Never rely on chat history.
3. **Don't assume. Ask.** If a required decision is missing from `brief.md`, ask the user before proceeding. Batch questions; max one round per gate.
4. **Gates are hard stops.** Record approvals in `state.json` (`"approved"`, with date and short note).
5. **Hash and cache.** Narration text is hashed per scene. Only changed scenes regenerate audio, timing, and downstream plan items. Anything downstream of a change is marked `stale` until re-confirmed.
6. **The plan is the source of truth.** If feedback changes intent, update the plan files first, then the code.
7. **Log everything user-facing** in `feedback.md` (append-only): scene, beat, timecode, issue, severity, resolution.
8. **Agent limits (be honest about them):** the agent cannot watch motion or judge pacing/emotion. It can inspect still frames, run validators, and measure audio. Judgment on pacing, feel, and voice quality belongs to the user.

### Working Directory Layout

```
WD/
  state.json              # phase, gates, per-scene status, hashes
  feedback.md             # append-only structured feedback log
  brief.md                # Phase 0
  style_guide.md          # Phase 0
  script/
    script.md             # approved narration (source of truth)
    scenes.json           # scene split: id, text, hash
    pronunciations.json   # word → respelling overrides
  audio/
    s01.wav ...           # one file per scene
    audio_manifest.json   # engine, voice, speed, duration, hash, loudness
  timing/
    s01.words.json ...    # word-level start/end (sec + frame)
    timing_report.md      # alignment coverage and flagged words
  planning/
    storyboard.md         # creative direction per scene
    beats.json            # beat map (layers, anchors, sources)
    asset_requests.md     # AI prompts, stock keywords, specs
    asset_manifest.json   # source, license, status per asset
    editing_plan.json     # transitions, effects, captions, sound
    validation_report.md  # output of plan validator
    execution_plan.md     # agent-only build contract (frozen at gate)
  assets/                 # user-provided files (+ _placeholders/)
  remotion/               # code: index.ts, Root, scenes/, shared/
  review/                 # contact sheets, preview renders
  output/                 # final renders, captions, credits
```

### Local Environment Defaults (Apple Silicon, 16 GB unified memory, fanless)

| Need | Default | Notes |
|---|---|---|
| TTS | Kokoro | Fast, Apache 2.0. Optional A/B: Chatterbox (MIT, voice cloning). Models above ~5B params are not practical on 16 GB. |
| Speech alignment | Forced alignment of the known script against audio (e.g. stable-ts align, WhisperX-style). Fallback: Whisper word timestamps + fuzzy match to script | Whisper `small`/`medium` is enough since the script is known. Verify the chosen aligner runs on Apple Silicon before relying on it. |
| Audio tools | ffmpeg | Loudness, trimming, mixing, measurement |
| Video | Remotion (Node LTS) | Studio for review, CLI for render |

**Render guardrails (thermal throttling):** low `--concurrency` (start at 2), preview at reduced `--scale`, avoid heavy blur/shadow/SVG filters, pre-downscale large images, use video components that stream frames (not full decode). Render per-scene chunks when memory is tight.

---

## Phase 0: Brief and Style

**Purpose:** remove ambiguity before any generation.

1. **Intake (agent asks, user answers → `brief.md`):**
   - Topic, goal, audience, tone
   - Format: explainer (Vox-style) / doodle / screen tutorial / other
   - Target length; fps (default 30); resolution; aspect ratio(s) (each extra aspect ratio is separate scope)
   - Narration language, voice preference, speed
   - Captions: yes/no, style
   - Music/SFX: yes/no, source
   - Visual sources allowed: code-only / stock / AI-generated / user-made
   - Branding (colors, fonts, logo), reference videos
2. **Style guide (`style_guide.md`):** palette (tokens), fonts, type scale, easing curves, default motion durations, image treatment (grain, outline, shadows), caption style and safe zones, transition vocabulary (max 3–4 types), what to avoid.
3. **Environment check:** confirm tools installed and runnable (TTS, aligner, ffmpeg, Node, Remotion); free disk space; record versions in `state.json`.
4. **Init `state.json`.**

**GATE 0:** user approves `brief.md` + `style_guide.md`.

---

## Phase 1: Script → Voice → Timing

### 1.1 Script
- Agent drafts (or ingests) the script. Split into **scenes**: one idea each, default 10–40 s of narration.
- Write `script/script.md` and `script/scenes.json` (id, text, hash).
- Read-aloud rules: numbers, acronyms, and names spelled out how they should sound.

**GATE 1a:** user approves script and scene split.

### 1.2 Pronunciation and voice test
- Agent builds `pronunciations.json` from proper nouns, jargon, and acronyms; asks user about uncertain ones.
- Generate a **voice sample** (one representative paragraph) with the default engine; optionally with one alternative. User picks engine, voice, and speed. **Lock these in `brief.md`** for consistency across scenes.

### 1.3 Voiceover
- Generate one audio file per scene (cache by hash).
- Post-process consistently: trim, add fixed head/tail padding (default 0.3 s / 0.5 s, defined in `audio_manifest.json` so transitions have room), normalize each scene to the same loudness.
- Write `audio_manifest.json` (engine, voice, speed, duration, hash, loudness).

### 1.4 Timestamps
- Align each scene's audio to its exact script text → `timing/sXX.words.json`: `{index, word, start_sec, end_sec, start_frame, end_frame}`. `frame = round(sec × fps)`.
- Validate: every script word matched; report coverage %, low-confidence words, long gaps → `timing_report.md`.
- If the engine exposes its own token timings, use them as a cross-check.

### 1.5 Audio review and lock
- Agent lists audio files with durations and any flagged words. User listens to every scene.

**GATE 1b, AUDIO LOCK:** user approves audio + timing per scene.

**Unlock procedure (any later narration change):** edit script → hash changes → regenerate only affected scenes → re-align → mark dependent beats, assets, and plan entries `stale` → user re-approves the affected scenes.

---

## Phase 2: Creative Planning

Everything here is **plan only, no build code**. Use the timing JSON as the clock.

### 2.1 Storyboard (`storyboard.md`), per scene
- **What:** the idea the viewer must get
- **Why:** why this visual approach (metaphor, contrast, reveal, proof)
- **How:** mood, pacing (fast/slow), key on-screen text, visual motifs
- Follow the format guidance in Appendix A.

### 2.2 Beat map (`beats.json`)
Each scene splits into **beats** (default 2–8 s; min ~1 s). Each beat is **anchored to narration word indices**, not raw seconds, so the plan survives small audio changes. The build code converts anchors to frames from the timing JSON.

```json
{
  "scene": "s03",
  "beats": [{
    "id": "s03_b02",
    "anchor": {"from_word": 12, "to_word": 27},
    "layers": {
      "bg":  {"source": "code",  "ref": "GradientBG"},
      "mid": {"source": "ai",    "asset": "s03_b02_mid_city"},
      "fg":  {"source": "code",  "ref": "KineticText", "props": {"text": "..."}}
    },
    "motion": "slow push-in",
    "transition_out": "cut"
  }]
}
```
- Layers: **background, midground, foreground**. `source` ∈ `code | stock | ai | user`.
- Beats must cover the full scene duration with no gaps or overlaps (except planned transition overlaps).

### 2.3 Asset requests (`asset_requests.md` + `asset_manifest.json`)
For every non-code asset:
- **ID and naming:** `assets/<scene>_<beat>_<layer>_<slug>.<ext>`
- **Spec:** dimensions (at least target resolution ×1.2 if it will be zoomed/panned), format, transparency needed, orientation
- **AI-generated:** full prompt, negative prompt, style reference/seed notes, consistency instructions (same style tokens across all assets from `style_guide.md`)
- **Stock:** search keywords, duration needed, orientation, licence requirement. The agent cannot judge clips visually, so it asks the user to pick from a shortlist.
- **User-made:** exact description of what to create/record
- **Status:** `requested → placed → verified` (or `placeholder`)

**Placeholders:** the agent creates labelled placeholders (`assets/_placeholders/`) so planning and building are never blocked. No placeholder may reach final render (checked in Phase 4).

**Asset intake loop:** user places files in `assets/` and confirms → agent verifies (exists, dimensions, format, transparency, size) and **views each image** → updates storyboard/beat notes where the real asset differs from the plan → records source and licence in the manifest.

### 2.4 Editing and sound plan (`editing_plan.json`)
- Scene-to-scene transitions and durations (from the style guide's vocabulary)
- Per-beat effects (zoom, parallax, wipe, highlight, etc.)
- Captions: style, position, safe zones, highlight behavior
- Music: source, level relative to voice, ducking rule
- SFX cues anchored to beats
- Loudness target (default −14 LUFS integrated, true peak ≤ −1 dBTP)

### 2.5 Automated validation
Agent runs a validator and writes `validation_report.md`. Must pass with zero errors:
- Schemas valid
- Every referenced asset exists and is not stale
- Beats cover each scene's audio duration
- Anchors within word range
- Transition durations fit inside scene padding
- No unresolved `stale` items

### 2.6 Revision loop
User reviews storyboard + beat map + assets + editing plan; feedback is logged and applied to the plan files. Repeat until approved.

**GATE 2:** user approves the plan.

### 2.7 Execution plan (`execution_plan.md`), agent-only
Written **after** Gate 2, for the agent's own use in Phase 3. Contains:
- Build order: shared foundation first, then a **pilot scene**, then remaining scenes
- Per scene: ordered tasks, files to create, components to reuse/create, props, frame math, acceptance criteria
- Shared components list (captions, transitions, layout, layer/parallax, SVG stroke-draw, screen-zoom, etc.)
- Technical rules (see Phase 3.0)
- Known risks

**GATE 3:** user approves the execution plan. It is then frozen; changes require an explicit plan revision entry.

---

## Phase 3: Build and Review

### 3.0 Foundation
- Create `WD/remotion/` with its own entry file so the studio can be launched on this video alone (e.g. `npm run studio` or the equivalent command pointing at the video's entry file).
- Implement design tokens from `style_guide.md`.
- Root composition assembles scenes from `scenes.json` + `audio_manifest.json` + timing. **Durations come from audio data, never hard-coded.**
- Build shared components (captions, transitions, etc.).

**Technical rules (determinism):**
- All animation is frame-driven (`useCurrentFrame`), with no CSS transitions/animations
- No unseeded randomness; use the framework's seeded random
- No network access at render; all assets local; fonts loaded locally
- Load files via the framework's static-file helper
- Keep every layer within its planned safe area

### 3.1 Pilot scene
Build one representative scene fully (narration, layers, captions, transitions). Review it with the user before continuing. This calibrates style and catches plan mistakes cheaply.

**GATE 4:** user approves the pilot (or feedback loop until approved).

### 3.2 Per-scene loop (repeat for every remaining scene)
1. **Implement** per `execution_plan.md`.
2. **Self-check (agent):** typecheck/lint; render still frames at every beat boundary and mid-beat → `review/sXX_contact_sheet.png`; agent inspects: overflow, clipping, safe zones, missing/placeholder assets, caption sync at sampled frames, contrast.
3. **Hand-off to user:** scene id, how to open the studio and jump to the scene, timecodes to watch, what changed vs plan, known deviations, open questions.
4. **User review** in the studio. Feedback format: `scene / beat / timecode / issue / severity`. Agent logs it in `feedback.md`.
5. **Fix and re-hand-off** until approved. If feedback changes intent, update plan files first and re-validate.
6. **Approve:** set scene `approved` in `state.json`. If version control exists, commit with the scene id; otherwise snapshot the scene folder.
7. **Cumulative preview:** render a low-res preview of all approved scenes so far → `review/preview_upto_sXX.mp4`. The user checks the transition into and out of the new scene.

**Change propagation:** if a fix affects earlier or later scenes (shared component, style token, transition), the agent lists impacted scenes and marks them `needs_recheck`.

---

## Phase 4: Finalize

### 4.1 Full preview
Render a low-res full preview. The user watches start to finish for pacing, flow, audio balance, and caption readability. Feedback is logged and applied; re-render preview until approved.

### 4.2 Audio mix and mastering
- Mix narration + music + SFX per `editing_plan.json` (ducking under narration)
- Measure with ffmpeg loudness analysis; hit target LUFS and true-peak limit
- Report measured values in `release_notes.md`

### 4.3 QC checklist (agent runs, user spot-checks)
- [ ] Captions match the approved script (diff)
- [ ] No placeholders in `asset_manifest.json`
- [ ] All assets have source and licence recorded
- [ ] No black frames, gaps, or audio clicks at scene boundaries
- [ ] On-screen text spell-checked
- [ ] Safe zones respected; contrast acceptable
- [ ] Audio start/end trimmed correctly; no clipping
- [ ] Duration matches audio total

### 4.4 Final render
- Default: H.264 MP4 at the resolution/fps from the brief
- Thumbnail still (agent proposes frames; user picks)
- Captions file (`.srt`) derived from word timings
- `credits.md` generated from the asset manifest (attribution requirements)
- Other aspect ratios only if planned in the brief; otherwise treat as a new scope with its own Phase 2 re-plan

### 4.5 Delivery
- Everything in `output/`
- `release_notes.md`: versions, engine/voice settings, loudness, render settings, file hashes

**GATE 5:** user approves the final render. Mark project `complete` in `state.json`.

---

## Appendix A: Format Guidance (used in Phase 2)

**Vox-style explainer**
- Heavy on B-roll, archival material, maps, charts, kinetic text, and consistent motion language.
- Main risk is visual sourcing. Plan every beat's source early and prefer layered motion (parallax, push-ins) over static images.

**Doodle explainer**
- Needs a consistent illustration style. Every asset uses the same stroke weight, palette, and paper texture (set in `style_guide.md`).
- Draw-on effects: SVG stroke animation, or mask reveals for raster art. AI-generated raster art needs clean edges/transparent backgrounds; plan a vectorization or masking step if strokes must animate.
- Keep one idea on screen at a time; hand-draw timing follows word anchors.

**Screen recording tutorial**
- Add a **recording plan** to Phase 2: exact steps, resolution, cursor behavior, and app state. Recording is done by the user (or by a scripted browser session for web apps) and placed in `assets/`.
- Decide sync direction up front: narration paced to the recording, or recording re-timed to narration. Default: record after audio lock, following the timing JSON.
- Plan zoom/highlight/callout keyframes per beat; capture at 2× the target resolution to allow zooms.
- Mask sensitive information (emails, keys, personal data) before use.

## Appendix B: `state.json` Skeleton

```json
{
  "video": "<slug>",
  "phase": "1.3",
  "fps": 30,
  "env": {"tts": "...", "aligner": "...", "node": "...", "remotion": "..."},
  "gates": {
    "g0_brief_style": {"status": "approved", "date": "..."},
    "g1a_script": {"status": "approved", "date": "..."},
    "g1b_audio_lock": {"status": "pending"},
    "g2_plan": {"status": "pending"},
    "g3_execution_plan": {"status": "pending"},
    "g4_pilot": {"status": "pending"},
    "g5_final": {"status": "pending"}
  },
  "scenes": {
    "s01": {"script_hash": "...", "audio": "done", "timing": "done",
            "plan": "pending", "build": "pending", "approved": false, "stale": false}
  }
}
```

## Appendix C: When to Ask the User (non-exhaustive)
- Any brief field missing or contradictory
- Uncertain pronunciation of names/terms
- Stock clip or image selection
- A plan change that affects an approved scene
- A requested change that alters length, format, or aspect ratio (scope change)
- Any tool that fails to run locally, with proposed fallback (do not silently substitute)