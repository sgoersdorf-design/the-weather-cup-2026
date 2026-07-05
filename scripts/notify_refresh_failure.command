#!/bin/zsh
set -euo pipefail

CANONICAL_PROJECT_DIR="/Users/steffengorsdorf/Projects/wm-projekt"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -d "$CANONICAL_PROJECT_DIR" && "$PROJECT_DIR" != "$CANONICAL_PROJECT_DIR" ]]; then
  PROJECT_DIR="$CANONICAL_PROJECT_DIR"
fi

mkdir -p "$PROJECT_DIR/logs"

title="${1:-WM Website Refresh fehlgeschlagen}"
message="${2:-Der automatische Netlify-Abgleich ist fehlgeschlagen. Bitte Logs prüfen.}"
subtitle="${3:-the-weather-cup-2026}"
timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
log_line="[$timestamp] $title | $subtitle | $message"

echo "$log_line" >> "$PROJECT_DIR/logs/refresh_alerts.log"
logger -t wm-projekt "$log_line" || true

if command -v osascript >/dev/null 2>&1; then
  osascript <<EOF >/dev/null 2>&1 || true
on run
  display notification "$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')" with title "$(printf '%s' "$title" | sed 's/\\/\\\\/g; s/"/\\"/g')" subtitle "$(printf '%s' "$subtitle" | sed 's/\\/\\\\/g; s/"/\\"/g')"
end run
EOF
fi

echo "$log_line"
