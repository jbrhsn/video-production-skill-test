"""Review state and input snapshots for the canonical production system."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from contracts import AUTONOMY_MODES, ROUTES, validate_project


SCOPES = {"source", "editorial", "pilot", "master", "delivery"}
PHASES = {"intake", "source-review", "editorial-review", "implementation", "pilot-review", "master-review", "delivery"}


def _state(data):
    if not isinstance(data, dict) or data.get("schema") != "production-state" or data.get("version") != 1:
        raise ValueError("production state requires schema production-state version 1")
    required = {"schema", "version", "projectId", "route", "autonomy", "phase", "pendingReview", "approvals", "feedback"}
    if set(data) != required:
        raise ValueError("production state fields must be exact")
    if not isinstance(data["projectId"], str) or not data["projectId"]:
        raise ValueError("production state requires projectId")
    if data["route"] not in ROUTES or data["autonomy"] not in AUTONOMY_MODES or data["phase"] not in PHASES:
        raise ValueError("production state route, autonomy, or phase is invalid")
    if data["pendingReview"] is not None and (not isinstance(data["pendingReview"], dict)
                                               or set(data["pendingReview"]) != {"scope", "target", "snapshot"}
                                               or data["pendingReview"].get("scope") not in SCOPES):
        raise ValueError("pending review is invalid")
    if not isinstance(data["approvals"], list) or not isinstance(data["feedback"], list):
        raise ValueError("approvals and feedback must be lists")
    for approval in data["approvals"]:
        if not isinstance(approval, dict) or set(approval) != {"scope", "decision", "target", "snapshot", "evidence"}:
            raise ValueError("approval fields must be exact")
        if approval["scope"] not in SCOPES or approval["decision"] not in {"approved", "changes-requested", "delegated"}:
            raise ValueError("approval scope or decision is invalid")
        if any(not isinstance(approval[key], str) or not approval[key] for key in ("target", "snapshot", "evidence")):
            raise ValueError("approval target, snapshot, and evidence are required")
    return data


def snapshot(project_dir, project):
    root = Path(project_dir)
    project = validate_project(project)
    digest = hashlib.sha256()
    # Review decisions and reports describe a run; they are not reviewed inputs.
    paths = sorted({root / path for name, path in project["artifacts"].items()
                    if name not in {"state", "qc", "delivery"}})
    for path in paths:
        if not path.is_file():
            continue
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def check_export(project_dir, project_path=None, state_path=None):
    root = Path(project_dir)
    project_path = Path(project_path) if project_path else root / "project.json"
    state_path = Path(state_path) if state_path else root / "production-state.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    state = _state(json.loads(state_path.read_text(encoding="utf-8")))
    validate_project(project)
    if state["projectId"] != project["id"] or state["route"] != project["route"] or state["autonomy"] != project["autonomy"]:
        raise ValueError("production state must match project route and autonomy")
    if state["pendingReview"] is not None:
        raise ValueError("export blocked by a pending review")
    current = snapshot(root, project)
    master = [row for row in state["approvals"] if row["scope"] == "master"]
    if not master:
        raise ValueError("export requires a master approval")
    decision = master[-1]
    permitted = {"approved"} if state["autonomy"] != "autonomous" else {"approved", "delegated"}
    if decision["decision"] not in permitted:
        raise ValueError("latest master decision does not authorize export")
    if decision["snapshot"] != current:
        raise ValueError("master approval is stale for the current project inputs")
    return {"snapshot": current, "approval": decision}
