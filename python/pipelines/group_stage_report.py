"""Structured report payload for the 2026 group-stage Weather Cup report."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


EDGE_THRESHOLD = 4.0


def _has_result(row: dict[str, Any]) -> bool:
    return row.get("result_team_a") is not None and row.get("result_team_b") is not None


def _stage(row: dict[str, Any]) -> str:
    return str(row.get("tournament_stage") or "").strip().lower()


def _safe_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _winner_side(row: dict[str, Any]) -> str:
    goals_a = int(row["result_team_a"])
    goals_b = int(row["result_team_b"])
    if goals_a > goals_b:
        return "team_a"
    if goals_b > goals_a:
        return "team_b"
    return "draw"


def _weather_leader_side(row: dict[str, Any]) -> str | None:
    score_a = _safe_float(row.get("team_a_weather_fit_score"))
    score_b = _safe_float(row.get("team_b_weather_fit_score"))
    if score_a is None or score_b is None:
        return None
    if abs(score_a - score_b) < EDGE_THRESHOLD:
        return None
    return "team_a" if score_a > score_b else "team_b"


def _display_label(row: dict[str, Any]) -> str:
    return f"{row.get('team_a_iso3') or 'TBD'} vs. {row.get('team_b_iso3') or 'TBD'}"


def _result_label(row: dict[str, Any]) -> str:
    if not _has_result(row):
        return "–"
    return f"{row['result_team_a']}:{row['result_team_b']}"


def _edge_team_iso3(row: dict[str, Any]) -> str | None:
    leader = _weather_leader_side(row)
    if leader is None:
        return None
    return row.get(f"{leader}_iso3") or row.get(f"team_{leader[-1]}_iso3")


def _match_entry(row: dict[str, Any], category: str) -> dict[str, Any]:
    leader = _weather_leader_side(row)
    edge_team = row.get("team_a_iso3") if leader == "team_a" else row.get("team_b_iso3") if leader == "team_b" else None
    return {
        "match_id": row.get("match_id"),
        "label": _display_label(row),
        "result": _result_label(row),
        "weather_edge": f"{edge_team} Edge" if edge_team else "Ausgeglichen",
        "weather_load_score": _safe_float(row.get("weather_load_score")),
        "gap": _safe_float(row.get("weather_fit_edge_gap")),
        "host_city": row.get("host_city"),
        "local_date": row.get("local_date"),
        "category": category,
        "team_a_iso3": row.get("team_a_iso3"),
        "team_b_iso3": row.get("team_b_iso3"),
    }


def _team_stats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    teams: dict[str, dict[str, Any]] = {}
    for row in rows:
        for side in ("a", "b"):
            iso3 = row.get(f"team_{side}_iso3")
            if not iso3:
                continue
            teams.setdefault(
                iso3,
                {
                    "iso3": iso3,
                    "name_de": row.get(f"team_{side}_name_de") or iso3,
                    "name_en": row.get(f"team_{side}_name_en") or iso3,
                    "flag": row.get(f"team_{side}_flag") or "",
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                },
            )
        if not _has_result(row):
            continue
        a = teams[row["team_a_iso3"]]
        b = teams[row["team_b_iso3"]]
        goals_a = int(row["result_team_a"])
        goals_b = int(row["result_team_b"])
        a["played"] += 1
        b["played"] += 1
        a["goals_for"] += goals_a
        a["goals_against"] += goals_b
        b["goals_for"] += goals_b
        b["goals_against"] += goals_a
        if goals_a > goals_b:
            a["wins"] += 1
            b["losses"] += 1
        elif goals_b > goals_a:
            b["wins"] += 1
            a["losses"] += 1
        else:
            a["draws"] += 1
            b["draws"] += 1
    output = []
    for team in teams.values():
        team["goal_difference"] = team["goals_for"] - team["goals_against"]
        output.append(team)
    return output


def _ranked_team_rows(teams: list[dict[str, Any]], key: str, reverse: bool = True) -> list[dict[str, Any]]:
    return sorted(
        teams,
        key=lambda item: (
            -(item[key] if reverse else -item[key]),
            -item["goal_difference"],
            -item["goals_for"],
            item["name_de"],
        ),
    )


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _share(count: int, total: int) -> float | None:
    return round(count / total, 3) if total else None


def _group_stage_event_coverage(group_stage_ids: set[str], fallback: dict[str, Any] | None, finished_matches: int) -> dict[str, Any]:
    events_path = Path("data/match_events.csv")
    appearances_path = Path("data/match_player_appearances.csv")
    if events_path.exists() and appearances_path.exists():
      with events_path.open(newline="", encoding="utf-8") as handle:
          events_rows = list(csv.DictReader(handle))
      with appearances_path.open(newline="", encoding="utf-8") as handle:
          appearances_rows = list(csv.DictReader(handle))
      goal_matches = {
          row["match_id"]
          for row in events_rows
          if row.get("match_id") in group_stage_ids and row.get("event_type") in {"goal", "own_goal", "penalty_goal"}
      }
      hydration_matches = {
          row["match_id"]
          for row in events_rows
          if row.get("match_id") in group_stage_ids and row.get("event_type") in {"hydration_break_start", "hydration_break_end"}
      }
      starter_counts: dict[str, int] = defaultdict(int)
      for row in appearances_rows:
          if row.get("match_id") in group_stage_ids and row.get("appearance_role") == "starter":
              starter_counts[row["match_id"]] += 1
      lineup_matches = len([match_id for match_id, starters in starter_counts.items() if starters >= 22])
      return {
          "finished_matches": finished_matches,
          "goal_event_matches": len(goal_matches),
          "goal_event_share": _share(len(goal_matches), finished_matches),
          "lineup_matches": lineup_matches,
          "hydration_matches": len(hydration_matches),
          "last_event_update": fallback.get("last_event_update") if fallback else None,
      }
    fallback = fallback or {}
    goal_matches = min(int(fallback.get("matches_with_goal_events") or 0), finished_matches)
    lineup_matches = min(int(fallback.get("matches_with_complete_lineups") or 0), finished_matches)
    hydration_matches = min(int(fallback.get("matches_with_hydration_markers") or 0), finished_matches)
    return {
        "finished_matches": finished_matches,
        "goal_event_matches": goal_matches,
        "goal_event_share": _share(goal_matches, finished_matches),
        "lineup_matches": lineup_matches,
        "hydration_matches": hydration_matches,
        "last_event_update": fallback.get("last_event_update"),
    }


def build_group_stage_report(rows: list[dict[str, Any]], event_stats: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a structured report for the completed group stage."""

    group_rows = [row for row in rows if _stage(row) == "group_stage"]
    finished = [row for row in group_rows if _has_result(row)]
    comparable = [row for row in finished if _weather_leader_side(row)]

    confirmed_rows: list[dict[str, Any]] = []
    missed_rows: list[dict[str, Any]] = []
    draw_rows: list[dict[str, Any]] = []
    for row in comparable:
        leader = _weather_leader_side(row)
        winner = _winner_side(row)
        if winner == "draw":
            draw_rows.append(row)
        elif winner == leader:
            confirmed_rows.append(row)
        else:
            missed_rows.append(row)

    goals = [int(row["result_team_a"]) + int(row["result_team_b"]) for row in finished]
    draw_count = len([row for row in finished if _winner_side(row) == "draw"])
    btts_count = len([row for row in finished if int(row["result_team_a"]) > 0 and int(row["result_team_b"]) > 0])
    load_values = [_safe_float(row.get("weather_load_score")) for row in finished]
    load_values = [value for value in load_values if value is not None]
    edge_gaps = [_safe_float(row.get("weather_fit_edge_gap")) for row in comparable]
    edge_gaps = [value for value in edge_gaps if value is not None]

    teams = _team_stats(finished)
    top_attack = sorted(teams, key=lambda item: (-item["goals_for"], item["goals_against"], item["name_de"]))[:5]
    top_defense = sorted(teams, key=lambda item: (-item["goal_difference"], item["goals_against"], item["name_de"]))[:5]
    top_conceded = sorted(teams, key=lambda item: (-item["goals_against"], -item["goals_for"], item["name_de"]))[:5]

    load_match = max(
        [row for row in finished if _safe_float(row.get("weather_load_score")) is not None],
        key=lambda row: _safe_float(row.get("weather_load_score")) or 0,
        default=None,
    )
    edge_match = max(
        [row for row in comparable if _safe_float(row.get("weather_fit_edge_gap")) is not None],
        key=lambda row: _safe_float(row.get("weather_fit_edge_gap")) or 0,
        default=None,
    )
    travel_match = max(
        [
            row
            for row in finished
            if _safe_float(row.get("team_a_travel_distance_km")) is not None or _safe_float(row.get("team_b_travel_distance_km")) is not None
        ],
        key=lambda row: max(_safe_float(row.get("team_a_travel_distance_km")) or 0, _safe_float(row.get("team_b_travel_distance_km")) or 0),
        default=None,
    )
    altitude_match = max(
        [row for row in finished if _safe_float(row.get("elevation_m")) is not None],
        key=lambda row: _safe_float(row.get("elevation_m")) or 0,
        default=None,
    )

    knockout_rows = [row for row in rows if _stage(row) != "group_stage" and _stage(row)]
    knockout_upcoming = [row for row in knockout_rows if not _has_result(row)]
    knockout_with_forecast = [row for row in knockout_upcoming if row.get("forecast_temp") is not None]
    knockout_with_fit = [row for row in knockout_upcoming if row.get("team_a_weather_fit_score") is not None]

    coverage = _group_stage_event_coverage(
        {str(row.get("match_id") or "") for row in finished},
        (event_stats or {}).get("coverage") or {},
        len(finished),
    )

    high_load_count = len([value for value in load_values if value >= 25])
    confirmed_count = len(confirmed_rows)
    missed_count = len(missed_rows)
    draw_edge_count = len(draw_rows)
    hit_rate = round((confirmed_count / len(comparable)) * 100) if comparable else None

    headline_de = (
        f"72 Spiele sind im Gruppenphasen-Report verarbeitet. {confirmed_count} von {len(comparable)} klaren Wetterkanten "
        f"deckten sich mit dem Siegerbild; die Trefferquote liegt bei {hit_rate}%."
        if comparable
        else "Die Gruppenphase ist abgeschlossen, aber es gibt noch keine klaren Wetterkanten im Datensatz."
    )
    headline_en = (
        f"The group-stage report covers 72 finished matches. {confirmed_count} of {len(comparable)} clear weather edges "
        f"matched the winning side, for a hit rate of {hit_rate}%."
        if comparable
        else "The group stage is complete, but no clear weather edges are available in the dataset yet."
    )

    key_findings_de = [
        f"Die Gruppenphase brachte {sum(goals)} Tore in {len(finished)} Spielen, also {round(sum(goals) / len(finished), 2) if finished else 0} pro Spiel.",
        f"Der durchschnittliche Weather Load lag bei {_avg(load_values) or '–'}/100; {high_load_count} Partien lagen im mindestens mittleren Belastungsbereich.",
        f"Die Event-Coverage deckt {coverage['goal_event_matches']}/{coverage['finished_matches']} beendete Spiele mit Tor-Events ab; Ist-Wetter bleibt bewusst offen, solange keine Messdaten vorliegen.",
    ]
    key_findings_en = [
        f"The group stage produced {sum(goals)} goals across {len(finished)} matches, or {round(sum(goals) / len(finished), 2) if finished else 0} per match.",
        f"Average Weather Load was {_avg(load_values) or '–'}/100; {high_load_count} matches landed in at least the medium-load band.",
        f"Event coverage reaches {coverage['goal_event_matches']}/{coverage['finished_matches']} finished matches with goal events; actual weather remains intentionally open until measurements exist.",
    ]

    return {
        "id": "weather-cup-2026-group-stage",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scope_stage": "group_stage",
        "scope_label_de": "Gruppenphase",
        "scope_label_en": "Group stage",
        "headline_de": headline_de,
        "headline_en": headline_en,
        "summary_de": "Erster wissenschaftlicher Zwischenstand zum Weather Cup 2026 nach Abschluss der Gruppenphase.",
        "summary_en": "First scientific checkpoint for the Weather Cup 2026 after the completed group stage.",
        "finished_matches": len(finished),
        "total_goals": sum(goals),
        "goals_per_match": _avg([float(value) for value in goals]),
        "draws": draw_count,
        "draw_share": _share(draw_count, len(finished)),
        "both_teams_scored": btts_count,
        "both_teams_scored_share": _share(btts_count, len(finished)),
        "avg_weather_load_score": _avg(load_values),
        "high_load_matches": high_load_count,
        "comparable_matches": len(comparable),
        "weather_edge_confirmed": confirmed_count,
        "weather_edge_missed": missed_count,
        "weather_edge_draws": draw_edge_count,
        "weather_edge_hit_rate": hit_rate,
        "avg_weather_edge_gap": _avg(edge_gaps),
        "event_coverage": {
            "finished_matches": coverage["finished_matches"],
            "goal_event_matches": coverage["goal_event_matches"],
            "goal_event_share": coverage["goal_event_share"],
            "lineup_matches": coverage["lineup_matches"],
            "hydration_matches": coverage["hydration_matches"],
            "last_event_update": coverage["last_event_update"],
        },
        "knockout_readiness": {
            "upcoming_matches": len(knockout_upcoming),
            "forecast_matches": len(knockout_with_forecast),
            "weather_fit_matches": len(knockout_with_fit),
            "forecast_share": _share(len(knockout_with_forecast), len(knockout_upcoming)),
            "weather_fit_share": _share(len(knockout_with_fit), len(knockout_upcoming)),
        },
        "key_findings_de": key_findings_de,
        "key_findings_en": key_findings_en,
        "method_note_de": "Weather Fit bleibt ein Kontextindikator. Ergebnisse, Tore und Wettermuster werden deskriptiv ausgewertet; Kausalität wird nicht behauptet.",
        "method_note_en": "Weather Fit remains a context indicator. Results, goals and weather patterns are evaluated descriptively; causality is not claimed.",
        "featured_matches": {
            "confirmed": [_match_entry(row, "confirmed") for row in sorted(confirmed_rows, key=lambda row: _safe_float(row.get("weather_fit_edge_gap")) or 0, reverse=True)[:3]],
            "missed": [_match_entry(row, "missed") for row in sorted(missed_rows, key=lambda row: _safe_float(row.get("weather_fit_edge_gap")) or 0, reverse=True)[:3]],
            "draw": [_match_entry(row, "draw") for row in sorted(draw_rows, key=lambda row: _safe_float(row.get("weather_fit_edge_gap")) or 0, reverse=True)[:3]],
        },
        "team_leaders": {
            "attack": top_attack,
            "goal_difference": top_defense,
            "conceded": top_conceded,
        },
        "context_extremes": {
            "highest_load": _match_entry(load_match, "context") if load_match else None,
            "sharpest_edge": _match_entry(edge_match, "context") if edge_match else None,
            "longest_travel": _match_entry(travel_match, "context") if travel_match else None,
            "highest_altitude": _match_entry(altitude_match, "context") if altitude_match else None,
        },
    }
