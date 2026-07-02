"""Pre-match Weather Fit matchup pipeline.

This answers the product question: which team appears better adapted to the
given weather situation? The result is a context indicator, not proof of match
performance.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from python.db import get_engine
from python.pipelines.generate_texts import SafeFormatDict, data_hash
from python.scoring.scores import (
    calculate_heat_index,
    weather_familiarity_score,
    weather_fit_label,
    weather_fit_score,
    weather_load_score,
    weather_tolerance_score,
)


def _load_sql():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _weather_from_forecast(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "weather_temp_c": _as_float(row.get("forecast_temp")),
        "weather_humidity": _as_float(row.get("forecast_humidity")),
        "weather_wind_speed": _as_float(row.get("forecast_wind_speed")),
        "precipitation_probability": _as_float(row.get("forecast_precipitation_probability")),
        "weather_heat_index": _as_float(row.get("forecast_heat_index")),
        "data_quality_score": _as_float(row.get("data_quality_score")) or 0,
        "source_weather_type": "forecast",
    }


def _weather_from_actual(row: dict[str, Any]) -> dict[str, Any]:
    precipitation = _as_float(row.get("actual_precipitation"))
    if precipitation is None:
        precipitation_probability = None
    elif precipitation > 2:
        precipitation_probability = 70
    elif precipitation > 0:
        precipitation_probability = 35
    else:
        precipitation_probability = 0
    return {
        "weather_temp_c": _as_float(row.get("actual_temp")),
        "weather_humidity": _as_float(row.get("actual_humidity")),
        "weather_wind_speed": _as_float(row.get("actual_wind_speed")),
        "precipitation_probability": precipitation_probability,
        "weather_heat_index": _as_float(row.get("actual_heat_index")),
        "data_quality_score": _as_float(row.get("data_quality_score")) or 0,
        "source_weather_type": "actual",
    }


def calculate_team_weather_fit(profile: dict[str, Any], weather: dict[str, Any]) -> dict[str, Any]:
    """Calculate weather fit metrics for one team."""

    temp = weather.get("weather_temp_c")
    humidity = weather.get("weather_humidity")
    wind = weather.get("weather_wind_speed")
    precipitation_probability = weather.get("precipitation_probability")
    load = weather_load_score(temp, humidity, wind, precipitation_probability)
    familiarity = weather_familiarity_score(
        _as_float(profile.get("reference_temp_c")),
        temp,
        _as_float(profile.get("reference_humidity")),
        humidity,
    )
    tolerance = weather_tolerance_score(
        temp,
        humidity,
        precipitation_probability,
        wind,
        _as_float(profile.get("heat_tolerance_score")),
        _as_float(profile.get("humidity_tolerance_score")),
        _as_float(profile.get("rain_tolerance_score")),
        _as_float(profile.get("wind_tolerance_score")),
    )
    fit = weather_fit_score(familiarity, tolerance, load)
    effective_load = round(load * (1 - tolerance / 180), 2)
    quality_scores = [
        _as_float(profile.get("data_quality_score")),
        _as_float(weather.get("data_quality_score")),
    ]
    data_quality = round(sum(score for score in quality_scores if score is not None) / max(1, len([score for score in quality_scores if score is not None])), 2)
    return {
        "weather_load_score": load,
        "weather_familiarity_score": familiarity,
        "weather_tolerance_score": tolerance,
        "effective_weather_load_score": effective_load,
        "weather_fit_score": fit,
        "weather_fit_label": weather_fit_label(fit),
        "data_quality_score": data_quality,
    }


def _fit_explanation_de(team_name: str, opponent_name: str, fit: float, opponent_fit: float, weather: dict[str, Any]) -> str:
    return (
        f"{team_name} wirkt für diese Wettersituation etwas besser eingeordnet als {opponent_name}: "
        f"Weather Fit {fit}/100 gegen {opponent_fit}/100 bei {weather.get('weather_temp_c')} Grad "
        f"und {weather.get('weather_humidity')}% Luftfeuchtigkeit. Das ist ein Kontextindikator, kein Leistungsbeweis."
    )


def _fit_explanation_en(team_name: str, opponent_name: str, fit: float, opponent_fit: float, weather: dict[str, Any]) -> str:
    return (
        f"{team_name} is rated as slightly better suited to these conditions than {opponent_name}: "
        f"Weather Fit {fit}/100 vs {opponent_fit}/100 at {weather.get('weather_temp_c')} degrees "
        f"and {weather.get('weather_humidity')}% humidity. This is a context indicator, not performance proof."
    )


def build_weather_matchup(
    match: dict[str, Any],
    team_a: dict[str, Any],
    team_b: dict[str, Any],
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    weather: dict[str, Any],
) -> dict[str, Any]:
    """Build one match-level Weather Fit product payload."""

    fit_a = calculate_team_weather_fit(profile_a, weather)
    fit_b = calculate_team_weather_fit(profile_b, weather)
    gap = round(fit_a["weather_fit_score"] - fit_b["weather_fit_score"], 2)
    if abs(gap) < 4:
        edge = "balanced"
        edge_team_iso3 = None
        edge_gap = abs(gap)
    elif gap > 0:
        edge = "team_a"
        edge_team_iso3 = team_a["iso3"]
        edge_gap = gap
    else:
        edge = "team_b"
        edge_team_iso3 = team_b["iso3"]
        edge_gap = abs(gap)

    context = {
        "match_id": match["match_id"],
        "matchday": match.get("matchday"),
        "tournament_stage": match.get("tournament_stage"),
        "group_name": match.get("group_name"),
        "local_date": match.get("local_date"),
        "local_time": match.get("local_time"),
        "host_city": match.get("host_city"),
        "stadium_name": match.get("stadium_name"),
        "team_a_iso3": team_a["iso3"],
        "team_a_name_de": team_a.get("name_de", team_a["iso3"]),
        "team_a_name_en": team_a.get("name_en", team_a["iso3"]),
        "team_a_flag": team_a.get("flag_emoji", ""),
        "team_b_iso3": team_b["iso3"],
        "team_b_name_de": team_b.get("name_de", team_b["iso3"]),
        "team_b_name_en": team_b.get("name_en", team_b["iso3"]),
        "team_b_flag": team_b.get("flag_emoji", ""),
        "weather_temp_c": weather.get("weather_temp_c"),
        "weather_humidity": weather.get("weather_humidity"),
        "weather_wind_speed": weather.get("weather_wind_speed"),
        "precipitation_probability": weather.get("precipitation_probability"),
        "source_weather_type": weather.get("source_weather_type"),
        "team_a_weather_fit_score": fit_a["weather_fit_score"],
        "team_b_weather_fit_score": fit_b["weather_fit_score"],
        "team_a_weather_familiarity_score": fit_a["weather_familiarity_score"],
        "team_b_weather_familiarity_score": fit_b["weather_familiarity_score"],
        "team_a_weather_tolerance_score": fit_a["weather_tolerance_score"],
        "team_b_weather_tolerance_score": fit_b["weather_tolerance_score"],
        "weather_load_score": fit_a["weather_load_score"],
        "weather_fit_edge": edge,
        "weather_fit_edge_team_iso3": edge_team_iso3,
        "weather_fit_edge_gap": edge_gap,
        "uncertainty_level": "medium" if min(fit_a["data_quality_score"], fit_b["data_quality_score"]) >= 60 else "high",
    }
    context["explanation_de"] = (
        "Die Wettereignung ist ausgeglichen."
        if edge == "balanced"
        else _fit_explanation_de(
            team_a.get("name_de", team_a["iso3"]) if edge == "team_a" else team_b.get("name_de", team_b["iso3"]),
            team_b.get("name_de", team_b["iso3"]) if edge == "team_a" else team_a.get("name_de", team_a["iso3"]),
            fit_a["weather_fit_score"] if edge == "team_a" else fit_b["weather_fit_score"],
            fit_b["weather_fit_score"] if edge == "team_a" else fit_a["weather_fit_score"],
            weather,
        )
    )
    context["explanation_en"] = (
        "Weather fit is balanced."
        if edge == "balanced"
        else _fit_explanation_en(
            team_a.get("name_en", team_a["iso3"]) if edge == "team_a" else team_b.get("name_en", team_b["iso3"]),
            team_b.get("name_en", team_b["iso3"]) if edge == "team_a" else team_a.get("name_en", team_a["iso3"]),
            fit_a["weather_fit_score"] if edge == "team_a" else fit_b["weather_fit_score"],
            fit_b["weather_fit_score"] if edge == "team_a" else fit_a["weather_fit_score"],
            weather,
        )
    )
    return {
        "match": context,
        "teams": [
            {**team_a, **fit_a, "team_role": "team_a"},
            {**team_b, **fit_b, "team_role": "team_b"},
        ],
    }


def render_weather_fit_texts(matchup: dict[str, Any]) -> dict[str, Any]:
    """Render concise website and social text snippets for Weather Fit."""

    context = matchup["match"]
    edge_de = "ausgeglichen" if context["weather_fit_edge"] == "balanced" else context["weather_fit_edge_team_iso3"]
    edge_en = "balanced" if context["weather_fit_edge"] == "balanced" else context["weather_fit_edge_team_iso3"]
    social_de = (
        "{team_a_iso3} vs. {team_b_iso3}: Bei {weather_temp_c} Grad und {weather_humidity}% "
        "Luftfeuchtigkeit ist der Weather-Fit-Vergleich ausgeglichen. Kein Wettmodell."
        if context["weather_fit_edge"] == "balanced"
        else "{team_a_iso3} vs. {team_b_iso3}: Bei {weather_temp_c} Grad und {weather_humidity}% "
        "Luftfeuchtigkeit sieht der Weather-Fit-Vergleich {weather_fit_edge_de} vorne. Kein Wettmodell."
    )
    social_en = (
        "{team_a_iso3} vs {team_b_iso3}: at {weather_temp_c} degrees and {weather_humidity}% "
        "humidity, the Weather Fit check is balanced. Not a betting model."
        if context["weather_fit_edge"] == "balanced"
        else "{team_a_iso3} vs {team_b_iso3}: at {weather_temp_c} degrees and {weather_humidity}% "
        "humidity, the Weather Fit check leans {weather_fit_edge_en}. Not a betting model."
    )
    template_context = {
        **context,
        "weather_fit_edge_de": edge_de,
        "weather_fit_edge_en": edge_en,
    }
    de_headline = "{team_a_flag} {team_a_iso3} vs. {team_b_flag} {team_b_iso3}: Wer passt besser zum Wetter?"
    en_headline = "{team_a_flag} {team_a_iso3} vs {team_b_flag} {team_b_iso3}: who fits the weather better?"
    return {
        "de": {
            "headline": de_headline.format_map(SafeFormatDict(template_context)),
            "teaser": (
                "Weather Fit: {team_a_iso3} {team_a_weather_fit_score}/100, "
                "{team_b_iso3} {team_b_weather_fit_score}/100. Vorteil: {weather_fit_edge_de}."
            ).format_map(SafeFormatDict(template_context)),
            "social_hook": social_de.format_map(SafeFormatDict(template_context)),
            "body": context["explanation_de"],
        },
        "en": {
            "headline": en_headline.format_map(SafeFormatDict(template_context)),
            "teaser": (
                "Weather Fit: {team_a_iso3} {team_a_weather_fit_score}/100, "
                "{team_b_iso3} {team_b_weather_fit_score}/100. Edge: {weather_fit_edge_en}."
            ).format_map(SafeFormatDict(template_context)),
            "social_hook": social_en.format_map(SafeFormatDict(template_context)),
            "body": context["explanation_en"],
        },
    }


def build_local_weather_matchups(
    weather_type: str = "forecast",
    schedule_path: str = "data/sample_schedule.csv",
    teams_path: str = "data/sample_teams.csv",
    venues_path: str = "data/sample_venues.csv",
    profiles_path: str = "data/sample_team_weather_profiles.csv",
    weather_path: str | None = None,
) -> list[dict[str, Any]]:
    """Build Weather Fit payloads from local sample CSV files."""

    matches = _read_csv(Path(schedule_path))
    teams = {row["iso3"]: row for row in _read_csv(Path(teams_path))}
    venues = {(row["stadium_name"], row["host_city"]): row for row in _read_csv(Path(venues_path))}
    profiles = {row["iso3"]: row for row in _read_csv(Path(profiles_path))}
    default_weather_path = "data/sample_weather_forecast.csv" if weather_type == "forecast" else "data/sample_weather_actual.csv"
    weather_rows = _read_csv(Path(weather_path or default_weather_path))
    weather_by_match = {row["match_id"]: (_weather_from_forecast(row) if weather_type == "forecast" else _weather_from_actual(row)) for row in weather_rows}

    outputs = []
    for match in matches:
        venue = venues.get((match["stadium_name"], match["host_city"]), {})
        match_context = {**match, **venue}
        team_a = teams.get(match["team_a_iso3"])
        team_b = teams.get(match["team_b_iso3"])
        profile_a = profiles.get(match["team_a_iso3"])
        profile_b = profiles.get(match["team_b_iso3"])
        weather = weather_by_match.get(match["match_id"])
        if not all([team_a, team_b, profile_a, profile_b, weather]):
            continue
        matchup = build_weather_matchup(match_context, team_a, team_b, profile_a, profile_b, weather)
        matchup["texts"] = render_weather_fit_texts(matchup)
        outputs.append(matchup)
    return outputs


def load_match_weather_context(match_id: str, weather_type: str = "forecast") -> dict[str, Any]:
    """Load match, team, venue, profile and weather context from the database."""

    text = _load_sql()
    engine = get_engine()
    with engine.connect() as conn:
        match = conn.execute(
            text(
                """
                select
                  m.match_id, m.matchday, m.tournament_stage, m.group_name,
                  m.local_date, m.local_time, v.host_city, v.stadium_name,
                  ta.id as team_a_id, ta.iso3 as team_a_iso3, ta.name_de as team_a_name_de,
                  ta.name_en as team_a_name_en, ta.flag_emoji as team_a_flag,
                  tb.id as team_b_id, tb.iso3 as team_b_iso3, tb.name_de as team_b_name_de,
                  tb.name_en as team_b_name_en, tb.flag_emoji as team_b_flag
                from matches m
                join venues v on v.id = m.venue_id
                join teams ta on ta.id = m.team_a_id
                join teams tb on tb.id = m.team_b_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings().first()
        if match is None:
            raise ValueError(f"Unknown match_id: {match_id}")
        table = "weather_actual" if weather_type == "actual" else "weather_forecast"
        weather = conn.execute(text(f"select * from {table} where match_id = :match_id"), {"match_id": match_id}).mappings().first()
        if weather is None:
            raise ValueError(f"No {weather_type} weather found for {match_id}")
        profiles = conn.execute(
            text(
                """
                select t.iso3, p.*
                from team_weather_profiles p
                join teams t on t.id = p.team_id
                where t.iso3 in (:team_a_iso3, :team_b_iso3) and p.is_active = true
                """
            ),
            {"team_a_iso3": match["team_a_iso3"], "team_b_iso3": match["team_b_iso3"]},
        ).mappings()
        profile_by_iso3 = {row["iso3"]: dict(row) for row in profiles}
    weather_dict = _weather_from_actual(dict(weather)) if weather_type == "actual" else _weather_from_forecast(dict(weather))
    return {
        "match": dict(match),
        "team_a": {
            "id": match["team_a_id"],
            "iso3": match["team_a_iso3"],
            "name_de": match["team_a_name_de"],
            "name_en": match["team_a_name_en"],
            "flag_emoji": match["team_a_flag"],
        },
        "team_b": {
            "id": match["team_b_id"],
            "iso3": match["team_b_iso3"],
            "name_de": match["team_b_name_de"],
            "name_en": match["team_b_name_en"],
            "flag_emoji": match["team_b_flag"],
        },
        "profile_a": profile_by_iso3.get(match["team_a_iso3"]),
        "profile_b": profile_by_iso3.get(match["team_b_iso3"]),
        "weather": weather_dict,
    }


def generate_weather_matchup_for_match(match_id: str, weather_type: str = "forecast") -> dict[str, Any]:
    """Generate and upsert Weather Fit metrics and generated text for one DB match."""

    text = _load_sql()
    engine = get_engine()
    context = load_match_weather_context(match_id, weather_type)
    if not context["profile_a"] or not context["profile_b"]:
        raise ValueError(f"Missing active weather profile for {match_id}")
    matchup = build_weather_matchup(
        context["match"],
        context["team_a"],
        context["team_b"],
        context["profile_a"],
        context["profile_b"],
        context["weather"],
    )
    matchup["texts"] = render_weather_fit_texts(matchup)
    source_type = context["weather"]["source_weather_type"]
    edge = matchup["match"]["weather_fit_edge"]
    edge_gap = matchup["match"]["weather_fit_edge_gap"]
    with engine.begin() as conn:
        for team in matchup["teams"]:
            role = "balanced"
            if edge != "balanced":
                role = "weather_edge" if team["team_role"] == edge else "weather_trailing"
            conn.execute(
                text(
                    """
                    insert into weather_matchup_metrics (
                      match_id, team_id, source_weather_type, weather_temp_c,
                      weather_humidity, weather_wind_speed, precipitation_probability,
                      weather_load_score, weather_familiarity_score, weather_tolerance_score,
                      effective_weather_load_score, weather_fit_score, weather_fit_label,
                      edge_team_role, edge_gap, explanation_de, explanation_en,
                      data_quality_score
                    )
                    values (
                      :match_id, :team_id, :source_weather_type, :weather_temp_c,
                      :weather_humidity, :weather_wind_speed, :precipitation_probability,
                      :weather_load_score, :weather_familiarity_score, :weather_tolerance_score,
                      :effective_weather_load_score, :weather_fit_score, :weather_fit_label,
                      :edge_team_role, :edge_gap, :explanation_de, :explanation_en,
                      :data_quality_score
                    )
                    on conflict (match_id, team_id, source_weather_type) do update set
                      weather_temp_c = excluded.weather_temp_c,
                      weather_humidity = excluded.weather_humidity,
                      weather_wind_speed = excluded.weather_wind_speed,
                      precipitation_probability = excluded.precipitation_probability,
                      weather_load_score = excluded.weather_load_score,
                      weather_familiarity_score = excluded.weather_familiarity_score,
                      weather_tolerance_score = excluded.weather_tolerance_score,
                      effective_weather_load_score = excluded.effective_weather_load_score,
                      weather_fit_score = excluded.weather_fit_score,
                      weather_fit_label = excluded.weather_fit_label,
                      edge_team_role = excluded.edge_team_role,
                      edge_gap = excluded.edge_gap,
                      explanation_de = excluded.explanation_de,
                      explanation_en = excluded.explanation_en,
                      data_quality_score = excluded.data_quality_score
                    """
                ),
                {
                    "match_id": match_id,
                    "team_id": team["id"],
                    "source_weather_type": source_type,
                    "weather_temp_c": context["weather"]["weather_temp_c"],
                    "weather_humidity": context["weather"]["weather_humidity"],
                    "weather_wind_speed": context["weather"]["weather_wind_speed"],
                    "precipitation_probability": context["weather"]["precipitation_probability"],
                    "edge_team_role": role,
                    "edge_gap": edge_gap,
                    "explanation_de": matchup["match"]["explanation_de"],
                    "explanation_en": matchup["match"]["explanation_en"],
                    **{key: team[key] for key in [
                        "weather_load_score",
                        "weather_familiarity_score",
                        "weather_tolerance_score",
                        "effective_weather_load_score",
                        "weather_fit_score",
                        "weather_fit_label",
                        "data_quality_score",
                    ]},
                },
            )
        for language in ("de", "en"):
            item = matchup["texts"][language]
            conn.execute(
                text(
                    """
                    insert into generated_texts (
                      match_id, language, content_type, headline, teaser, body,
                      social_hook, generated_from_data_hash
                    )
                    values (
                      :match_id, :language, :content_type, :headline, :teaser, :body,
                      :social_hook, :generated_from_data_hash
                    )
                    on conflict (match_id, language, content_type) do update set
                      headline = excluded.headline,
                      teaser = excluded.teaser,
                      body = excluded.body,
                      social_hook = excluded.social_hook,
                      generated_from_data_hash = excluded.generated_from_data_hash
                    """
                ),
                {
                    "match_id": match_id,
                    "language": language,
                    "content_type": f"weather_fit_{source_type}",
                    "headline": item["headline"],
                    "teaser": item["teaser"],
                    "body": item["body"],
                    "social_hook": item["social_hook"],
                    "generated_from_data_hash": data_hash(matchup["match"]),
                },
            )
    return matchup


def generate_weather_matchups_for_all_matches(weather_type: str = "forecast") -> dict[str, Any]:
    """Generate Weather Fit matchup rows for every match with stored weather."""

    text = _load_sql()
    engine = get_engine()
    table = "weather_actual" if weather_type == "actual" else "weather_forecast"
    with engine.connect() as conn:
        match_ids = [
            row[0]
            for row in conn.execute(
                text(
                    f"""
                    select w.match_id
                    from {table} w
                    join matches m on m.match_id = w.match_id
                    where m.team_a_id is not null and m.team_b_id is not null
                    order by m.date_utc nulls last, w.match_id
                    """
                )
            )
        ]

    generated: list[str] = []
    skipped: list[dict[str, str]] = []
    for match_id in match_ids:
        try:
            generate_weather_matchup_for_match(match_id, weather_type)
            generated.append(match_id)
        except Exception as exc:  # noqa: BLE001
            skipped.append({"match_id": match_id, "error": str(exc)})
    return {
        "weather_type": weather_type,
        "matches_with_weather": len(match_ids),
        "generated": len(generated),
        "skipped": skipped,
        "generated_match_ids": generated,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Weather Fit matchup")
    parser.add_argument("--match-id", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--weather-type", choices=["forecast", "actual"], default="forecast")
    parser.add_argument("--schedule", default="data/sample_schedule.csv")
    parser.add_argument("--teams", default="data/sample_teams.csv")
    parser.add_argument("--venues", default="data/sample_venues.csv")
    parser.add_argument("--profiles", default="data/sample_team_weather_profiles.csv")
    parser.add_argument("--weather-csv", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    try:
        if args.all:
            output = generate_weather_matchups_for_all_matches(args.weather_type)
        elif args.match_id:
            output = generate_weather_matchup_for_match(args.match_id, args.weather_type)
        else:
            output = build_local_weather_matchups(
                weather_type=args.weather_type,
                schedule_path=args.schedule,
                teams_path=args.teams,
                venues_path=args.venues,
                profiles_path=args.profiles,
                weather_path=args.weather_csv,
            )
        rendered = json.dumps(output, indent=2, ensure_ascii=False, default=str)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
            print({"output": args.output, "weather_matchups": len(output) if isinstance(output, list) else 1})
        else:
            print(rendered)
    except (RuntimeError, ValueError) as exc:
        print(f"Weather matchup not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
