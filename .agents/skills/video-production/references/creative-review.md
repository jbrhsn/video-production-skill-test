# Creative review and iteration

Read before delivering a publishable project. Use specific observations and fixes rather than a fabricated engagement score.

Review the promise/payoff, progression of understanding, visual explanation, motion continuity, readability, speech/mix clarity, and intended platform composition. For each issue, record a scene or master timestamp, what failed, why it matters, and a concrete correction. Watch muted, listen without visuals, then review the combined video. Metadata and stills cannot establish smooth motion or intelligible speech.

`scripts/05_review_bundle.py --project-dir PROJECT` prepares a review manifest and report without rendering. Add `--render` to execute the listed scene, boundary, full-video, and still renders plus a contact sheet. This is a rendering operation, so honor any user request to pause before testing. Run through the pipeline's uv environment. The helper expects the new visual-only timeline contract and installed local dependencies; legacy projects use the manual review commands in the pipeline reference.

The report distinguishes render execution from editorial/playback review. A completed render is not a passed creative review. Inspect `BoundaryN` for joins; isolated `SceneN` lacks the master music/effects. Inspect final master playback as well as opening, dense, boundary, and final frames. `SafeAreaReview` is available for additional placement inspection; the bundle does not automatically validate platform UI coverage.

When authorized analytics exports are available, map observations to master timestamps and beat IDs. Compare similar formats, durations, audiences, and traffic sources; record sample and time-window limitations. Inspect drops for stalled value, confusing graphics, or unreadable pacing. Replay spikes may indicate either interest or confusion; [YouTube's audience-retention guidance](https://support.google.com/youtube/answer/9314415?hl=en) describes that ambiguity. Treat causes as hypotheses until tested. Propose one controlled change, keep its baseline, and evaluate against the same defined outcome.

Without analytics, report editorial hypotheses only. Do not claim measured retention improvements from a polished preview, a score, or observed popularity. Publishing, external account access, and fetching private analytics require the relevant authorization; the local review helper does none of those.
