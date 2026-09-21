# Narration, mix, and captions

Read when directing speech or adding music/effects. Narration explains; visuals demonstrate; captions preserve speech access. Give the opening energy, let important distinctions breathe, and allow a takeaway to settle. Do not accelerate every passage to maximize density.

Kokoro remains the local default. Use phrasing, punctuation, sentence length, and supported speed/voice controls; inspect the installed implementation before claiming SSML, emotion, or phoneme control. Audition neighboring scene clips together for cadence and tone. If segmentation repeatedly harms delivery, synthesize a longer passage and implement timestamp-driven boundaries explicitly; the default scaffold still expects one WAV per scene. Do not pretend it automatically segments a longer take.

Preserve original narration files. Explicit edit-plan holds can add breathing room after speech without clipping or stretching it. Measured WAV spans include silence; compare captions with the approved transcript, since recognition is not forced alignment.

## Optional mix

Stage inspected, usable audio under `public/media/` and record provenance and usage rights. Add cues to edit-plan `audio`:

```json
{"src":"media/music.wav","role":"music","startFrame":0,"durationFrames":180,
 "volume":0.15,"duckVolume":0.06,"fadeFrames":8}
```

Set cue duration to the intended range within the compiled timeline; ensure the media actually covers it using ffprobe. Cues start from the beginning of their source; pre-trim a working copy for another in-point. The scaffold verifies file presence, not source duration or rights. `role` is music/effect. Gains range from 0 to 1; duck gain must not exceed normal gain. Fades cannot consume more than half a cue. Music ducks across speech segments with a short ramp; it does not analyze word gaps or source loudness. Effects are not automatically ducked. Neither cue type loops automatically.

Treat these as starting controls, not loudness normalization. Measure the full mix, choose a documented delivery target, check peaks and intelligibility, then listen on suitable speakers/headphones. Do not assert a universal platform LUFS rule. A -1 dBFS normalized speech source can still clip when mixed with music/effects. Adjust the mix after measurement. Cue meaningful actions; continuous ambience can bridge scenes; silence is valid.

## Captions

The included component groups words using punctuation, pauses, word count, and a width-based character budget, with optional active-word highlighting. It preserves speech words and hides captions in gaps. It is not font measurement or automatic layout certification. Inspect long words, fast speech, non-English scripts, punctuation, and narrow safe areas; adjust project typography/grouping deliberately. Keep titles and diagram labels out of the caption region. Prefer stable captions over decorative motion that makes reading harder.

For requested SRT/VTT exports, use corrected timestamp words offset by compiled narration starts (`start / fps`), not visual starts. Group into readable phrases without changing speech content. Include explicit holds in the start offsets. Validate chronological order and review the resulting captions. Burned captions and sidecar files must come from the same corrected timing source.
