"""Import team weather profiles used for Weather Fit scoring."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
    "iso3",
    "reference_temp_c",
    "reference_humidity",
    "heat_tolerance_score",
    "humidity_tolerance_score",
    "rain_tolerance_score",
    "wind_tolerance_score",
    "profile_method",
    "data_source_name",
    "is_active",
    "data_quality_score",
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


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _clean(row: dict[str, object]) -> dict[str, object]:
    return {key: (None if value == "" else value) for key, value in row.items()}


def validate_weather_profiles(rows: list[dict[str, str]]) -> list[str]:
    """Validate profile CSV rows."""

    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
        return errors
    if not rows:
        errors.append("CSV contains no rows")
        return errors
    if any(len(str(row.get("iso3", ""))) != 3 for row in rows):
        errors.append("All iso3 values must have length 3")
    identities = [(row.get("iso3"), row.get("profile_method")) for row in rows]
    if len(identities) != len(set(identities)):
        errors.append("Duplicate iso3 + profile_method values found")
    for row in rows:
        for field in [
            "heat_tolerance_score",
            "humidity_tolerance_score",
            "rain_tolerance_score",
            "wind_tolerance_score",
            "data_quality_score",
        ]:
            try:
                value = float(row.get(field, ""))
            except ValueError:
                errors.append(f"{field} must be numeric")
                return errors
            if not 0 <= value <= 100:
                errors.append(f"{field} must be between 0 and 100")
                return errors
    return errors


def import_weather_profiles(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    """Import team weather profiles by team ISO3."""

    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_weather_profiles(rows)
    if errors:
        raise ValueError("; ".join(errors))

    for row in rows:
        row["iso3"] = row["iso3"].upper()
        row["is_active"] = _parse_bool(row.get("is_active", True))

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
                        insert into team_weather_profiles (
                          team_id, reference_temp_c, reference_humidity,
                          heat_tolerance_score, humidity_tolerance_score,
                          rain_tolerance_score, wind_tolerance_score,
                          profile_method, data_source_name, is_active, data_quality_score
                        )
                        values (
                          (select id from teams where iso3 = :iso3),
                          :reference_temp_c, :reference_humidity,
                          :heat_tolerance_score, :humidity_tolerance_score,
                          :rain_tolerance_score, :wind_tolerance_score,
                          :profile_method, :data_source_name, :is_active, :data_quality_score
                        )
                        on conflict (team_id, profile_method) do update set
                          reference_temp_c = excluded.reference_temp_c,
                          reference_humidity = excluded.reference_humidity,
                          heat_tolerance_score = excluded.heat_tolerance_score,
                          humidity_tolerance_score = excluded.humidity_tolerance_score,
                          rain_tolerance_score = excluded.rain_tolerance_score,
                          wind_tolerance_score = excluded.wind_tolerance_score,
                          data_source_name = excluded.data_source_name,
                          is_active = excluded.is_active,
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
                print(f"Failed profile {row.get('iso3')}: {exc}", file=sys.stderr)

        conn.execute(
            text(
                """
                insert into import_logs(
                  import_type, source_file, rows_processed, rows_inserted,
                  rows_updated, rows_failed, status, error_message
                )
                values (
                  'team_weather_profiles_csv', :source_file, :rows_processed, :rows_inserted,
                  :rows_updated, :rows_failed, :status, :error_message
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
    parser = argparse.ArgumentParser(description="Import team weather profiles")
    parser.add_argument("--file", default="data/sample_team_weather_profiles.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(import_weather_profiles(args.file, dry_run=args.dry_run))
    except (RuntimeError, ValueError) as exc:
        print(f"Weather-profile import not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
