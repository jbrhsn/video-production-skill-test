"""Read-only checks for generated v2 and recorded-edit v3 production contracts."""
from __future__ import annotations

import json
from pathlib import Path

def validate_state(state):
    """Return schema errors without changing decisions or feedback."""
    if not isinstance(state, dict):
        return ["Production state must be an object"]
    if state.get("version") == 2:
        from workflow_v2 import validate_v2
        return validate_v2(state)
    if state.get("version") == 3 and state.get("track") == "recorded-edit":
        from recorded_workflow import validate_v3
        return validate_v3(state)
    return ["Unsupported production state version/track"]


def readiness_errors(state, stage, scene_ids):
    if not isinstance(state, dict) or state.get("version") != 2:
        return ["readiness_errors is the legacy v2 interface; use check_production for recorded projects"]
    from workflow_v2 import readiness_v2
    return readiness_v2(state, stage, scene_ids)


def check_production(project, stage, scene_ids=None, state_path=None, required=True, scene=None, draft=False):
    """Dispatch state and artifact checks without changing project decisions."""
    project = Path(project)
    path = Path(state_path).expanduser().resolve() if state_path is not None else project / "production-state.json"
    if not path.exists():
        raise ValueError(f"Missing production state: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read production state {path}: {exc}") from exc
    if isinstance(state, dict) and state.get("version") == 2:
        from workflow_v2 import check_v2
        if scene_ids is None:
            raise ValueError("Version-2 checks require scene IDs")
        return check_v2(project, state, stage, scene_ids, scene)
    if isinstance(state, dict) and state.get("version") == 3 and state.get("track") == "recorded-edit":
        from recorded_workflow import check_v3
        return check_v3(project, state, stage, scene, draft)
    raise ValueError("Unsupported production state version/track; do not migrate approvals implicitly")
