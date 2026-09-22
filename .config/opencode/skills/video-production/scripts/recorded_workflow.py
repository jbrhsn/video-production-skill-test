"""Read-only state, snapshot, and readiness checks for recorded-edit v3 projects."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from recorded_contract import (read_json, validate_cut_plan, validate_recorded_execution,
                               validate_source_manifest, validate_sync_map)
from recorded_timeline import compile_project


SCOPES = re.compile(r"source|edit|plan|video|delivery|scene:[1-9][0-9]*")
PHASES = ("intake", "source-review", "edit-review", "planning", "plan-review",
          "implementation", "scene-review", "final-review", "delivery")


def validate_v3(state):
    errors = []
    if not isinstance(state, dict):
        return ["Production state must be an object"]
    if state.get("version") != 3 or state.get("track") != "recorded-edit":
        return ["Recorded projects require production state version 3 and track recorded-edit"]
    if state.get("mode") not in ("collaborative", "autonomous"):
        errors.append("mode must be collaborative or autonomous")
    if state.get("phase") not in PHASES:
        errors.append("Unknown recorded-edit phase")
    for key in ("sourceRevision", "editRevision", "planRevision", "projectRevision"):
        if not isinstance(state.get(key), str) or not state[key].strip():
            errors.append(f"{key} is required")
    if not isinstance(state.get("scenes"), list) or not isinstance(state.get("feedback"), list):
        errors.append("scenes and feedback must be arrays")
    pending = state.get("pendingReview")
    if pending is not None and (not isinstance(pending, dict)
            or not all(isinstance(pending.get(k), str) and pending[k] for k in ("scope", "revision", "reviewTarget", "snapshot"))
            or not SCOPES.fullmatch(pending["scope"]) or not re.fullmatch(r"[a-f0-9]{64}", pending["snapshot"])):
        errors.append("pendingReview requires a valid scope, revision, reviewTarget, and SHA-256 snapshot")
    if not isinstance(state.get("approvals"), list):
        errors.append("approvals must be an array")
        return errors
    for entry in state["approvals"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("scope"), str)
                or not SCOPES.fullmatch(entry["scope"])):
            errors.append("Invalid recorded approval scope")
            continue
        if entry.get("decision") not in ("approved", "changes-requested", "delegated"):
            errors.append("Invalid approval decision")
        if not all(isinstance(entry.get(k), str) and entry[k] for k in ("revision", "date", "evidence", "reviewTarget")):
            errors.append("Approval requires revision, date, evidence, and reviewTarget")
        if not isinstance(entry.get("snapshot"), str) or not re.fullmatch(r"[a-f0-9]{64}", entry["snapshot"]):
            errors.append("Approval requires a SHA-256 snapshot")
    return errors


def _paths(project: Path, scope: str):
    groups = {
        "source": ("brief.md", "source/manifest.json", "source/derivatives.json", "sync/map.json",
                   "analysis/observations.json", "source/sensitive-regions.json"),
        "edit": ("brief.md", "source/manifest.json", "source/derivatives.json", "sync/map.json",
                 "transcript/source-words.json", "analysis/observations.json", "analysis/cut-proposals.json",
                 "source/sensitive-regions.json", "cut-plan.json"),
        "plan": ("brief.md", "source/manifest.json", "source/derivatives.json", "sync/map.json",
                 "transcript/source-words.json", "source/sensitive-regions.json", "cut-plan.json",
                 "storyboard.json", "design-system.json", "execution-plan.json", "edit-plan.json",
                 "asset-plan.md", "asset-manifest.json", "implementation-plan.md"),
    }
    base = "source" if scope == "source" else "edit" if scope == "edit" else "plan"
    paths = {project / name for name in groups[base]}
    if scope.startswith("scene:") or scope in ("video", "delivery"):
        for name in ("package.json", "package-lock.json", "tsconfig.json"):
            paths.add(project / name)
        paths.update((project / "src").rglob("*"))
        paths.update((project / "public").rglob("*"))
        paths.update(path for path in (project / "scripts").rglob("*")
                     if "__pycache__" not in path.parts and path.suffix != ".pyc")
    if scope == "delivery":
        paths.update((project / "out").rglob("*"))
    return paths


def snapshot(project, scope):
    if not isinstance(scope, str) or not SCOPES.fullmatch(scope):
        raise ValueError("Invalid recorded snapshot scope")
    project = Path(project)
    digest = hashlib.sha256()
    for path in sorted(_paths(project, scope)):
        if path.is_file():
            digest.update(str(path.relative_to(project)).encode())
            digest.update(b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def approved(state, scope, revision, project=None):
    rows = [row for row in state["approvals"] if row["scope"] == scope and row["revision"] == revision]
    if not rows:
        return False
    allowed = ("approved", "delegated") if state["mode"] == "autonomous" else ("approved",)
    return rows[-1]["decision"] in allowed and (project is None or rows[-1]["snapshot"] == snapshot(project, scope))


def validate_project_artifacts(project: Path, stage):
    required = ["brief.md", "source/manifest.json", "sync/map.json",
                "analysis/observations.json", "source/sensitive-regions.json"]
    if stage != "source":
        required += ["analysis/cut-proposals.json", "cut-plan.json"]
    if stage not in ("source", "edit"):
        required += ["storyboard.json", "design-system.json", "execution-plan.json", "edit-plan.json",
                     "asset-plan.md", "asset-manifest.json", "implementation-plan.md"]
    missing = [name for name in required if not (project / name).is_file()]
    if missing:
        raise ValueError(f"Missing recorded project artifacts: {missing}")
    sources = validate_source_manifest(read_json(project / "source/manifest.json"), project)
    mappings = validate_sync_map(read_json(project / "sync/map.json"), sources)
    if stage == "source":
        return []
    clips = validate_cut_plan(read_json(project / "cut-plan.json"), sources, mappings)
    if stage == "edit":
        return [clip["id"] for clip in clips]
    execution = validate_recorded_execution(read_json(project / "execution-plan.json"), [clip["id"] for clip in clips])
    design = read_json(project / "design-system.json")
    colors = design.get("colors", {}) if isinstance(design, dict) else {}
    captions = design.get("captions", {}) if isinstance(design, dict) else {}
    if not isinstance(colors.get("background"), str) or not colors["background"].strip():
        raise ValueError("design-system colors.background is required for the composition canvas")
    words_path = project / "transcript/source-words.json"
    speech_present = False
    if words_path.is_file():
        words_data = read_json(words_path)
        speech_present = isinstance(words_data.get("words"), list) and bool(words_data["words"])
    if speech_present:
        for key in ("fontScale", "bottomInset"):
            value = captions.get(key)
            if type(value) not in (int, float) or not 0 < value < 1:
                raise ValueError(f"design-system captions.{key} must be a normalized positive number when speech captions are present")
    safe = execution.get("safeArea")
    if not isinstance(safe, dict) or any(type(safe.get(key)) not in (int, float) for key in ("top", "right", "bottom", "left")):
        raise ValueError("recorded execution plan requires normalized safeArea edges")
    if any(not 0 <= safe[key] < .5 for key in ("top", "right", "bottom", "left")):
        raise ValueError("recorded execution safeArea edges must be between 0 and 0.5")
    if speech_present and safe["bottom"] < captions["bottomInset"]:
        raise ValueError("execution safeArea.bottom cannot be smaller than captions.bottomInset")
    if stage in ("implement", "scene", "render", "delivery"):
        compiled = compile_project(project)
        existing = project / "src/timeline-data.json"
        if existing.is_file() and read_json(existing) != compiled:
            raise ValueError("Compiled recorded timeline is stale; rerun the recorded scaffold/compiler")
    return [scene["scene"] for scene in execution["scenes"]]


def readiness_v3(project: Path, state, stage, scene=None, draft=False):
    errors = validate_v3(state)
    if errors:
        return errors
    allowed_phases = {
        "source": ("source-review",), "edit": ("edit-review",),
        "plan": ("planning", "plan-review"),
        "implement": ("implementation", "scene-review", "final-review", "delivery"),
        "scene": ("implementation", "scene-review"),
        "render": ("final-review", "delivery"), "delivery": ("delivery",),
    }
    if stage not in allowed_phases:
        return [f"Unknown recorded stage: {stage}"]
    if state["phase"] not in allowed_phases[stage]:
        errors.append(f"Phase {state['phase']} does not permit {stage}")
    try:
        scene_ids = validate_project_artifacts(project, stage)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"Artifact check: {exc}")
        scene_ids = []
    if stage == "source":
        return errors
    if not approved(state, "source", state["sourceRevision"], project):
        errors.append("Source review approval is missing or stale")
    if stage == "edit":
        return errors
    if not approved(state, "edit", state["editRevision"], project):
        errors.append("Rough-cut approval is missing or stale")
    if stage == "plan":
        return errors
    if not approved(state, "plan", state["planRevision"], project):
        errors.append("Refined-plan approval is missing or stale")
    rows = {row.get("scene"): row for row in state["scenes"] if isinstance(row, dict)}
    if set(rows) != set(scene_ids):
        errors.append("Scene state coverage must match execution-plan scenes")
    if stage == "scene":
        if scene not in rows or state.get("activeScene") != scene:
            errors.append("--scene must match activeScene")
        order = state.get("reviewOrder", scene_ids)
        if sorted(order) != sorted(scene_ids):
            errors.append("reviewOrder must contain every scene exactly once")
        elif scene in order:
            for prior in order[:order.index(scene)]:
                row = rows[prior]
                if row.get("status") != "approved" or not approved(state, f"scene:{prior}", row.get("revision"), project):
                    errors.append(f"Scene {prior} must be approved before scene {scene} in reviewOrder")
    if stage in ("render", "delivery") and not draft:
        for number, row in rows.items():
            if row.get("status") != "approved" or not approved(state, f"scene:{number}", row.get("revision"), project):
                errors.append(f"Scene {number} approval is missing or stale")
        if not approved(state, "video", state["projectRevision"], project):
            errors.append("Final master review/export approval is missing or stale")
        for item in state["feedback"]:
            if item.get("status") in ("open", "implemented"):
                errors.append(f"Feedback {item.get('id')} requires review resolution")
    if stage == "delivery" and not approved(state, "delivery", state["projectRevision"], project):
        errors.append("Delivery acceptance is missing or stale")
    return errors


def check_v3(project, state, stage, scene=None, draft=False):
    errors = readiness_v3(Path(project), state, stage, scene, draft)
    if errors:
        raise ValueError("Recorded production preflight failed:\n- " + "\n- ".join(errors))
    return state
