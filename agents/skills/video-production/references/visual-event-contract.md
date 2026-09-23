# Visual story events

A visual story event is the contract for a generated explanation inside a narration or recorded edit. It requires a stable ID, a dialogue clip occurrence, master frame range, purpose, presentation mode, layer ownership, visible sequence, acceptance criterion, and a source re-entry.

Use `background`, `midground`, and `foreground` only for assets or named code visuals that genuinely own a role. Empty layers are allowed. The sequence describes visible changes in order; it must let a reviewer verify the intended explanation occurred.

The re-entry names a specific picture clip occurrence and method. It keeps source PTS, captions, primary dialogue, and sound continuity explicit. Repeated source intervals are distinct occurrences, so an event never refers only to a source range.
