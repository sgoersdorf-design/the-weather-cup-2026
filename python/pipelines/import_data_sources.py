"""Import the source catalogue into the data_sources table."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
    "source_name",
    "source_type",
    "source_url",
    "license_status",
    "usage_notes",
    "is_active",
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


def validate_data_sources(rows: list[dict[str, str]]) -> list[str]:
    """Validate source-catalog rows."""

    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
        return errors
    if not rows:
        errors.append("CSV contains no rows")
        return errors
    if any(not row.get("source_name") or not row.get("source_type") for row in rows):
        errors.append("source_name and source_type must not be empty")
    source_names = [row.get("source_name") for row in rows]
    if len(source_names) != len(set(source_names)):
        errors.append("Duplicate source_name values found")
    return errors


def import_data_sources(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    """Import data sources with PostgreSQL upserts."""

    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_data_sources(rows)
    if errors:
        raise ValueError("; ".join(errors))

    for row in rows:
        row["is_active"] = _parse_bool(row.get("is_active", True))

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
                        insert into data_sources (
                          source_name, source_type, source_url, license_status,
                          usage_notes, is_active
                        )
                        values (
                          :source_name, :source_type, :source_url, :license_status,
                          :usage_notes, :is_active
                        )
                        on conflict (source_name) do update set
                          source_type = excluded.source_type,
                          source_url = excluded.source_url,
                          license_status = excluded.license_status,
                          usage_notes = excluded.usage_notes,
                          is_active = excluded.is_active
                        returning (xmax = 0) as inserted
                        """
                    ),
                    row,
                )
                inserted = bool(result.scalar())
                rows_inserted += int(inserted)
                rows_updated += int(not inserted)
            except Exception as exc:  # noqa: BLE001
                rows_failed += 1
                print(f"Failed source {row.get('source_name')}: {exc}", file=sys.stderr)

        conn.execute(
            text(
                """
                insert into import_logs(
                  import_type, source_file, rows_processed, rows_inserted, rows_updated,
                  rows_failed, status, error_message
                )
                values (
                  'data_sources_csv', :source_file, :rows_processed, :rows_inserted,
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
    parser = argparse.ArgumentParser(description="Import data sources CSV")
    parser.add_argument("--file", default="data/data_sources_catalog.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = import_data_sources(args.file, dry_run=args.dry_run)
    except (RuntimeError, ValueError) as exc:
        print(f"Data-source import not completed: {exc}")
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
