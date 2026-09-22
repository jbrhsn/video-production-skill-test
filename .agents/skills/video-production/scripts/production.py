"""Read-only checks for the version-2 collaborative production contract."""
from __future__ import annotations

import json
from pathlib import Path

def validate_state(state):
    """Return schema errors without changing decisions or feedback."""
    if not isinstance(state, dict):
        return ["Production state must be an object"]
    if state.get("version") != 2:
        return ["Only production state version 2 is supported"]
    from workflow_v2 import validate_v2
    return validate_v2(state)


def readiness_errors(state, stage, scene_ids):
    if not isinstance(state, dict) or state.get("version") != 2:
        return ["Only production state version 2 is supported"]
    from workflow_v2 import readiness_v2
    return readiness_v2(state, stage, scene_ids)


def check_production(project, stage, scene_ids, state_path=None, required=True, scene=None):
    """Check required version-2 state before a production mutation."""
    project = Path(project)
    path = Path(state_path).expanduser().resolve() if state_path is not None else project / "production-state.json"
    if not path.exists():
        raise ValueError(f"Missing production state: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read production state {path}: {exc}") from exc
    if not isinstance(state, dict) or state.get("version") != 2:
        raise ValueError("Only version-2 production state is supported; create a new v2 production instead of migrating approvals")
    from workflow_v2 import check_v2
    return check_v2(project, state, stage, scene_ids, scene)
