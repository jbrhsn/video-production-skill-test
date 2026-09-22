# Video Editing Workflow (Existing Footage → Remotion)

Edits **fixed, already-recorded** footage (screen recording + voiceover, screen recording + talking head, or talking head alone). Source content cannot be regenerated — bad audio/video is a constraint to cut around, not a hash to invalidate and re-synthesize. Confirmed scope: single continuous take per topic (no best-take selection needed), output length is content-driven (no fixed-duration fitting), screen recording can switch sources/monitors within one video.

Same gate discipline as the faceless workflow: hard stops, `state.json` as memory, `feedback.md` append-only log.

---

## 0. Ground Rules

1. **WD** = `<workspace>/videos/<video-slug>/`. Self-contained, never touch outside it.
2. **Files are memory.** Every session starts by reading `WD/state.json` + latest `WD/feedback.md`.
3. **Don't assume — ask**, batched, max one round per gate.
4. **Gates are hard stops**, recorded in `state.json`.
5. **Source footage is immutable.** All processing is non-destructive: cut lists / EDLs reference original file + timecode range, never trim originals in place.
6. **The cut plan is the source of truth** downstream of transcript lock.
7. **Agent limits:** cannot judge pacing/delivery/emotion by watching. Can measure audio (silence, levels), detect filler words via transcript, detect source switches via frame-diffing, render stills, run validators. Pacing/feel/masking-completeness judgment stays with the user for final sign-off.
8. **Irreversibility bias.** Because nothing can be re-shot, any step that is hard to undo (masking, cut approval, sync lock) gets an explicit gate and a diff-style review, not a silent pass-through.

### WD Layout
```
WD/
  state.json
  feedback.md
  brief.md
  style_guide.md
  source/
    raw/                       # original files, read-only, untouched
    source_manifest.json       # file, duration, fps, resolution, codec, role, audio-present
  sync/
    sync_map.json               # per-checkpoint offset (not a single global offset)
    sync_report.md               # confidence, drift-per-checkpoint, unresolved segments
  transcript/
    transcript.txt
    transcript.json              # word-level timestamps
    cut_proposals.json           # auto-detected filler/silence/false-start ranges
    corrections_log.md
  screen_sources/
    source_switches.json         # timecode, resolution, app/monitor label, confidence
    sensitive_regions.json       # timecode range, bounding box, type (email/key/notification), status
    masking_report.md
  scenes/
    scenes.json                  # id, topic, source timecode range(s) per track, source-switch boundaries
    s01/
      audio.wav
      screen.mp4 (one or more, if multiple sources in-scene)
      talking_head.mp4 (if applicable)
      words.json
      samples/                    # sampled frames for this scene
  planning/
    content_classification.json  # per scene/segment: content type (code/terminal/browser/slides/design-tool/etc.), notes
    storyboard.md
    beats.json
    editing_plan.json
    masking_plan.json            # links sensitive_regions.json to a cover strategy per beat
    asset_requests.md / asset_manifest.json
    validation_report.md
    execution_plan.md
  assets/
  remotion/
  review/
    sXX_source_contact_sheet.png # sampled frames, one sheet per scene
  output/
```

---

## Phase 0: Brief and Style

- Intake: platform/aspect ratio(s), audience, tone, captions style, music/SFX policy, branding.
- **Editing-specific:** PiP vs full-bleed layout, cursor-highlight/zoom convention, B-roll allowed, masking policy for sensitive on-screen info (blur / solid box / crop-out / replace with placeholder graphic — pick one default, allow per-instance override).
- Confirm every source file opens and plays; record resolution/fps/codec/duration per file in `source_manifest.json`; flag any file with variable frame rate (common in screen recorders — breaks frame-accurate timing later if not normalized now).

**Edge cases**
- **Missing or corrupted source file:** stop, do not proceed with placeholders for primary narration/video — only asset-level placeholders are allowed later, never source-level.
- **Mismatched resolution/aspect ratio across sources** (e.g. 4K screen rec + 1080p webcam): record both natively; scaling decision belongs in Phase 2 layout planning, not silently normalized here.
- **Variable frame rate source:** flag and normalize to constant fps via ffmpeg before any timestamp work — VFR timestamps will not survive the transcript-alignment → frame-math pipeline.

**GATE 0:** user approves brief + style guide.

---

## Phase 1: Ingest, Sync, Transcript

### 1.1 Split and sync
- Split audio from each video source.
- Align talking-head and screen-recording tracks. Prefer a hard sync marker (clap, on-screen timestamp, shared audio bleed) over cross-correlation — cross-correlation on two mics in different rooms/gain levels is unreliable and should be treated as a low-confidence fallback, not a default.
- **Write sync as checkpoints, not one global offset.** Two independently-recorded devices drift against each other over time (clock drift), especially on long single-continuous takes. Re-check alignment every N minutes (e.g. every 5) using local audio correlation around that checkpoint; `sync_map.json` stores offset-per-checkpoint. Interpolate between checkpoints; flag if drift between adjacent checkpoints exceeds one frame — that segment needs manual confirmation.
- If no marker exists and correlation confidence is low: **ask the user for a manual anchor** (first shared word/action) rather than guessing. This is a hard stop, not a warning — an undetected desync breaks every downstream cut and can't be fixed by re-shooting.

**Edge cases**
- No audio on one track (silent screen recording): sync via visual cue instead (cursor click matched to a talking-head gesture/mouth movement) — lower confidence, flag for manual confirmation regardless.
- Talking-head track has gaps (camera briefly stopped/dropped frames): treat as a hard scene boundary at that point, not a continuous take — re-sync required on the far side.
- Recording length mismatch (one track much shorter): confirm with user whether the shorter one is the usable range or a separate/incomplete take.

### 1.2 Screen source detection
*(new — required because screen recording can switch monitors/apps within one video)*
- Frame-diff or scene-change detection across the screen-recording track to find source/app/monitor switches → `source_switches.json` (timecode, resolution if it changes, rough label like "browser" / "IDE" / "terminal").
- Independently, run a **sensitive-content pass**: detect visible emails, API keys/tokens, personal names, account numbers, notification pop-ups → `sensitive_regions.json` (timecode range, bounding box, type). This is pattern/OCR-assisted detection, not a guarantee — flag for user review, never auto-approve a mask as sufficient.

**GATE 1a:** user reviews `sensitive_regions.json` and confirms coverage (misses here are irreversible once published) and confirms/edits `source_switches.json` labels.

**Edge cases**
- Sensitive info visible for a single frame during a fast switch (e.g. flicker of a notification): still flag — a single frame is screenshot-able by viewers.
- Detector produces false positives on code that merely looks like a key (hashes, UUIDs in test data): user disposition each flagged region as mask/ignore rather than agent auto-deciding.
- New sensitive content discovered later (Phase 3 review): re-open this gate for that scene, do not patch silently in the build.

### 1.3 Transcript (Whisper)
- Generate `transcript.txt` + `transcript.json` from the primary voice track.
- Run filler-word / silence / false-start detection → `cut_proposals.json`, each with timecode range, type, confidence.

**GATE 1b:** user reviews `transcript.txt` (wording accuracy) and `cut_proposals.json` (approve/reject/edit each cut) as two separate review tasks.

**Edge cases**
- **Low-confidence words** (jargon, accents, background noise): list separately in `transcript.json` with a confidence flag; don't silently accept Whisper's best guess for technical terms — these are exactly the words most damaging to get wrong (product names, commands).
- **Thinking pauses vs. dead air:** a long pause while the speaker is visibly working (e.g. typing on screen, mid-demo) is not the same as a false start — cross-reference silence detection against screen-recording activity before proposing a cut; don't cut a silence that has active on-screen action underneath it.
- **Cut adjacent to a word boundary, not exactly on it:** proposed cut ranges must snap to nearest silence/breath gaps, never mid-word or mid-phoneme — validate this before presenting proposals, not after.
- **Cumulative jump-cut roughness:** many small approved cuts back-to-back can make audio sound chopped even if each cut is individually clean. Flag cut density per scene (cuts per minute above a threshold) and suggest either a small crossfade/L-cut treatment or consolidating adjacent cuts, since re-recording isn't an option to fix awkward pacing after the fact.

### 1.4 Sync corrections into JSON
- Apply approved text corrections and approved cuts to `transcript.json` (non-destructive — cut ranges are marked, not deleted from source).

---

## Phase 2: Scene Definition and Creative Planning

### 2.1 Scenes by content
- Define scenes at topic boundaries in the post-cut transcript.
- **Scene boundaries must also respect screen-source switches and sync checkpoints** — a scene should not silently straddle a monitor/app switch or a low-confidence sync segment without that being called out in the plan.
- `scenes.json`: id, topic, source timecode range(s) per track, transcript slice, associated screen-source segment(s), associated sensitive-region references.

**GATE 1c:** user approves scene split.

**Edge cases**
- A topic spans a screen-source switch mid-sentence (e.g. talks about switching from browser to IDE while still talking): keep as one scene, but flag the internal source switch as a beat-level layer change, not a scene break.
- A scene has no screen recording at all (pure talking-head aside): mark explicitly so the build phase doesn't expect a screen layer.
- A scene overlaps a segment with unresolved masking (Gate 1a not fully closed for that range): block scene approval until masking is resolved for that range.

### 2.2 Per-scene split
- Split audio/video per scene using the cut transcript.
- Regenerate per-scene `words.json`.
- Carry forward per-scene sync offset (from the nearest checkpoint) and any masking regions that fall in-range.

### 2.3 Visual sampling
*(new — grounds the plan in what's actually on screen instead of transcript/timing alone; this is squarely within the agent's allowed capability of inspecting stills)*
- For each scene, extract representative frames: scene start, scene end, every source-switch point (from `source_switches.json`), and a periodic sample through any uncut stretch longer than ~15s. Denser sampling around fast on-screen activity (rapid clicking/scrolling/typing) if that's detectable; sparse static content needs only a couple of frames to confirm nothing changes.
- Assemble into `review/sXX_source_contact_sheet.png` per scene.
- Classify each segment's screen content type (code/terminal, browser, slides, design tool, spreadsheet, doc, other) → `content_classification.json`. This drives which treatments actually fit: syntax-aware callouts for code, tab/URL emphasis for browser, wipe/slide transitions for slide decks, typewriter/keystroke emphasis for terminal — rather than one generic zoom-and-caption template applied everywhere.
- For talking-head frames: note framing/composition and background only (headroom, off-center, busy background) — **not** delivery or emotional read, which the agent cannot judge from stills. Framing notes inform PiP size/position per scene, not content decisions.
- Flag anything surprising immediately rather than holding it for Gate 2: unexpected app/content not caught by transcript-based cut planning, illegible/blurry text, watermarks or recording artifacts, additional sensitive content missed by the Phase 1 detector pass (route back to `sensitive_regions.json` and re-open Gate 1a for that scene if found).
- This sampling output feeds directly into storyboard/beats/editing-plan decisions in 2.4: animation style per content type, text-overlay placement that avoids busy UI regions, motion-graphic choices grounded in actual on-screen density, and SFX cues tied to visible actions (keystroke sound under visible typing, click sound at a visible cursor click, whoosh only where a real transition/switch happens) instead of generic cues applied on a timer.

**Edge cases**
- Long static stretch (e.g. two minutes on one unchanging code file): sampling confirms nothing visually changes — flag as a pacing risk and propose a motion-graphic treatment (progressive highlight, animated annotation) or a PiP emphasis shift to talking-head, rather than leaving a dead frame on screen for the full duration.
- Fast-changing content between samples: periodic sampling alone can miss a key action; increase sample density around detected activity rather than trusting a fixed interval.
- Contact sheet reveals content that contradicts the earlier scene/cut plan (e.g. an app switch mid-sentence that wasn't caught as a source-switch boundary): treat as a hold — revisit 2.1/1.2 for that range before continuing to plan on top of it.

### 2.4 Planning
- `storyboard.md`: what/why/how per scene, informed by `content_classification.json` and the contact sheets, not transcript alone.
- `beats.json`: word-anchored beats; layers = background / screen-recording (per source, if multiple) / talking-head / foreground / mask-overlay.
- **Screen-recording plan:** per-beat cursor highlight, zoom keyframes on clicks/actions, callout boxes, layout per source switch, and — grounded in 2.3 — a per-content-type animation/motion-graphic vocabulary (e.g. code gets highlight-line + line-number callouts, slides get crossfade/wipe, terminal gets keystroke-synced emphasis).
- SFX plan tied to visible on-screen actions confirmed in the contact sheet, not assumed from the transcript.
- `masking_plan.json`: links each `sensitive_regions.json` entry to a concrete cover strategy and confirms it holds through any zoom/crop applied in that beat.
- `editing_plan.json`: transitions, captions, music/SFX + ducking, loudness target, cut-smoothing treatment for high-cut-density scenes (from 1.3).
- Validator additions: masking region still covers the sensitive area at every applied zoom/crop level; no scene straddles an unresolved sync or masking issue; source-switch layout is defined for every switch inside a scene; every beat's animation/SFX choice traces back to a classified content type or a confirmed visible action, not a default template.

**GATE 2:** user approves full plan (contact sheets + storyboard + beats + editing plan + assets).

**Edge cases**
- Screen content itself is low quality/low-res at the point it needs to be zoomed in (common with multi-monitor captures at lower per-monitor resolution): flag as an asset issue — options are accept lower quality, crop tighter without zoom, or supplement with a redrawn/graphic callout instead of a raw zoom.
- Masking region moves within the frame across the beat (e.g. a notification that slides in and out, or cursor dragging over sensitive text): mask needs to be keyframed, not a static box — flag any moving sensitive region for keyframed masking, not a single bounding box.

### 2.5 Execution plan
Agent-only build contract, frozen after Gate 2: build order (shared components → pilot scene → rest), per-scene tasks, frame math, masking implementation approach, technical rules.

**GATE 3:** user approves execution plan.

---

## Phase 3: Build and Review

- **3.0 Foundation:** Remotion scaffold, design tokens, shared components (captions, zoom/highlight component, masking-overlay component, transitions). Durations from audio data, never hard-coded. Sync offsets applied per-checkpoint, not globally.
- **3.1 Pilot scene:** choose a scene that exercises a source switch and a masking region if one exists, in addition to normal talking-head/screen-rec layering — calibrates the riskiest mechanics first.

**GATE 4:** pilot approved.

- **3.2 Per-scene loop:** implement → self-check (contact sheets at beat boundaries; **specifically verify masking regions at zoomed frames, not just base frames**; verify sync holds at scene start/end against the nearest checkpoint) → hand off → user reviews in studio → feedback logged → fix → approve → cumulative low-res preview.

**Change propagation:** a masking miss or sync correction found mid-build invalidates every downstream scene sharing that source range or that region — flag and mark `needs_recheck`, never patch silently since the underlying footage can't be re-shot to fix it differently later.

**Edge cases**
- A fix to one scene's masking treatment implies the same sensitive content appears in another scene's screen-source segment (e.g. same browser tab visible again later): search `sensitive_regions.json` for recurring regions across scenes when one is fixed, don't treat each scene's masking as isolated.
- Cursor-highlight component behaves differently across screen-source resolutions (multi-monitor capture): confirm the component scales its highlight/zoom math per-source resolution, not a single hardcoded scale.

---

## Phase 4: Finalize

- Full low-res preview review: pacing, flow, sync drift across the whole timeline, audio balance, cut-smoothing quality.
- Audio mix/mastering to loudness target.
- **QC checklist:**
  - [ ] Captions match final cut transcript
  - [ ] No black frames, gaps, or audio clicks at any cut/scene boundary
  - [ ] No talking-head/screen-rec drift at any scene boundary (spot-check against sync checkpoints)
  - [ ] **Every entry in `sensitive_regions.json` is masked in the final render — check at actual output resolution, not preview resolution** (masks sized for preview can under-cover at full res)
  - [ ] No masked region exposed by a zoom/crop applied after masking was set
  - [ ] Safe zones/contrast respected
  - [ ] On-screen text spell-checked
- Final render, `.srt` captions, thumbnail, `credits.md` if B-roll used, `release_notes.md` including a masking sign-off line (who confirmed, when) given the irreversibility of a miss.

**GATE 5:** final approved.

**Edge cases**
- Different target aspect ratios need different crops of the same screen recording: a crop for vertical may cut a masked region out of frame (fine) or crop *into* an unmasked sensitive region that wasn't visible/flagged in the original 16:9 framing (not fine) — re-run the sensitive-content pass against each aspect-ratio crop separately, don't assume the 16:9 masking pass covers every derived aspect ratio.

---

## Appendix: Fallback rules when detection fails or is low-confidence
- Sync: no marker, low correlation confidence → ask user for manual anchor. Never proceed on an unconfirmed guess.
- Sensitive-content detection: any flagged region → user disposition required. Never auto-approve, never auto-reject.
- Filler/silence detection: any proposed cut overlapping active on-screen action → hold for explicit approval, do not include in a "safe to auto-approve" batch even if the audio pattern looks like a clear filler.
- Screen-source detection: ambiguous switch boundary (gradual transition, not a hard cut) → snap to the nearest stable frame and flag low confidence rather than picking an arbitrary frame.
