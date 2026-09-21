"""Sequential review gates and executable beat contracts for new productions."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path


def text(value):
    return isinstance(value, str) and bool(value.strip())


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_v2(state):
    from production import validate_state
    # Reuse the v1 feedback/history checks, but validate expanded approval scopes here.
    base = {**state, "version": 1, "phase": "review", "approvals": []}
    errors = validate_state(base)
    if type(state.get("version")) is not int or state["version"] != 2:
        errors.append("Production state version must be integer 2")
    if state.get("phase") not in ("narration", "planning", "assets", "plan-review",
                                   "implementation", "scene-review", "final-review", "delivery"):
        errors.append("Unknown v2 phase")
    if not text(state.get("narrationRevision")):
        errors.append("narrationRevision is required")
    active = state.get("activeScene")
    if active is not None and (type(active) is not int or active < 1):
        errors.append("activeScene must be null or a positive integer")
    pending = state.get("pendingReview")
    if pending is not None:
        if (not isinstance(pending, dict)
                or not all(text(pending.get(key)) for key in ("scope", "revision", "reviewTarget", "snapshot"))
                or not re.fullmatch(r"narration|plan|video|scene:[1-9][0-9]*", pending["scope"])
                or not re.fullmatch(r"[a-f0-9]{64}", pending["snapshot"])):
            errors.append("pendingReview requires scope, revision, reviewTarget, and SHA-256 snapshot")
    approvals = state.get("approvals")
    if not isinstance(approvals, list):
        return errors + ["approvals must be an array"]
    for entry in approvals:
        if not isinstance(entry, dict):
            errors.append("Approval must be an object")
            continue
        scope = entry.get("scope")
        if not text(scope) or not re.fullmatch(r"narration|plan|video|scene:[1-9][0-9]*", scope):
            errors.append("Approval scope must be narration, plan, scene:N, or video")
        if entry.get("decision") not in ("approved", "changes-requested", "delegated"):
            errors.append("Invalid approval decision")
        if not all(text(entry.get(key)) for key in ("revision", "date", "evidence", "reviewTarget")):
            errors.append("Approval requires revision, date, actual user evidence, and reviewTarget")
        if not isinstance(entry.get("snapshot"), str) or not re.fullmatch(r"[a-f0-9]{64}", entry["snapshot"]):
            errors.append("Approval requires a SHA-256 snapshot of the reviewed artifacts")
    return errors


def snapshot(project, scope):
    """Hash bounded project inputs, including filenames; never writes approval."""
    project = Path(project)
    paths = {project / "transcript.txt"}
    paths.update((project / "public/audio").rglob("*"))
    if scope != "narration":
        paths.update(project / name for name in ("storyboard.json", "asset-plan.md", "implementation-plan.md",
                                                 "execution-plan.json", "edit-plan.json"))
        for folder in ("assets", "public/media"):
            paths.update((project / folder).rglob("*"))
    if scope == "video" or scope.startswith("scene:"):
        paths.update(project / name for name in ("package.json", "package-lock.json", "tsconfig.json"))
        for path in (project / "src").rglob("*"):
            if scope.startswith("scene:") and path.parent == project / "src/scenes":
                if re.fullmatch(r"Scene[1-9][0-9]*\.tsx", path.name) and path.name != f"Scene{scope.split(':')[1]}.tsx":
                    continue
            paths.add(path)
        paths.update((project / "public").rglob("*"))
    digest = hashlib.sha256()
    for path in sorted(paths):
        if path.is_file():
            digest.update(str(path.relative_to(project)).encode())
            digest.update(b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def approved(state, scope, revision, project=None):
    records = [entry for entry in state["approvals"] if entry["scope"] == scope and entry["revision"] == revision]
    if not records:
        return False
    entry = records[-1]
    allowed = ("approved", "delegated") if state["mode"] == "autonomous" else ("approved",)
    return entry["decision"] in allowed and (project is None or entry["snapshot"] == snapshot(project, scope))


def readiness_v2(state, stage, scene_ids, scene=None, project=None):
    errors = validate_v2(state)
    if errors:
        return errors
    phases = {"plan": ("planning", "assets", "plan-review"),
              "implement": ("implementation", "scene-review", "final-review", "delivery"),
              "scene": ("implementation", "scene-review"), "render": ("final-review", "delivery")}
    if stage not in phases:
        return [f"Unknown v2 stage: {stage}"]
    if state["phase"] not in phases[stage]:
        errors.append(f"Phase {state['phase']} does not permit {stage}; finish the current gate first")
    if not approved(state, "narration", state["narrationRevision"], project):
        errors.append("Narration package approval is missing, revoked, or stale")
    if stage == "plan":
        return errors
    if state.get("assetsReadyRevision") != state["planRevision"]:
        errors.append("Required assets have not been accepted for the current plan")
    if not approved(state, "plan", state["planRevision"], project):
        errors.append("Refined plan approval is missing, revoked, or stale")
    rows = {row["scene"]: row for row in state["scenes"]}
    if set(rows) != set(scene_ids) or not scene_ids:
        errors.append("Scene state coverage must match narration/storyboard scene IDs")
    if stage == "scene":
        if scene not in rows or state.get("activeScene") != scene:
            errors.append("--scene must match the existing activeScene")
        for number, row in rows.items():
            if scene is not None and number < scene:
                if row["status"] != "approved" or not approved(state, f"scene:{number}", row["revision"], project):
                    errors.append(f"Scene {number} must be reviewed and approved before Scene {scene}")
    if stage == "render":
        if not approved(state, "video", state["projectRevision"], project):
            errors.append("Final Studio review / export approval is missing, revoked, or stale")
        for number, row in rows.items():
            if row["status"] != "approved" or not approved(state, f"scene:{number}", row["revision"], project):
                errors.append(f"Scene {number} review approval is missing or stale")
        for item in state["feedback"]:
            if item["status"] in ("open", "implemented"):
                errors.append(f"Feedback {item['id']} requires user review resolution")
    return errors


def local_file(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError(f"Invalid local asset path: {name!r}")
    candidate = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts or not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Asset path escapes project: {name}")
    if not candidate.is_file() or not candidate.stat().st_size:
        raise ValueError(f"Required file is missing/empty: {candidate}")
    return candidate


def narration_data(project):
    metadata = read(local_file(project, "public/audio/metadata.json"))
    rows = metadata["scenes"]
    transcript = local_file(project, "transcript.txt").read_text(encoding="utf-8")
    parts = [part.strip() for part in re.split(r"(?m)^\s*---\s*$", transcript) if part.strip()]
    if not rows or [row["scene"] for row in rows] != list(range(1, len(rows) + 1)) or len(parts) != len(rows):
        raise ValueError("Transcript and audio metadata must cover the same consecutive scenes")
    timestamps = {}
    for row, phrase in zip(rows, parts):
        duration = row["duration_s"]
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
            raise ValueError("Audio duration must be finite and positive")
        if " ".join(row.get("text", "").split()) != " ".join(phrase.split()):
            raise ValueError(f"Scene {row['scene']}: transcript differs from synthesized/imported text")
        audio = local_file(project / "public/audio", row["file"])
        stamp = row.get("timestamps_file", audio.stem + "-timestamps.json")
        data = read(local_file(project / "public/audio", stamp))
        words = data["words"]
        if not words or abs(data["duration_s"] - duration) > .02:
            raise ValueError(f"Scene {row['scene']}: empty or inconsistent timestamps")
        previous = 0
        for word in words:
            start, end = word["start"], word["end"]
            if (not text(word.get("word")) or type(start) not in (int, float) or type(end) not in (int, float)
                    or not 0 <= start <= end <= duration + .02 or start < previous):
                raise ValueError(f"Scene {row['scene']}: invalid word timing")
            previous = start
        timestamps[row["scene"]] = words
    return rows, timestamps


def validate_execution(project, scene_ids):
    """Validate coverage and concrete fields, not artistic quality or listening."""
    plan = read(local_file(project, "execution-plan.json"))
    rows, timestamps = narration_data(project)
    fps = plan.get("fps")
    if plan.get("version") != 1 or type(fps) is not int or fps <= 0:
        raise ValueError("Execution plan requires version 1 and positive integer fps")
    scenes = plan["scenes"]
    if [row["scene"] for row in scenes] != list(scene_ids) or list(scene_ids) != [row["scene"] for row in rows]:
        raise ValueError("Execution plan must match narration and storyboard scene coverage")
    for planned, audio in zip(scenes, rows):
        words = timestamps[planned["scene"]]
        covered = set()
        identifiers = set()
        last_start = -1
        for beat in planned["beats"]:
            for field in ("id", "quote", "initial", "action", "result", "acceptance"):
                if not text(beat.get(field)) or re.search(r"\b(TODO|TBD)\b", beat[field], re.I):
                    raise ValueError(f"Beat requires concrete {field}")
            if beat["id"] in identifiers:
                raise ValueError("Duplicate beat ID within scene")
            identifiers.add(beat["id"])
            first, end = beat["words"]  # zero-based, end exclusive
            start_frame, end_frame = beat["frames"]
            if (any(type(n) is not int for n in (first, end, start_frame, end_frame))
                    or not 0 <= first < end <= len(words)
                    or not 0 <= start_frame < end_frame <= math.ceil(audio["duration_s"] * fps)
                    or start_frame < last_start):
                raise ValueError("Invalid beat word/frame range or ordering")
            expected_start = math.floor(words[first]["start"] * fps)
            expected_end = math.ceil(words[end - 1]["end"] * fps)
            if (start_frame != expected_start or end_frame != expected_end) and not text(beat.get("timingReason")):
                raise ValueError("Beat differs from word anchors; document timingReason for anticipation/hold")
            quote = " ".join(word["word"].strip() for word in words[first:end])
            if " ".join(beat["quote"].split()) != " ".join(quote.split()):
                raise ValueError("Beat quote must match its checked timestamp word range")
            last_start = start_frame
            covered.update(range(first, end))
            layers = beat["layers"]
            if not isinstance(layers, dict) or set(layers) != {"bg", "mid", "fg"}:
                raise ValueError("Beat layers must contain bg, mid, fg (empty arrays allowed)")
            for entries in layers.values():
                if not isinstance(entries, list):
                    raise ValueError("Each layer must be an array of file paths or code:name references")
                for entry in entries:
                    if not text(entry):
                        raise ValueError("Empty layer reference")
                    if not entry.startswith("code:"):
                        if not entry.startswith("public/media/"):
                            raise ValueError("Selected file layers must use public/media paths")
                        local_file(project, entry)
                    elif len(entry) <= 5:
                        raise ValueError("Code visuals need a name")
            steps = beat.get("steps")
            if not isinstance(steps, list) or not steps or not all(text(step) for step in steps):
                raise ValueError("Beat requires ordered implementation steps")
        if covered != set(range(len(words))):
            raise ValueError(f"Scene {planned['scene']}: narration words are not fully mapped to beats")
    return plan


def check_v2(project, state, stage, scene_ids, scene=None):
    errors = readiness_v2(state, stage, scene_ids, scene, project)
    try:
        rows, _ = narration_data(project)
        if [row["scene"] for row in rows] != list(scene_ids):
            raise ValueError("Scene IDs differ from narration metadata")
        if stage != "plan":
            for name in ("storyboard.json", "asset-plan.md", "implementation-plan.md", "edit-plan.json"):
                local_file(project, name)
            validate_execution(project, scene_ids)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"Artifact check: {exc}")
    if errors:
        raise ValueError("Production preflight failed:\n- " + "\n- ".join(errors))
    return state
