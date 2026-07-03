"""Generate a launchd plist with daily and post-match WM refresh triggers."""

from __future__ import annotations

import argparse
import csv
import plistlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_DIR = REPO_ROOT
DEFAULT_SCHEDULE = DEFAULT_PROJECT_DIR / "data/full_schedule_openfootball.csv"
DEFAULT_OUTPUT = DEFAULT_PROJECT_DIR / "automation/com.wmprojekt.refresh-mvp.plist"
DEFAULT_LOG_DIR = Path("/Users/steffengorsdorf/Library/Logs/wm-projekt")
DEFAULT_TIMEZONE = "Europe/Berlin"
JOB_LABEL = "com.wmprojekt.refresh-mvp"

POST_MATCH_BUFFER_MINUTES = {
    "group_stage": 135,
    "round_of_32": 180,
    "round_of_16": 180,
    "quarterfinals": 180,
    "semifinals": 185,
    "third_place": 185,
    "final": 190,
}


@dataclass(frozen=True)
class Trigger:
    month: int | None
    day: int | None
    hour: int
    minute: int

    def to_launchd(self) -> dict[str, int]:
        payload = {"Hour": self.hour, "Minute": self.minute}
        if self.month is not None:
            payload["Month"] = self.month
        if self.day is not None:
            payload["Day"] = self.day
        return payload


def _read_schedule(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _post_match_trigger(row: dict[str, str], timezone: ZoneInfo) -> Trigger | None:
    date_utc = row.get("date_utc") or ""
    if not date_utc:
        return None
    stage = row.get("tournament_stage") or "group_stage"
    kickoff = _parse_utc(date_utc)
    buffer_minutes = POST_MATCH_BUFFER_MINUTES.get(stage, 180)
    scheduled = (kickoff + timedelta(minutes=buffer_minutes)).astimezone(timezone)
    return Trigger(month=scheduled.month, day=scheduled.day, hour=scheduled.hour, minute=scheduled.minute)


def build_triggers(schedule_rows: list[dict[str, str]], timezone_name: str = DEFAULT_TIMEZONE) -> list[Trigger]:
    timezone = ZoneInfo(timezone_name)
    triggers = {Trigger(month=None, day=None, hour=6, minute=0)}
    for row in schedule_rows:
        trigger = _post_match_trigger(row, timezone)
        if trigger is not None:
            triggers.add(trigger)
    return sorted(triggers, key=lambda item: (item.month or 0, item.day or 0, item.hour, item.minute))


def build_launchd_plist(
    schedule_rows: list[dict[str, str]],
    project_dir: Path = DEFAULT_PROJECT_DIR,
    log_dir: Path = DEFAULT_LOG_DIR,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> dict[str, object]:
    triggers = build_triggers(schedule_rows, timezone_name=timezone_name)
    project_dir_str = str(project_dir)
    log_dir_str = str(log_dir)
    return {
        "Label": JOB_LABEL,
        "ProgramArguments": [
            "/bin/zsh",
            f"{project_dir_str}/scripts/refresh_mvp.command",
            "--auto-publish",
        ],
        "WorkingDirectory": project_dir_str,
        "StartCalendarInterval": [trigger.to_launchd() for trigger in triggers],
        "RunAtLoad": True,
        "StandardOutPath": f"{log_dir_str}/refresh_mvp.out.log",
        "StandardErrorPath": f"{log_dir_str}/refresh_mvp.err.log",
    }


def write_plist(output_path: Path, payload: dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        plistlib.dump(payload, handle, sort_keys=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate launchd schedule for WM refresh jobs")
    parser.add_argument("--schedule", default=str(DEFAULT_SCHEDULE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--project-dir", default=str(DEFAULT_PROJECT_DIR))
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    args = parser.parse_args(argv)

    schedule_path = Path(args.schedule)
    output_path = Path(args.output)
    project_dir = Path(args.project_dir)
    log_dir = Path(args.log_dir)

    rows = _read_schedule(schedule_path)
    payload = build_launchd_plist(rows, project_dir=project_dir, log_dir=log_dir, timezone_name=args.timezone)
    log_dir.mkdir(parents=True, exist_ok=True)
    write_plist(output_path, payload)

    triggers = payload["StartCalendarInterval"]
    print(
        {
            "output": str(output_path),
            "trigger_count": len(triggers),
            "daily_trigger": {"Hour": 6, "Minute": 0},
            "first_match_trigger": triggers[1] if len(triggers) > 1 else None,
            "last_match_trigger": triggers[-1] if triggers else None,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
