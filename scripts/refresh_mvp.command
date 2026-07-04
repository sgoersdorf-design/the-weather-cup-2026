#!/bin/zsh
set -euo pipefail

CANONICAL_PROJECT_DIR="/Users/steffengorsdorf/Projects/wm-projekt"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -d "$CANONICAL_PROJECT_DIR" && "$PROJECT_DIR" != "$CANONICAL_PROJECT_DIR" ]]; then
  PROJECT_DIR="$CANONICAL_PROJECT_DIR"
fi
cd "$PROJECT_DIR"
mkdir -p logs
mkdir -p .run

LOCK_DIR="$PROJECT_DIR/.run/refresh_mvp.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "WM MVP refresh skipped: another run is already active ($(date))"
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

auto_publish=0
refresh_args=()
for arg in "$@"; do
  if [[ "$arg" == "--auto-publish" ]]; then
    auto_publish=1
    continue
  fi
  refresh_args+=("$arg")
done

echo "WM MVP refresh started: $(date)"
.venv/bin/python -u -m python.pipelines.refresh_mvp_data "${refresh_args[@]}"
if [[ "$auto_publish" -eq 1 ]]; then
  echo "WM MVP publish started: $(date)"
  scripts/publish_repo_update.command
  echo "WM MVP publish finished: $(date)"
fi
echo "WM MVP refresh finished: $(date)"
