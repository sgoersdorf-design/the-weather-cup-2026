"""Import forecast-weather CSV rows into weather_forecast."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
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


def _load_sql():
    try:
        from sqlalchemy import bindparam, text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return bindparam, text


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _clean(row: dict[str, object]) -> dict[str, object]:
    return {key: (None if value == "" else value) for key, value in row.items()}


def is_forecast_error_placeholder(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    return set(rows[0].keys()) == {"match_id", "error", "data_quality_score"}


def validate_weather_forecast(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if is_forecast_error_placeholder(rows):
        return errors
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
    if not rows:
        errors.append("CSV contains no rows")
    return errors


def import_weather_forecast(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    path = Path(csv_path)
    rows = _read_rows(path)
    if is_forecast_error_placeholder(rows):
        return {
            "rows_processed": len(rows),
            "rows_inserted": 0,
            "rows_updated": 0,
            "rows_failed": len(rows),
            "rows_deleted": 0,
            "rows_skipped": len(rows),
        }
    errors = validate_weather_forecast(rows)
    if errors:
        raise ValueError("; ".join(errors))
    if dry_run:
        return {"rows_processed": len(rows), "rows_inserted": 0, "rows_updated": 0, "rows_failed": 0, "rows_deleted": 0, "rows_skipped": 0}

    bindparam, text = _load_sql()
    engine = get_engine()
    rows_inserted = rows_updated = rows_failed = rows_deleted = 0
    with engine.begin() as conn:
        match_ids = [row["match_id"] for row in rows]
        delete_result = conn.execute(
            text("delete from weather_forecast where match_id not in :match_ids").bindparams(
                bindparam("match_ids", expanding=True)
            ),
            {"match_ids": tuple(match_ids)},
        )
        rows_deleted = delete_result.rowcount or 0
        for row in rows:
            try:
                result = conn.execute(
                    text(
                        """
                        insert into weather_forecast (
                          match_id, forecast_temp, forecast_min_temp, forecast_max_temp,
                          forecast_precipitation_probability, forecast_humidity,
                          forecast_wind_speed, forecast_heat_index, forecast_weather_code,
                          forecast_data_source, data_quality_score
                        )
                        values (
                          :match_id, :forecast_temp, :forecast_min_temp, :forecast_max_temp,
                          :forecast_precipitation_probability, :forecast_humidity,
                          :forecast_wind_speed, :forecast_heat_index, :forecast_weather_code,
                          :forecast_data_source, :data_quality_score
                        )
                        on conflict (match_id) do update set
                          forecast_temp = excluded.forecast_temp,
                          forecast_min_temp = excluded.forecast_min_temp,
                          forecast_max_temp = excluded.forecast_max_temp,
                          forecast_precipitation_probability = excluded.forecast_precipitation_probability,
                          forecast_humidity = excluded.forecast_humidity,
                          forecast_wind_speed = excluded.forecast_wind_speed,
                          forecast_heat_index = excluded.forecast_heat_index,
                          forecast_weather_code = excluded.forecast_weather_code,
                          forecast_data_source = excluded.forecast_data_source,
                          forecast_last_updated = now(),
                          data_quality_score = excluded.data_quality_score
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
                print(f"Failed forecast {row.get('match_id')}: {exc}", file=sys.stderr)
    return {
        "rows_processed": len(rows),
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_failed": rows_failed,
        "rows_deleted": rows_deleted,
        "rows_skipped": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import weather forecast CSV")
    parser.add_argument("--file", default="data/live_weather_forecast.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(import_weather_forecast(args.file, dry_run=args.dry_run))
    except (RuntimeError, ValueError) as exc:
        print(f"Weather forecast import not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
