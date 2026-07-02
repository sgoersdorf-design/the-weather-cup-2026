"""Batch-import match results from a CSV result feed."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {"match_id", "result_team_a", "result_team_b"}


def _load_sql():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_results(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
    if not rows:
        errors.append("CSV contains no rows")
    for row in rows:
        if row.get("result_team_a") in ("", None) and row.get("result_team_b") in ("", None):
            continue
        try:
            int(row["result_team_a"])
            int(row["result_team_b"])
        except (TypeError, ValueError):
            errors.append(f"Invalid result for {row.get('match_id')}")
            break
    return errors


def import_results(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_results(rows)
    if errors:
        raise ValueError("; ".join(errors))
    result_rows = [row for row in rows if row.get("result_team_a") not in ("", None) and row.get("result_team_b") not in ("", None)]
    if dry_run:
        return {"rows_processed": len(rows), "result_rows": len(result_rows), "rows_updated": 0, "rows_failed": 0}

    text = _load_sql()
    engine = get_engine()
    rows_updated = rows_failed = 0
    with engine.begin() as conn:
        for row in result_rows:
            try:
                conn.execute(
                    text(
                        """
                        update matches
                        set result_team_a = :result_team_a,
                            result_team_b = :result_team_b,
                            match_status = coalesce(nullif(:match_status, ''), 'finished')
                        where match_id = :match_id
                        """
                    ),
                    {
                        "match_id": row["match_id"],
                        "result_team_a": int(row["result_team_a"]),
                        "result_team_b": int(row["result_team_b"]),
                        "match_status": row.get("match_status") or "finished",
                    },
                )
                rows_updated += 1
            except Exception as exc:  # noqa: BLE001
                rows_failed += 1
                print(f"Failed result {row.get('match_id')}: {exc}", file=sys.stderr)
    return {"rows_processed": len(rows), "result_rows": len(result_rows), "rows_updated": rows_updated, "rows_failed": rows_failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import match results CSV")
    parser.add_argument("--file", default="data/sample_results.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(import_results(args.file, dry_run=args.dry_run))
    except (RuntimeError, ValueError) as exc:
        print(f"Results import not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
