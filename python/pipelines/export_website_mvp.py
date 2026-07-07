"""Export a static data bundle for the local website MVP viewer."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from python.db import get_engine
from python.pipelines.event_tournament_stats import compute_event_tournament_stats
from python.pipelines.group_stage_report import build_group_stage_report


def _load_dependencies():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc
    return text


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date | time):
        return value.isoformat()
    return str(value)


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(row, default=_json_default, ensure_ascii=False))


def _has_result(row: dict[str, Any]) -> bool:
    return row.get("result_team_a") is not None and row.get("result_team_b") is not None


def _knockout_resolution_type(row: dict[str, Any]) -> str | None:
    value = str(row.get("result_resolution") or "").strip().lower()
    if value in {"regular", "extra_time", "penalties"}:
        return value
    return None


def _advanced_side(row: dict[str, Any]) -> str | None:
    value = str(row.get("advanced_team_side") or "").strip().lower()
    if value in {"a", "b"}:
        return value
    return None


def _shootout_result_label(row: dict[str, Any]) -> str | None:
    score_a = row.get("shootout_score_team_a")
    score_b = row.get("shootout_score_team_b")
    if score_a is None or score_b is None:
        return None
    return f"{score_a}:{score_b}"


def _decision_note(row: dict[str, Any]) -> str | None:
    resolution = _knockout_resolution_type(row)
    if resolution not in {"extra_time", "penalties"}:
        return None
    side = _advanced_side(row)
    if side is None:
        return "nach Verlängerung entschieden" if resolution == "extra_time" else "im Elfmeterschießen entschieden"
    winner = row[f"team_{side}_iso3"]
    if resolution == "extra_time":
        return f"{winner} gewinnt n.V."
    shootout = _shootout_result_label(row)
    if shootout:
        return f"{winner} gewinnt {shootout} i.E."
    return f"{winner} gewinnt i.E."


def _normalize_stage_key(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    aliases = {
        "group": "group_stage",
        "quarter_final": "quarterfinals",
        "quarter_finals": "quarterfinals",
        "semi_final": "semifinals",
        "semi_finals": "semifinals",
        "match_for_third_place": "third_place",
    }
    return aliases.get(normalized, normalized)


def _weather_edge(row: dict[str, Any]) -> str:
    if row.get("team_a_weather_fit_score") is None or row.get("team_b_weather_fit_score") is None:
        return "Forecast offen"
    team_a = float(row["team_a_weather_fit_score"])
    team_b = float(row["team_b_weather_fit_score"])
    if abs(team_a - team_b) < 4:
        return "Ausgeglichen"
    return f"{row['team_a_iso3']} Edge" if team_a > team_b else f"{row['team_b_iso3']} Edge"


def _team_seed(row: dict[str, Any], side: str) -> dict[str, Any]:
    return {
        "iso3": row[f"team_{side}_iso3"],
        "name_de": row[f"team_{side}_name_de"],
        "flag": row[f"team_{side}_flag"],
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "points": 0,
    }


def build_group_standings(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build current group tables from imported real result fields."""

    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        group = row.get("group_name") or "–"
        groups.setdefault(group, {})
        for side in ("a", "b"):
            iso3 = row[f"team_{side}_iso3"]
            groups[group].setdefault(iso3, _team_seed(row, side))

        if not _has_result(row):
            continue

        team_a = groups[group][row["team_a_iso3"]]
        team_b = groups[group][row["team_b_iso3"]]
        goals_a = int(row["result_team_a"])
        goals_b = int(row["result_team_b"])
        team_a["played"] += 1
        team_b["played"] += 1
        team_a["goals_for"] += goals_a
        team_a["goals_against"] += goals_b
        team_b["goals_for"] += goals_b
        team_b["goals_against"] += goals_a
        if goals_a > goals_b:
            team_a["wins"] += 1
            team_b["losses"] += 1
            team_a["points"] += 3
        elif goals_b > goals_a:
            team_b["wins"] += 1
            team_a["losses"] += 1
            team_b["points"] += 3
        else:
            team_a["draws"] += 1
            team_b["draws"] += 1
            team_a["points"] += 1
            team_b["points"] += 1

    output: dict[str, list[dict[str, Any]]] = {}
    for group, teams in groups.items():
        table = []
        for team in teams.values():
            team["goal_difference"] = team["goals_for"] - team["goals_against"]
            table.append(team)
        table.sort(key=lambda item: (-item["points"], -item["goal_difference"], -item["goals_for"], item["name_de"]))
        output[group] = table
    return dict(sorted(output.items()))


def _analysis_note(row: dict[str, Any]) -> str:
    edge = _weather_edge(row)
    if _has_result(row):
        result = f"{row['team_a_iso3']} {row['result_team_a']}:{row['result_team_b']} {row['team_b_iso3']}"
        decision = _decision_note(row)
        if decision:
            result = f"{result} ({decision})"
        return f"{result}. Forecast-Edge: {edge}. Ist-Wetter-Abgleich folgt, sobald Actual-Wetterdaten importiert sind."
    if row.get("forecast_temp") is not None:
        return f"Noch nicht gespielt. Forecast-Edge: {edge}; Weather Load {row.get('weather_load_score') or '–'}/100."
    return "Noch nicht gespielt. Forecast liegt ausserhalb des aktuellen Vorhersagefensters."


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forecast_rows = [row for row in rows if row.get("forecast_temp") is not None]
    fit_rows = [row for row in rows if row.get("team_a_weather_fit_score") is not None]
    actual_rows = [row for row in rows if row.get("actual_temp") is not None]
    finished_rows = [row for row in rows if _has_result(row)]
    edge_rows = [row for row in fit_rows if float(row.get("weather_fit_edge_gap") or 0) >= 4]
    loads = [float(row["weather_load_score"]) for row in rows if row.get("weather_load_score") is not None]
    return {
        "matches": len(rows),
        "finished": len(finished_rows),
        "forecast_matches": len(forecast_rows),
        "actual_weather_matches": len(actual_rows),
        "weather_fit_matches": len(fit_rows),
        "weather_fit_edges": len(edge_rows),
        "avg_weather_load_score": round(sum(loads) / len(loads), 2) if loads else None,
        "report_ready_matches": len([row for row in finished_rows if row.get("actual_temp") is not None]),
    }


def _group_aggregate(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or "–"), []).append(row)
    return {group: _aggregate(items) for group, items in sorted(grouped.items(), key=lambda item: item[0])}


def build_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build report-ready match, matchday, phase and tournament analysis payload."""

    match_analyses = [
        {
            "match_id": row["match_id"],
            "matchday": row.get("matchday"),
            "matchday_label": row.get("matchday_label"),
            "calendar_day": row.get("calendar_day"),
            "calendar_day_label": row.get("calendar_day_label"),
            "phase": row.get("tournament_stage"),
            "group_name": row.get("group_name"),
            "label": f"{row['team_a_iso3']} vs. {row['team_b_iso3']}",
            "host_city": row.get("host_city"),
            "status": "finished" if _has_result(row) else row.get("match_status") or "scheduled",
            "result": f"{row['result_team_a']}:{row['result_team_b']}" if _has_result(row) else None,
            "result_resolution": _knockout_resolution_type(row),
            "advanced_team_side": _advanced_side(row),
            "shootout_result": _shootout_result_label(row),
            "weather_edge": _weather_edge(row),
            "weather_load_score": row.get("weather_load_score"),
            "forecast_available": row.get("forecast_temp") is not None,
            "actual_weather_available": row.get("actual_temp") is not None,
            "note_de": _analysis_note(row),
        }
        for row in rows
    ]
    return {
        "matches": match_analyses,
        "matchdays": _group_aggregate(rows, "matchday"),
        "phases": _group_aggregate(rows, "tournament_stage"),
        "tournament": _aggregate(rows),
    }


def load_ads(conn, text) -> list[dict[str, Any]]:
    """Load active ad placements for the static MVP export."""

    return [
        _clean_row(dict(row))
        for row in conn.execute(
            text(
                """
                select
                  s.slot_key, s.section_key, s.placement_key, s.display_name,
                  s.allowed_sizes, s.max_width, s.min_height, s.device_targeting,
                  p.priority, p.weight,
                  c.creative_key, c.creative_name, c.creative_type, c.label,
                  c.headline, c.body, c.call_to_action, c.image_url, c.click_url,
                  c.tracking_pixel_url, c.alt_text, c.background_color, c.text_color,
                  c.width, c.height,
                  ca.campaign_key, ca.campaign_name,
                  ap.partner_key, ap.partner_name
                from ad_placements p
                join ad_slots s on s.id = p.slot_id
                join ad_creatives c on c.id = p.creative_id
                join ad_campaigns ca on ca.id = c.campaign_id
                left join ad_partners ap on ap.id = ca.partner_id
                where p.is_active = true
                  and s.is_active = true
                  and c.is_active = true
                  and ca.booking_status in ('active', 'ready')
                  and (p.starts_at is null or p.starts_at <= now())
                  and (p.ends_at is null or p.ends_at >= now())
                  and (ca.starts_at is null or ca.starts_at <= now())
                  and (ca.ends_at is null or ca.ends_at >= now())
                order by s.section_key, s.placement_key, p.priority desc, p.weight desc
                """
            )
        ).mappings()
    ]


def _read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_event_stats_from_csv(match_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fallback event stats from local CSV files when DB event tables are empty or unavailable."""

    events_path = Path("data/match_events.csv")
    appearances_path = Path("data/match_player_appearances.csv")
    events_rows = _read_csv_if_exists(events_path)
    appearances_rows = _read_csv_if_exists(appearances_path)
    finished_matches = len([row for row in match_rows if _has_result(row)])
    if not events_rows and not appearances_rows:
        return {
            "available": False,
            "coverage": {
                "finished_matches": finished_matches,
                "matches_with_goal_events": 0,
                "matches_with_complete_lineups": 0,
                "matches_with_substitutions": 0,
                "matches_with_hydration_markers": 0,
                "last_event_update": None,
                "goal_event_coverage_share": 0 if finished_matches else None,
            },
            "goal_rows": 0,
            "data_gaps": {
                "player_level_possible": False,
                "hydration_break_markers_present": False,
                "note": "Lokale Event-CSV-Dateien fehlen oder sind leer.",
            },
        }

    stats = compute_event_tournament_stats(
        events_rows=events_rows,
        schedule_rows=[
            {
                "match_id": row["match_id"],
                "team_a_iso3": row["team_a_iso3"],
                "team_b_iso3": row["team_b_iso3"],
            }
            for row in match_rows
            if row.get("team_a_iso3") and row.get("team_b_iso3")
        ],
    )
    lineup_counts: dict[str, int] = {}
    for row in appearances_rows:
        if row.get("appearance_role") == "starter":
            lineup_counts[row["match_id"]] = lineup_counts.get(row["match_id"], 0) + 1
    matches_with_goal_events = len(
        {row["match_id"] for row in events_rows if row.get("event_type") in {"goal", "own_goal", "penalty_goal"}}
    )
    matches_with_substitutions = len(
        {row["match_id"] for row in events_rows if row.get("event_type") in {"sub_in", "sub_out"}}
    )
    matches_with_hydration_markers = len(
        {row["match_id"] for row in events_rows if row.get("event_type") in {"hydration_break_start", "hydration_break_end"}}
    )
    last_update = datetime.fromtimestamp(events_path.stat().st_mtime).isoformat(timespec="seconds") if events_path.exists() else None
    return {
        "available": True,
        "coverage": {
            "finished_matches": finished_matches,
            "matches_with_goal_events": matches_with_goal_events,
            "matches_with_complete_lineups": len([match_id for match_id, starters in lineup_counts.items() if starters >= 22]),
            "matches_with_substitutions": matches_with_substitutions,
            "matches_with_hydration_markers": matches_with_hydration_markers,
            "last_event_update": last_update,
            "goal_event_coverage_share": round(matches_with_goal_events / finished_matches, 3) if finished_matches else None,
        },
        **stats,
    }


def load_event_stats(conn, text, match_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Load event-level tournament stats and coverage from DB tables when available."""

    try:
        schedule_rows = [
            {
                "match_id": row["match_id"],
                "team_a_iso3": row["team_a_iso3"],
                "team_b_iso3": row["team_b_iso3"],
            }
            for row in match_rows
            if row.get("team_a_iso3") and row.get("team_b_iso3")
        ]
        event_rows = [
            _clean_row(dict(row))
            for row in conn.execute(
                text(
                    """
                    select
                      me.match_id,
                      me.event_type,
                      me.minute,
                      me.stoppage_minute,
                      me.period,
                      tt.iso3 as team_iso3,
                      bt.iso3 as beneficiary_team_iso3,
                      p.player_name,
                      rp.player_name as related_player_name
                    from match_events me
                    left join teams tt on tt.id = me.team_id
                    left join teams bt on bt.id = me.beneficiary_team_id
                    left join players p on p.id = me.player_id
                    left join players rp on rp.id = me.related_player_id
                    order by me.match_id, me.minute, me.stoppage_minute nulls first, me.id
                    """
                )
            ).mappings()
        ]

        coverage_counts = _clean_row(
            dict(
                conn.execute(
                    text(
                        """
                        select
                          coalesce((select count(distinct match_id) from match_events where event_type in ('goal', 'own_goal', 'penalty_goal')), 0) as matches_with_goal_events,
                          coalesce((select count(*) from (
                            select match_id
                            from match_player_appearances
                            where appearance_role = 'starter'
                            group by match_id
                            having count(*) >= 22
                          ) starters), 0) as matches_with_complete_lineups,
                          coalesce((select count(distinct match_id) from match_events where event_type in ('sub_in', 'sub_out')), 0) as matches_with_substitutions,
                          coalesce((select count(distinct match_id) from match_events where event_type in ('hydration_break_start', 'hydration_break_end')), 0) as matches_with_hydration_markers,
                          coalesce((select max(updated_at) from match_events), null) as last_event_update
                        """
                    )
                ).mappings().one()
            )
        )
    except Exception as exc:  # noqa: BLE001
        return load_event_stats_from_csv(match_rows)

    if not event_rows:
        return load_event_stats_from_csv(match_rows)

    stats = compute_event_tournament_stats(
        events_rows=[
            {
                "match_id": str(row.get("match_id") or ""),
                "event_type": str(row.get("event_type") or ""),
                "minute": str(row.get("minute") or 0),
                "stoppage_minute": "" if row.get("stoppage_minute") is None else str(row.get("stoppage_minute")),
                "period": str(row.get("period") or "unknown"),
                "team_iso3": str(row.get("team_iso3") or ""),
                "beneficiary_team_iso3": str(row.get("beneficiary_team_iso3") or ""),
                "player_name": str(row.get("player_name") or ""),
                "related_player_name": str(row.get("related_player_name") or ""),
            }
            for row in event_rows
        ],
        schedule_rows=schedule_rows,
    )
    finished_matches = len([row for row in match_rows if _has_result(row)])
    return {
        "available": True,
        "coverage": {
            "finished_matches": finished_matches,
            "matches_with_goal_events": int(coverage_counts["matches_with_goal_events"]),
            "matches_with_complete_lineups": int(coverage_counts["matches_with_complete_lineups"]),
            "matches_with_substitutions": int(coverage_counts["matches_with_substitutions"]),
            "matches_with_hydration_markers": int(coverage_counts["matches_with_hydration_markers"]),
            "last_event_update": coverage_counts.get("last_event_update"),
            "goal_event_coverage_share": round(int(coverage_counts["matches_with_goal_events"]) / finished_matches, 3) if finished_matches else None,
        },
        **stats,
    }


def _coverage_value(event_stats: dict[str, Any], key: str) -> int:
    coverage = event_stats.get("coverage") or {}
    value = coverage.get(key)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def prefer_richer_event_stats(
    match_rows: list[dict[str, Any]],
    primary_event_stats: dict[str, Any],
) -> dict[str, Any]:
    """Prefer local CSV-derived event stats when they cover more matches than the DB export."""

    local_event_stats = load_event_stats_from_csv(match_rows)
    comparison_keys = (
        "matches_with_goal_events",
        "matches_with_complete_lineups",
        "matches_with_substitutions",
        "matches_with_hydration_markers",
    )
    primary_score = sum(_coverage_value(primary_event_stats, key) for key in comparison_keys)
    local_score = sum(_coverage_value(local_event_stats, key) for key in comparison_keys)
    if local_score > primary_score:
        local_event_stats["source"] = "local_csv_preferred"
        return local_event_stats
    primary_event_stats["source"] = "database"
    return primary_event_stats


def _read_existing_export_payload(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").strip()
    prefix = "window.WM_MVP_DATA = "
    if not raw.startswith(prefix):
        raise ValueError(f"Unsupported data.js format in {path}")
    payload = raw[len(prefix):]
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


def _schedule_overlay_rows() -> dict[str, dict[str, str]]:
    schedule_path = Path("data/full_schedule_openfootball.csv")
    if not schedule_path.exists():
        return {}
    with schedule_path.open(newline="", encoding="utf-8") as handle:
        return {row["match_id"]: row for row in csv.DictReader(handle)}


def _knockout_resolution_override_rows() -> dict[str, dict[str, str]]:
    candidate = Path("data/knockout_resolution_overrides.csv")
    if not candidate.exists():
        return {}
    with candidate.open(newline="", encoding="utf-8") as handle:
        return {row["match_id"]: row for row in csv.DictReader(handle)}


def _knockout_event_resolution_rows() -> dict[str, dict[str, Any]]:
    candidate = Path("data/match_events.csv")
    if not candidate.exists():
        return {}
    periods_by_match: dict[str, set[str]] = {}
    with candidate.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            match_id = row.get("match_id") or ""
            period = str(row.get("period") or "").strip()
            if not match_id or not period:
                continue
            periods_by_match.setdefault(match_id, set()).add(period)
    derived: dict[str, dict[str, Any]] = {}
    for match_id, periods in periods_by_match.items():
        has_extra_time = bool({"ET1", "ET2"} & periods)
        has_penalties = "PEN" in periods
        resolution = None
        if has_penalties:
            resolution = "penalties"
        elif has_extra_time:
            resolution = "extra_time"
        if resolution:
            derived[match_id] = {
                "result_resolution": resolution,
                "event_periods": sorted(periods),
            }
    return derived


def _as_int_or_none(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)


def _apply_schedule_overlay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    schedule_rows = _schedule_overlay_rows()
    if not schedule_rows:
        return rows
    teams = _team_lookup()
    for row in rows:
        schedule_row = schedule_rows.get(str(row.get("match_id") or ""))
        if schedule_row is None:
            continue
        row["result_team_a"] = _as_int_or_none(schedule_row.get("result_team_a"))
        row["result_team_b"] = _as_int_or_none(schedule_row.get("result_team_b"))
        row["tournament_stage"] = _normalize_stage_key(schedule_row.get("tournament_stage") or row.get("tournament_stage"))
        row["match_status"] = schedule_row.get("match_status") or row.get("match_status")
        row["local_date"] = schedule_row.get("local_date") or row.get("local_date")
        row["local_time"] = schedule_row.get("local_time") or row.get("local_time")
        row["date_utc"] = schedule_row.get("date_utc") or row.get("date_utc")
        if schedule_row.get("calendar_day") not in ("", None):
            row["calendar_day"] = _as_int_or_none(schedule_row.get("calendar_day"))
        if schedule_row.get("matchday") not in ("", None):
            row["matchday"] = _as_int_or_none(schedule_row.get("matchday"))
        team_a_iso3 = schedule_row.get("team_a_iso3") or row.get("team_a_iso3")
        team_b_iso3 = schedule_row.get("team_b_iso3") or row.get("team_b_iso3")
        if team_a_iso3:
            team_a = _team_stub(team_a_iso3, teams)
            row["team_a_iso3"] = team_a["iso3"]
            row["team_a_name_de"] = team_a["name_de"]
            row["team_a_name_en"] = team_a["name_en"]
            row["team_a_flag"] = team_a["flag"]
        if team_b_iso3:
            team_b = _team_stub(team_b_iso3, teams)
            row["team_b_iso3"] = team_b["iso3"]
            row["team_b_name_de"] = team_b["name_de"]
            row["team_b_name_en"] = team_b["name_en"]
            row["team_b_flag"] = team_b["flag"]
    return rows


def _apply_knockout_resolution_overlay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_rows = _knockout_event_resolution_rows()
    override_rows = _knockout_resolution_override_rows()
    for row in rows:
        row.setdefault("result_resolution", None)
        row.setdefault("advanced_team_side", None)
        row.setdefault("shootout_score_team_a", None)
        row.setdefault("shootout_score_team_b", None)
        row.setdefault("event_periods", [])
        event_row = event_rows.get(str(row.get("match_id") or ""))
        if event_row:
            row["result_resolution"] = event_row.get("result_resolution") or row.get("result_resolution")
            row["event_periods"] = event_row.get("event_periods") or row.get("event_periods") or []
        if _has_result(row) and row.get("result_resolution") == "extra_time" and row.get("advanced_team_side") is None:
            if int(row["result_team_a"]) != int(row["result_team_b"]):
                row["advanced_team_side"] = "a" if int(row["result_team_a"]) > int(row["result_team_b"]) else "b"
        override_row = override_rows.get(str(row.get("match_id") or ""))
        if override_row:
            row["result_resolution"] = override_row.get("result_resolution") or row.get("result_resolution")
            row["advanced_team_side"] = override_row.get("advanced_team_side") or row.get("advanced_team_side")
            row["shootout_score_team_a"] = _as_int_or_none(override_row.get("shootout_score_team_a"))
            row["shootout_score_team_b"] = _as_int_or_none(override_row.get("shootout_score_team_b"))
            row["result_resolution_source_note"] = override_row.get("source_note") or None
        if _has_result(row) and row.get("result_resolution") == "penalties" and row.get("advanced_team_side") is None:
            shootout_a = row.get("shootout_score_team_a")
            shootout_b = row.get("shootout_score_team_b")
            if shootout_a is not None and shootout_b is not None and shootout_a != shootout_b:
                row["advanced_team_side"] = "a" if int(shootout_a) > int(shootout_b) else "b"
    return rows


def _team_lookup() -> dict[str, dict[str, str]]:
    for candidate in (Path("data/full_teams_restcountries.csv"), Path("data/sample_teams.csv")):
        if candidate.exists():
            with candidate.open(newline="", encoding="utf-8") as handle:
                return {row["iso3"]: row for row in csv.DictReader(handle)}
    return {}


def _venue_lookup() -> dict[tuple[str, str], dict[str, str]]:
    candidate = Path("data/sample_venues.csv")
    if not candidate.exists():
        return {}
    with candidate.open(newline="", encoding="utf-8") as handle:
        return {(row["stadium_name"], row["host_city"]): row for row in csv.DictReader(handle)}


def _forecast_lookup() -> dict[str, dict[str, str]]:
    candidate = Path("data/live_weather_forecast_full.csv")
    if not candidate.exists():
        return {}
    rows = _read_csv_if_exists(candidate)
    if not rows:
        return {}
    required = {
        "match_id",
        "forecast_temp",
        "forecast_min_temp",
        "forecast_max_temp",
        "forecast_precipitation_probability",
        "forecast_humidity",
        "forecast_wind_speed",
        "forecast_heat_index",
        "forecast_weather_code",
        "forecast_data_source",
        "data_quality_score",
    }
    if not required.issubset(rows[0].keys()):
        return {}
    return {row["match_id"]: row for row in rows}


def _value_or_none(value: str | None) -> Any:
    if value in ("", None):
        return None
    return value


def _number_or_none(value: str | None, caster=float) -> Any:
    if value in ("", None):
        return None
    try:
        return caster(value)
    except (TypeError, ValueError):
        return None


def _team_stub(iso3: str, lookup: dict[str, dict[str, str]]) -> dict[str, Any]:
    team = lookup.get(iso3)
    if team:
        return {
            "iso3": iso3,
            "name_de": team.get("name_de") or iso3,
            "name_en": team.get("name_en") or team.get("name_de") or iso3,
            "flag": team.get("flag_emoji") or "",
        }
    return {
        "iso3": iso3,
        "name_de": iso3,
        "name_en": iso3,
        "flag": "",
    }


def _append_missing_schedule_matches(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    schedule_rows = _schedule_overlay_rows()
    if not schedule_rows:
        return rows
    existing_ids = {str(row.get("match_id") or "") for row in rows}
    teams = _team_lookup()
    venues = _venue_lookup()
    forecasts = _forecast_lookup()
    for match_id, schedule_row in schedule_rows.items():
        if match_id in existing_ids:
            continue
        venue = venues.get((schedule_row.get("stadium_name") or "", schedule_row.get("host_city") or ""), {})
        forecast = forecasts.get(match_id, {})
        team_a = _team_stub(schedule_row.get("team_a_iso3") or "", teams)
        team_b = _team_stub(schedule_row.get("team_b_iso3") or "", teams)
        rows.append(
            {
                "match_id": match_id,
                "tournament_stage": _normalize_stage_key(schedule_row.get("tournament_stage")),
                "group_name": schedule_row.get("group_name") or "",
                "matchday": _as_int_or_none(schedule_row.get("matchday")),
                "matchday_label": schedule_row.get("matchday_label") or "",
                "calendar_day": _as_int_or_none(schedule_row.get("calendar_day")),
                "calendar_day_label": schedule_row.get("calendar_day_label") or "",
                "local_date": schedule_row.get("local_date") or "",
                "local_time": schedule_row.get("local_time") or "",
                "local_timezone": schedule_row.get("local_timezone") or venue.get("timezone") or "",
                "date_utc": schedule_row.get("date_utc") or "",
                "result_team_a": _as_int_or_none(schedule_row.get("result_team_a")),
                "result_team_b": _as_int_or_none(schedule_row.get("result_team_b")),
                "result_resolution": None,
                "advanced_team_side": None,
                "shootout_score_team_a": None,
                "shootout_score_team_b": None,
                "event_periods": [],
                "match_status": schedule_row.get("match_status") or "scheduled",
                "stadium_name": schedule_row.get("stadium_name") or "",
                "host_city": schedule_row.get("host_city") or "",
                "host_country": venue.get("host_country") or "",
                "latitude": _number_or_none(venue.get("latitude")),
                "longitude": _number_or_none(venue.get("longitude")),
                "elevation_m": _number_or_none(venue.get("elevation_m"), int),
                "stadium_type_basic": venue.get("stadium_type_basic") or "",
                "stadium_capacity": _number_or_none(venue.get("stadium_capacity"), int),
                "roof_available_boolean": venue.get("roof_available_boolean") == "true",
                "roof_type": venue.get("roof_type") or "",
                "climate_control_available": venue.get("climate_control_available") == "true",
                "weather_protection_level": _number_or_none(venue.get("weather_protection_level"), int),
                "climate_control_note_de": venue.get("climate_control_note_de") or "",
                "pitch_surface_note_de": venue.get("pitch_surface_note_de") or "",
                "venue_weather_note_de": venue.get("venue_weather_note_de") or "",
                "capacity_source_note": venue.get("capacity_source_note") or "",
                "coordinate_precision": venue.get("coordinate_precision") or "",
                "coordinate_accuracy_m": _number_or_none(venue.get("coordinate_accuracy_m"), int),
                "google_place_id": venue.get("google_place_id") or "",
                "maps_url": venue.get("maps_url") or "",
                "coordinate_verified_at": _value_or_none(venue.get("coordinate_verified_at")),
                "venue_data_quality_score": _number_or_none(venue.get("data_quality_score"), int),
                "team_a_iso3": team_a["iso3"],
                "team_a_name_de": team_a["name_de"],
                "team_a_name_en": team_a["name_en"],
                "team_a_flag": team_a["flag"],
                "team_b_iso3": team_b["iso3"],
                "team_b_name_de": team_b["name_de"],
                "team_b_name_en": team_b["name_en"],
                "team_b_flag": team_b["flag"],
                "forecast_temp": _number_or_none(forecast.get("forecast_temp")),
                "forecast_humidity": _number_or_none(forecast.get("forecast_humidity")),
                "forecast_wind_speed": _number_or_none(forecast.get("forecast_wind_speed")),
                "forecast_precipitation_probability": _number_or_none(forecast.get("forecast_precipitation_probability")),
                "forecast_heat_index": _number_or_none(forecast.get("forecast_heat_index")),
                "forecast_last_updated": None,
                "forecast_quality": _number_or_none(forecast.get("data_quality_score"), int),
                "actual_temp": None,
                "actual_humidity": None,
                "actual_precipitation": None,
                "actual_wind_speed": None,
                "actual_heat_index": None,
                "team_a_weather_fit_score": None,
                "team_a_weather_familiarity_score": None,
                "team_a_weather_tolerance_score": None,
                "team_a_effective_weather_load_score": None,
                "team_a_weather_fit_label": None,
                "team_a_weather_edge_role": None,
                "team_b_weather_fit_score": None,
                "team_b_weather_familiarity_score": None,
                "team_b_weather_tolerance_score": None,
                "team_b_effective_weather_load_score": None,
                "team_b_weather_fit_label": None,
                "team_b_weather_edge_role": None,
                "weather_load_score": None,
                "weather_fit_edge_gap": None,
                "predicted_result_category": None,
                "probability_team_a_win": None,
                "probability_draw": None,
                "probability_team_b_win": None,
                "main_context_advantage": None,
                "biggest_load_factor": None,
                "uncertainty_level": None,
                "team_a_travel_distance_km": None,
                "team_a_travel_time_hours": None,
                "team_a_rest_days": None,
                "team_a_recovery_hours": None,
                "team_a_cumulative_travel_km": None,
                "team_a_cumulative_recovery_load": None,
                "team_a_travel_recovery_score": None,
                "team_b_travel_distance_km": None,
                "team_b_travel_time_hours": None,
                "team_b_rest_days": None,
                "team_b_recovery_hours": None,
                "team_b_cumulative_travel_km": None,
                "team_b_cumulative_recovery_load": None,
                "team_b_travel_recovery_score": None,
                "team_a_timezone_shift": None,
                "team_a_timezone_shift_reference": None,
                "team_a_circadian_load_score": None,
                "team_b_timezone_shift": None,
                "team_b_timezone_shift_reference": None,
                "team_b_circadian_load_score": None,
                "team_a_elevation_change_m": None,
                "team_a_altitude_load_score": None,
                "team_b_elevation_change_m": None,
                "team_b_altitude_load_score": None,
                "team_a_fan_proximity_score": None,
                "team_b_fan_proximity_score": None,
                "team_a_strength_score": None,
                "team_b_strength_score": None,
                "preview_headline_de": None,
                "preview_subheadline_de": None,
                "preview_teaser_de": None,
                "preview_social_hook_de": None,
                "weather_headline_de": None,
                "weather_teaser_de": None,
                "weather_body_de": None,
                "weather_social_hook_de": None,
            }
        )
    rows.sort(key=lambda row: (str(row.get("date_utc") or ""), str(row.get("match_id") or "")))
    return rows


def _offline_payload_from_existing_export(output: str) -> dict[str, Any]:
    output_path = Path(output)
    fallback_path = output_path if output_path.exists() else Path("website/mvp/data.js")
    payload = _read_existing_export_payload(fallback_path)
    rows = _apply_knockout_resolution_overlay(
        _append_missing_schedule_matches(_apply_schedule_overlay([_clean_row(dict(row)) for row in payload.get("matches", [])]))
    )
    ads = payload.get("ads", [])
    event_stats = load_event_stats_from_csv(rows)
    offline_payload = {
        "metadata": {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "source": "Local offline export with schedule/result overlay",
            "language": "de",
            "matches": len(rows),
            "forecast_matches": len([row for row in rows if row.get("forecast_temp") is not None]),
            "weather_fit_matches": len([row for row in rows if row.get("team_a_weather_fit_score") is not None]),
        },
        "matches": rows,
        "standings": build_group_standings(rows),
        "analysis": build_analysis(rows),
        "event_stats": event_stats,
        "reports": {
            "group_stage_2026": build_group_stage_report(rows, event_stats),
        },
        "ads": ads,
    }
    encoded = json.dumps(offline_payload, ensure_ascii=False, indent=2, default=_json_default)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"window.WM_MVP_DATA = {encoded};\n", encoding="utf-8")
    return {"output": str(output_path), **offline_payload["metadata"]}


def export_website_mvp_data(output: str = "website/mvp/data.js") -> dict[str, Any]:
    """Export fixed-team matches and generated content to a browser-readable JS file."""

    text = _load_dependencies()
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = [
                _clean_row(dict(row))
                for row in conn.execute(
                    text(
                        """
                        select
                          m.match_id, m.tournament_stage, m.group_name, m.matchday,
                          m.matchday_label, m.calendar_day, m.calendar_day_label,
                          m.local_date, m.local_time, m.local_timezone, m.date_utc,
                          m.result_team_a, m.result_team_b, m.match_status,
                          v.stadium_name, v.host_city, v.host_country, v.latitude,
                          v.longitude, v.elevation_m,
                          v.stadium_type_basic, v.stadium_capacity, v.roof_available_boolean,
                          v.roof_type, v.climate_control_available, v.weather_protection_level,
                          v.climate_control_note_de, v.pitch_surface_note_de,
                          v.venue_weather_note_de, v.capacity_source_note,
                          v.coordinate_precision,
                          v.coordinate_accuracy_m, v.google_place_id, v.maps_url,
                          v.coordinate_verified_at, v.data_quality_score as venue_data_quality_score,
                          ta.iso3 as team_a_iso3, ta.name_de as team_a_name_de,
                          ta.name_en as team_a_name_en, ta.flag_emoji as team_a_flag,
                          tb.iso3 as team_b_iso3, tb.name_de as team_b_name_de,
                          tb.name_en as team_b_name_en, tb.flag_emoji as team_b_flag,
                          wf.forecast_temp, wf.forecast_humidity, wf.forecast_wind_speed,
                          wf.forecast_precipitation_probability, wf.forecast_heat_index,
                          wf.forecast_last_updated, wf.data_quality_score as forecast_quality,
                          wa.actual_temp, wa.actual_humidity, wa.actual_precipitation,
                          wa.actual_wind_speed, wa.actual_heat_index,
                          wma.weather_fit_score as team_a_weather_fit_score,
                          wma.weather_familiarity_score as team_a_weather_familiarity_score,
                          wma.weather_tolerance_score as team_a_weather_tolerance_score,
                          wma.effective_weather_load_score as team_a_effective_weather_load_score,
                          wma.weather_fit_label as team_a_weather_fit_label,
                          wma.edge_team_role as team_a_weather_edge_role,
                          wmb.weather_fit_score as team_b_weather_fit_score,
                          wmb.weather_familiarity_score as team_b_weather_familiarity_score,
                          wmb.weather_tolerance_score as team_b_weather_tolerance_score,
                          wmb.effective_weather_load_score as team_b_effective_weather_load_score,
                          wmb.weather_fit_label as team_b_weather_fit_label,
                          wmb.edge_team_role as team_b_weather_edge_role,
                          coalesce(wma.weather_load_score, wmb.weather_load_score) as weather_load_score,
                          coalesce(wma.edge_gap, wmb.edge_gap) as weather_fit_edge_gap,
                          p.predicted_result_category, p.probability_team_a_win,
                          p.probability_draw, p.probability_team_b_win,
                          p.main_context_advantage, p.biggest_load_factor,
                          p.uncertainty_level,
                          tma.distance_from_previous_venue_km as team_a_travel_distance_km,
                          tma.estimated_travel_time_hours as team_a_travel_time_hours,
                          tma.rest_days_since_previous_match as team_a_rest_days,
                          tma.hours_since_previous_kickoff as team_a_recovery_hours,
                          tma.cumulative_travel_distance_km as team_a_cumulative_travel_km,
                          tma.cumulative_recovery_load as team_a_cumulative_recovery_load,
                          tma.travel_recovery_score as team_a_travel_recovery_score,
                          tmb.distance_from_previous_venue_km as team_b_travel_distance_km,
                          tmb.estimated_travel_time_hours as team_b_travel_time_hours,
                          tmb.rest_days_since_previous_match as team_b_rest_days,
                          tmb.hours_since_previous_kickoff as team_b_recovery_hours,
                          tmb.cumulative_travel_distance_km as team_b_cumulative_travel_km,
                          tmb.cumulative_recovery_load as team_b_cumulative_recovery_load,
                          tmb.travel_recovery_score as team_b_travel_recovery_score,
                          tzma.timezone_shift_from_previous_match as team_a_timezone_shift,
                          tzma.timezone_shift_from_reference as team_a_timezone_shift_reference,
                          tzma.circadian_load_score as team_a_circadian_load_score,
                          tzmb.timezone_shift_from_previous_match as team_b_timezone_shift,
                          tzmb.timezone_shift_from_reference as team_b_timezone_shift_reference,
                          tzmb.circadian_load_score as team_b_circadian_load_score,
                          ama.elevation_change_from_previous_match_m as team_a_elevation_change_m,
                          ama.altitude_load_score as team_a_altitude_load_score,
                          amb.elevation_change_from_previous_match_m as team_b_elevation_change_m,
                          amb.altitude_load_score as team_b_altitude_load_score,
                          fpma.fan_proximity_score as team_a_fan_proximity_score,
                          fpmb.fan_proximity_score as team_b_fan_proximity_score,
                          sma.team_strength_score as team_a_strength_score,
                          smb.team_strength_score as team_b_strength_score,
                          preview_de.headline as preview_headline_de,
                          preview_de.subheadline as preview_subheadline_de,
                          preview_de.teaser as preview_teaser_de,
                          preview_de.social_hook as preview_social_hook_de,
                          weather_de.headline as weather_headline_de,
                          weather_de.teaser as weather_teaser_de,
                          weather_de.body as weather_body_de,
                          weather_de.social_hook as weather_social_hook_de
                        from matches m
                        join teams ta on ta.id = m.team_a_id
                        join teams tb on tb.id = m.team_b_id
                        join venues v on v.id = m.venue_id
                        left join weather_forecast wf on wf.match_id = m.match_id
                        left join weather_actual wa on wa.match_id = m.match_id
                        left join weather_matchup_metrics wma
                          on wma.match_id = m.match_id
                         and wma.team_id = m.team_a_id
                         and wma.source_weather_type = 'forecast'
                        left join weather_matchup_metrics wmb
                          on wmb.match_id = m.match_id
                         and wmb.team_id = m.team_b_id
                         and wmb.source_weather_type = 'forecast'
                        left join predictions p on p.match_id = m.match_id
                        left join travel_metrics tma
                          on tma.match_id = m.match_id and tma.team_id = m.team_a_id
                        left join travel_metrics tmb
                          on tmb.match_id = m.match_id and tmb.team_id = m.team_b_id
                        left join timezone_metrics tzma
                          on tzma.match_id = m.match_id and tzma.team_id = m.team_a_id
                        left join timezone_metrics tzmb
                          on tzmb.match_id = m.match_id and tzmb.team_id = m.team_b_id
                        left join altitude_metrics ama
                          on ama.match_id = m.match_id and ama.team_id = m.team_a_id
                        left join altitude_metrics amb
                          on amb.match_id = m.match_id and amb.team_id = m.team_b_id
                        left join fan_proximity_metrics fpma
                          on fpma.match_id = m.match_id and fpma.team_id = m.team_a_id
                        left join fan_proximity_metrics fpmb
                          on fpmb.match_id = m.match_id and fpmb.team_id = m.team_b_id
                        left join lateral (
                          select sm.team_strength_score
                          from sport_metrics sm
                          where sm.team_id = m.team_a_id
                          order by sm.last_updated_at desc
                          limit 1
                        ) sma on true
                        left join lateral (
                          select sm.team_strength_score
                          from sport_metrics sm
                          where sm.team_id = m.team_b_id
                          order by sm.last_updated_at desc
                          limit 1
                        ) smb on true
                        left join generated_texts preview_de
                          on preview_de.match_id = m.match_id
                         and preview_de.language = 'de'
                         and preview_de.content_type = 'match_preview'
                        left join generated_texts weather_de
                          on weather_de.match_id = m.match_id
                         and weather_de.language = 'de'
                         and weather_de.content_type = 'weather_fit_forecast'
                        where m.team_a_id is not null and m.team_b_id is not null
                        order by m.date_utc nulls last, m.match_id
                        """
                    )
                ).mappings()
            ]
            rows = _apply_knockout_resolution_overlay(_append_missing_schedule_matches(_apply_schedule_overlay(rows)))
            ads = load_ads(conn, text)
            event_stats = prefer_richer_event_stats(rows, load_event_stats(conn, text, rows))
    except Exception:  # noqa: BLE001
        return _offline_payload_from_existing_export(output)

    payload = {
        "metadata": {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "source": "Supabase/PostgreSQL static export",
            "language": "de",
            "matches": len(rows),
            "forecast_matches": len([row for row in rows if row.get("forecast_temp") is not None]),
            "weather_fit_matches": len([row for row in rows if row.get("team_a_weather_fit_score") is not None]),
            "event_stats_source": event_stats.get("source") or "database",
        },
        "matches": rows,
        "standings": build_group_standings(rows),
        "analysis": build_analysis(rows),
        "event_stats": event_stats,
        "reports": {
            "group_stage_2026": build_group_stage_report(rows, event_stats),
        },
        "ads": ads,
    }

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)
    output_path.write_text(f"window.WM_MVP_DATA = {encoded};\n", encoding="utf-8")
    return {"output": str(output_path), **payload["metadata"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export static website MVP data")
    parser.add_argument("--output", default="website/mvp/data.js")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(export_website_mvp_data(args.output), indent=2, ensure_ascii=False))
    except RuntimeError as exc:
        print(f"Website MVP export not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
