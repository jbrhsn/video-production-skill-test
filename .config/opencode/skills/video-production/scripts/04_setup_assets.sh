#!/usr/bin/env bash
# Run from the target workspace, or pass its explicit root.
set -euo pipefail
if [[ $# -gt 1 ]]; then
  echo "Usage: bash $0 [workspace-root]" >&2
  exit 2
fi
workspace="${1:-$PWD}"
[[ -d "$workspace" ]] || { echo "Workspace does not exist: $workspace" >&2; exit 2; }
assets_dir="$(cd "$workspace" && pwd)/.video_production_assets/kokoro"
release="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
mkdir -p "$assets_dir"
temporary=""
trap 'if [[ -n "$temporary" ]]; then rm -f -- "$temporary"; fi' EXIT
download() {
  local filename="$1" expected="$2" destination size
  destination="$assets_dir/$filename"
  if [[ -f "$destination" ]]; then
    size=$(wc -c < "$destination" | tr -d '[:space:]')
    if [[ "$size" == "$expected" ]]; then
      echo "Using cached $filename ($size bytes)"
      return
    fi
    echo "Replacing invalid $filename ($size bytes; expected $expected)"
  fi
  temporary=$(mktemp "$assets_dir/.download.XXXXXX")
  curl --fail --location --show-error --silent --retry 3 --connect-timeout 30 \
    --max-time 1800 --output "$temporary" "$release/$filename"
  size=$(wc -c < "$temporary" | tr -d '[:space:]')
  if [[ "$size" != "$expected" ]]; then
    echo "Invalid download: $filename has $size bytes; expected $expected" >&2
    exit 1
  fi
  mv -- "$temporary" "$destination"
  temporary=""
  echo "Downloaded $filename ($size bytes)"
}
# Release byte counts detect truncated responses, not malicious content.
# TTS additionally validates the archive and loads the ONNX model.
download kokoro-v1.0.onnx 325532387
download voices-v1.0.bin 28214398
echo "Assets ready: $assets_dir"
