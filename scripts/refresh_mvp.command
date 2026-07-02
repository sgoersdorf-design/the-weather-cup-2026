#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/steffengorsdorf/Documents/WM Projekt"
cd "$PROJECT_DIR"
mkdir -p logs

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
.venv/bin/python -m python.pipelines.refresh_mvp_data "${refresh_args[@]}"
if [[ "$auto_publish" -eq 1 ]]; then
  echo "WM MVP publish started: $(date)"
  scripts/publish_repo_update.command
  echo "WM MVP publish finished: $(date)"
fi
echo "WM MVP refresh finished: $(date)"
