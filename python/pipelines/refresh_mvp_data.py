"""Run the repeatable MVP refresh chain for data, scores, text and website export."""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
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
STEP_HEARTBEAT_SECONDS = 15


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


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print_progress(message: str) -> None:
    print(f"[{_timestamp()}] {message}", flush=True)


def _stream_process_output(
    name: str,
    command: list[str],
    timeout_seconds: int,
) -> tuple[int, str, str, float]:
    started = time.monotonic()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    process = subprocess.Popen(
        command,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    assert process.stdout is not None

    output_lines: list[str] = []
    last_output_at = time.monotonic()
    output_queue: queue.Queue[str | None] = queue.Queue()

    def _reader() -> None:
        assert process.stdout is not None
        try:
            for line in process.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    reader = threading.Thread(target=_reader, name=f"{name}-stream-reader", daemon=True)
    reader.start()

    try:
        while True:
            elapsed = time.monotonic() - started
            if elapsed >= timeout_seconds:
                process.kill()
                process.wait()
                raise subprocess.TimeoutExpired(command, timeout_seconds, output="".join(output_lines), stderr="")

            try:
                line = output_queue.get(timeout=1)
            except queue.Empty:
                if process.poll() is not None:
                    duration_seconds = round(time.monotonic() - started, 2)
                    return process.returncode or 0, "".join(output_lines).strip(), "", duration_seconds
                if time.monotonic() - last_output_at >= STEP_HEARTBEAT_SECONDS:
                    _print_progress(f"{name}: still running ({int(elapsed)}s elapsed)")
                    last_output_at = time.monotonic()
                continue

            if line is None:
                process.wait()
                duration_seconds = round(time.monotonic() - started, 2)
                return process.returncode or 0, "".join(output_lines).strip(), "", duration_seconds

            clean_line = line.rstrip()
            output_lines.append(line)
            last_output_at = time.monotonic()
            if clean_line:
                _print_progress(f"{name}: {clean_line}")

            if time.monotonic() - last_output_at >= STEP_HEARTBEAT_SECONDS:
                _print_progress(f"{name}: still running ({int(elapsed)}s elapsed)")
    finally:
        reader.join(timeout=1)
        if process.stdout and not process.stdout.closed:
            process.stdout.close()


def _run(name: str, command: list[str], dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {"name": name, "status": "dry_run", "command": command}
    timeout_seconds = STEP_TIMEOUT_SECONDS.get(name, DEFAULT_STEP_TIMEOUT_SECONDS)
    max_attempts = RETRYABLE_STEPS.get(name, 0) + 1
    attempts: list[dict[str, Any]] = []
    started_at = datetime.now().isoformat(timespec="seconds")
    for attempt in range(1, max_attempts + 1):
        _print_progress(
            f"Starting step {name} (attempt {attempt}/{max_attempts}, timeout {timeout_seconds}s)"
        )
        try:
            returncode, stdout, stderr, duration_seconds = _stream_process_output(
                name,
                command,
                timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "").strip()
            stderr = (exc.stderr or "").strip()
            duration_seconds = round(float(timeout_seconds), 2)
            _print_progress(f"Step {name} timed out after {timeout_seconds}s")
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
                _print_progress(f"Retrying step {name} after timeout")
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
        status = "ok" if returncode == 0 else "failed"
        attempts.append(
            {
                "attempt": attempt,
                "status": status,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_seconds": duration_seconds,
            }
        )
        _print_progress(f"Finished step {name} with status {status} in {duration_seconds}s")
        if returncode == 0:
            break
        if attempt >= max_attempts or not _should_retry(name, stderr, stdout):
            break
        _print_progress(f"Retrying step {name} after detected transient failure")
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
    only_steps: set[str] | None = None,
    dry_run: bool = False,
    continue_on_error: bool = False,
) -> dict[str, Any]:
    """Refresh external data where possible and rebuild DB/UI derived outputs."""

    _print_progress("WM refresh pipeline started")
    results: list[dict[str, Any]] = []
    if only_steps is None or "dns_health" in only_steps:
        results.append(_dns_health_result(dry_run=dry_run))
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

    if only_steps is not None:
        steps = [step for step in steps if step[0] in only_steps]

    for name, command in steps:
        dns_health_result = next((result for result in results if result["name"] == "dns_health"), None)
        if name == "import_match_event_data" and not dry_run and dns_health_result is not None and not _supabase_dns_available(dns_health_result):
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
            _print_progress(f"Stopping pipeline after blocking failure in {name}")
            break

    failed = [result for result in results if result["status"] == "failed" and result["name"] not in NON_BLOCKING_FAILURE_STEPS]
    warnings = [
        result
        for result in results
        if (result["status"] == "failed" and result["name"] in NON_BLOCKING_FAILURE_STEPS) or result["status"] == "skipped"
    ]
    output = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "status": "failed" if failed else "ok",
        "steps": results,
        "warnings": warnings,
    }
    _print_progress(f"WM refresh pipeline finished with status {output['status']}")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh WM 2026 MVP data and website export")
    parser.add_argument("--skip-schedule-fetch", action="store_true")
    parser.add_argument("--skip-weather-fetch", action="store_true")
    parser.add_argument("--skip-event-fetch", action="store_true")
    parser.add_argument("--with-event-db-import", action="store_true")
    parser.add_argument("--only-step", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args(argv)
    only_steps = set(args.only_step) or None
    output = refresh_mvp_data(
        skip_schedule_fetch=args.skip_schedule_fetch,
        skip_weather_fetch=args.skip_weather_fetch,
        skip_event_fetch=args.skip_event_fetch,
        with_event_db_import=args.with_event_db_import,
        only_steps=only_steps,
        dry_run=args.dry_run,
        continue_on_error=args.continue_on_error,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
