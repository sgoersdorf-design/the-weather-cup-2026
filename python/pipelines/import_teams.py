"""Import teams CSV into the teams table."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
    "name_de",
    "name_en",
    "iso2",
    "iso3",
    "confederation",
    "continent",
    "reference_timezone",
}


def _load_sql():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _clean(row: dict[str, object]) -> dict[str, object]:
    return {key: (None if value == "" else value) for key, value in row.items()}


def validate_teams(rows: list[dict[str, str]]) -> list[str]:
    """Validate team rows for MVP import."""

    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
        return errors

    if not rows:
        errors.append("CSV contains no rows")
        return errors

    if any(not row.get("iso2") or not row.get("iso3") for row in rows):
        errors.append("ISO2 and ISO3 must not be empty")
    if any(len(str(row.get("iso2", ""))) != 2 for row in rows):
        errors.append("All iso2 values must have length 2")
    if any(len(str(row.get("iso3", ""))) != 3 for row in rows):
        errors.append("All iso3 values must have length 3")
    iso3_values = [row.get("iso3") for row in rows]
    if len(iso3_values) != len(set(iso3_values)):
        errors.append("Duplicate iso3 values found")
    if any(not row.get("name_de") or not row.get("name_en") for row in rows):
        errors.append("Localized team names must not be empty")
    return errors


def import_teams(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    """Import teams from a CSV file with PostgreSQL upserts."""

    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_teams(rows)
    if errors:
        raise ValueError("; ".join(errors))

    for row in rows:
        row["iso2"] = str(row["iso2"]).upper()
        row["iso3"] = str(row["iso3"]).upper()
        row.setdefault("flag_emoji", "")
        row.setdefault("capital_city", "")
        row.setdefault("capital_latitude", "")
        row.setdefault("capital_longitude", "")
        row.setdefault("reference_timezone_method", "")

    if dry_run:
        return {"rows_processed": len(rows), "rows_inserted": 0, "rows_updated": 0, "rows_failed": 0}

    text = _load_sql()
    engine = get_engine()
    rows_inserted = rows_updated = rows_failed = 0
    with engine.begin() as conn:
        for row in rows:
            try:
                result = conn.execute(
                    text(
                        """
                        insert into teams (
                          name_de, name_en, iso2, iso3, flag_emoji, confederation, continent,
                          capital_city, capital_latitude, capital_longitude,
                          reference_timezone, reference_timezone_method
                        )
                        values (
                          :name_de, :name_en, :iso2, :iso3, :flag_emoji, :confederation, :continent,
                          :capital_city, :capital_latitude, :capital_longitude,
                          :reference_timezone, :reference_timezone_method
                        )
                        on conflict (iso3) do update set
                          name_de = excluded.name_de,
                          name_en = excluded.name_en,
                          iso2 = excluded.iso2,
                          flag_emoji = excluded.flag_emoji,
                          confederation = excluded.confederation,
                          continent = excluded.continent,
                          capital_city = excluded.capital_city,
                          capital_latitude = excluded.capital_latitude,
                          capital_longitude = excluded.capital_longitude,
                          reference_timezone = excluded.reference_timezone,
                          reference_timezone_method = excluded.reference_timezone_method
                        returning (xmax = 0) as inserted
                        """
                    ),
                    _clean(row),
                )
                inserted = bool(result.scalar())
                rows_inserted += int(inserted)
                rows_updated += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                rows_failed += 1
                print(f"Failed team {row.get('iso3')}: {exc}", file=sys.stderr)

        conn.execute(
            text(
                """
                insert into import_logs(
                  import_type, source_file, rows_processed, rows_inserted, rows_updated,
                  rows_failed, status, error_message
                )
                values (
                  'teams_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated,
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
    parser = argparse.ArgumentParser(description="Import teams CSV")
    parser.add_argument("--file", default="data/sample_teams.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = import_teams(args.file, dry_run=args.dry_run)
    except (RuntimeError, ValueError) as exc:
        print(f"Team import not completed: {exc}")
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
