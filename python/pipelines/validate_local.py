"""Local no-database validation for the MVP project files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from python.pipelines.context_metrics import compute_context_metrics
from python.pipelines.generate_predictions import sample_prediction
from python.pipelines.generate_texts import generate_text_bundle, sample_context
from python.pipelines.import_data_sources import validate_data_sources
from python.pipelines.import_schedule import validate_schedule
from python.pipelines.import_teams import validate_teams
from python.pipelines.import_venues import validate_venues
from python.pipelines.import_weather_profiles import validate_weather_profiles
from python.pipelines.import_sport_metrics import validate_sport_metrics
from python.pipelines.import_weather_forecast import is_forecast_error_placeholder, validate_weather_forecast
from python.pipelines.import_results import validate_results
from python.pipelines.import_ads import validate_ads
from python.pipelines.weather_matchup import build_local_weather_matchups
from python.pipelines.weather_reports import build_weather_report


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_json(path: Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))


def validate_local_project() -> dict[str, object]:
    """Validate local files without requiring DB, network or third-party packages."""

    teams = _read_csv(Path("data/sample_teams.csv"))
    venues = _read_csv(Path("data/sample_venues.csv"))
    schedule = _read_csv(Path("data/sample_schedule.csv"))
    sources = _read_csv(Path("data/data_sources_catalog.csv"))
    groups = _read_csv(Path("data/world_cup_2026_groups.csv"))
    profiles = _read_csv(Path("data/sample_team_weather_profiles.csv"))
    weather_forecast = _read_csv(Path("data/sample_weather_forecast.csv"))
    weather_actual = _read_csv(Path("data/sample_weather_actual.csv"))
    results = _read_csv(Path("data/sample_results.csv"))
    sport_metrics = _read_csv(Path("data/sample_sport_metrics.csv"))
    ads = _read_csv(Path("data/ad_inventory.csv"))

    errors: list[str] = []
    errors.extend(validate_teams(teams))
    errors.extend(validate_venues(venues))
    errors.extend(validate_schedule(schedule))
    errors.extend(validate_data_sources(sources))
    errors.extend(validate_weather_profiles(profiles))
    errors.extend(validate_sport_metrics(sport_metrics))
    errors.extend(validate_results(results))
    errors.extend(validate_ads(ads))
    if len(groups) != 48:
        errors.append(f"Expected 48 group rows, found {len(groups)}")
    if len(weather_forecast) != len(schedule):
        errors.append("Sample forecast row count must match sample schedule row count")
    if len(weather_actual) != len(schedule):
        errors.append("Sample actual-weather row count must match sample schedule row count")
    if len(results) != len(schedule):
        errors.append("Sample results row count must match sample schedule row count")
    if Path("data/full_schedule_openfootball.csv").exists():
        full_schedule = _read_csv(Path("data/full_schedule_openfootball.csv"))
        if len(full_schedule) != 104:
            errors.append(f"Expected 104 OpenFootball matches, found {len(full_schedule)}")
        errors.extend(validate_results(full_schedule))
    else:
        full_schedule = []
    if Path("data/full_teams_restcountries.csv").exists():
        full_teams = _read_csv(Path("data/full_teams_restcountries.csv"))
        if len(full_teams) != 48:
            errors.append(f"Expected 48 full team rows, found {len(full_teams)}")
    else:
        full_teams = []
    if Path("data/live_weather_forecast.csv").exists():
        live_forecast = _read_csv(Path("data/live_weather_forecast.csv"))
        if not live_forecast:
            errors.append("Live weather forecast file exists but is empty")
        elif not is_forecast_error_placeholder(live_forecast):
            errors.extend(validate_weather_forecast(live_forecast))
    else:
        live_forecast = []
    if Path("data/live_weather_forecast_full.csv").exists():
        live_forecast_full = _read_csv(Path("data/live_weather_forecast_full.csv"))
        if not live_forecast_full:
            errors.append("Full live weather forecast file exists but is empty")
        elif not is_forecast_error_placeholder(live_forecast_full):
            errors.extend(validate_weather_forecast(live_forecast_full))
    else:
        live_forecast_full = []

    for path in [
        Path("content/match_card_templates.json"),
        Path("content/social_templates.json"),
        Path("content/disclaimer_texts.json"),
        Path("content/weather_fit_templates.json"),
    ]:
        try:
            _validate_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in {path}: {exc}")

    context_records = compute_context_metrics(schedule, venues, teams)
    prediction = sample_prediction()
    text_bundle = generate_text_bundle(sample_context())
    weather_matchups = build_local_weather_matchups("forecast")
    weather_report = build_weather_report()

    return {
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "sample_counts": {
            "teams": len(teams),
            "venues": len(venues),
            "schedule_matches": len(schedule),
            "group_rows": len(groups),
            "context_records": len(context_records),
            "weather_matchups": len(weather_matchups),
            "weather_report_matches": len(weather_report["matches"]),
            "full_schedule_matches": len(full_schedule),
            "full_team_rows": len(full_teams),
            "live_weather_rows": len(live_forecast),
            "live_weather_full_rows": len(live_forecast_full),
            "sample_result_rows": len(results),
            "ad_inventory_rows": len(ads),
        },
        "sample_prediction_category": prediction["predicted_result_category"],
        "sample_text_languages": [key for key in text_bundle.keys() if key in {"de", "en"}],
    }


def main() -> int:
    result = validate_local_project()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
