"""Run live deploy verification and emit a local failure notification when it does not pass."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from python.pipelines.verify_live_deploy import DEFAULT_LIVE_URL, DEFAULT_LOCAL_HTML, verify_live_deploy

ROOT_DIR = Path(__file__).resolve().parents[2]
NOTIFIER = ROOT_DIR / "scripts/notify_refresh_failure.command"
FAILURE_REPORT = ROOT_DIR / "logs/latest_live_verify_failure.json"


def _notify_failure(message: str) -> None:
    command = [
        str(NOTIFIER),
        "WM Website Refresh fehlgeschlagen",
        message,
        "Netlify Live-Abgleich",
    ]
    subprocess.run(command, cwd=ROOT_DIR, check=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify live deploy and notify on failure")
    parser.add_argument("--file", default=str(DEFAULT_LOCAL_HTML))
    parser.add_argument("--url", default=DEFAULT_LIVE_URL)
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--max-wait-seconds", type=int, default=900)
    parser.add_argument("--poll-interval-seconds", type=int, default=30)
    args = parser.parse_args(argv)

    result = verify_live_deploy(
        local_html=Path(args.file),
        live_url=args.url,
        timeout_seconds=args.timeout_seconds,
        max_wait_seconds=args.max_wait_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

    FAILURE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    if result["status"] != "ok":
        FAILURE_REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        _notify_failure(
            f"Live-Site liefert nicht den erwarteten Stand {result.get('expected_exported_at')}. Details in logs/latest_live_verify_failure.json."
        )
        return 1

    if FAILURE_REPORT.exists():
        FAILURE_REPORT.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
