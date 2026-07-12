"""Fetch the CC0 OpenFootball World Cup 2026 schedule and normalize to CSV."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import signal
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any

OPENFOOTBALL_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
NETWORK_HARD_TIMEOUT_SECONDS = 25
RESULT_OVERRIDES_PATH = Path("data/result_score_overrides.csv")

TEAM_CODE_MAP = {
    "Algeria": ("DZ", "DZA"),
    "Argentina": ("AR", "ARG"),
    "Australia": ("AU", "AUS"),
    "Austria": ("AT", "AUT"),
    "Belgium": ("BE", "BEL"),
    "Bosnia & Herzegovina": ("BA", "BIH"),
    "Brazil": ("BR", "BRA"),
    "Canada": ("CA", "CAN"),
    "Cape Verde": ("CV", "CPV"),
    "Colombia": ("CO", "COL"),
    "Croatia": ("HR", "HRV"),
    "Curaçao": ("CW", "CUW"),
    "Czech Republic": ("CZ", "CZE"),
    "DR Congo": ("CD", "COD"),
    "Ecuador": ("EC", "ECU"),
    "Egypt": ("EG", "EGY"),
    "England": ("EN", "ENG"),
    "France": ("FR", "FRA"),
    "Germany": ("DE", "DEU"),
    "Ghana": ("GH", "GHA"),
    "Haiti": ("HT", "HTI"),
    "Iran": ("IR", "IRN"),
    "Iraq": ("IQ", "IRQ"),
    "Ivory Coast": ("CI", "CIV"),
    "Japan": ("JP", "JPN"),
    "Jordan": ("JO", "JOR"),
    "Mexico": ("MX", "MEX"),
    "Morocco": ("MA", "MAR"),
    "Netherlands": ("NL", "NLD"),
    "New Zealand": ("NZ", "NZL"),
    "Norway": ("NO", "NOR"),
    "Panama": ("PA", "PAN"),
    "Paraguay": ("PY", "PRY"),
    "Portugal": ("PT", "PRT"),
    "Qatar": ("QA", "QAT"),
    "Saudi Arabia": ("SA", "SAU"),
    "Scotland": ("SC", "SCO"),
    "Senegal": ("SN", "SEN"),
    "South Africa": ("ZA", "ZAF"),
    "South Korea": ("KR", "KOR"),
    "Spain": ("ES", "ESP"),
    "Sweden": ("SE", "SWE"),
    "Switzerland": ("CH", "CHE"),
    "Tunisia": ("TN", "TUN"),
    "Turkey": ("TR", "TUR"),
    "Uruguay": ("UY", "URY"),
    "USA": ("US", "USA"),
    "Uzbekistan": ("UZ", "UZB"),
}

GROUND_MAP = {
    "Atlanta": ("Atlanta Stadium", "Atlanta", "America/New_York"),
    "Boston (Foxborough)": ("Boston Stadium", "Foxborough", "America/New_York"),
    "Dallas (Arlington)": ("Dallas Stadium", "Arlington", "America/Chicago"),
    "Guadalajara (Zapopan)": ("Guadalajara Stadium", "Guadalajara", "America/Mexico_City"),
    "Houston": ("Houston Stadium", "Houston", "America/Chicago"),
    "Kansas City": ("Kansas City Stadium", "Kansas City", "America/Chicago"),
    "Los Angeles (Inglewood)": ("Los Angeles Stadium", "Inglewood", "America/Los_Angeles"),
    "Mexico City": ("Mexico City Stadium", "Mexico City", "America/Mexico_City"),
    "Miami (Miami Gardens)": ("Miami Stadium", "Miami Gardens", "America/New_York"),
    "Monterrey (Guadalupe)": ("Monterrey Stadium", "Monterrey", "America/Monterrey"),
    "New York/New Jersey (East Rutherford)": ("New York New Jersey Stadium", "East Rutherford", "America/New_York"),
    "Philadelphia": ("Philadelphia Stadium", "Philadelphia", "America/New_York"),
    "San Francisco Bay Area (Santa Clara)": ("San Francisco Bay Area Stadium", "Santa Clara", "America/Los_Angeles"),
    "Seattle": ("Seattle Stadium", "Seattle", "America/Los_Angeles"),
    "Toronto": ("Toronto Stadium", "Toronto", "America/Toronto"),
    "Vancouver": ("BC Place Vancouver", "Vancouver", "America/Vancouver"),
}


def _load_requests():
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("requests missing. Run: pip install -r requirements.txt") from exc
    return requests


@contextmanager
def _hard_timeout(seconds: int):
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _raise_timeout(_signum, _frame):
        raise TimeoutError(f"OpenFootball fetch exceeded {seconds} seconds")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def _parse_time(date_value: str, time_value: str) -> tuple[str, str, str]:
    match = re.fullmatch(r"(\d{2}:\d{2}) UTC([+-]\d+)", time_value)
    if not match:
        raise ValueError(f"Unsupported time format: {time_value}")
    local_time = match.group(1)
    offset_hours = int(match.group(2))
    local_dt = dt.datetime.fromisoformat(f"{date_value}T{local_time}:00")
    utc_dt = local_dt - dt.timedelta(hours=offset_hours)
    date_utc = utc_dt.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return date_utc, date_value, local_time


def _source_calendar_day(round_value: str) -> int | None:
    match = re.search(r"Matchday\s+(\d+)", round_value)
    return int(match.group(1)) if match else None


def _stage(round_value: str) -> str:
    if round_value.startswith("Matchday"):
        return "group_stage"
    normalized = round_value.lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "quarter_final": "quarterfinals",
        "quarter_finals": "quarterfinals",
        "semi_final": "semifinals",
        "semi_finals": "semifinals",
        "match_for_third_place": "third_place",
    }
    return aliases.get(normalized, normalized)


def _group_matchday(position_in_group: int) -> int:
    return ((position_in_group - 1) // 2) + 1


def _matchday_label(stage: str, matchday: int | str | None) -> str:
    if stage == "group" and matchday:
        return f"{matchday}. Gruppenspieltag"
    labels = {
        "round_of_32": "Sechzehntelfinale",
        "round_of_16": "Achtelfinale",
        "quarterfinals": "Viertelfinale",
        "semifinals": "Halbfinale",
        "third_place": "Spiel um Platz 3",
        "final": "Finale",
    }
    return labels.get(stage, "")


def _calendar_day_label(calendar_day: int | None) -> str:
    return f"Turniertag {calendar_day}" if calendar_day else ""


def _score(match: dict[str, Any]) -> tuple[int | None, int | None, str]:
    score = match.get("score")
    if isinstance(score, dict):
        ft = score.get("ft") or score.get("fulltime")
        if isinstance(ft, list | tuple) and len(ft) >= 2:
            return ft[0], ft[1], "finished"
    if match.get("score1") is not None and match.get("score2") is not None:
        return match.get("score1"), match.get("score2"), "finished"
    return None, None, "scheduled"


def fetch_openfootball_json(url: str = OPENFOOTBALL_URL) -> dict[str, Any]:
    requests = _load_requests()
    with _hard_timeout(NETWORK_HARD_TIMEOUT_SECONDS):
        response = requests.get(url, timeout=(5, 20))
        response.raise_for_status()
        return response.json()


def normalize_schedule(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    group_positions: dict[str, int] = defaultdict(int)
    for index, match in enumerate(data.get("matches", []), start=1):
        stadium_name, host_city, local_timezone = GROUND_MAP.get(match["ground"], (match["ground"], match["ground"], "UTC"))
        date_utc, local_date, local_time = _parse_time(match["date"], match["time"])
        team_a_iso3 = TEAM_CODE_MAP.get(match["team1"], ("", match["team1"]))[1]
        team_b_iso3 = TEAM_CODE_MAP.get(match["team2"], ("", match["team2"]))[1]
        group_name = match.get("group", "").replace("Group ", "") or None
        result_team_a, result_team_b, match_status = _score(match)
        stage = _stage(match["round"])
        calendar_day = _source_calendar_day(match["round"])
        if stage == "group" and group_name:
            group_positions[group_name] += 1
            matchday: int | str = _group_matchday(group_positions[group_name])
        else:
            matchday = ""
        rows.append(
            {
                "match_id": f"M{int(match.get('num', index)):03d}",
                "tournament_stage": stage,
                "group_name": group_name or "",
                "matchday": matchday,
                "matchday_label": _matchday_label(stage, matchday),
                "calendar_day": calendar_day or "",
                "calendar_day_label": _calendar_day_label(calendar_day),
                "date_utc": date_utc,
                "local_date": local_date,
                "local_time": local_time,
                "local_timezone": local_timezone,
                "team_a_iso3": team_a_iso3,
                "team_b_iso3": team_b_iso3,
                "stadium_name": stadium_name,
                "host_city": host_city,
                "result_team_a": "" if result_team_a is None else result_team_a,
                "result_team_b": "" if result_team_b is None else result_team_b,
                "match_status": match_status,
                "data_source_name": "OpenFootball worldcup.json CC0",
                "data_quality_score": 90,
            }
        )
    return rows


def _result_override_rows(path: Path = RESULT_OVERRIDES_PATH) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["match_id"]: row for row in csv.DictReader(handle) if row.get("match_id")}


def apply_result_overrides(rows: list[dict[str, Any]], path: Path = RESULT_OVERRIDES_PATH) -> list[dict[str, Any]]:
    overrides = _result_override_rows(path)
    if not overrides:
        return rows
    for row in rows:
        override = overrides.get(str(row.get("match_id") or ""))
        if override is None:
            continue
        row["result_team_a"] = override.get("result_team_a", row.get("result_team_a", ""))
        row["result_team_b"] = override.get("result_team_b", row.get("result_team_b", ""))
        row["match_status"] = override.get("match_status") or row.get("match_status") or "finished"
        row["data_source_name"] = override.get("data_source_name") or row.get("data_source_name")
    return rows


def write_csv(rows: list[dict[str, Any]], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch OpenFootball World Cup 2026 schedule")
    parser.add_argument("--url", default=OPENFOOTBALL_URL)
    parser.add_argument("--output", default="data/full_schedule_openfootball.csv")
    args = parser.parse_args(argv)
    try:
        rows = apply_result_overrides(normalize_schedule(fetch_openfootball_json(args.url)))
        write_csv(rows, args.output)
    except Exception as exc:  # noqa: BLE001
        cached_output = Path(args.output)
        if cached_output.exists():
            with cached_output.open(encoding="utf-8") as handle:
                cached_matches = len(list(csv.DictReader(handle)))
            print(
                {
                    "output": args.output,
                    "matches": cached_matches,
                    "warning": str(exc),
                    "used_cached_output": True,
                }
            )
            return 0
        print(f"OpenFootball schedule fetch not completed: {exc}")
        return 1
    print({"output": args.output, "matches": len(rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
