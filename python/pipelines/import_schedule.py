"""Import a validated WM 2026 schedule CSV into PostgreSQL/Supabase."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
    "match_id",
    "date_utc",
    "local_date",
    "local_time",
    "local_timezone",
    "team_a_iso3",
    "team_b_iso3",
    "stadium_name",
    "host_city",
}


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


def validate_schedule(rows: list[dict[str, str]]) -> list[str]:
    """Validate schedule rows before database import."""

    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
        return errors
    if not rows:
        errors.append("CSV contains no rows")
        return errors
    match_ids = [row.get("match_id") for row in rows]
    if len(match_ids) != len(set(match_ids)):
        errors.append("Duplicate match_id values found")
    for row in rows:
        try:
            datetime.fromisoformat(str(row.get("date_utc", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append("Some date_utc values are invalid")
            break
    if any(not row.get("team_a_iso3") or not row.get("team_b_iso3") or not row.get("stadium_name") or not row.get("host_city") for row in rows):
        errors.append("Teams and venue identity columns must not be empty")
    return errors


def import_schedule(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    """Import a schedule CSV with team and venue lookup by ISO3 and venue name."""

    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_schedule(rows)
    if errors:
        raise ValueError("; ".join(errors))

    for row in rows:
        row["team_a_iso3"] = str(row["team_a_iso3"]).upper()
        row["team_b_iso3"] = str(row["team_b_iso3"]).upper()
        row.setdefault("tournament_stage", "")
        row.setdefault("group_name", "")
        row.setdefault("matchday", "")
        row.setdefault("matchday_label", "")
        row.setdefault("calendar_day", "")
        row.setdefault("calendar_day_label", "")
        row.setdefault("match_status", "scheduled")
        row.setdefault("data_source_name", "schedule_csv")
        row.setdefault("data_quality_score", "70")

    if dry_run:
        return {"rows_processed": len(rows), "rows_inserted": 0, "rows_updated": 0, "rows_failed": 0}

    text = _load_sql()
    engine = get_engine()
    rows_inserted = rows_updated = rows_failed = 0
    with engine.begin() as conn:
        for row in rows:
            payload = _clean(row)
            try:
                result = conn.execute(
                    text(
                        """
                        insert into matches (
                          match_id, tournament_stage, group_name, matchday,
                          matchday_label, calendar_day, calendar_day_label, date_utc,
                          local_date, local_time, local_timezone, team_a_id, team_b_id,
                          venue_id, match_status, data_source_name, data_quality_score
                        )
                        values (
                          :match_id, :tournament_stage, :group_name, :matchday,
                          :matchday_label, :calendar_day, :calendar_day_label, :date_utc,
                          :local_date, :local_time, :local_timezone,
                          (select id from teams where iso3 = :team_a_iso3),
                          (select id from teams where iso3 = :team_b_iso3),
                          (select id from venues where stadium_name = :stadium_name and host_city = :host_city),
                          :match_status, :data_source_name, :data_quality_score
                        )
                        on conflict (match_id) do update set
                          tournament_stage = excluded.tournament_stage,
                          group_name = excluded.group_name,
                          matchday = excluded.matchday,
                          matchday_label = excluded.matchday_label,
                          calendar_day = excluded.calendar_day,
                          calendar_day_label = excluded.calendar_day_label,
                          date_utc = excluded.date_utc,
                          local_date = excluded.local_date,
                          local_time = excluded.local_time,
                          local_timezone = excluded.local_timezone,
                          team_a_id = excluded.team_a_id,
                          team_b_id = excluded.team_b_id,
                          venue_id = excluded.venue_id,
                          match_status = excluded.match_status,
                          data_source_name = excluded.data_source_name,
                          data_quality_score = excluded.data_quality_score
                        returning (xmax = 0) as inserted
                        """
                    ),
                    payload,
                )
                inserted = bool(result.scalar())
                rows_inserted += int(inserted)
                rows_updated += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                rows_failed += 1
                print(f"Failed match {row.get('match_id')}: {exc}", file=sys.stderr)

        conn.execute(
            text(
                """
                insert into import_logs(
                  import_type, source_file, rows_processed, rows_inserted, rows_updated,
                  rows_failed, status, error_message
                )
                values (
                  'schedule_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated,
                  :rows_failed, :status, :error_message
                )
                """
            ),
            {
                "source_file": str(path),
                "rows_processed": len(rows),
                "rows_inserted": rows_inserted,
                "rows_updated": rows_updated,
                "rows_failed": rows_failed,
                "status": "completed" if rows_failed == 0 else "partial",
                "error_message": None if rows_failed == 0 else "Some rows failed; see stderr.",
            },
        )

    return {
        "rows_processed": len(rows),
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_failed": rows_failed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import schedule CSV")
    parser.add_argument("--file", default="data/sample_schedule.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = import_schedule(args.file, dry_run=args.dry_run)
    except (RuntimeError, ValueError) as exc:
        print(f"Schedule import not completed: {exc}")
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
