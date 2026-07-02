"""Generate transparent MVP predictions from structured match context."""

from __future__ import annotations

import argparse
import json
from typing import Any

from python.config import settings
from python.db import get_engine
from python.scoring.scores import (
    basic_team_strength_score,
    predict_match,
    uncertainty_score,
    venue_type_factor,
    weather_load_score,
)

PUBLIC_CONTEXT_FACTORS = {
    "weather_load_gap": ("Weather Load", "weather load"),
    "weather_fit_gap": ("Weather Fit", "weather fit"),
    "circadian_load_gap": ("Anstoßzeit-/Zeitzonenkontext", "kickoff-time/time-zone context"),
    "altitude_load_gap": ("Höhenkontext", "altitude context"),
    "fan_proximity_gap": ("Standortnähe", "venue proximity"),
    "team_strength_gap": ("Basis-Teamstärke", "basic team strength"),
    "travel_recovery_gap": ("Wetter-/Standortkontext", "weather/venue context"),
}


def _load_dependencies():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc
    return text


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _float_or(value: Any, default: float) -> float:
    converted = _as_float(value)
    return default if converted is None else converted


def _latest_sport_metrics(conn, text, team_id: str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            select *
            from sport_metrics
            where team_id = :team_id
            order by last_updated_at desc
            limit 1
            """
        ),
        {"team_id": team_id},
    ).mappings().first()
    return dict(row) if row else {}


def _latest_squad_age(conn, text, team_id: str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            select *
            from squad_age_metrics
            where team_id = :team_id and is_active_in_model = true
            order by squad_age_last_updated desc nulls last
            limit 1
            """
        ),
        {"team_id": team_id},
    ).mappings().first()
    return dict(row) if row else {}


def _team_context(conn, text, match_id: str, team_id: str, venue_type: str | None, forecast: dict[str, Any]) -> dict[str, Any]:
    travel = conn.execute(
        text("select * from travel_metrics where match_id = :match_id and team_id = :team_id"),
        {"match_id": match_id, "team_id": team_id},
    ).mappings().first()
    timezone = conn.execute(
        text("select * from timezone_metrics where match_id = :match_id and team_id = :team_id"),
        {"match_id": match_id, "team_id": team_id},
    ).mappings().first()
    altitude = conn.execute(
        text("select * from altitude_metrics where match_id = :match_id and team_id = :team_id"),
        {"match_id": match_id, "team_id": team_id},
    ).mappings().first()
    fan = conn.execute(
        text("select * from fan_proximity_metrics where match_id = :match_id and team_id = :team_id"),
        {"match_id": match_id, "team_id": team_id},
    ).mappings().first()
    sport = _latest_sport_metrics(conn, text, team_id)
    squad_age = _latest_squad_age(conn, text, team_id)

    quality_scores = [
        _as_float((travel or {}).get("data_quality_score")),
        _as_float((timezone or {}).get("data_quality_score")),
        _as_float((altitude or {}).get("data_quality_score")),
        _as_float((fan or {}).get("data_quality_score")),
        _as_float(sport.get("data_quality_score")),
        _as_float(forecast.get("data_quality_score")),
    ]
    missing_required = sum(1 for value in quality_scores if value is None)
    team_strength = _as_float(sport.get("team_strength_score"))
    return {
        "basic_team_strength_score": team_strength
        if team_strength is not None
        else basic_team_strength_score(
            sport.get("fifa_ranking_position"),
            _as_float(sport.get("fifa_ranking_points")),
            _as_float(sport.get("elo_rating")),
            _as_float(sport.get("basic_form_score")),
        ),
        "weather_familiarity_score": 50,
        "weather_load_score": weather_load_score(
            _as_float(forecast.get("forecast_temp")),
            _as_float(forecast.get("forecast_humidity")),
            _as_float(forecast.get("forecast_wind_speed")),
            _as_float(forecast.get("forecast_precipitation_probability")),
        ),
        "travel_recovery_score": _float_or((travel or {}).get("travel_recovery_score"), 50),
        "circadian_load_score": _float_or((timezone or {}).get("circadian_load_score"), 50),
        "altitude_load_score": _float_or((altitude or {}).get("altitude_load_score"), 50),
        "venue_type_factor": venue_type_factor(venue_type),
        "fan_proximity_score": _float_or((fan or {}).get("fan_proximity_score"), 50),
        "squad_age_resilience_score": _float_or(squad_age.get("squad_age_resilience_score"), 50),
        "uncertainty_score": uncertainty_score(quality_scores, missing_required),
    }


def load_match_context(match_id: str) -> dict[str, Any]:
    """Load all available structured context for a match."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.connect() as conn:
        match = conn.execute(
            text(
                """
                select
                  m.match_id, m.team_a_id, m.team_b_id,
                  ta.iso3 as team_a_iso3, ta.name_de as team_a_name_de, ta.name_en as team_a_name_en,
                  tb.iso3 as team_b_iso3, tb.name_de as team_b_name_de, tb.name_en as team_b_name_en,
                  v.stadium_name, v.host_city, v.stadium_type_basic
                from matches m
                join teams ta on ta.id = m.team_a_id
                join teams tb on tb.id = m.team_b_id
                join venues v on v.id = m.venue_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings().first()
        if match is None:
            raise ValueError(f"Unknown match_id: {match_id}")

        forecast = conn.execute(
            text("select * from weather_forecast where match_id = :match_id"),
            {"match_id": match_id},
        ).mappings().first()
        forecast_dict = dict(forecast) if forecast else {}
        match_dict = dict(match)
        return {
            "match": match_dict,
            "forecast": forecast_dict,
            "team_a_scores": _team_context(conn, text, match_id, match_dict["team_a_id"], match_dict["stadium_type_basic"], forecast_dict),
            "team_b_scores": _team_context(conn, text, match_id, match_dict["team_b_id"], match_dict["stadium_type_basic"], forecast_dict),
        }


def _build_explanations(context: dict[str, Any], prediction: dict[str, Any]) -> dict[str, str]:
    match = context["match"]
    factor_de, factor_en = PUBLIC_CONTEXT_FACTORS.get(str(prediction["biggest_load_factor"]), ("Kontextdaten", "context data"))
    de = (
        f"{match['team_a_iso3']} gegen {match['team_b_iso3']}: Das MVP kombiniert Basis-Teamstärke, "
        f"Wetter, Zeitzonen, Höhe und Standortnähe. Der sichtbare Kontextfaktor ist {factor_de}. "
        f"Die Einordnung ist ein transparenter Kontextindikator, kein Wettmodell."
    )
    en = (
        f"{match['team_a_iso3']} vs {match['team_b_iso3']}: The MVP combines basic team strength, "
        f"weather, time zones, altitude and proximity. The visible context factor is {factor_en}. "
        f"This is a transparent context indicator, not a betting model."
    )
    return {"explanation_de": de, "explanation_en": en}


def generate_prediction_for_match(match_id: str) -> dict[str, Any]:
    """Generate and upsert a prediction for one match."""

    text = _load_dependencies()
    engine = get_engine()
    context = load_match_context(match_id)
    prediction = predict_match(context["team_a_scores"], context["team_b_scores"])
    explanations = _build_explanations(context, prediction)
    match = context["match"]
    payload = {
        "match_id": match_id,
        **prediction,
        **explanations,
        "social_hook_de": f"{match['team_a_iso3']} vs. {match['team_b_iso3']}: Kontextvorteil {prediction['main_context_advantage']}.",
        "social_hook_en": f"{match['team_a_iso3']} vs {match['team_b_iso3']}: context edge {prediction['main_context_advantage']}.",
        "website_teaser_de": explanations["explanation_de"],
        "website_teaser_en": explanations["explanation_en"],
        "model_version": settings.model_version,
    }
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into predictions (
                  match_id, predicted_result_category, probability_team_a_win,
                  probability_draw, probability_team_b_win, main_context_advantage,
                  biggest_load_factor, uncertainty_level, explanation_de, explanation_en,
                  social_hook_de, social_hook_en, website_teaser_de, website_teaser_en,
                  model_version
                )
                values (
                  :match_id, :predicted_result_category, :probability_team_a_win,
                  :probability_draw, :probability_team_b_win, :main_context_advantage,
                  :biggest_load_factor, :uncertainty_level, :explanation_de, :explanation_en,
                  :social_hook_de, :social_hook_en, :website_teaser_de, :website_teaser_en,
                  :model_version
                )
                on conflict (match_id) do update set
                  predicted_result_category = excluded.predicted_result_category,
                  probability_team_a_win = excluded.probability_team_a_win,
                  probability_draw = excluded.probability_draw,
                  probability_team_b_win = excluded.probability_team_b_win,
                  main_context_advantage = excluded.main_context_advantage,
                  biggest_load_factor = excluded.biggest_load_factor,
                  uncertainty_level = excluded.uncertainty_level,
                  explanation_de = excluded.explanation_de,
                  explanation_en = excluded.explanation_en,
                  social_hook_de = excluded.social_hook_de,
                  social_hook_en = excluded.social_hook_en,
                  website_teaser_de = excluded.website_teaser_de,
                  website_teaser_en = excluded.website_teaser_en,
                  model_version = excluded.model_version
                """
            ),
            payload,
        )
    return payload


def generate_predictions_for_all_matches() -> list[dict[str, Any]]:
    """Generate predictions for every scheduled match with minimum data."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.connect() as conn:
        match_ids = [row[0] for row in conn.execute(text("select match_id from matches order by date_utc nulls last"))]
    outputs = []
    for match_id in match_ids:
        try:
            outputs.append(generate_prediction_for_match(match_id))
        except Exception as exc:  # noqa: BLE001
            outputs.append({"match_id": match_id, "status": "skipped", "error": str(exc)})
    return outputs


def summarize_prediction_outputs(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact generation counts for CLI/database runs."""

    generated = [item for item in outputs if item.get("status") != "skipped"]
    skipped = [item for item in outputs if item.get("status") == "skipped"]
    by_uncertainty: dict[str, int] = {}
    for item in generated:
        uncertainty = str(item.get("uncertainty_level") or "unknown")
        by_uncertainty[uncertainty] = by_uncertainty.get(uncertainty, 0) + 1
    return {
        "matches_requested": len(outputs),
        "generated": len(generated),
        "skipped": skipped,
        "uncertainty_counts": by_uncertainty,
    }


def sample_prediction() -> dict[str, Any]:
    """Local sample that does not need a database."""

    team_a = {
        "basic_team_strength_score": 72,
        "weather_familiarity_score": 65,
        "weather_load_score": 42,
        "travel_recovery_score": 78,
        "circadian_load_score": 18,
        "altitude_load_score": 32,
        "venue_type_factor": 76,
        "fan_proximity_score": 56,
        "squad_age_resilience_score": 55,
        "uncertainty_score": 34,
    }
    team_b = {
        "basic_team_strength_score": 68,
        "weather_familiarity_score": 72,
        "weather_load_score": 42,
        "travel_recovery_score": 67,
        "circadian_load_score": 28,
        "altitude_load_score": 32,
        "venue_type_factor": 76,
        "fan_proximity_score": 32,
        "squad_age_resilience_score": 60,
        "uncertainty_score": 38,
    }
    return predict_match(team_a, team_b)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate MVP predictions")
    parser.add_argument("--match-id", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.all:
            output = generate_predictions_for_all_matches()
            if args.summary:
                output = summarize_prediction_outputs(output)
            print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
        elif args.match_id:
            print(json.dumps(generate_prediction_for_match(args.match_id), indent=2, ensure_ascii=False, default=str))
        else:
            print(json.dumps(sample_prediction(), indent=2, ensure_ascii=False))
    except (RuntimeError, ValueError) as exc:
        print(f"Prediction generation not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
