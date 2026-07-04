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
git push origin main
