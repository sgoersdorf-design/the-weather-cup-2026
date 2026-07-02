#!/bin/zsh
set -e

PROJECT_DIR="/Users/steffengorsdorf/Documents/WM Projekt"
cd "$PROJECT_DIR"
mkdir -p logs

echo "WM MVP refresh started: $(date)"
.venv/bin/python -m python.pipelines.refresh_mvp_data "$@"
echo "WM MVP refresh finished: $(date)"
