"""Import licensed sport metrics from CSV into sport_metrics."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from python.db import get_engine

REQUIRED_COLUMNS = {
    "iso3",
    "fifa_ranking_position",
    "fifa_ranking_points",
    "elo_rating",
    "basic_form_score",
    "team_strength_score",
    "data_source_name",
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


def _clean(row: dict[str, object]) -> dict[str, object]:
    return {key: (None if value == "" else value) for key, value in row.items()}


def validate_sport_metrics(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
    if not rows:
        errors.append("CSV contains no rows")
    return errors


def import_sport_metrics(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_sport_metrics(rows)
    if errors:
        raise ValueError("; ".join(errors))
    for row in rows:
        row["iso3"] = row["iso3"].upper()
    if dry_run:
        return {"rows_processed": len(rows), "rows_inserted": 0, "rows_failed": 0}

    text = _load_sql()
    engine = get_engine()
    rows_inserted = rows_failed = 0
    with engine.begin() as conn:
        for row in rows:
            try:
                conn.execute(
                    text(
                        """
                        insert into sport_metrics (
                          team_id, fifa_ranking_position, fifa_ranking_points, elo_rating,
                          recent_matches_played, recent_wins, recent_draws, recent_losses,
                          recent_goals_for, recent_goals_against, basic_form_score,
                          team_strength_score, data_source_name, last_updated_at, data_quality_score
                        )
                        values (
                          (select id from teams where iso3 = :iso3),
                          :fifa_ranking_position, :fifa_ranking_points, :elo_rating,
                          :recent_matches_played, :recent_wins, :recent_draws, :recent_losses,
                          :recent_goals_for, :recent_goals_against, :basic_form_score,
                          :team_strength_score, :data_source_name,
                          coalesce(cast(:last_updated_at as timestamptz), now()),
                          :data_quality_score
                        )
                        """
                    ),
                    _clean(row),
                )
                rows_inserted += 1
            except Exception as exc:  # noqa: BLE001
                rows_failed += 1
                print(f"Failed sport metrics {row.get('iso3')}: {exc}", file=sys.stderr)
    return {"rows_processed": len(rows), "rows_inserted": rows_inserted, "rows_failed": rows_failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import licensed sport metrics CSV")
    parser.add_argument("--file", default="data/sample_sport_metrics.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(import_sport_metrics(args.file, dry_run=args.dry_run))
    except (RuntimeError, ValueError) as exc:
        print(f"Sport metrics import not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
