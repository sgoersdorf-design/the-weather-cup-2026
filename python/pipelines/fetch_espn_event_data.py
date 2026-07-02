"""Backfill structured match event data from ESPN's public soccer endpoints."""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary"
SOURCE_NAME = "ESPN public summary API"
SOURCE_SCORE = 82

DISPLAY_ALIASES: dict[str, str] = {
    "South Africa": "ZAF",
    "Korea Republic": "KOR",
    "South Korea": "KOR",
    "United States": "USA",
    "United States of America": "USA",
    "Iran": "IRN",
    "DR Congo": "COD",
    "Congo DR": "COD",
    "Congo, DR": "COD",
    "Algeria": "DZA",
    "Ivory Coast": "CIV",
    "Côte d'Ivoire": "CIV",
    "Bosnia and Herzegovina": "BIH",
}

ABBREVIATION_ALIASES: dict[str, str] = {
    "RSA": "ZAF",
    "PAR": "PRY",
    "SUI": "CHE",
    "HAI": "HTI",
    "ALG": "DZA",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fetch_json(base_url: str, **params: str) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{base_url}?{query}", headers={"User-Agent": "Mozilla/5.0"})
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover
        context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=20, context=context) as response:  # noqa: S310
        return json.load(response)


def _load_team_name_map(teams_path: Path) -> dict[str, str]:
    rows = _read_csv(teams_path)
    mapping: dict[str, str] = {}
    for row in rows:
        iso3 = row["iso3"]
        for key in ("name_en", "name_de"):
            value = row.get(key)
            if value:
                mapping[value.strip().lower()] = iso3
    for alias, iso3 in DISPLAY_ALIASES.items():
        mapping[alias.lower()] = iso3
    return mapping


def _finished_matches(schedule_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    today = date.today().isoformat()
    return [
        row
        for row in schedule_rows
        if row.get("result_team_a") not in ("", None)
        and row.get("result_team_b") not in ("", None)
        and (row.get("local_date") or today) <= today
    ]


def _espn_iso3(team: dict[str, Any], name_map: dict[str, str]) -> str | None:
    candidates = [
        (team.get("abbreviation") or "").upper(),
        team.get("displayName") or "",
        team.get("shortDisplayName") or "",
        team.get("name") or "",
        team.get("location") or "",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        alias = ABBREVIATION_ALIASES.get(candidate)
        if alias:
            return alias
        if len(candidate) == 3 and candidate in {
            "MEX", "ZAF", "KOR", "CZE", "CAN", "CHE", "QAT", "BIH", "BRA", "MAR", "HTI", "SCO",
            "ESP", "NZL", "ARG", "AUT", "CMR", "SWE", "FRA", "IRQ", "NOR", "SEN", "POR", "UZB",
            "COL", "COD", "ENG", "GHA", "PAN", "HRV", "ITA", "AUS", "TUN", "JPN", "NED", "EGY",
            "GER", "JAM", "BEL", "CRC", "IRN", "DZA", "URU", "PAR", "USA", "ECU", "DEN", "JOR",
        }:
            return candidate
        iso3 = name_map.get(candidate.strip().lower())
        if iso3:
            return iso3
    return None


def _match_event_ids(
    finished_rows: list[dict[str, str]],
    name_map: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    date_cache: dict[str, dict[frozenset[str], list[dict[str, Any]]]] = {}
    match_ids: dict[str, str] = {}
    unmatched: list[dict[str, Any]] = []
    for row in finished_rows:
        candidate_dates = {row["local_date"], str(row.get("date_utc") or "")[:10]}
        key = frozenset([row["team_a_iso3"], row["team_b_iso3"]])
        candidates: list[dict[str, Any]] = []
        for candidate_date in sorted(date for date in candidate_dates if date):
            if candidate_date not in date_cache:
                scoreboard = _fetch_json(ESPN_SCOREBOARD_URL, dates=candidate_date.replace("-", ""))
                events = scoreboard.get("events") or []
                event_lookup: dict[frozenset[str], list[dict[str, Any]]] = defaultdict(list)
                for event in events:
                    competitors = ((event.get("competitions") or [{}])[0].get("competitors") or [])
                    iso_set = frozenset(
                        iso3
                        for iso3 in (
                            _espn_iso3((competitor.get("team") or {}), name_map)
                            for competitor in competitors
                        )
                        if iso3
                    )
                    if iso_set:
                        event_lookup[iso_set].append(event)
                date_cache[candidate_date] = event_lookup
            candidates.extend(date_cache[candidate_date].get(key) or [])
        unique_candidates = {str(candidate["id"]): candidate for candidate in candidates}
        if len(unique_candidates) != 1:
            unmatched.append(
                {
                    "match_id": row["match_id"],
                    "candidate_dates": sorted(candidate_dates),
                    "team_a_iso3": row["team_a_iso3"],
                    "team_b_iso3": row["team_b_iso3"],
                    "candidates_found": len(unique_candidates),
                }
            )
            continue
        match_ids[row["match_id"]] = next(iter(unique_candidates))
    return match_ids, unmatched


def _period_label(number: int | None) -> str:
    return {
        1: "1H",
        2: "2H",
        3: "ET1",
        4: "ET2",
        5: "PEN",
    }.get(number or 0, "unknown")


def _minute_parts(clock: dict[str, Any]) -> tuple[int, int | None]:
    display = str(clock.get("displayValue") or "")
    match = re.match(r"(?P<minute>\d+)'(?:\+(?P<stoppage>\d+))?", display)
    if match:
        minute = int(match.group("minute"))
        stoppage = int(match.group("stoppage")) if match.group("stoppage") else None
        return minute, stoppage
    value = clock.get("value")
    if value is None:
        return 0, None
    minute = max(1, int(float(value) // 60))
    return minute, None


def _player_name(participant: dict[str, Any]) -> str | None:
    athlete = participant.get("athlete") or {}
    return athlete.get("displayName")


def _goal_event_type(item: dict[str, Any]) -> str:
    if item.get("ownGoal"):
        return "own_goal"
    if item.get("penaltyKick"):
        return "penalty_goal"
    return "goal"


def _dedupe_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        item.get("event_type"),
        item.get("team_iso3"),
        item.get("beneficiary_team_iso3"),
        item.get("player_name"),
        item.get("related_player_name"),
        item.get("minute"),
        item.get("stoppage_minute"),
        item.get("period"),
        item.get("notes"),
    )


def fetch_espn_event_data(
    schedule_file: str = "data/full_schedule_openfootball.csv",
    teams_file: str = "data/full_teams_restcountries.csv",
    players_output: str = "data/players.csv",
    team_sheets_output: str = "data/match_team_sheets.csv",
    appearances_output: str = "data/match_player_appearances.csv",
    events_output: str = "data/match_events.csv",
) -> dict[str, Any]:
    """Fetch event, lineup and appearance data for completed matches."""

    schedule_rows = _read_csv(Path(schedule_file))
    finished_rows = _finished_matches(schedule_rows)
    name_map = _load_team_name_map(Path(teams_file))
    event_ids, unmatched_matches = _match_event_ids(finished_rows, name_map)

    players: dict[tuple[str, str], dict[str, Any]] = {}
    team_sheets: list[dict[str, Any]] = []
    appearances: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for row in finished_rows:
        event_id = event_ids.get(row["match_id"])
        if not event_id:
            continue
        summary = _fetch_json(ESPN_SUMMARY_URL, event=event_id)
        rosters = summary.get("rosters") or []
        competitors = ((summary.get("header") or {}).get("competitions") or [{}])[0].get("competitors") or []
        team_order = []
        for competitor in competitors:
            team_iso3 = _espn_iso3((competitor.get("team") or {}), name_map)
            if team_iso3:
                team_order.append(team_iso3)

        substitution_in: dict[tuple[str, str], tuple[int, int | None]] = {}
        substitution_out: dict[tuple[str, str], tuple[int, int | None]] = {}
        score_a = 0
        score_b = 0
        seen_events: set[tuple[Any, ...]] = set()

        for item in summary.get("keyEvents") or []:
            event_text = (item.get("type") or {}).get("text") or ""
            event_kind = (item.get("type") or {}).get("type") or ""
            team_iso3 = _espn_iso3(item.get("team") or {}, name_map)
            minute, stoppage = _minute_parts(item.get("clock") or {})
            period = _period_label(((item.get("period") or {}).get("number")))
            participants = item.get("participants") or []
            player_name = _player_name(participants[0]) if participants else None
            related_name = _player_name(participants[1]) if len(participants) > 1 else None

            event_type: str | None = None
            beneficiary = team_iso3
            if item.get("scoringPlay"):
                event_type = _goal_event_type(item)
                if team_iso3 == row["team_a_iso3"]:
                    score_a += int(item.get("scoreValue") or 1)
                elif team_iso3 == row["team_b_iso3"]:
                    score_b += int(item.get("scoreValue") or 1)
            elif event_kind == "substitution":
                event_type = "sub_in"
                substitution_in[(team_iso3 or "", player_name or "")] = (minute, stoppage)
                if team_iso3 and related_name:
                    substitution_out[(team_iso3, related_name)] = (minute, stoppage)
            elif event_text == "Yellow Card":
                event_type = "yellow_card"
            elif event_text == "Red Card":
                event_type = "red_card"
            elif event_text == "Start Delay" and "drinks break" in (item.get("text") or "").lower():
                event_type = "hydration_break_start"
                player_name = None
                related_name = None
            elif event_text == "End Delay" and "delay over" in (item.get("text") or "").lower():
                event_type = "hydration_break_end"
                player_name = None
                related_name = None

            if event_type:
                event_row = {
                    "match_id": row["match_id"],
                    "team_iso3": team_iso3 or "",
                    "beneficiary_team_iso3": beneficiary or "",
                    "player_name": player_name or "",
                    "related_player_name": related_name or "",
                    "event_type": event_type,
                    "minute": minute,
                    "stoppage_minute": stoppage or "",
                    "period": period,
                    "scoreboard_team_a": score_a if event_type in {"goal", "own_goal", "penalty_goal"} else "",
                    "scoreboard_team_b": score_b if event_type in {"goal", "own_goal", "penalty_goal"} else "",
                    "notes": item.get("text") or "",
                    "data_source_name": SOURCE_NAME,
                    "data_quality_score": SOURCE_SCORE,
                }
                key = _dedupe_key(event_row)
                if key not in seen_events:
                    seen_events.add(key)
                    events.append(event_row)
                if event_kind == "substitution" and team_iso3 and related_name:
                    sub_out_row = {
                        **event_row,
                        "player_name": related_name,
                        "related_player_name": player_name or "",
                        "event_type": "sub_out",
                    }
                    sub_key = _dedupe_key(sub_out_row)
                    if sub_key not in seen_events:
                        seen_events.add(sub_key)
                        events.append(sub_out_row)

        for team in rosters:
            team_iso3 = _espn_iso3(team.get("team") or {}, name_map)
            if not team_iso3:
                raise ValueError(f"Unknown roster team for {row['match_id']}: {team.get('team')}")
            team_sheets.append(
                {
                    "match_id": row["match_id"],
                    "team_iso3": team_iso3,
                    "formation": team.get("formation") or "",
                    "coach_name": "",
                    "captain_player_name": "",
                    "hydration_break_planned": "",
                    "notes": "ESPN roster backfill",
                    "data_source_name": SOURCE_NAME,
                    "data_quality_score": SOURCE_SCORE,
                }
            )
            for player in team.get("roster") or []:
                athlete = player.get("athlete") or {}
                player_name = athlete.get("displayName") or ""
                if not player_name:
                    continue
                position = player.get("position") or {}
                is_goalkeeper = str(position.get("abbreviation") or "").upper() == "GK"
                players[(team_iso3, player_name)] = {
                    "team_iso3": team_iso3,
                    "player_name": player_name,
                    "preferred_name": athlete.get("shortName") or "",
                    "shirt_number": player.get("jersey") or "",
                    "position_group": position.get("abbreviation") or "",
                    "date_of_birth": "",
                    "is_goalkeeper": "true" if is_goalkeeper else "false",
                    "data_source_name": SOURCE_NAME,
                    "data_quality_score": SOURCE_SCORE,
                }
                starter = bool(player.get("starter"))
                minute_in_tuple = substitution_in.get((team_iso3, player_name))
                minute_out_tuple = substitution_out.get((team_iso3, player_name))
                if starter:
                    appearance_role = "starter"
                    minute_in = 0
                elif minute_in_tuple:
                    appearance_role = "bench"
                    minute_in = minute_in_tuple[0]
                else:
                    appearance_role = "unused"
                    minute_in = ""

                appearances.append(
                    {
                        "match_id": row["match_id"],
                        "team_iso3": team_iso3,
                        "player_name": player_name,
                        "appearance_role": appearance_role,
                        "shirt_number": player.get("jersey") or "",
                        "position_label": position.get("abbreviation") or "",
                        "lineup_slot": player.get("formationPlace") or "",
                        "minute_in": minute_in,
                        "minute_out": minute_out_tuple[0] if minute_out_tuple else "",
                        "minutes_played": "",
                        "is_captain": "false",
                        "is_goalkeeper": "true" if is_goalkeeper else "false",
                        "data_source_name": SOURCE_NAME,
                        "data_quality_score": SOURCE_SCORE,
                    }
                )

    player_rows = sorted(players.values(), key=lambda item: (item["team_iso3"], item["player_name"]))
    team_sheet_rows = sorted(team_sheets, key=lambda item: (item["match_id"], item["team_iso3"]))
    appearance_rows = sorted(
        appearances,
        key=lambda item: (item["match_id"], item["team_iso3"], 0 if item["appearance_role"] == "starter" else 1, item["player_name"]),
    )
    event_rows = sorted(
        events,
        key=lambda item: (
            item["match_id"],
            int(item["minute"]),
            int(item["stoppage_minute"] or 0),
            item["event_type"],
            item["team_iso3"],
            item["player_name"],
        ),
    )

    _write_csv(
        Path(players_output),
        player_rows,
        ["team_iso3", "player_name", "preferred_name", "shirt_number", "position_group", "date_of_birth", "is_goalkeeper", "data_source_name", "data_quality_score"],
    )
    _write_csv(
        Path(team_sheets_output),
        team_sheet_rows,
        ["match_id", "team_iso3", "formation", "coach_name", "captain_player_name", "hydration_break_planned", "notes", "data_source_name", "data_quality_score"],
    )
    _write_csv(
        Path(appearances_output),
        appearance_rows,
        ["match_id", "team_iso3", "player_name", "appearance_role", "shirt_number", "position_label", "lineup_slot", "minute_in", "minute_out", "minutes_played", "is_captain", "is_goalkeeper", "data_source_name", "data_quality_score"],
    )
    _write_csv(
        Path(events_output),
        event_rows,
        ["match_id", "team_iso3", "beneficiary_team_iso3", "player_name", "related_player_name", "event_type", "minute", "stoppage_minute", "period", "scoreboard_team_a", "scoreboard_team_b", "notes", "data_source_name", "data_quality_score"],
    )

    return {
        "matches_processed": len(finished_rows),
        "matches_mapped": len(event_ids),
        "matches_unmatched": len(unmatched_matches),
        "players": len(player_rows),
        "team_sheets": len(team_sheet_rows),
        "appearances": len(appearance_rows),
        "events": len(event_rows),
        "unmatched": unmatched_matches,
        "outputs": {
            "players": players_output,
            "team_sheets": team_sheets_output,
            "appearances": appearances_output,
            "events": events_output,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch ESPN-backed event data for completed FIFA World Cup matches")
    parser.add_argument("--schedule", default="data/full_schedule_openfootball.csv")
    parser.add_argument("--teams", default="data/full_teams_restcountries.csv")
    parser.add_argument("--players-output", default="data/players.csv")
    parser.add_argument("--team-sheets-output", default="data/match_team_sheets.csv")
    parser.add_argument("--appearances-output", default="data/match_player_appearances.csv")
    parser.add_argument("--events-output", default="data/match_events.csv")
    args = parser.parse_args(argv)
    print(
        json.dumps(
            fetch_espn_event_data(
                schedule_file=args.schedule,
                teams_file=args.teams,
                players_output=args.players_output,
                team_sheets_output=args.team_sheets_output,
                appearances_output=args.appearances_output,
                events_output=args.events_output,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
