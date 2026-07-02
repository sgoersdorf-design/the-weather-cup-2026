"""Print compact Supabase/PostgreSQL MVP table counts."""

from __future__ import annotations

import argparse
import json
from typing import Any

from python.db import get_engine

TABLES = [
    "data_sources",
    "teams",
    "venues",
    "matches",
    "weather_forecast",
    "weather_actual",
    "team_weather_profiles",
    "travel_metrics",
    "timezone_metrics",
    "altitude_metrics",
    "fan_proximity_metrics",
    "weather_matchup_metrics",
    "predictions",
    "generated_texts",
    "post_match_evaluations",
    "analysis_reports",
    "ad_partners",
    "ad_campaigns",
    "ad_creatives",
    "ad_slots",
    "ad_placements",
]


def _load_dependencies():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc
    return text


def get_db_status() -> dict[str, Any]:
    """Return compact row counts and content-type counts."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.connect() as conn:
        counts = {table: conn.execute(text(f"select count(*) from {table}")).scalar_one() for table in TABLES}
        generated_text_types = {
            row["content_type"]: row["count"]
            for row in conn.execute(
                text(
                    """
                    select content_type, count(*) as count
                    from generated_texts
                    group by content_type
                    order by content_type
                    """
                )
            ).mappings()
        }
        fixed_team_matches = conn.execute(
            text("select count(*) from matches where team_a_id is not null and team_b_id is not null")
        ).scalar_one()
        forecast_matches = conn.execute(text("select count(distinct match_id) from weather_forecast")).scalar_one()
    return {
        "table_counts": counts,
        "fixed_team_matches": fixed_team_matches,
        "forecast_matches": forecast_matches,
        "generated_text_types": generated_text_types,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show MVP database status")
    parser.parse_args(argv)
    try:
        print(json.dumps(get_db_status(), indent=2, ensure_ascii=False, default=str))
    except RuntimeError as exc:
        print(f"DB status not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
