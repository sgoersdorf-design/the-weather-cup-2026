"""Fetch real Open-Meteo forecasts for a schedule CSV and venues CSV."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Any

from python.pipelines.weather_open_meteo import fetch_forecast_data, normalize_forecast_weather

FORECAST_COLUMNS = {
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _is_valid_forecast_file(path: Path) -> bool:
    if not path.exists():
        return False
    rows = _read_csv(path)
    if not rows:
        return False
    return FORECAST_COLUMNS.issubset(rows[0].keys())


def fetch_forecasts_for_csv(schedule_path: str, venues_path: str, output_path: str) -> dict[str, int]:
    schedule = _read_csv(Path(schedule_path))
    venues = {(row["stadium_name"], row["host_city"]): row for row in _read_csv(Path(venues_path))}
    today = dt.date.today()
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    venue_forecasts: dict[tuple[float, float, str], tuple[dict[str, Any], str, int]] = {}
    skipped = 0
    failed = 0
    for match in schedule:
        venue = venues.get((match["stadium_name"], match["host_city"]))
        if not venue:
            skipped += 1
            continue
        local_date = dt.date.fromisoformat(match["local_date"])
        if not 0 <= (local_date - today).days <= 16:
            skipped += 1
            continue
        try:
            venue_key = (float(venue["latitude"]), float(venue["longitude"]), match["local_timezone"])
            if venue_key not in venue_forecasts:
                venue_forecasts[venue_key] = fetch_forecast_data(*venue_key)
            forecast_data, source_name, quality_score = venue_forecasts[venue_key]
            weather = normalize_forecast_weather(
                forecast_data,
                match["local_date"],
                source_name,
                quality_score,
            )
            rows.append({"match_id": match["match_id"], **weather})
        except Exception as exc:  # noqa: BLE001
            errors.append({"match_id": match["match_id"], "error": str(exc), "data_quality_score": 0})
            failed += 1
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    errors_path = path.with_suffix(f"{path.suffix}.errors.csv")
    if rows:
        fieldnames = sorted({key for row in rows for key in row})
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    elif errors and not _is_valid_forecast_file(path):
        fieldnames = sorted({key for row in errors for key in row})
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors)
    if errors:
        fieldnames = sorted({key for row in errors for key in row})
        with errors_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors)
    elif errors_path.exists():
        errors_path.unlink()
    return {
        "written": len(rows),
        "skipped_out_of_forecast_window_or_missing_venue": skipped,
        "failed": failed,
        "used_cached_output": int(not rows and _is_valid_forecast_file(path)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch Open-Meteo forecasts for CSV matches")
    parser.add_argument("--schedule", default="data/sample_schedule.csv")
    parser.add_argument("--venues", default="data/sample_venues.csv")
    parser.add_argument("--output", default="data/live_weather_forecast.csv")
    args = parser.parse_args(argv)
    try:
        print(fetch_forecasts_for_csv(args.schedule, args.venues, args.output))
    except Exception as exc:  # noqa: BLE001
        print(f"Open-Meteo CSV fetch not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
