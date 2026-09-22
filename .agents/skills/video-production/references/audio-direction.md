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

## Planned mix

Decide music, ambience and effects during creative planning. Each may be deliberately `none`; sound is not an effect quota. Register every selected sound in `asset-manifest.json`, stage it under `public/media/`, and record source, usage rights, attribution, inspection and hash when used. Version-2 edit plans reference the manifest asset ID and a shared visual event or other stable anchor:

```json
{"id":"cue-filter-contact","assetId":"sfx-paper-contact","role":"effect",
 "purpose":"Confirm the note contacting the filter, not decorate the cut","required":true,
 "anchor":{"type":"event","scene":2,"beat":"s02-b03","event":"contact","offsetFrames":0},
 "durationFrames":18,"sourceStartSeconds":0.08,"gainDb":-9,"duckGainDb":-9,
 "duckAttackFrames":4,"duckReleaseFrames":6,"fadeInFrames":0,"fadeOutFrames":4,
 "acceptance":"Audible at contact without masking the word filter"}
```

Execution-plan version 2 declares named events inside checked beat frame ranges. Visual code and audio cues reference that same event ID. Other anchors are checked word boundaries, scene speech start/end, scene span end, transition boundary, master start/end, or a reasoned absolute frame. The compiler resolves master frames after holds; do not copy master frame numbers into visual code. Align the audible transient, not merely the beginning of a file.

Set cue duration and source in-point explicitly. Scaffold uses ffprobe to reject missing/short selected sources. Roles are music, ambience or effect. Gains are dB and are converted once for rendering. Fade-in and fade-out are independent; music duck attack/release applies around scene narration spans, not every word gap. Effects only duck when deliberately configured. Cues do not loop. Use a pre-edited sufficiently long file or explicit repeated segments until seamless loop behavior is intentionally implemented.


Treat gain values as starting controls, not loudness normalization. Measure the full mix, choose a documented delivery target, check peaks and intelligibility, then listen on suitable speakers/headphones. A possible house starting point is -16 LUFS integrated ±1 LU and true peak no higher than -1 dBTP, but it is not a universal platform rule. Short programs or substantial silence can make integrated figures less useful. A -1 dBFS peak-normalized speech source can still clip when mixed. Cue meaningful actions; continuous ambience can bridge scenes; silence is valid.

Measure an authorized rendered master with `scripts/10_audio_qc.py --input PROJECT/out/video.mp4 --out PROJECT/out/audio-qc.json` and the project's target flags. This is analysis, not a mastered deliverable or a listening check. Adjust source/cue levels or implement a deliberate mastering pass, then remeasure and re-review material audible changes. The skill supplies no licensed music catalog.

## Captions

The included component groups words using punctuation, pauses, word count, and a width-based character budget, with optional active-word highlighting. It preserves speech words and hides captions in gaps. It is not font measurement or automatic layout certification. Inspect long words, fast speech, non-English scripts, punctuation, and narrow safe areas; adjust project typography/grouping deliberately. Keep titles and diagram labels out of the caption region. Prefer stable captions over decorative motion that makes reading harder.

For requested SRT/VTT exports, use corrected timestamp words offset by compiled narration starts (`start / fps`), not visual starts. Group into readable phrases without changing speech content. Include explicit holds in the start offsets. Validate chronological order and review the resulting captions. Burned captions and sidecar files must come from the same corrected timing source.
