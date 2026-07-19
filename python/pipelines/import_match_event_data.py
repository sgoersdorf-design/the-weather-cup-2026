"""Import player, lineup and event CSV data for post-match analysis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
from pathlib import Path
from typing import Any

from python.db import get_engine

PLAYER_REQUIRED_COLUMNS = {"team_iso3", "player_name"}
TEAM_SHEET_REQUIRED_COLUMNS = {"match_id", "team_iso3"}
APPEARANCE_REQUIRED_COLUMNS = {"match_id", "team_iso3", "player_name", "appearance_role"}
EVENT_REQUIRED_COLUMNS = {"match_id", "event_type", "minute"}
GOAL_EVENT_TYPES = {"goal", "own_goal", "penalty_goal"}
RETRYABLE_CONNECTION_ERROR_MARKERS = (
    "server closed the connection unexpectedly",
    "can't reconnect until invalid transaction is rolled back",
    "connection not open",
    "ssl connection has been closed unexpectedly",
)


def _load_sql():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _clean(row: dict[str, object]) -> dict[str, object]:
    return {key: (None if value == "" else value) for key, value in row.items()}


def _parse_int(value: str | None) -> int | None:
    if value in ("", None):
        return None
    return int(value)


def _parse_bool(value: str | None) -> bool | None:
    if value in ("", None):
        return None
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _event_row_key(row: dict[str, str]) -> str:
    payload = "|".join(
        [
            row.get("match_id", ""),
            row.get("team_iso3", ""),
            row.get("beneficiary_team_iso3", ""),
            row.get("player_name", ""),
            row.get("related_player_name", ""),
            row.get("event_type", ""),
            row.get("minute", ""),
            row.get("stoppage_minute", ""),
            row.get("period", ""),
            row.get("scoreboard_team_a", ""),
            row.get("scoreboard_team_b", ""),
            row.get("notes", ""),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _validate_columns(rows: list[dict[str, str]], required: set[str]) -> list[str]:
    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = required - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
    if not rows:
        errors.append("CSV contains no rows")
    return errors


def validate_players(rows: list[dict[str, str]]) -> list[str]:
    errors = _validate_columns(rows, PLAYER_REQUIRED_COLUMNS)
    for row in rows:
        if not row.get("team_iso3") or len(str(row.get("team_iso3"))) != 3:
            errors.append(f"Invalid team_iso3 for player row: {row.get('player_name')}")
            break
    return errors


def validate_team_sheets(rows: list[dict[str, str]]) -> list[str]:
    return _validate_columns(rows, TEAM_SHEET_REQUIRED_COLUMNS)


def validate_appearances(rows: list[dict[str, str]]) -> list[str]:
    errors = _validate_columns(rows, APPEARANCE_REQUIRED_COLUMNS)
    allowed_roles = {"starter", "bench", "unused"}
    for row in rows:
        if row.get("appearance_role") not in allowed_roles:
            errors.append(f"Invalid appearance_role for {row.get('player_name')}: {row.get('appearance_role')}")
            break
    return errors


def validate_events(rows: list[dict[str, str]]) -> list[str]:
    errors = _validate_columns(rows, EVENT_REQUIRED_COLUMNS)
    allowed_types = {
        "goal", "own_goal", "penalty_goal", "missed_penalty",
        "yellow_card", "red_card", "sub_in", "sub_out",
        "hydration_break_start", "hydration_break_end", "var_overturn", "other",
    }
    allowed_periods = {"1H", "2H", "ET1", "ET2", "PEN", "unknown", "", None}
    for row in rows:
        try:
            _parse_int(row.get("minute"))
        except (TypeError, ValueError):
            errors.append(f"Invalid minute for event row: {row}")
            break
        if row.get("event_type") not in allowed_types:
            errors.append(f"Invalid event_type in row: {row.get('event_type')}")
            break
        if row.get("period") not in allowed_periods:
            errors.append(f"Invalid period in row: {row.get('period')}")
            break
    return errors


def _team_id(conn, text, team_iso3: str) -> str:
    team_id = conn.execute(
        text("select id from teams where iso3 = :iso3"),
        {"iso3": team_iso3.upper()},
    ).scalar()
    if team_id is None:
        raise ValueError(f"Unknown team_iso3: {team_iso3}")
    return str(team_id)


def _player_id(conn, text, team_id: str, player_name: str) -> str | None:
    player_id = conn.execute(
        text("select id from players where team_id = :team_id and player_name = :player_name"),
        {"team_id": team_id, "player_name": player_name},
    ).scalar()
    return str(player_id) if player_id is not None else None


def _ensure_player(conn, text, team_id: str, row: dict[str, Any]) -> str:
    player_name = str(row["player_name"]).strip()
    existing = _player_id(conn, text, team_id, player_name)
    if existing:
        return existing
    inserted = conn.execute(
        text(
            """
            insert into players (
              team_id, player_name, preferred_name, shirt_number, position_group,
              date_of_birth, is_goalkeeper, data_source_name, data_quality_score
            )
            values (
              :team_id, :player_name, :preferred_name, :shirt_number, :position_group,
              :date_of_birth, :is_goalkeeper, :data_source_name, :data_quality_score
            )
            returning id
            """
        ),
        _clean(
            {
                "team_id": team_id,
                "player_name": player_name,
                "preferred_name": row.get("preferred_name"),
                "shirt_number": _parse_int(row.get("shirt_number")),
                "position_group": row.get("position_group") or row.get("position_label"),
                "date_of_birth": row.get("date_of_birth"),
                "is_goalkeeper": _parse_bool(row.get("is_goalkeeper")) or False,
                "data_source_name": row.get("data_source_name"),
                "data_quality_score": row.get("data_quality_score") or 0,
            }
        ),
    ).scalar()
    return str(inserted)


def _is_retryable_connection_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in RETRYABLE_CONNECTION_ERROR_MARKERS)


def _execute_with_retry(engine, operation, attempts: int = 3):
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with engine.begin() as conn:
                return operation(conn)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= attempts or not _is_retryable_connection_error(exc):
                raise
            time.sleep(min(attempt, 3))
    assert last_error is not None
    raise last_error


def import_match_event_data(
    players_file: str | None = None,
    team_sheets_file: str | None = None,
    appearances_file: str | None = None,
    events_file: str | None = None,
    dry_run: bool = False,
) -> dict[str, dict[str, int]]:
    """Import post-match event data from one or more CSV files."""

    payloads: dict[str, tuple[list[dict[str, str]], Any]] = {}
    if players_file:
        rows = _read_rows(Path(players_file))
        errors = validate_players(rows)
        if errors:
            raise ValueError("; ".join(errors))
        payloads["players"] = (rows, Path(players_file))
    if team_sheets_file:
        rows = _read_rows(Path(team_sheets_file))
        errors = validate_team_sheets(rows)
        if errors:
            raise ValueError("; ".join(errors))
        payloads["team_sheets"] = (rows, Path(team_sheets_file))
    if appearances_file:
        rows = _read_rows(Path(appearances_file))
        errors = validate_appearances(rows)
        if errors:
            raise ValueError("; ".join(errors))
        payloads["appearances"] = (rows, Path(appearances_file))
    if events_file:
        rows = _read_rows(Path(events_file))
        errors = validate_events(rows)
        if errors:
            raise ValueError("; ".join(errors))
        payloads["events"] = (rows, Path(events_file))
    if not payloads:
        raise ValueError("Pass at least one CSV file.")

    summary = {
        key: {"rows_processed": len(rows), "rows_inserted": 0, "rows_updated": 0, "rows_failed": 0}
        for key, (rows, _) in payloads.items()
    }
    if dry_run:
        return summary

    text = _load_sql()
    engine = get_engine()
    if "players" in payloads:
        rows, path = payloads["players"]
        for row in rows:
            try:
                def _upsert_player(conn):
                    team_id = _team_id(conn, text, row["team_iso3"])
                    result = conn.execute(
                            text(
                                """
                                insert into players (
                                  team_id, player_name, preferred_name, shirt_number, position_group,
                                  date_of_birth, is_goalkeeper, data_source_name, data_quality_score
                                )
                                values (
                                  :team_id, :player_name, :preferred_name, :shirt_number, :position_group,
                                  :date_of_birth, :is_goalkeeper, :data_source_name, :data_quality_score
                                )
                                on conflict (team_id, player_name) do update set
                                  preferred_name = excluded.preferred_name,
                                  shirt_number = excluded.shirt_number,
                                  position_group = excluded.position_group,
                                  date_of_birth = excluded.date_of_birth,
                                  is_goalkeeper = excluded.is_goalkeeper,
                                  data_source_name = excluded.data_source_name,
                                  data_quality_score = excluded.data_quality_score
                                returning (xmax = 0) as inserted
                                """
                            ),
                            _clean(
                                {
                                    "team_id": team_id,
                                    "player_name": row["player_name"],
                                    "preferred_name": row.get("preferred_name"),
                                    "shirt_number": _parse_int(row.get("shirt_number")),
                                    "position_group": row.get("position_group"),
                                    "date_of_birth": row.get("date_of_birth"),
                                    "is_goalkeeper": _parse_bool(row.get("is_goalkeeper")) or False,
                                    "data_source_name": row.get("data_source_name"),
                                    "data_quality_score": row.get("data_quality_score") or 0,
                                }
                            ),
                        )
                    return bool(result.scalar())

                inserted = _execute_with_retry(engine, _upsert_player)
                summary["players"]["rows_inserted"] += int(inserted)
                summary["players"]["rows_updated"] += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                summary["players"]["rows_failed"] += 1
                print(f"Failed player {row.get('player_name')}: {exc}", file=sys.stderr)
        _execute_with_retry(
            engine,
            lambda conn: conn.execute(
                text(
                    """
                    insert into import_logs(
                      import_type, source_file, rows_processed, rows_inserted, rows_updated, rows_failed, status, error_message
                    )
                    values (
                      'match_players_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated, :rows_failed, :status, :error_message
                    )
                    """
                ),
                {
                    "source_file": str(path),
                    "rows_processed": summary["players"]["rows_processed"],
                    "rows_inserted": summary["players"]["rows_inserted"],
                    "rows_updated": summary["players"]["rows_updated"],
                    "rows_failed": summary["players"]["rows_failed"],
                    "status": "completed" if summary["players"]["rows_failed"] == 0 else "partial",
                    "error_message": None if summary["players"]["rows_failed"] == 0 else "Some player rows failed; see stderr.",
                },
            ),
        )

    if "team_sheets" in payloads:
        rows, path = payloads["team_sheets"]
        for row in rows:
            try:
                def _upsert_team_sheet(conn):
                    team_id = _team_id(conn, text, row["team_iso3"])
                    captain_player_id = None
                    if row.get("captain_player_name"):
                        captain_player_id = _ensure_player(conn, text, team_id, {"player_name": row["captain_player_name"], "data_source_name": row.get("data_source_name"), "data_quality_score": row.get("data_quality_score")})
                    result = conn.execute(
                            text(
                                """
                                insert into match_team_sheets (
                                  match_id, team_id, formation, coach_name, captain_player_id,
                                  hydration_break_planned, notes, data_source_name, data_quality_score
                                )
                                values (
                                  :match_id, :team_id, :formation, :coach_name, :captain_player_id,
                                  :hydration_break_planned, :notes, :data_source_name, :data_quality_score
                                )
                                on conflict (match_id, team_id) do update set
                                  formation = excluded.formation,
                                  coach_name = excluded.coach_name,
                                  captain_player_id = excluded.captain_player_id,
                                  hydration_break_planned = excluded.hydration_break_planned,
                                  notes = excluded.notes,
                                  data_source_name = excluded.data_source_name,
                                  data_quality_score = excluded.data_quality_score
                                returning (xmax = 0) as inserted
                                """
                            ),
                            _clean(
                                {
                                    "match_id": row["match_id"],
                                    "team_id": team_id,
                                    "formation": row.get("formation"),
                                    "coach_name": row.get("coach_name"),
                                    "captain_player_id": captain_player_id,
                                    "hydration_break_planned": _parse_bool(row.get("hydration_break_planned")),
                                    "notes": row.get("notes"),
                                    "data_source_name": row.get("data_source_name"),
                                    "data_quality_score": row.get("data_quality_score") or 0,
                                }
                            ),
                        )
                    return bool(result.scalar())

                inserted = _execute_with_retry(engine, _upsert_team_sheet)
                summary["team_sheets"]["rows_inserted"] += int(inserted)
                summary["team_sheets"]["rows_updated"] += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                summary["team_sheets"]["rows_failed"] += 1
                print(f"Failed team sheet {row.get('match_id')} {row.get('team_iso3')}: {exc}", file=sys.stderr)
        _execute_with_retry(
            engine,
            lambda conn: conn.execute(
                text(
                    """
                    insert into import_logs(
                      import_type, source_file, rows_processed, rows_inserted, rows_updated, rows_failed, status, error_message
                    )
                    values (
                      'match_team_sheets_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated, :rows_failed, :status, :error_message
                    )
                    """
                ),
                {
                    "source_file": str(path),
                    "rows_processed": summary["team_sheets"]["rows_processed"],
                    "rows_inserted": summary["team_sheets"]["rows_inserted"],
                    "rows_updated": summary["team_sheets"]["rows_updated"],
                    "rows_failed": summary["team_sheets"]["rows_failed"],
                    "status": "completed" if summary["team_sheets"]["rows_failed"] == 0 else "partial",
                    "error_message": None if summary["team_sheets"]["rows_failed"] == 0 else "Some team sheet rows failed; see stderr.",
                },
            ),
        )

    if "appearances" in payloads:
        rows, path = payloads["appearances"]
        for row in rows:
            try:
                def _upsert_appearance(conn):
                    team_id = _team_id(conn, text, row["team_iso3"])
                    player_id = _ensure_player(conn, text, team_id, row)
                    result = conn.execute(
                            text(
                                """
                                insert into match_player_appearances (
                                  match_id, team_id, player_id, appearance_role, shirt_number,
                                  position_label, lineup_slot, minute_in, minute_out, minutes_played,
                                  is_captain, is_goalkeeper, data_source_name, data_quality_score
                                )
                                values (
                                  :match_id, :team_id, :player_id, :appearance_role, :shirt_number,
                                  :position_label, :lineup_slot, :minute_in, :minute_out, :minutes_played,
                                  :is_captain, :is_goalkeeper, :data_source_name, :data_quality_score
                                )
                                on conflict (match_id, team_id, player_id) do update set
                                  appearance_role = excluded.appearance_role,
                                  shirt_number = excluded.shirt_number,
                                  position_label = excluded.position_label,
                                  lineup_slot = excluded.lineup_slot,
                                  minute_in = excluded.minute_in,
                                  minute_out = excluded.minute_out,
                                  minutes_played = excluded.minutes_played,
                                  is_captain = excluded.is_captain,
                                  is_goalkeeper = excluded.is_goalkeeper,
                                  data_source_name = excluded.data_source_name,
                                  data_quality_score = excluded.data_quality_score
                                returning (xmax = 0) as inserted
                                """
                            ),
                            _clean(
                                {
                                    "match_id": row["match_id"],
                                    "team_id": team_id,
                                    "player_id": player_id,
                                    "appearance_role": row["appearance_role"],
                                    "shirt_number": _parse_int(row.get("shirt_number")),
                                    "position_label": row.get("position_label"),
                                    "lineup_slot": row.get("lineup_slot"),
                                    "minute_in": _parse_int(row.get("minute_in")),
                                    "minute_out": _parse_int(row.get("minute_out")),
                                    "minutes_played": _parse_int(row.get("minutes_played")),
                                    "is_captain": _parse_bool(row.get("is_captain")) or False,
                                    "is_goalkeeper": _parse_bool(row.get("is_goalkeeper")) or False,
                                    "data_source_name": row.get("data_source_name"),
                                    "data_quality_score": row.get("data_quality_score") or 0,
                                }
                            ),
                        )
                    return bool(result.scalar())

                inserted = _execute_with_retry(engine, _upsert_appearance)
                summary["appearances"]["rows_inserted"] += int(inserted)
                summary["appearances"]["rows_updated"] += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                summary["appearances"]["rows_failed"] += 1
                print(f"Failed appearance {row.get('match_id')} {row.get('player_name')}: {exc}", file=sys.stderr)
        _execute_with_retry(
            engine,
            lambda conn: conn.execute(
                text(
                    """
                    insert into import_logs(
                      import_type, source_file, rows_processed, rows_inserted, rows_updated, rows_failed, status, error_message
                    )
                    values (
                      'match_player_appearances_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated, :rows_failed, :status, :error_message
                    )
                    """
                ),
                {
                    "source_file": str(path),
                    "rows_processed": summary["appearances"]["rows_processed"],
                    "rows_inserted": summary["appearances"]["rows_inserted"],
                    "rows_updated": summary["appearances"]["rows_updated"],
                    "rows_failed": summary["appearances"]["rows_failed"],
                    "status": "completed" if summary["appearances"]["rows_failed"] == 0 else "partial",
                    "error_message": None if summary["appearances"]["rows_failed"] == 0 else "Some appearance rows failed; see stderr.",
                },
            ),
        )

    if "events" in payloads:
        rows, path = payloads["events"]
        for row in rows:
            try:
                def _upsert_event(conn):
                    team_id = _team_id(conn, text, row["team_iso3"]) if row.get("team_iso3") else None
                    player_id = _ensure_player(conn, text, team_id, row) if team_id and row.get("player_name") else None
                    related_player_id = None
                    if team_id and row.get("related_player_name"):
                        related_player_id = _ensure_player(
                            conn,
                            text,
                            team_id,
                            {"player_name": row["related_player_name"], "data_source_name": row.get("data_source_name"), "data_quality_score": row.get("data_quality_score")},
                        )
                    beneficiary_team_id = _team_id(conn, text, row["beneficiary_team_iso3"]) if row.get("beneficiary_team_iso3") else team_id
                    result = conn.execute(
                            text(
                                """
                                insert into match_events (
                                  match_id, source_row_key, team_id, beneficiary_team_id, player_id, related_player_id,
                                  event_type, minute, stoppage_minute, period,
                                  scoreboard_team_a, scoreboard_team_b, notes,
                                  data_source_name, data_quality_score
                                )
                                values (
                                  :match_id, :source_row_key, :team_id, :beneficiary_team_id, :player_id, :related_player_id,
                                  :event_type, :minute, :stoppage_minute, :period,
                                  :scoreboard_team_a, :scoreboard_team_b, :notes,
                                  :data_source_name, :data_quality_score
                                )
                                on conflict (source_row_key) do update set
                                  team_id = excluded.team_id,
                                  beneficiary_team_id = excluded.beneficiary_team_id,
                                  player_id = excluded.player_id,
                                  related_player_id = excluded.related_player_id,
                                  event_type = excluded.event_type,
                                  minute = excluded.minute,
                                  stoppage_minute = excluded.stoppage_minute,
                                  period = excluded.period,
                                  scoreboard_team_a = excluded.scoreboard_team_a,
                                  scoreboard_team_b = excluded.scoreboard_team_b,
                                  notes = excluded.notes,
                                  data_source_name = excluded.data_source_name,
                                  data_quality_score = excluded.data_quality_score
                                returning (xmax = 0) as inserted
                                """
                            ),
                            _clean(
                                {
                                    "match_id": row["match_id"],
                                    "source_row_key": _event_row_key(row),
                                    "team_id": team_id,
                                    "beneficiary_team_id": beneficiary_team_id if row.get("event_type") in GOAL_EVENT_TYPES else row.get("beneficiary_team_iso3") and beneficiary_team_id,
                                    "player_id": player_id,
                                    "related_player_id": related_player_id,
                                    "event_type": row["event_type"],
                                    "minute": _parse_int(row.get("minute")),
                                    "stoppage_minute": _parse_int(row.get("stoppage_minute")),
                                    "period": row.get("period") or "unknown",
                                    "scoreboard_team_a": _parse_int(row.get("scoreboard_team_a")),
                                    "scoreboard_team_b": _parse_int(row.get("scoreboard_team_b")),
                                    "notes": row.get("notes"),
                                    "data_source_name": row.get("data_source_name"),
                                    "data_quality_score": row.get("data_quality_score") or 0,
                                }
                            ),
                        )
                    return bool(result.scalar())

                inserted = _execute_with_retry(engine, _upsert_event)
                summary["events"]["rows_inserted"] += int(inserted)
                summary["events"]["rows_updated"] += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                summary["events"]["rows_failed"] += 1
                print(f"Failed event {row.get('match_id')} {row.get('event_type')} {row.get('minute')}: {exc}", file=sys.stderr)
        _execute_with_retry(
            engine,
            lambda conn: conn.execute(
                text(
                    """
                    insert into import_logs(
                      import_type, source_file, rows_processed, rows_inserted, rows_updated, rows_failed, status, error_message
                    )
                    values (
                      'match_events_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated, :rows_failed, :status, :error_message
                    )
                    """
                ),
                {
                    "source_file": str(path),
                    "rows_processed": summary["events"]["rows_processed"],
                    "rows_inserted": summary["events"]["rows_inserted"],
                    "rows_updated": summary["events"]["rows_updated"],
                    "rows_failed": summary["events"]["rows_failed"],
                    "status": "completed" if summary["events"]["rows_failed"] == 0 else "partial",
                    "error_message": None if summary["events"]["rows_failed"] == 0 else "Some event rows failed; see stderr.",
                },
            ),
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import player, lineup and event CSVs")
    parser.add_argument("--players", default=None)
    parser.add_argument("--team-sheets", default=None)
    parser.add_argument("--appearances", default=None)
    parser.add_argument("--events", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(
            import_match_event_data(
                players_file=args.players,
                team_sheets_file=args.team_sheets,
                appearances_file=args.appearances,
                events_file=args.events,
                dry_run=args.dry_run,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Match event import not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
