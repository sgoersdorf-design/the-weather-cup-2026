"""Compute tournament timing and player/team event stats from match event CSV data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GOAL_EVENT_TYPES = {"goal", "own_goal", "penalty_goal"}
HYDRATION_BREAK_END = "hydration_break_end"
TIME_BUCKETS = [
    ("00-15", 0, 15),
    ("16-30", 16, 30),
    ("31-45+", 31, 45),
    ("46-60", 46, 60),
    ("61-75", 61, 75),
    ("76-90", 76, 90),
    ("90+X", 91, 999),
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _minute(row: dict[str, str]) -> int:
    return int(row["minute"])


def _stoppage(row: dict[str, str]) -> int:
    return int(row["stoppage_minute"]) if row.get("stoppage_minute") not in ("", None) else 0


def effective_minute(row: dict[str, str]) -> int:
    minute = _minute(row)
    stoppage = _stoppage(row)
    if minute in {45, 90, 105, 120} and stoppage:
        return minute + stoppage
    return minute


def time_bucket(row: dict[str, str]) -> str:
    minute = effective_minute(row)
    for label, start, end in TIME_BUCKETS:
        if start <= minute <= end:
            return label
    return "unknown"


def scoring_team(row: dict[str, str]) -> str | None:
    return row.get("beneficiary_team_iso3") or row.get("team_iso3") or None


def actor_team(row: dict[str, str]) -> str | None:
    return row.get("team_iso3") or None


def build_match_teams(schedule_rows: list[dict[str, str]]) -> dict[str, tuple[str, str]]:
    return {
        row["match_id"]: (row["team_a_iso3"], row["team_b_iso3"])
        for row in schedule_rows
        if row.get("team_a_iso3") and row.get("team_b_iso3")
    }


def opponent_iso3(match_teams: dict[str, tuple[str, str]], match_id: str, iso3: str) -> str | None:
    pair = match_teams.get(match_id)
    if not pair:
        return None
    if pair[0] == iso3:
        return pair[1]
    if pair[1] == iso3:
        return pair[0]
    return None


def compute_event_tournament_stats(
    events_rows: list[dict[str, str]],
    schedule_rows: list[dict[str, str]],
) -> dict[str, Any]:
    match_teams = build_match_teams(schedule_rows)
    goal_rows = [row for row in events_rows if row.get("event_type") in GOAL_EVENT_TYPES]

    goals_by_bucket: Counter[str] = Counter()
    team_scored_bucket: defaultdict[str, Counter[str]] = defaultdict(Counter)
    team_conceded_bucket: defaultdict[str, Counter[str]] = defaultdict(Counter)
    player_scored_bucket: defaultdict[str, Counter[str]] = defaultdict(Counter)
    first_half_goals: Counter[str] = Counter()
    second_half_goals: Counter[str] = Counter()
    first_half_conceded: Counter[str] = Counter()
    second_half_conceded: Counter[str] = Counter()
    crunchtime_goals: Counter[str] = Counter()
    early_goals: Counter[str] = Counter()
    hydration_post_break_goals: Counter[str] = Counter()
    player_totals: Counter[str] = Counter()
    player_team_map: dict[str, str] = {}

    hydration_windows: defaultdict[str, list[tuple[int, int]]] = defaultdict(list)
    break_starts: defaultdict[str, list[int]] = defaultdict(list)
    for row in events_rows:
        if row.get("event_type") == "hydration_break_start":
            break_starts[row["match_id"]].append(effective_minute(row))
        if row.get("event_type") == HYDRATION_BREAK_END and break_starts[row["match_id"]]:
            start = break_starts[row["match_id"]].pop(0)
            hydration_windows[row["match_id"]].append((start, effective_minute(row) + 5))

    for row in goal_rows:
        scoring_iso3 = scoring_team(row)
        if not scoring_iso3:
            continue
        bucket = time_bucket(row)
        goals_by_bucket[bucket] += 1
        team_scored_bucket[scoring_iso3][bucket] += 1
        player_name = row.get("player_name")
        if player_name:
            player_scored_bucket[player_name][bucket] += 1
            player_totals[player_name] += 1
            player_team_map.setdefault(player_name, scoring_iso3)

        opponent = opponent_iso3(match_teams, row["match_id"], scoring_iso3)
        if opponent:
            team_conceded_bucket[opponent][bucket] += 1

        minute = effective_minute(row)
        if minute <= 15:
            early_goals[scoring_iso3] += 1
        if minute <= 45:
            first_half_goals[scoring_iso3] += 1
            if opponent:
                first_half_conceded[opponent] += 1
        else:
            second_half_goals[scoring_iso3] += 1
            if opponent:
                second_half_conceded[opponent] += 1
        if minute >= 90:
            crunchtime_goals[scoring_iso3] += 1

        for start, end in hydration_windows.get(row["match_id"], []):
            if start <= minute <= end:
                hydration_post_break_goals[scoring_iso3] += 1
                break

    def top_counter(counter: Counter[str], limit: int = 5) -> list[dict[str, Any]]:
        return [{"key": key, "count": value} for key, value in counter.most_common(limit)]

    def top_nested(counter_map: defaultdict[str, Counter[str]], limit: int = 5) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key, nested in counter_map.items():
            label, count = nested.most_common(1)[0] if nested else ("unknown", 0)
            rows.append({"key": key, "bucket": label, "count": count, "total": sum(nested.values())})
        return sorted(rows, key=lambda item: (-item["count"], -item["total"], item["key"]))[:limit]

    player_profiles: list[dict[str, Any]] = []
    for player_name, nested in player_scored_bucket.items():
        top_bucket_label, top_bucket_count = nested.most_common(1)[0] if nested else ("unknown", 0)
        player_profiles.append(
            {
                "player_name": player_name,
                "team_iso3": player_team_map.get(player_name, ""),
                "total_goals": player_totals.get(player_name, 0),
                "top_bucket": top_bucket_label,
                "top_bucket_goals": top_bucket_count,
                "buckets": [{"bucket": bucket, "goals": nested.get(bucket, 0)} for bucket, _, _ in TIME_BUCKETS],
            }
        )
    player_profiles.sort(
        key=lambda item: (-item["total_goals"], -item["top_bucket_goals"], item["player_name"])
    )

    return {
        "goal_rows": len(goal_rows),
        "goals_by_15min_bucket": [{"bucket": bucket, "goals": goals_by_bucket.get(bucket, 0)} for bucket, _, _ in TIME_BUCKETS],
        "teams_most_often_scored_in_bucket": top_nested(team_scored_bucket),
        "teams_most_often_conceded_in_bucket": top_nested(team_conceded_bucket),
        "early_starters": top_counter(early_goals),
        "crunchtime_scorers": top_counter(crunchtime_goals),
        "first_half_scoring_teams": top_counter(first_half_goals),
        "second_half_scoring_teams": top_counter(second_half_goals),
        "first_half_conceding_teams": top_counter(first_half_conceded),
        "second_half_conceding_teams": top_counter(second_half_conceded),
        "hydration_break_post_window_goals": top_counter(hydration_post_break_goals),
        "player_level_scoring_buckets": top_nested(player_scored_bucket),
        "player_goal_timing_profiles": player_profiles,
        "top_scorers": [
            {
                "player_name": item["player_name"],
                "team_iso3": item["team_iso3"],
                "total_goals": item["total_goals"],
                "top_bucket": item["top_bucket"],
                "top_bucket_goals": item["top_bucket_goals"],
            }
            for item in player_profiles
        ],
        "data_gaps": {
            "player_level_possible": bool(player_scored_bucket),
            "hydration_break_markers_present": any(hydration_windows.values()),
            "note": "Reliable hydration-break and timing analysis requires event rows with minute, period and hydration markers.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute tournament event timing stats from CSV files")
    parser.add_argument("--events", required=True, help="CSV with match event rows")
    parser.add_argument("--schedule", default="data/full_schedule_openfootball.csv", help="Schedule CSV used to resolve opponents")
    args = parser.parse_args(argv)
    events = _read_csv(Path(args.events))
    schedule = _read_csv(Path(args.schedule))
    print(json.dumps(compute_event_tournament_stats(events, schedule), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
