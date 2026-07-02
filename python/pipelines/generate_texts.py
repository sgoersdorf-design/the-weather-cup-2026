"""Template-based bilingual text generation without external LLM APIs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from python.db import get_engine
from python.scoring.scores import weather_load_score

CONTENT_DIR = Path("content")

PUBLIC_CONTEXT_FACTORS = {
    "weather_load_gap": ("Weather Load", "weather load"),
    "weather_fit_gap": ("Weather Fit", "weather fit"),
    "circadian_load_gap": ("Anstoßzeit-/Zeitzonenkontext", "kickoff-time/time-zone context"),
    "altitude_load_gap": ("Höhenkontext", "altitude context"),
    "fan_proximity_gap": ("Standortnähe", "venue proximity"),
    "team_strength_gap": ("Basis-Teamstärke", "basic team strength"),
    "travel_recovery_gap": ("Wetter-/Standortkontext", "weather/venue context"),
    "data_pending": ("Datenlage offen", "data pending"),
}


class SafeFormatDict(dict):
    """Keep missing template variables visible instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _load_dependencies():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc
    return text


def load_templates() -> dict[str, Any]:
    """Load all JSON templates needed by text generation."""

    return {
        "match_card": json.loads((CONTENT_DIR / "match_card_templates.json").read_text(encoding="utf-8")),
        "social": json.loads((CONTENT_DIR / "social_templates.json").read_text(encoding="utf-8")),
        "disclaimer": json.loads((CONTENT_DIR / "disclaimer_texts.json").read_text(encoding="utf-8")),
    }


def render(value: Any, context: dict[str, Any]) -> Any:
    """Render a string or list of strings with safe formatting."""

    if isinstance(value, str):
        return value.format_map(SafeFormatDict(context))
    if isinstance(value, list):
        return [render(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render(item, context) for key, item in value.items()}
    return value


def data_hash(context: dict[str, Any]) -> str:
    """Hash the structured input used to generate text."""

    encoded = json.dumps(context, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_text_context(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw match, weather and prediction data into template variables."""

    context = dict(raw)
    context.setdefault("forecast_temp", "n/a")
    context.setdefault("forecast_humidity", "n/a")
    context.setdefault("forecast_wind_speed", "n/a")
    context.setdefault("forecast_precipitation_probability", "n/a")
    if context.get("weather_load_score") is None:
        context["weather_load_score"] = weather_load_score(
            _maybe_float(context.get("forecast_temp")),
            _maybe_float(context.get("forecast_humidity")),
            _maybe_float(context.get("forecast_wind_speed")),
            _maybe_float(context.get("forecast_precipitation_probability")),
        )
    context.setdefault("predicted_result_category", "unknown")
    context.setdefault("probability_team_a_win", "n/a")
    context.setdefault("probability_draw", "n/a")
    context.setdefault("probability_team_b_win", "n/a")
    context.setdefault("main_context_advantage", "balanced")
    context.setdefault("biggest_load_factor", "data_pending")
    context.setdefault("uncertainty_level", "unknown")
    public_factor = PUBLIC_CONTEXT_FACTORS.get(str(context["biggest_load_factor"]), PUBLIC_CONTEXT_FACTORS["data_pending"])
    context["public_context_factor_de"] = public_factor[0]
    context["public_context_factor_en"] = public_factor[1]
    return context


def _maybe_float(value: Any) -> float | None:
    try:
        return None if value in (None, "n/a") else float(value)
    except (TypeError, ValueError):
        return None


def generate_text_bundle(raw_context: dict[str, Any]) -> dict[str, Any]:
    """Generate DE/EN match-card and social text bundle."""

    templates = load_templates()
    context = build_text_context(raw_context)
    match_preview = templates["match_card"]["match_preview"]
    social = templates["social"]
    return {
        "data_hash": data_hash(context),
        "de": {
            **render(match_preview["de"], context),
            "social_hook": render(social["x_twitter"]["de"], context),
            "social_templates": render({key: value["de"] if isinstance(value, dict) and "de" in value else value for key, value in social.items()}, context),
            "disclaimer": templates["disclaimer"]["de"],
        },
        "en": {
            **render(match_preview["en"], context),
            "social_hook": render(social["x_twitter"]["en"], context),
            "social_templates": render({key: value["en"] if isinstance(value, dict) and "en" in value else value for key, value in social.items()}, context),
            "disclaimer": templates["disclaimer"]["en"],
        },
    }


def load_match_text_context(match_id: str) -> dict[str, Any]:
    """Load structured data for text generation from the database."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                select
                  m.match_id, m.local_date, m.local_time,
                  ta.iso3 as team_a_iso3, ta.name_de as team_a_name_de, ta.name_en as team_a_name_en,
                  ta.flag_emoji as team_a_flag,
                  tb.iso3 as team_b_iso3, tb.name_de as team_b_name_de, tb.name_en as team_b_name_en,
                  tb.flag_emoji as team_b_flag,
                  v.host_city, v.stadium_name,
                  wf.forecast_temp, wf.forecast_humidity, wf.forecast_wind_speed,
                  wf.forecast_precipitation_probability,
                  p.predicted_result_category, p.probability_team_a_win, p.probability_draw,
                  p.probability_team_b_win, p.main_context_advantage, p.biggest_load_factor,
                  p.uncertainty_level
                from matches m
                join teams ta on ta.id = m.team_a_id
                join teams tb on tb.id = m.team_b_id
                join venues v on v.id = m.venue_id
                left join weather_forecast wf on wf.match_id = m.match_id
                left join predictions p on p.match_id = m.match_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings().first()
    if row is None:
        raise ValueError(f"Unknown match_id: {match_id}")
    return dict(row)


def generate_texts_for_match(match_id: str) -> dict[str, Any]:
    """Generate and upsert bilingual match preview text."""

    text = _load_dependencies()
    engine = get_engine()
    raw_context = load_match_text_context(match_id)
    bundle = generate_text_bundle(raw_context)
    with engine.begin() as conn:
        for language in ("de", "en"):
            item = bundle[language]
            conn.execute(
                text(
                    """
                    insert into generated_texts (
                      match_id, language, content_type, headline, subheadline,
                      teaser, body, social_hook, generated_from_data_hash
                    )
                    values (
                      :match_id, :language, 'match_preview', :headline, :subheadline,
                      :teaser, :body, :social_hook, :generated_from_data_hash
                    )
                    on conflict (match_id, language, content_type) do update set
                      headline = excluded.headline,
                      subheadline = excluded.subheadline,
                      teaser = excluded.teaser,
                      body = excluded.body,
                      social_hook = excluded.social_hook,
                      generated_from_data_hash = excluded.generated_from_data_hash
                    """
                ),
                {
                    "match_id": match_id,
                    "language": language,
                    "headline": item["headline"],
                    "subheadline": item["subheadline"],
                    "teaser": item["teaser"],
                    "body": item["body"],
                    "social_hook": item["social_hook"],
                    "generated_from_data_hash": bundle["data_hash"],
                },
            )
    return bundle


def generate_texts_for_all_matches() -> dict[str, Any]:
    """Generate bilingual match-preview text rows for every match with fixed teams."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.connect() as conn:
        match_ids = [
            row[0]
            for row in conn.execute(
                text(
                    """
                    select match_id
                    from matches
                    where team_a_id is not null and team_b_id is not null
                    order by date_utc nulls last, match_id
                    """
                )
            )
        ]

    generated: list[str] = []
    skipped: list[dict[str, str]] = []
    for match_id in match_ids:
        try:
            generate_texts_for_match(match_id)
            generated.append(match_id)
        except Exception as exc:  # noqa: BLE001
            skipped.append({"match_id": match_id, "error": str(exc)})
    return {
        "matches_with_fixed_teams": len(match_ids),
        "generated": len(generated),
        "skipped": skipped,
        "generated_match_ids": generated,
    }


def sample_context() -> dict[str, Any]:
    """Return local sample context for no-DB smoke tests."""

    return {
        "match_id": "M001",
        "local_date": "2026-06-11",
        "local_time": "13:00",
        "team_a_iso3": "MEX",
        "team_a_name_de": "Mexiko",
        "team_a_name_en": "Mexico",
        "team_a_flag": "🇲🇽",
        "team_b_iso3": "ZAF",
        "team_b_name_de": "Südafrika",
        "team_b_name_en": "South Africa",
        "team_b_flag": "🇿🇦",
        "host_city": "Mexico City",
        "stadium_name": "Mexico City Stadium",
        "forecast_temp": 26,
        "forecast_humidity": 58,
        "forecast_wind_speed": 14,
        "forecast_precipitation_probability": 35,
        "predicted_result_category": "team_a_win",
        "probability_team_a_win": 45.2,
        "probability_draw": 29.8,
        "probability_team_b_win": 25.0,
        "main_context_advantage": "team_a",
        "biggest_load_factor": "altitude_load",
        "uncertainty_level": "medium",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate bilingual texts")
    parser.add_argument("--match-id", default=None)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.all:
            bundle = generate_texts_for_all_matches()
        elif args.match_id:
            bundle = generate_texts_for_match(args.match_id)
        else:
            bundle = generate_text_bundle(sample_context())
        print(json.dumps(bundle, indent=2, ensure_ascii=False, default=str))
    except (RuntimeError, ValueError) as exc:
        print(f"Text generation not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
