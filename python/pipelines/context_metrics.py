"""Compute travel, timezone, altitude and fan-proximity context metrics."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from python.db import get_engine
from python.scoring.scores import (
    altitude_load_score,
    circadian_load_score,
    fan_proximity_score,
    travel_recovery_score,
    venue_altitude_factor,
)
from python.utils.geo import estimate_travel_time_hours, haversine_distance_km as _haversine_distance_km
from python.utils.timezones import perceived_kickoff_time, timezone_shift_hours

HOST_COUNTRY_ISO3 = {"Canada": "CAN", "Mexico": "MEX", "United States": "USA"}
HOST_COUNTRY_CONTINENT = {"Canada": "North America", "Mexico": "North America", "United States": "North America"}


def _load_dependencies():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def haversine_distance_km_public(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Public wrapper matching the briefing function name."""

    return _haversine_distance_km(lat1, lon1, lat2, lon2)


def _load_team_matches(conn, text, team_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            select
              m.match_id, m.date_utc, m.local_date, m.local_time, m.local_timezone,
              t.id as team_id, t.iso3, t.continent, t.capital_latitude, t.capital_longitude,
              t.reference_timezone,
              v.host_city, v.host_country, v.latitude, v.longitude, v.elevation_m, v.timezone
            from matches m
            join teams t on t.id in (m.team_a_id, m.team_b_id)
            join venues v on v.id = m.venue_id
            where t.id = :team_id
            order by m.date_utc nulls last, m.match_id
            """
        ),
        {"team_id": team_id},
    ).mappings()
    return [dict(row) for row in rows]


def calculate_team_travel_metrics(team_id: str) -> list[dict[str, Any]]:
    """Calculate and upsert travel metrics for a team sorted by match date."""

    text = _load_dependencies()
    engine = get_engine()
    outputs: list[dict[str, Any]] = []
    with engine.begin() as conn:
        rows = _load_team_matches(conn, text, team_id)
        previous = None
        cumulative_distance = 0.0
        cumulative_timezone = 0.0
        cumulative_recovery_load = 0.0
        for row in rows:
            if previous:
                distance = _haversine_distance_km(
                    _as_float(previous["latitude"]),
                    _as_float(previous["longitude"]),
                    _as_float(row["latitude"]),
                    _as_float(row["longitude"]),
                )
                estimated_travel = estimate_travel_time_hours(distance)
                hours_since = (row["date_utc"] - previous["date_utc"]).total_seconds() / 3600 if row["date_utc"] and previous["date_utc"] else None
                rest_days = hours_since / 24 if hours_since is not None else None
                shift = timezone_shift_hours(previous["timezone"], row["timezone"], row["date_utc"].replace(tzinfo=None)) or 0
                previous_match_id = previous["match_id"]
                previous_city = previous["host_city"]
                previous_lat = previous["latitude"]
                previous_lon = previous["longitude"]
            else:
                distance = 0.0
                estimated_travel = 0.0
                hours_since = None
                rest_days = None
                shift = 0.0
                previous_match_id = None
                previous_city = None
                previous_lat = None
                previous_lon = None

            cumulative_distance += distance
            cumulative_timezone += abs(shift)
            net_recovery = hours_since - estimated_travel if hours_since is not None and estimated_travel is not None else None
            cumulative_recovery_load += max(0.0, 72 - (net_recovery or 72))
            score = travel_recovery_score(distance, hours_since, shift, cumulative_distance)
            payload = {
                "match_id": row["match_id"],
                "team_id": team_id,
                "previous_match_id": previous_match_id,
                "previous_host_city": previous_city,
                "previous_latitude": previous_lat,
                "previous_longitude": previous_lon,
                "current_host_city": row["host_city"],
                "current_latitude": row["latitude"],
                "current_longitude": row["longitude"],
                "distance_from_previous_venue_km": round(distance, 2),
                "estimated_travel_time_hours": round(estimated_travel or 0, 2),
                "rest_days_since_previous_match": None if rest_days is None else round(rest_days, 2),
                "hours_since_previous_kickoff": None if hours_since is None else round(hours_since, 2),
                "net_recovery_hours_after_estimated_travel": None if net_recovery is None else round(net_recovery, 2),
                "cumulative_travel_distance_km": round(cumulative_distance, 2),
                "cumulative_timezone_shift": round(cumulative_timezone, 2),
                "cumulative_recovery_load": round(cumulative_recovery_load, 2),
                "travel_recovery_score": score,
                "data_quality_score": 80 if previous else 65,
            }
            conn.execute(
                text(
                    """
                    insert into travel_metrics (
                      match_id, team_id, previous_match_id, previous_host_city,
                      previous_latitude, previous_longitude, current_host_city,
                      current_latitude, current_longitude, distance_from_previous_venue_km,
                      estimated_travel_time_hours, rest_days_since_previous_match,
                      hours_since_previous_kickoff, net_recovery_hours_after_estimated_travel,
                      cumulative_travel_distance_km, cumulative_timezone_shift,
                      cumulative_recovery_load, travel_recovery_score, data_quality_score
                    )
                    values (
                      :match_id, :team_id, :previous_match_id, :previous_host_city,
                      :previous_latitude, :previous_longitude, :current_host_city,
                      :current_latitude, :current_longitude, :distance_from_previous_venue_km,
                      :estimated_travel_time_hours, :rest_days_since_previous_match,
                      :hours_since_previous_kickoff, :net_recovery_hours_after_estimated_travel,
                      :cumulative_travel_distance_km, :cumulative_timezone_shift,
                      :cumulative_recovery_load, :travel_recovery_score, :data_quality_score
                    )
                    on conflict (match_id, team_id) do update set
                      previous_match_id = excluded.previous_match_id,
                      previous_host_city = excluded.previous_host_city,
                      previous_latitude = excluded.previous_latitude,
                      previous_longitude = excluded.previous_longitude,
                      current_host_city = excluded.current_host_city,
                      current_latitude = excluded.current_latitude,
                      current_longitude = excluded.current_longitude,
                      distance_from_previous_venue_km = excluded.distance_from_previous_venue_km,
                      estimated_travel_time_hours = excluded.estimated_travel_time_hours,
                      rest_days_since_previous_match = excluded.rest_days_since_previous_match,
                      hours_since_previous_kickoff = excluded.hours_since_previous_kickoff,
                      net_recovery_hours_after_estimated_travel = excluded.net_recovery_hours_after_estimated_travel,
                      cumulative_travel_distance_km = excluded.cumulative_travel_distance_km,
                      cumulative_timezone_shift = excluded.cumulative_timezone_shift,
                      cumulative_recovery_load = excluded.cumulative_recovery_load,
                      travel_recovery_score = excluded.travel_recovery_score,
                      data_quality_score = excluded.data_quality_score
                    """
                ),
                payload,
            )
            outputs.append(payload)
            previous = row
    return outputs


def calculate_timezone_metrics(team_id: str) -> list[dict[str, Any]]:
    """Calculate and upsert timezone and perceived-kickoff metrics for a team."""

    text = _load_dependencies()
    engine = get_engine()
    outputs: list[dict[str, Any]] = []
    with engine.begin() as conn:
        rows = _load_team_matches(conn, text, team_id)
        previous = None
        for row in rows:
            moment = row["date_utc"].replace(tzinfo=None) if row["date_utc"] else datetime.combine(row["local_date"], row["local_time"])
            prev_shift = timezone_shift_hours(previous["timezone"], row["timezone"], moment) if previous else 0
            ref_shift = timezone_shift_hours(row["reference_timezone"], row["timezone"], moment)
            local_dt = datetime.combine(row["local_date"], row["local_time"])
            perceived = perceived_kickoff_time(local_dt, row["timezone"], row["reference_timezone"])
            days_since = None
            if previous and previous["date_utc"] and row["date_utc"]:
                days_since = (row["date_utc"] - previous["date_utc"]).total_seconds() / 86400
            perceived_hour = perceived.hour + perceived.minute / 60 if perceived else None
            score = circadian_load_score(ref_shift, perceived_hour, days_since)
            payload = {
                "match_id": row["match_id"],
                "team_id": team_id,
                "team_reference_timezone": row["reference_timezone"],
                "previous_match_timezone": previous["timezone"] if previous else None,
                "current_match_timezone": row["timezone"],
                "timezone_shift_from_previous_match": prev_shift,
                "timezone_shift_from_reference": ref_shift,
                "local_kickoff_time": row["local_time"],
                "perceived_kickoff_time_reference": perceived,
                "days_since_timezone_shift": None if days_since is None else round(days_since, 2),
                "circadian_load_score": score,
                "data_quality_score": 80 if row["reference_timezone"] else 45,
            }
            conn.execute(
                text(
                    """
                    insert into timezone_metrics (
                      match_id, team_id, team_reference_timezone, previous_match_timezone,
                      current_match_timezone, timezone_shift_from_previous_match,
                      timezone_shift_from_reference, local_kickoff_time,
                      perceived_kickoff_time_reference, days_since_timezone_shift,
                      circadian_load_score, data_quality_score
                    )
                    values (
                      :match_id, :team_id, :team_reference_timezone, :previous_match_timezone,
                      :current_match_timezone, :timezone_shift_from_previous_match,
                      :timezone_shift_from_reference, :local_kickoff_time,
                      :perceived_kickoff_time_reference, :days_since_timezone_shift,
                      :circadian_load_score, :data_quality_score
                    )
                    on conflict (match_id, team_id) do update set
                      team_reference_timezone = excluded.team_reference_timezone,
                      previous_match_timezone = excluded.previous_match_timezone,
                      current_match_timezone = excluded.current_match_timezone,
                      timezone_shift_from_previous_match = excluded.timezone_shift_from_previous_match,
                      timezone_shift_from_reference = excluded.timezone_shift_from_reference,
                      local_kickoff_time = excluded.local_kickoff_time,
                      perceived_kickoff_time_reference = excluded.perceived_kickoff_time_reference,
                      days_since_timezone_shift = excluded.days_since_timezone_shift,
                      circadian_load_score = excluded.circadian_load_score,
                      data_quality_score = excluded.data_quality_score
                    """
                ),
                payload,
            )
            outputs.append(payload)
            previous = row
    return outputs


def calculate_altitude_metrics(team_id: str) -> list[dict[str, Any]]:
    """Calculate and upsert altitude metrics for a team."""

    text = _load_dependencies()
    engine = get_engine()
    outputs: list[dict[str, Any]] = []
    with engine.begin() as conn:
        rows = _load_team_matches(conn, text, team_id)
        previous = None
        for row in rows:
            current_elevation = _as_float(row["elevation_m"])
            previous_elevation = _as_float(previous["elevation_m"]) if previous else None
            elevation_change = (current_elevation or 0) - (previous_elevation or 0)
            venue_factor = venue_altitude_factor(current_elevation)
            load_score = altitude_load_score(current_elevation, elevation_change)
            payload = {
                "match_id": row["match_id"],
                "team_id": team_id,
                "current_venue_elevation_m": current_elevation,
                "previous_venue_elevation_m": previous_elevation,
                "elevation_change_from_previous_match_m": round(elevation_change, 2),
                "venue_altitude_factor": venue_factor,
                "altitude_load_score": load_score,
                "data_quality_score": 80 if current_elevation is not None else 35,
            }
            conn.execute(
                text(
                    """
                    insert into altitude_metrics (
                      match_id, team_id, current_venue_elevation_m, previous_venue_elevation_m,
                      elevation_change_from_previous_match_m, venue_altitude_factor,
                      altitude_load_score, data_quality_score
                    )
                    values (
                      :match_id, :team_id, :current_venue_elevation_m, :previous_venue_elevation_m,
                      :elevation_change_from_previous_match_m, :venue_altitude_factor,
                      :altitude_load_score, :data_quality_score
                    )
                    on conflict (match_id, team_id) do update set
                      current_venue_elevation_m = excluded.current_venue_elevation_m,
                      previous_venue_elevation_m = excluded.previous_venue_elevation_m,
                      elevation_change_from_previous_match_m = excluded.elevation_change_from_previous_match_m,
                      venue_altitude_factor = excluded.venue_altitude_factor,
                      altitude_load_score = excluded.altitude_load_score,
                      data_quality_score = excluded.data_quality_score
                    """
                ),
                payload,
            )
            outputs.append(payload)
            previous = row
    return outputs


def calculate_fan_proximity_metrics(match_id: str) -> list[dict[str, Any]]:
    """Calculate and upsert fan proximity indicators for both teams in a match."""

    text = _load_dependencies()
    engine = get_engine()
    outputs: list[dict[str, Any]] = []
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                select
                  m.match_id, t.id as team_id, t.iso3, t.continent, t.capital_latitude,
                  t.capital_longitude, v.host_country, v.latitude, v.longitude
                from matches m
                join teams t on t.id in (m.team_a_id, m.team_b_id)
                join venues v on v.id = m.venue_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings()
        for row in rows:
            host_iso3 = HOST_COUNTRY_ISO3.get(row["host_country"])
            host_continent = HOST_COUNTRY_CONTINENT.get(row["host_country"])
            is_host = row["iso3"] == host_iso3
            same_continent = row["continent"] == host_continent
            distance = None
            if row["capital_latitude"] is not None and row["capital_longitude"] is not None:
                distance = _haversine_distance_km(
                    _as_float(row["capital_latitude"]),
                    _as_float(row["capital_longitude"]),
                    _as_float(row["latitude"]),
                    _as_float(row["longitude"]),
                )
            score = fan_proximity_score(is_host, distance, same_continent)
            payload = {
                "match_id": row["match_id"],
                "team_id": row["team_id"],
                "host_country_team_boolean": is_host,
                "host_region_proximity_score": 100 if same_continent else 25,
                "distance_team_capital_to_venue_km": None if distance is None else round(distance, 2),
                "distance_team_country_centroid_to_venue_km": None,
                "same_continent_boolean": same_continent,
                "official_host_advantage_boolean": is_host,
                "fan_proximity_score": score,
                "data_quality_score": 78 if distance is not None else 40,
            }
            conn.execute(
                text(
                    """
                    insert into fan_proximity_metrics (
                      match_id, team_id, host_country_team_boolean, host_region_proximity_score,
                      distance_team_capital_to_venue_km, distance_team_country_centroid_to_venue_km,
                      same_continent_boolean, official_host_advantage_boolean,
                      fan_proximity_score, data_quality_score
                    )
                    values (
                      :match_id, :team_id, :host_country_team_boolean, :host_region_proximity_score,
                      :distance_team_capital_to_venue_km, :distance_team_country_centroid_to_venue_km,
                      :same_continent_boolean, :official_host_advantage_boolean,
                      :fan_proximity_score, :data_quality_score
                    )
                    on conflict (match_id, team_id) do update set
                      host_country_team_boolean = excluded.host_country_team_boolean,
                      host_region_proximity_score = excluded.host_region_proximity_score,
                      distance_team_capital_to_venue_km = excluded.distance_team_capital_to_venue_km,
                      distance_team_country_centroid_to_venue_km = excluded.distance_team_country_centroid_to_venue_km,
                      same_continent_boolean = excluded.same_continent_boolean,
                      official_host_advantage_boolean = excluded.official_host_advantage_boolean,
                      fan_proximity_score = excluded.fan_proximity_score,
                      data_quality_score = excluded.data_quality_score
                    """
                ),
                payload,
            )
            outputs.append(payload)
    return outputs


def calculate_context_metrics_for_all() -> dict[str, Any]:
    """Calculate all DB-backed context metrics for matches with fixed teams."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.connect() as conn:
        team_ids = [
            row[0]
            for row in conn.execute(
                text(
                    """
                    select t.id
                    from teams t
                    where exists (
                      select 1
                      from matches m
                      where m.team_a_id = t.id or m.team_b_id = t.id
                    )
                    order by t.iso3
                    """
                )
            )
        ]
        match_ids = [
            row[0]
            for row in conn.execute(
                text(
                    """
                    select match_id
                    from matches
                    where team_a_id is not null and team_b_id is not null
                    order by date_utc nulls last, match_id
                    """
                )
            )
        ]

    summary: dict[str, Any] = {
        "teams": len(team_ids),
        "matches_with_fixed_teams": len(match_ids),
        "travel_rows": 0,
        "timezone_rows": 0,
        "altitude_rows": 0,
        "fan_proximity_rows": 0,
        "skipped": [],
    }
    for team_id in team_ids:
        try:
            summary["travel_rows"] += len(calculate_team_travel_metrics(team_id))
            summary["timezone_rows"] += len(calculate_timezone_metrics(team_id))
            summary["altitude_rows"] += len(calculate_altitude_metrics(team_id))
        except Exception as exc:  # noqa: BLE001
            summary["skipped"].append({"team_id": str(team_id), "error": str(exc)})
    for match_id in match_ids:
        try:
            summary["fan_proximity_rows"] += len(calculate_fan_proximity_metrics(match_id))
        except Exception as exc:  # noqa: BLE001
            summary["skipped"].append({"match_id": str(match_id), "error": str(exc)})
    return summary


def compute_context_metrics(matches: list[dict[str, str]], venues: list[dict[str, str]], teams: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Return one sample metric row per match/team from CSV rows."""

    venue_by_key = {(row["stadium_name"], row["host_city"]): row for row in venues}
    team_by_iso3 = {row["iso3"]: row for row in teams}
    records: list[dict[str, Any]] = []
    for match in matches:
        venue = venue_by_key.get((match["stadium_name"], match["host_city"]))
        if venue is None:
            continue
        for side in ("a", "b"):
            team = team_by_iso3.get(match[f"team_{side}_iso3"])
            if team is None:
                continue
            distance = _haversine_distance_km(
                float(team["capital_latitude"]),
                float(team["capital_longitude"]),
                float(venue["latitude"]),
                float(venue["longitude"]),
            )
            host_iso3 = HOST_COUNTRY_ISO3.get(venue["host_country"])
            same_continent = team["continent"] == HOST_COUNTRY_CONTINENT.get(venue["host_country"])
            records.append(
                {
                    "match_id": match["match_id"],
                    "team_iso3": team["iso3"],
                    "distance_team_capital_to_venue_km": round(distance, 1),
                    "estimated_travel_time_hours": round(estimate_travel_time_hours(distance) or 0, 1),
                    "venue_altitude_factor": venue_altitude_factor(float(venue["elevation_m"]) if venue.get("elevation_m") else None),
                    "fan_proximity_score": fan_proximity_score(team["iso3"] == host_iso3, distance, same_continent),
                }
            )
    return records


def _print_records(records: list[dict[str, Any]]) -> None:
    if not records:
        print("No records")
        return
    columns = list(records[0].keys())
    print(" | ".join(columns))
    print("-" * 96)
    for row in records:
        print(" | ".join(str(row.get(column, "")) for column in columns))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute context metrics")
    parser.add_argument("--team-id", default=None)
    parser.add_argument("--match-id", default=None)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    if args.all:
        try:
            print(json.dumps(calculate_context_metrics_for_all(), default=str, indent=2))
        except RuntimeError as exc:
            print(f"Context metrics not completed: {exc}")
            return 1
        return 0

    if args.team_id:
        try:
            print(json.dumps(calculate_team_travel_metrics(args.team_id), default=str, indent=2))
            print(json.dumps(calculate_timezone_metrics(args.team_id), default=str, indent=2))
            print(json.dumps(calculate_altitude_metrics(args.team_id), default=str, indent=2))
        except RuntimeError as exc:
            print(f"Context metrics not completed: {exc}")
            return 1
        return 0

    if args.match_id:
        try:
            print(json.dumps(calculate_fan_proximity_metrics(args.match_id), default=str, indent=2))
        except RuntimeError as exc:
            print(f"Fan proximity not completed: {exc}")
            return 1
        return 0

    try:
        matches = _read_csv(Path("data/sample_schedule.csv"))
        venues = _read_csv(Path("data/sample_venues.csv"))
        teams = _read_csv(Path("data/sample_teams.csv"))
        _print_records(compute_context_metrics(matches, venues, teams)[:12])
    except (RuntimeError, ValueError) as exc:
        print(f"Sample context metrics not completed: {exc}")
        return 1
    return 0


# Briefing-compatible function alias.
haversine_distance_km = haversine_distance_km_public


if __name__ == "__main__":
    raise SystemExit(main())
