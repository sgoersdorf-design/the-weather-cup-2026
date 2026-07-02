"""Run the repeatable MVP refresh chain for data, scores, text and website export."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
EVENT_IMPORT_FILES = {
    "--players": "data/players.csv",
    "--team-sheets": "data/match_team_sheets.csv",
    "--appearances": "data/match_player_appearances.csv",
    "--events": "data/match_events.csv",
}
NON_BLOCKING_FAILURE_STEPS = {
    "dns_health",
    "fetch_schedule",
    "fetch_weather_forecast",
    "fetch_event_data",
    "import_venues",
    "import_schedule",
    "import_results",
    "import_ads",
    "import_weather_forecast",
    "context_metrics",
    "weather_matchups",
    "predictions",
    "texts",
    "db_status",
}
DEFAULT_STEP_TIMEOUT_SECONDS = 300
STEP_TIMEOUT_SECONDS = {
    "dns_health": 30,
    "fetch_schedule": 120,
    "fetch_weather_forecast": 240,
    "fetch_event_data": 240,
    "import_venues": 120,
    "import_schedule": 120,
    "import_results": 120,
    "import_ads": 120,
    "import_weather_forecast": 180,
    "import_match_event_data": 240,
    "context_metrics": 480,
    "weather_matchups": 480,
    "predictions": 480,
    "texts": 480,
    "website_export": 240,
    "standalone_html": 120,
    "deploy_html": 120,
    "browser_check_local": 90,
    "local_validation": 180,
    "db_status": 120,
}
RETRYABLE_STEPS = {
    "dns_health": 1,
    "fetch_schedule": 2,
    "fetch_weather_forecast": 2,
    "fetch_event_data": 2,
    "import_match_event_data": 1,
    "db_status": 1,
}
SUPABASE_DNS_HOSTS = [
    "aws-0-eu-west-1.pooler.supabase.com",
    "db.srcwznnkbhrtstqbkijx.supabase.co",
]


def _command(module: str, *args: str) -> list[str]:
    return [sys.executable, "-m", module, *args]


def _should_retry(name: str, stderr: str, stdout: str) -> bool:
    combined = f"{stderr}\n{stdout}".lower()
    if "temporary failure in name resolution" in combined:
        return True
    if "name or service not known" in combined:
        return True
    if "could not translate host name" in combined:
        return True
    if "nodename nor servname provided" in combined:
        return True
    if "failed to resolve" in combined:
        return True
    return name in {"fetch_schedule", "fetch_weather_forecast", "fetch_event_data"} and "timed out" in combined


def _run(name: str, command: list[str], dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {"name": name, "status": "dry_run", "command": command}
    timeout_seconds = STEP_TIMEOUT_SECONDS.get(name, DEFAULT_STEP_TIMEOUT_SECONDS)
    max_attempts = RETRYABLE_STEPS.get(name, 0) + 1
    attempts: list[dict[str, Any]] = []
    started_at = datetime.now().isoformat(timespec="seconds")
    for attempt in range(1, max_attempts + 1):
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT_DIR,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            duration_seconds = round(time.monotonic() - started, 2)
            stdout = (exc.stdout or "").strip()
            stderr = (exc.stderr or "").strip()
            attempts.append(
                {
                    "attempt": attempt,
                    "status": "timeout",
                    "returncode": None,
                    "stdout": stdout,
                    "stderr": stderr,
                    "duration_seconds": duration_seconds,
                }
            )
            if attempt < max_attempts:
                continue
            return {
                "name": name,
                "status": "failed",
                "returncode": None,
                "stdout": stdout,
                "stderr": stderr or f"Timed out after {timeout_seconds} seconds",
                "command": command,
                "attempts": attempts,
                "duration_seconds": round(sum(item["duration_seconds"] for item in attempts), 2),
                "timeout_seconds": timeout_seconds,
                "started_at": started_at,
            }

        duration_seconds = round(time.monotonic() - started, 2)
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        status = "ok" if completed.returncode == 0 else "failed"
        attempts.append(
            {
                "attempt": attempt,
                "status": status,
                "returncode": completed.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_seconds": duration_seconds,
            }
        )
        if completed.returncode == 0:
            break
        if attempt >= max_attempts or not _should_retry(name, stderr, stdout):
            break
    return {
        "name": name,
        "status": attempts[-1]["status"],
        "returncode": attempts[-1]["returncode"],
        "stdout": attempts[-1]["stdout"],
        "stderr": attempts[-1]["stderr"],
        "command": command,
        "attempts": attempts,
        "duration_seconds": round(sum(item["duration_seconds"] for item in attempts), 2),
        "timeout_seconds": timeout_seconds,
        "started_at": started_at,
    }


def _event_import_args() -> list[str]:
    args: list[str] = []
    for flag, relative_path in EVENT_IMPORT_FILES.items():
        if (ROOT_DIR / relative_path).exists():
            args.extend([flag, relative_path])
    return args


def _dns_health_result(dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {"name": "dns_health", "status": "dry_run", "command": _command("python.pipelines.check_dns_health")}
    return _run("dns_health", _command("python.pipelines.check_dns_health"))


def _supabase_dns_available(dns_health: dict[str, Any]) -> bool:
    try:
        payload = json.loads(dns_health.get("stdout") or "{}")
    except json.JSONDecodeError:
        return False
    host_status = {item.get("host"): item.get("status") for item in payload.get("hosts") or []}
    return any(host_status.get(host) == "ok" for host in SUPABASE_DNS_HOSTS)


def refresh_mvp_data(
    skip_schedule_fetch: bool = False,
    skip_weather_fetch: bool = False,
    skip_event_fetch: bool = False,
    with_event_db_import: bool = False,
    dry_run: bool = False,
    continue_on_error: bool = False,
) -> dict[str, Any]:
    """Refresh external data where possible and rebuild DB/UI derived outputs."""

    results = [_dns_health_result(dry_run=dry_run)]
    steps: list[tuple[str, list[str]]] = []
    if not skip_schedule_fetch:
        steps.append(
            (
                "fetch_schedule",
                _command("python.pipelines.fetch_openfootball_schedule", "--output", "data/full_schedule_openfootball.csv"),
            )
        )
    if not skip_weather_fetch:
        steps.append(
            (
                "fetch_weather_forecast",
                _command(
                    "python.pipelines.fetch_open_meteo_csv",
                    "--schedule",
                    "data/full_schedule_openfootball.csv",
                    "--venues",
                    "data/sample_venues.csv",
                    "--output",
                    "data/live_weather_forecast_full.csv",
                ),
            )
        )
    if not skip_event_fetch:
        steps.append(
            (
                "fetch_event_data",
                _command(
                    "python.pipelines.fetch_espn_event_data",
                    "--schedule",
                    "data/full_schedule_openfootball.csv",
                    "--teams",
                    "data/full_teams_restcountries.csv",
                ),
            )
        )

    steps.extend(
        [
            ("import_venues", _command("python.pipelines.import_venues", "--file", "data/sample_venues.csv")),
            ("import_schedule", _command("python.pipelines.import_schedule", "--file", "data/full_schedule_openfootball.csv")),
            ("import_results", _command("python.pipelines.import_results", "--file", "data/full_schedule_openfootball.csv")),
            ("import_ads", _command("python.pipelines.import_ads", "--file", "data/ad_inventory.csv")),
            ("import_weather_forecast", _command("python.pipelines.import_weather_forecast", "--file", "data/live_weather_forecast_full.csv")),
            ("context_metrics", _command("python.pipelines.context_metrics", "--all")),
            ("weather_matchups", _command("python.pipelines.weather_matchup", "--all")),
            ("predictions", _command("python.pipelines.generate_predictions", "--all", "--summary")),
            ("texts", _command("python.pipelines.generate_texts", "--all")),
            ("website_export", _command("python.pipelines.export_website_mvp")),
            ("standalone_html", _command("python.pipelines.build_standalone_mvp")),
            (
                "deploy_html",
                _command(
                    "python.pipelines.build_standalone_mvp",
                    "--output",
                    "website/deploy/index.html",
                ),
            ),
            ("browser_check_local", _command("python.pipelines.browser_check_local")),
            ("local_validation", _command("python.pipelines.validate_local")),
            ("db_status", _command("python.pipelines.db_status")),
        ]
    )

    event_import_args = _event_import_args()
    if with_event_db_import and event_import_args:
        insert_at = next(index for index, step in enumerate(steps) if step[0] == "context_metrics")
        steps.insert(insert_at, ("import_match_event_data", _command("python.pipelines.import_match_event_data", *event_import_args)))

    for name, command in steps:
        if name == "import_match_event_data" and not dry_run and not _supabase_dns_available(results[0]):
            results.append(
                {
                    "name": name,
                    "status": "skipped",
                    "returncode": None,
                    "stdout": "",
                    "stderr": "Skipped because Supabase DNS preflight failed; local CSV export path remains available.",
                    "command": command,
                    "attempts": [],
                    "duration_seconds": 0,
                    "timeout_seconds": STEP_TIMEOUT_SECONDS.get(name, DEFAULT_STEP_TIMEOUT_SECONDS),
                    "started_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            continue
        result = _run(name, command, dry_run=dry_run)
        results.append(result)
        if result["status"] == "failed" and not continue_on_error and name not in NON_BLOCKING_FAILURE_STEPS:
            break

    failed = [result for result in results if result["status"] == "failed" and result["name"] not in NON_BLOCKING_FAILURE_STEPS]
    warnings = [
        result
        for result in results
        if (result["status"] == "failed" and result["name"] in NON_BLOCKING_FAILURE_STEPS) or result["status"] == "skipped"
    ]
    return {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "status": "failed" if failed else "ok",
        "steps": results,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh WM 2026 MVP data and website export")
    parser.add_argument("--skip-schedule-fetch", action="store_true")
    parser.add_argument("--skip-weather-fetch", action="store_true")
    parser.add_argument("--skip-event-fetch", action="store_true")
    parser.add_argument("--with-event-db-import", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args(argv)
    output = refresh_mvp_data(
        skip_schedule_fetch=args.skip_schedule_fetch,
        skip_weather_fetch=args.skip_weather_fetch,
        skip_event_fetch=args.skip_event_fetch,
        with_event_db_import=args.with_event_db_import,
        dry_run=args.dry_run,
        continue_on_error=args.continue_on_error,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
