"""Verify that the live Netlify site serves the latest exported MVP payload."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_LOCAL_HTML = Path("website/deploy/index.html")
DEFAULT_LIVE_URL = "https://the-weather-cup-2026.netlify.app/"
PAYLOAD_PREFIX = "window.WM_MVP_DATA = "


def _extract_payload(html: str) -> dict[str, Any]:
    start = html.find(PAYLOAD_PREFIX)
    if start == -1:
        raise ValueError("Embedded WM_MVP_DATA payload not found")
    start += len(PAYLOAD_PREFIX)
    end = html.find("</script>", start)
    if end == -1:
        raise ValueError("Embedded WM_MVP_DATA payload is not terminated correctly")
    payload = html[start:end].strip()
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


def _read_local_exported_at(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    payload = _extract_payload(html)
    metadata = payload.get("metadata") or {}
    exported_at = metadata.get("exported_at") or metadata.get("generated_at")
    if not exported_at:
        raise ValueError(f"No exported_at metadata found in {path}")
    return str(exported_at)


def _cache_busted_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("codex_verify_ts", str(int(time.time()))))
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))


def _fetch_live_html(url: str, timeout_seconds: int) -> str:
    cache_busted_url = _cache_busted_url(url)
    command = [
        "curl",
        "-fsSL",
        "--max-time",
        str(timeout_seconds),
        "-H",
        "User-Agent: wm-projekt-live-verifier/1.0",
        "-H",
        "Cache-Control: no-cache",
        "-H",
        "Pragma: no-cache",
        cache_busted_url,
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def _read_live_exported_at(url: str, timeout_seconds: int) -> str:
    html = _fetch_live_html(url, timeout_seconds)
    payload = _extract_payload(html)
    metadata = payload.get("metadata") or {}
    exported_at = metadata.get("exported_at") or metadata.get("generated_at")
    if not exported_at:
        raise ValueError(f"No exported_at metadata found on live site {url}")
    return str(exported_at)


def _parse_exported_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def verify_live_deploy(
    local_html: Path = DEFAULT_LOCAL_HTML,
    live_url: str = DEFAULT_LIVE_URL,
    timeout_seconds: int = 15,
    max_wait_seconds: int = 900,
    poll_interval_seconds: int = 30,
) -> dict[str, Any]:
    expected_exported_at = _read_local_exported_at(local_html)
    expected_exported_at_dt = _parse_exported_at(expected_exported_at)
    deadline = time.monotonic() + max_wait_seconds
    attempts: list[dict[str, Any]] = []
    last_error: str | None = None

    while True:
        try:
            live_exported_at = _read_live_exported_at(live_url, timeout_seconds)
            attempts.append({"status": "ok", "live_exported_at": live_exported_at})
            print(
                f"[live-verify] local={expected_exported_at} live={live_exported_at} attempt={len(attempts)}",
                flush=True,
            )
            if _parse_exported_at(live_exported_at) >= expected_exported_at_dt:
                return {
                    "status": "ok",
                    "live_url": live_url,
                    "local_html": str(local_html),
                    "expected_exported_at": expected_exported_at,
                    "live_exported_at": live_exported_at,
                    "attempts": attempts,
                }
            last_error = (
                f"Live exported_at mismatch: expected {expected_exported_at}, got {live_exported_at}"
            )
            attempts[-1]["status"] = "mismatch"
            attempts[-1]["error"] = last_error
        except (subprocess.CalledProcessError, TimeoutError, ValueError) as exc:
            last_error = str(exc)
            attempts.append({"status": "error", "error": last_error})
            print(f"[live-verify] attempt={len(attempts)} error={last_error}", flush=True)

        if time.monotonic() >= deadline:
            return {
                "status": "failed",
                "live_url": live_url,
                "local_html": str(local_html),
                "expected_exported_at": expected_exported_at,
                "live_exported_at": attempts[-1].get("live_exported_at") if attempts else None,
                "attempts": attempts,
                "error": last_error or "Live verification timed out",
            }
        print(
            f"[live-verify] waiting {poll_interval_seconds}s for Netlify to serve {expected_exported_at}",
            flush=True,
        )
        time.sleep(poll_interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Netlify serves the latest exported WM payload")
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
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
