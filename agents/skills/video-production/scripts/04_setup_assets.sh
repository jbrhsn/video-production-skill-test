#!/usr/bin/env bash
# Compatibility wrapper. Run from the target workspace, or pass its explicit root.
set -euo pipefail
if [[ $# -gt 1 ]]; then
  echo "Usage: bash $0 [workspace-root]" >&2
  exit 2
fi
workspace="${1:-$PWD}"
[[ -d "$workspace" ]] || { echo "Workspace does not exist: $workspace" >&2; exit 2; }
workspace="$(cd "$workspace" && pwd)"
script_dir="$(cd "$(dirname "$0")" && pwd)"
interpreter="$workspace/.venv/bin/python"
[[ -x "$interpreter" ]] || interpreter="$workspace/.venv-video-production/bin/python"
if command -v uv >/dev/null 2>&1 && [[ -x "$interpreter" ]]; then
  exec uv run --no-project --python "$interpreter" python "$script_dir/model_cache.py" --workspace-root "$workspace" --require kokoro --ensure
fi
if [[ -x "$interpreter" ]]; then
  echo "WARNING: uv is unavailable; using the project-local interpreter directly." >&2
  exec "$interpreter" "$script_dir/model_cache.py" --workspace-root "$workspace" --require kokoro --ensure
fi
echo "ERROR: uv or a project-local .venv/.venv-video-production interpreter is required." >&2
exit 1
