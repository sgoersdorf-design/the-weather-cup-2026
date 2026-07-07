#!/bin/zsh
set -euo pipefail

CANONICAL_PROJECT_DIR="/Users/steffengorsdorf/Projects/wm-projekt"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -d "$CANONICAL_PROJECT_DIR" && "$PROJECT_DIR" != "$CANONICAL_PROJECT_DIR" ]]; then
  PROJECT_DIR="$CANONICAL_PROJECT_DIR"
fi
cd "$PROJECT_DIR"

commit_message="${1:-Automated WM refresh $(date '+%Y-%m-%d %H:%M:%S')}"
notify_failure() {
  scripts/notify_refresh_failure.command \
    "WM Website Publish fehlgeschlagen" \
    "$1" \
    "GitHub/Netlify Publish" >/dev/null 2>&1 || true
}

push_with_retry() {
  local max_attempts=3
  local attempt=1
  while [[ "$attempt" -le "$max_attempts" ]]; do
    echo "Pushing to origin main (attempt $attempt/$max_attempts)..."
    if git push origin main; then
      return 0
    fi

    if [[ "$attempt" -lt "$max_attempts" ]]; then
      echo "Push failed; syncing with origin/main before retry..."
      git fetch origin main || true
      git pull --rebase origin main || true
      sleep $((attempt * 10))
    fi
    attempt=$((attempt + 1))
  done
  return 1
}

if [[ -z "$(git status --short)" ]]; then
  echo "No repository changes to publish."
  exit 0
fi

git add -A

if git diff --cached --quiet; then
  echo "No staged changes after git add."
  exit 0
fi

git commit -m "$commit_message"
if ! push_with_retry; then
  notify_failure "Git push nach mehreren Versuchen fehlgeschlagen. Bitte Netzwerk/GitHub und den lokalen Branch prüfen."
  exit 128
fi

echo "Verifying Netlify live deploy..."
.venv/bin/python -u -m python.pipelines.run_and_verify_live_deploy
