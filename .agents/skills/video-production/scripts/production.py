"""Read-only checks for recorded collaborative production decisions.

V2 delegates to snapshot-aware sequential gates. V1 retains recorded-revision
compatibility checks. Neither authenticates user evidence or judges creative quality.
"""
from __future__ import annotations

import json
from pathlib import Path


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_state(state):
    """Return schema errors without changing decisions or feedback."""
    if not isinstance(state, dict):
        return ["Production state must be an object"]
    if state.get("version") == 2:
        from workflow_v2 import validate_v2
        return validate_v2(state)
    errors = []
    if type(state.get("version")) is not int or state["version"] != 1:
        errors.append("Production state version must be 1")
    if state.get("mode") not in ("collaborative", "autonomous"):
        errors.append("mode must be collaborative or autonomous")
    if state.get("phase") not in ("narration", "planning", "assets", "implementation", "review", "delivery"):
        errors.append("Unknown production phase")
    for key in ("planRevision", "projectRevision"):
        if not _text(state.get(key)):
            errors.append(f"{key} must be a nonempty revision ID")
    if state.get("assetsReadyRevision") is not None and not _text(state["assetsReadyRevision"]):
        errors.append("assetsReadyRevision must be null or a revision ID")
    for key in ("approvals", "scenes", "feedback"):
        if not isinstance(state.get(key), list) or not all(isinstance(item, dict) for item in state[key]):
            errors.append(f"{key} must be an array of objects")
    if errors:
        return errors
    for index, approval in enumerate(state["approvals"]):
        if (approval.get("scope") not in ("plan", "video")
                or approval.get("decision") not in ("approved", "changes-requested", "delegated")
                or not all(_text(approval.get(key)) for key in ("revision", "date", "evidence"))):
            errors.append(f"approvals[{index}] requires scope, revision, decision, date, and user evidence")
    scene_ids = set()
    for scene in state["scenes"]:
        number = scene.get("scene")
        if type(number) is not int or number < 1:
            errors.append("Scene IDs must be positive integers")
        elif number in scene_ids:
            errors.append(f"Duplicate scene {number}")
        else:
            scene_ids.add(number)
        if (not _text(scene.get("revision"))
                or scene.get("status") not in ("pending", "in-review", "changes-requested", "approved")):
            errors.append(f"Scene {number} requires a revision and valid review status")
    feedback_ids = set()
    for item in state["feedback"]:
        identifier = item.get("id")
        if not _text(identifier):
            errors.append("Feedback requires a nonempty id")
        elif identifier in feedback_ids:
            errors.append(f"Duplicate feedback {identifier}")
        else:
            feedback_ids.add(identifier)
        if not all(_text(item.get(key)) for key in ("scope", "request")):
            errors.append(f"Feedback {identifier} requires scope and original request")
        status = item.get("status")
        if status not in ("open", "implemented", "resolved", "deferred", "superseded"):
            errors.append(f"Feedback {identifier} has an invalid status")
        history = item.get("history")
        if (not isinstance(history, list) or not history
                or not all(isinstance(event, dict) and _text(event.get("date"))
                           and _text(event.get("note")) for event in history)):
            errors.append(f"Feedback {identifier} requires dated history notes")
        if status in ("resolved", "deferred") and not _text(item.get("resolution")):
            errors.append(f"Feedback {identifier} requires recorded confirmation/delegation in resolution")
    for item in state["feedback"]:
        if item.get("status") == "superseded":
            replacement = item.get("supersededBy")
            if not _text(replacement) or replacement not in feedback_ids or replacement == item.get("id"):
                errors.append(f"Feedback {item.get('id')} requires a different existing supersededBy ID")
    # A cycle could otherwise hide unresolved feedback behind superseded entries.
    if not errors:
        entries = {item["id"]: item for item in state["feedback"]}
        for identifier in entries:
            seen = set()
            current = identifier
            while entries[current]["status"] == "superseded":
                if current in seen:
                    errors.append(f"Feedback {identifier} has a supersession cycle")
                    break
                seen.add(current)
                current = entries[current]["supersededBy"]
    return errors


def decision(state, scope, revision):
    records = [entry for entry in state["approvals"]
               if entry["scope"] == scope and entry["revision"] == revision]
    return records[-1]["decision"] if records else None


def readiness_errors(state, stage, scene_ids):
    if isinstance(state, dict) and state.get("version") == 2:
        from workflow_v2 import readiness_v2
        return readiness_v2(state, stage, scene_ids)
    errors = validate_state(state)
    if errors:
        return errors
    if stage not in ("implement", "render"):
        raise ValueError(f"Unknown production stage: {stage}")
    plan_revision = state["planRevision"]
    project_revision = state["projectRevision"]
    allowed = {"approved", "delegated"} if state["mode"] == "autonomous" else {"approved"}
    if state.get("assetsReadyRevision") != plan_revision:
        errors.append(f"Required assets have not been accepted for {plan_revision}")
    if decision(state, "plan", plan_revision) not in allowed:
        errors.append(f"Current plan {plan_revision} requires approval or explicit autonomous delegation")
    if stage == "render":
        video_decision = decision(state, "video", project_revision)
        if video_decision not in allowed:
            errors.append(f"Current video {project_revision} requires approval or explicit autonomous delegation")
        expected = set(scene_ids)
        actual = {entry["scene"] for entry in state["scenes"]}
        if not expected or actual != expected:
            errors.append(f"Scene review coverage must match the composition: expected {sorted(expected)}, got {sorted(actual)}")
        delegated = state["mode"] == "autonomous" and video_decision == "delegated"
        for scene in state["scenes"]:
            if scene["revision"] != project_revision:
                errors.append(f"Scene {scene['scene']} review is stale for {project_revision}")
            if scene["status"] != "approved" and not delegated:
                errors.append(f"Scene {scene['scene']} is not user-approved")
        for item in state["feedback"]:
            if item["status"] in ("open", "implemented"):
                errors.append(f"Feedback {item['id']} remains {item['status']}; record its review resolution")
    return errors


def check_production(project, stage, scene_ids, state_path=None, required=False, scene=None):
    """Check optional project state before a mutation; raise an actionable error."""
    project = Path(project)
    path = Path(state_path).expanduser().resolve() if state_path is not None else project / "production-state.json"
    if not path.exists():
        if required or state_path is not None:
            raise ValueError(f"Missing production state: {path}")
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read production state {path}: {exc}") from exc
    if isinstance(state, dict) and state.get("version") == 2:
        from workflow_v2 import check_v2
        return check_v2(project, state, stage, scene_ids, scene)
    errors = readiness_errors(state, stage, scene_ids)
    for name in ("transcript.txt", "storyboard.json", "asset-plan.md", "implementation-plan.md", "edit-plan.json"):
        target = project / name
        if not target.is_file() or not target.stat().st_size:
            errors.append(f"Missing/empty planning artifact: {name}")
    if errors:
        raise ValueError("Production preflight failed:\n- " + "\n- ".join(errors))
    return state
