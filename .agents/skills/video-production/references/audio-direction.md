# Narration, mix, and captions

Read when directing speech or adding music/effects. Narration explains; visuals demonstrate; captions preserve speech access. Give the opening energy, let important distinctions breathe, and allow a takeaway to settle. Do not accelerate every passage to maximize density.

Kokoro remains the local default. Use phrasing, punctuation, sentence length, and supported speed/voice controls; inspect the installed implementation before claiming SSML, emotion, or phoneme control. Audition neighboring scene clips together for cadence and tone. If segmentation repeatedly harms delivery, synthesize a longer passage and implement timestamp-driven boundaries explicitly; the default scaffold still expects one WAV per scene. Do not pretend it automatically segments a longer take.

Preserve original narration files. Explicit edit-plan holds can add breathing room after speech without clipping or stretching it. Measured WAV spans include silence; compare captions with the approved transcript, since recognition is not forced alignment.

## Auditions and supplied recordings

For a long video, audition a short passage containing narrative phrasing, numbers, and a difficult name with a few supported voices. Use separate scratch output directories so auditions cannot overwrite production takes. Choose the voice and pronunciation approach before synthesizing chapters. The included CLI exposes voice and language, not emotion, SSML, or speed; do not pass unsupported flags. A requested human performance or exact narrator match may require supplied recording or an available authorized speech provider.

Import a recorded voiceover using `scripts/06_import_narration.py --manifest PROJECT/narration-import.json --out-dir PROJECT/public/audio`, run through the pipeline's uv environment. The output directory must not yet exist; for revisions import to a new take directory and explicitly replace selected production files after review. Example manifest:

```json
{"voice":"supplied narrator","lang":"en","scenes":[
  {"scene":1,"source":"recordings/full-take.wav","start_s":0,"end_s":12.4,"text":"The approved first scene narration."},
  {"scene":2,"source":"recordings/full-take.wav","start_s":12.4,"end_s":28.1,"text":"The approved second scene narration."}
]}
```

Source paths are relative to the manifest. Omit start/end to import a whole separate scene recording. Choose explicit trims at pauses after listening; this helper does not discover speech boundaries or validate spoken words. It converts the first audio stream to mono 24 kHz float WAV, validates duration and finite nonsilent samples, and produces scaffold-compatible metadata without modifying source recordings or normalizing their loudness. Keep `transcript.txt` consistent with the approved manifest text. Run `02_timestamps.py` for each resulting WAV, correct recognized words against the script, then scaffold normally. Continuous performance is preserved only if the selected trims preserve it; inspect joins and avoid duplicated breaths or cut words.

## Optional mix

Stage inspected, usable audio under `public/media/` and record provenance and usage rights. Add cues to edit-plan `audio`:

```json
{"src":"media/music.wav","role":"music","startFrame":0,"durationFrames":180,
 "volume":0.15,"duckVolume":0.06,"fadeFrames":8}
```

Set cue duration to the intended range within the compiled timeline; ensure the media actually covers it using ffprobe. Cues start from the beginning of their source; pre-trim a working copy for another in-point. The scaffold verifies file presence, not source duration or rights. `role` is music/effect. Gains range from 0 to 1; duck gain must not exceed normal gain. Fades cannot consume more than half a cue. Music ducks across speech segments with a short ramp; it does not analyze word gaps or source loudness. Effects are not automatically ducked. Neither cue type loops automatically.

Treat these as starting controls, not loudness normalization. Measure the full mix, choose a documented delivery target, check peaks and intelligibility, then listen on suitable speakers/headphones. Do not assert a universal platform LUFS rule. A -1 dBFS normalized speech source can still clip when mixed with music/effects. Adjust the mix after measurement. Cue meaningful actions; continuous ambience can bridge scenes; silence is valid.

Measure a rendered master with `ffmpeg -hide_banner -i PROJECT/out/video.mp4 -af loudnorm=print_format=json -f null -`. Record input integrated loudness and true peak from the report alongside the project's chosen targets. This is analysis with discarded output, not a mastered deliverable or a listening check. Adjust source/cue levels or implement a deliberate mastering pass, then remeasure. Store music/effect source, usage basis, trim, and cue intent in the asset manifest; the skill supplies no licensed music catalog.

## Captions

The included component groups words using punctuation, pauses, word count, and a width-based character budget, with optional active-word highlighting. It preserves speech words and hides captions in gaps. It is not font measurement or automatic layout certification. Inspect long words, fast speech, non-English scripts, punctuation, and narrow safe areas; adjust project typography/grouping deliberately. Keep titles and diagram labels out of the caption region. Prefer stable captions over decorative motion that makes reading harder.

For requested SRT/VTT exports, use corrected timestamp words offset by compiled narration starts (`start / fps`), not visual starts. Group into readable phrases without changing speech content. Include explicit holds in the start offsets. Validate chronological order and review the resulting captions. Burned captions and sidecar files must come from the same corrected timing source.
