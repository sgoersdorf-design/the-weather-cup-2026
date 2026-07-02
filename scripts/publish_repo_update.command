#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/steffengorsdorf/Documents/wm-projekt"
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
