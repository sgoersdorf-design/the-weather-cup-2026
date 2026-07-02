"""Import venues CSV into the venues table."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
    "stadium_name",
    "host_city",
    "host_country",
    "latitude",
    "longitude",
    "timezone",
    "stadium_type_basic",
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


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _parse_int_or_empty(value):
    if value in ("", None):
        return ""
    return int(value)


def validate_venues(rows: list[dict[str, str]]) -> list[str]:
    """Validate venue rows for MVP import."""

    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
        return errors
    if not rows:
        errors.append("CSV contains no rows")
        return errors
    if any(not row.get("stadium_name") or not row.get("host_city") or not row.get("host_country") or not row.get("timezone") for row in rows):
        errors.append("Venue identity and timezone columns must not be empty")
    for row in rows:
        try:
            latitude = float(row.get("latitude", ""))
            longitude = float(row.get("longitude", ""))
        except ValueError:
            errors.append("Latitude and longitude must be numeric")
            break
        if not -90 <= latitude <= 90:
            errors.append("Latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            errors.append("Longitude must be between -180 and 180")
    invalid_types = {row.get("stadium_type_basic") for row in rows} - {"indoor", "outdoor", "retractable_roof", "unknown"}
    if invalid_types:
        errors.append(f"Invalid stadium_type_basic values: {sorted(invalid_types)}")
    identities = [(row.get("stadium_name"), row.get("host_city")) for row in rows]
    if len(identities) != len(set(identities)):
        errors.append("Duplicate stadium_name + host_city values found")
    return errors


def import_venues(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    """Import venues from a CSV file with PostgreSQL upserts."""

    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_venues(rows)
    if errors:
        raise ValueError("; ".join(errors))

    for row in rows:
        row["roof_available_boolean"] = _parse_bool(row.get("roof_available_boolean", False))
        row["climate_control_available"] = _parse_bool(row.get("climate_control_available", False))
        row.setdefault("elevation_m", "")
        row.setdefault("stadium_capacity", "")
        row.setdefault("roof_type", "")
        row["weather_protection_level"] = _parse_int_or_empty(row.get("weather_protection_level", ""))
        row.setdefault("climate_control_note_de", "")
        row.setdefault("pitch_surface_note_de", "")
        row.setdefault("venue_weather_note_de", "")
        row.setdefault("capacity_source_note", "")
        row.setdefault("coordinate_precision", "")
        row.setdefault("coordinate_accuracy_m", "")
        row.setdefault("google_place_id", "")
        row.setdefault("maps_url", "")
        row.setdefault("coordinate_verified_at", "")
        row.setdefault("data_source_name", "")
        row.setdefault("data_quality_score", "70")

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
                        insert into venues (
                          stadium_name, host_city, host_country, latitude, longitude,
                          elevation_m, timezone, stadium_type_basic, stadium_capacity,
                          roof_available_boolean, roof_type, climate_control_available,
                          weather_protection_level, climate_control_note_de, pitch_surface_note_de,
                          venue_weather_note_de, capacity_source_note,
                          coordinate_precision, coordinate_accuracy_m,
                          google_place_id, maps_url, coordinate_verified_at, data_source_name,
                          data_quality_score
                        )
                        values (
                          :stadium_name, :host_city, :host_country, :latitude, :longitude,
                          :elevation_m, :timezone, :stadium_type_basic, :stadium_capacity,
                          :roof_available_boolean, :roof_type, :climate_control_available,
                          :weather_protection_level, :climate_control_note_de, :pitch_surface_note_de,
                          :venue_weather_note_de, :capacity_source_note,
                          :coordinate_precision, :coordinate_accuracy_m,
                          :google_place_id, :maps_url, :coordinate_verified_at, :data_source_name,
                          :data_quality_score
                        )
                        on conflict (stadium_name, host_city) do update set
                          host_country = excluded.host_country,
                          latitude = excluded.latitude,
                          longitude = excluded.longitude,
                          elevation_m = excluded.elevation_m,
                          timezone = excluded.timezone,
                          stadium_type_basic = excluded.stadium_type_basic,
                          stadium_capacity = excluded.stadium_capacity,
                          roof_available_boolean = excluded.roof_available_boolean,
                          roof_type = excluded.roof_type,
                          climate_control_available = excluded.climate_control_available,
                          weather_protection_level = excluded.weather_protection_level,
                          climate_control_note_de = excluded.climate_control_note_de,
                          pitch_surface_note_de = excluded.pitch_surface_note_de,
                          venue_weather_note_de = excluded.venue_weather_note_de,
                          capacity_source_note = excluded.capacity_source_note,
                          coordinate_precision = excluded.coordinate_precision,
                          coordinate_accuracy_m = excluded.coordinate_accuracy_m,
                          google_place_id = excluded.google_place_id,
                          maps_url = excluded.maps_url,
                          coordinate_verified_at = excluded.coordinate_verified_at,
                          data_source_name = excluded.data_source_name,
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
                print(f"Failed venue {row.get('stadium_name')}: {exc}", file=sys.stderr)

        conn.execute(
            text(
                """
                insert into import_logs(
                  import_type, source_file, rows_processed, rows_inserted, rows_updated,
                  rows_failed, status, error_message
                )
                values (
                  'venues_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated,
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
    parser = argparse.ArgumentParser(description="Import venues CSV")
    parser.add_argument("--file", default="data/sample_venues.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = import_venues(args.file, dry_run=args.dry_run)
    except (RuntimeError, ValueError) as exc:
        print(f"Venue import not completed: {exc}")
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
