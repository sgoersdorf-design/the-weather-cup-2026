"""Transparent MVP scoring helpers for WM 2026 Context Lab.

The scores are data-journalistic indicators. They are not betting predictions,
medical performance claims or proof that a single factor causes a match result.
"""

from __future__ import annotations

import json
from math import exp
from typing import Any

from python.utils.geo import haversine_distance_km


def clamp_score(value: float | int | None, min_value: float = 0, max_value: float = 100) -> float:
    """Clamp a numeric score to the configured range."""

    if value is None:
        return min_value
    return float(max(min_value, min(max_value, value)))


def calculate_heat_index(temp_c: float | None, humidity: float | None) -> float | None:
    """Approximate heat index in Celsius using the NOAA formula via Fahrenheit."""

    if temp_c is None or humidity is None:
        return None
    if temp_c < 26.7 or humidity < 40:
        return round(float(temp_c), 2)

    temp_f = temp_c * 9 / 5 + 32
    rh = humidity
    heat_index_f = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * rh
        - 0.22475541 * temp_f * rh
        - 0.00683783 * temp_f * temp_f
        - 0.05481717 * rh * rh
        + 0.00122874 * temp_f * temp_f * rh
        + 0.00085282 * temp_f * rh * rh
        - 0.00000199 * temp_f * temp_f * rh * rh
    )
    return round((heat_index_f - 32) * 5 / 9, 2)


def weather_load_score(
    temp_c: float | None,
    humidity: float | None,
    wind_speed: float | None,
    precipitation_probability: float | None,
) -> float:
    """Return 0..100 where higher means stronger weather load."""

    score = 0.0
    if temp_c is not None:
        if temp_c >= 35:
            score += 42
        elif temp_c >= 30:
            score += 32
        elif temp_c >= 26:
            score += 18
        elif temp_c <= 5:
            score += 18
        elif temp_c <= 10:
            score += 8

    if humidity is not None:
        if humidity >= 85:
            score += 22
        elif humidity >= 70:
            score += 14
        elif humidity >= 60:
            score += 7

    heat_index = calculate_heat_index(temp_c, humidity)
    if heat_index is not None and temp_c is not None and heat_index - temp_c >= 4:
        score += 10

    if wind_speed is not None:
        if wind_speed >= 35:
            score += 15
        elif wind_speed >= 25:
            score += 8

    if precipitation_probability is not None:
        if precipitation_probability >= 70:
            score += 14
        elif precipitation_probability >= 40:
            score += 7

    return round(clamp_score(score), 2)


def weather_familiarity_score(
    team_reference_temp: float | None,
    venue_temp: float | None,
    team_reference_humidity: float | None = None,
    venue_humidity: float | None = None,
) -> float:
    """Return 0..100 where higher means conditions resemble the team's reference context."""

    if team_reference_temp is None or venue_temp is None:
        return 50.0

    temp_penalty = min(55, abs(team_reference_temp - venue_temp) * 3.2)
    humidity_penalty = 0.0
    if team_reference_humidity is not None and venue_humidity is not None:
        humidity_penalty = min(25, abs(team_reference_humidity - venue_humidity) * 0.45)
    return round(clamp_score(100 - temp_penalty - humidity_penalty), 2)


def weather_tolerance_score(
    temp_c: float | None,
    humidity: float | None,
    precipitation_probability: float | None,
    wind_speed: float | None,
    heat_tolerance_score: float | None = 50,
    humidity_tolerance_score: float | None = 50,
    rain_tolerance_score: float | None = 50,
    wind_tolerance_score: float | None = 50,
) -> float:
    """Return weather-type tolerance relevant to the current conditions."""

    weighted_parts: list[tuple[float, float]] = []
    if temp_c is not None and temp_c >= 26:
        weighted_parts.append((clamp_score(heat_tolerance_score), 0.38))
    if humidity is not None and humidity >= 65:
        weighted_parts.append((clamp_score(humidity_tolerance_score), 0.26))
    if precipitation_probability is not None and precipitation_probability >= 35:
        weighted_parts.append((clamp_score(rain_tolerance_score), 0.18))
    if wind_speed is not None and wind_speed >= 20:
        weighted_parts.append((clamp_score(wind_tolerance_score), 0.18))
    if not weighted_parts:
        return round(
            clamp_score(
                (
                    clamp_score(heat_tolerance_score)
                    + clamp_score(humidity_tolerance_score)
                    + clamp_score(rain_tolerance_score)
                    + clamp_score(wind_tolerance_score)
                )
                / 4
            ),
            2,
        )
    weighted = sum(value * weight for value, weight in weighted_parts)
    weight_total = sum(weight for _, weight in weighted_parts)
    return round(clamp_score(weighted / weight_total), 2)


def weather_fit_score(
    weather_familiarity: float | None,
    weather_tolerance: float | None,
    weather_load: float | None,
) -> float:
    """Return 0..100 where higher means better expected fit for current weather."""

    familiarity = clamp_score(weather_familiarity, 50)
    tolerance = clamp_score(weather_tolerance, 50)
    load = clamp_score(weather_load, 50)
    effective_load = load * (1 - tolerance / 180)
    return round(clamp_score(familiarity * 0.56 + tolerance * 0.24 + (100 - effective_load) * 0.20), 2)


def weather_fit_label(score: float | None) -> str:
    """Return a compact label for website and social formats."""

    value = clamp_score(score, 50)
    if value >= 75:
        return "strong_fit"
    if value >= 60:
        return "moderate_fit"
    if value >= 45:
        return "neutral_fit"
    return "low_fit"


def travel_recovery_score(
    distance_km: float | None,
    rest_hours: float | None,
    timezone_shift: float | None,
    cumulative_distance_km: float = 0,
) -> float:
    """Return 0..100 where higher means better recovery and lower travel load."""

    score = 100.0
    if distance_km is not None:
        score -= min(30, distance_km / 120)
    if rest_hours is not None:
        if rest_hours < 72:
            score -= 30
        elif rest_hours < 96:
            score -= 18
        elif rest_hours < 120:
            score -= 8
    if timezone_shift is not None:
        score -= min(24, abs(timezone_shift) * 6)
    if cumulative_distance_km:
        score -= min(16, cumulative_distance_km / 600)
    return round(clamp_score(score), 2)


def circadian_load_score(
    timezone_shift: float | None,
    perceived_kickoff_hour: float | None,
    days_since_shift: float | None,
) -> float:
    """Return 0..100 where higher means stronger potential circadian load."""

    score = 0.0
    if timezone_shift is not None:
        score += min(42, abs(timezone_shift) * 8)
        if days_since_shift is not None:
            unresolved = max(0, abs(timezone_shift) - days_since_shift)
            score += min(24, unresolved * 5)

    if perceived_kickoff_hour is not None:
        if perceived_kickoff_hour < 10 or perceived_kickoff_hour >= 22:
            score += 24
        elif perceived_kickoff_hour < 12 or perceived_kickoff_hour >= 20:
            score += 14
        elif perceived_kickoff_hour < 14 or perceived_kickoff_hour >= 19:
            score += 7
    return round(clamp_score(score), 2)


def venue_altitude_factor(elevation_m: float | None) -> float:
    """Return 0..100 where higher means greater venue altitude context."""

    if elevation_m is None:
        return 50.0
    if elevation_m >= 2200:
        return 72.0
    if elevation_m >= 1500:
        return 52.0
    if elevation_m >= 1000:
        return 32.0
    if elevation_m >= 600:
        return 16.0
    return 5.0


def altitude_load_score(elevation_m: float | None, elevation_change_m: float | None = None) -> float:
    """Return 0..100 where higher means stronger altitude or altitude-change load."""

    score = venue_altitude_factor(elevation_m)
    if elevation_change_m is not None:
        score += min(24, abs(elevation_change_m) / 70)
    return round(clamp_score(score), 2)


def venue_type_factor(stadium_type_basic: str | None) -> float:
    """Return 0..100 where higher means more weather-buffered conditions."""

    mapping = {
        "indoor": 88.0,
        "retractable_roof": 76.0,
        "outdoor": 42.0,
        "unknown": 50.0,
        None: 50.0,
    }
    return mapping.get(stadium_type_basic, 50.0)


def fan_proximity_score(
    host_country_team_boolean: bool,
    distance_team_capital_to_venue_km: float | None,
    same_continent_boolean: bool,
) -> float:
    """Return proximity indicator only, not a real fan-advantage claim."""

    score = 0.0
    if host_country_team_boolean:
        score += 44
    if same_continent_boolean:
        score += 24
    if distance_team_capital_to_venue_km is not None:
        if distance_team_capital_to_venue_km < 1000:
            score += 32
        elif distance_team_capital_to_venue_km < 3000:
            score += 22
        elif distance_team_capital_to_venue_km < 6000:
            score += 12
    return round(clamp_score(score), 2)


def basic_team_strength_score(
    fifa_ranking_position: int | None = None,
    fifa_ranking_points: float | None = None,
    elo_rating: float | None = None,
    basic_form_score: float | None = None,
) -> float:
    """Return 0..100 from available structured sport indicators."""

    parts: list[tuple[float, float]] = []
    if fifa_ranking_position is not None and fifa_ranking_position > 0:
        parts.append((clamp_score(105 - fifa_ranking_position * 1.7), 0.30))
    if fifa_ranking_points is not None:
        parts.append((clamp_score((fifa_ranking_points - 900) / 11), 0.25))
    if elo_rating is not None:
        parts.append((clamp_score((elo_rating - 1200) / 8), 0.30))
    if basic_form_score is not None:
        parts.append((clamp_score(basic_form_score), 0.15))
    if not parts:
        return 50.0
    weighted = sum(value * weight for value, weight in parts)
    weights = sum(weight for _, weight in parts)
    return round(clamp_score(weighted / weights), 2)


def uncertainty_score(data_quality_scores: list[float | int | None] | tuple[float | int | None, ...], missing_required_fields_count: int) -> float:
    """Return 0..100 where higher means stronger uncertainty."""

    valid_scores = [float(score) for score in data_quality_scores if score is not None]
    quality_penalty = 45.0 if not valid_scores else 100 - (sum(valid_scores) / len(valid_scores))
    missing_penalty = min(45.0, missing_required_fields_count * 9.0)
    return round(clamp_score(quality_penalty * 0.65 + missing_penalty * 0.35), 2)


def _team_composite(scores: dict[str, Any], weights: dict[str, float]) -> float:
    strength = clamp_score(scores.get("basic_team_strength_score", 50))
    weather_familiarity = clamp_score(scores.get("weather_familiarity_score", 50))
    travel = clamp_score(scores.get("travel_recovery_score", 50))
    circadian = 100 - clamp_score(scores.get("circadian_load_score", 50))
    altitude = 100 - clamp_score(scores.get("altitude_load_score", scores.get("venue_altitude_factor", 50)))
    venue_type = clamp_score(scores.get("venue_type_factor", 50))
    fan = clamp_score(scores.get("fan_proximity_score", 50))
    squad_age = clamp_score(scores.get("squad_age_resilience_score", 50))
    weather_load = 100 - clamp_score(scores.get("weather_load_score", 50))

    components = {
        "basic_team_strength_score": strength,
        "weather_familiarity_score": weather_familiarity,
        "travel_recovery_score": travel,
        "circadian_context": circadian,
        "altitude_context": altitude,
        "venue_type_factor": venue_type,
        "fan_proximity_score": fan,
        "squad_age_resilience_score": squad_age,
        "weather_load_context": weather_load,
    }
    return round(sum(components[key] * weights[key] for key in components), 2)


def _probabilities(diff: float, uncertainty: float) -> tuple[float, float, float]:
    balance = max(0, 1 - abs(diff) / 55)
    draw = clamp_score(18 + balance * 14 + uncertainty * 0.08, 14, 38)
    remaining = 100 - draw
    a_share = 1 / (1 + exp(-diff / 18))
    a_win = remaining * a_share
    b_win = remaining - a_win
    total = a_win + draw + b_win
    return round(a_win * 100 / total, 1), round(draw * 100 / total, 1), round(b_win * 100 / total, 1)


def predict_match(
    team_a_scores: dict[str, Any],
    team_b_scores: dict[str, Any],
    model_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Combine transparent score inputs into an MVP match prediction dict."""

    weights = {
        "basic_team_strength_score": 0.48,
        "weather_familiarity_score": 0.07,
        "travel_recovery_score": 0.12,
        "circadian_context": 0.08,
        "altitude_context": 0.05,
        "venue_type_factor": 0.03,
        "fan_proximity_score": 0.07,
        "squad_age_resilience_score": 0.04,
        "weather_load_context": 0.06,
    }
    if model_weights:
        weights.update(model_weights)
    weight_total = sum(weights.values())
    weights = {key: value / weight_total for key, value in weights.items()}

    team_a_total = _team_composite(team_a_scores, weights)
    team_b_total = _team_composite(team_b_scores, weights)
    diff = team_a_total - team_b_total
    uncertainty = max(
        clamp_score(team_a_scores.get("uncertainty_score", 50)),
        clamp_score(team_b_scores.get("uncertainty_score", 50)),
    )
    a_win, draw, b_win = _probabilities(diff, uncertainty)

    category = "draw"
    if a_win > draw and a_win > b_win:
        category = "team_a_win"
    elif b_win > draw and b_win > a_win:
        category = "team_b_win"

    load_factors = {
        "weather_load": max(team_a_scores.get("weather_load_score", 0), team_b_scores.get("weather_load_score", 0)),
        "travel_recovery_gap": abs(team_a_scores.get("travel_recovery_score", 50) - team_b_scores.get("travel_recovery_score", 50)),
        "circadian_load_gap": abs(team_a_scores.get("circadian_load_score", 50) - team_b_scores.get("circadian_load_score", 50)),
        "altitude_load": max(team_a_scores.get("altitude_load_score", 0), team_b_scores.get("altitude_load_score", 0)),
    }
    biggest_load_factor = max(load_factors, key=load_factors.get)
    if abs(diff) < 3:
        main_context_advantage = "balanced"
    else:
        main_context_advantage = "team_a" if diff > 0 else "team_b"

    if uncertainty < 35:
        uncertainty_level = "low"
    elif uncertainty < 70:
        uncertainty_level = "medium"
    else:
        uncertainty_level = "high"

    return {
        "predicted_result_category": category,
        "probability_team_a_win": a_win,
        "probability_draw": draw,
        "probability_team_b_win": b_win,
        "main_context_advantage": main_context_advantage,
        "biggest_load_factor": biggest_load_factor,
        "uncertainty_level": uncertainty_level,
        "team_a_composite_score": team_a_total,
        "team_b_composite_score": team_b_total,
    }


# Backward-compatible aliases for earlier MVP skeleton code.
clamp = clamp_score
heat_index_celsius = calculate_heat_index
haversine_km = haversine_distance_km


def altitude_factor(elevation_m: float | None, elevation_change_m: float | None = None) -> float:
    """Backward-compatible wrapper for altitude load."""

    return altitude_load_score(elevation_m, elevation_change_m)


def fan_proximity_indicator(is_host: bool, same_continent: bool, distance_km: float | None) -> float:
    """Backward-compatible wrapper for fan proximity."""

    return fan_proximity_score(is_host, distance_km, same_continent)


def prediction_probabilities(
    team_a_strength: float,
    team_b_strength: float,
    team_a_context: float,
    team_b_context: float,
    uncertainty: float,
) -> dict[str, Any]:
    """Backward-compatible wrapper around predict_match."""

    return predict_match(
        {
            "basic_team_strength_score": team_a_strength,
            "travel_recovery_score": team_a_context,
            "uncertainty_score": uncertainty,
        },
        {
            "basic_team_strength_score": team_b_strength,
            "travel_recovery_score": team_b_context,
            "uncertainty_score": uncertainty,
        },
    )


if __name__ == "__main__":
    example_a = {
        "basic_team_strength_score": 78,
        "weather_familiarity_score": 64,
        "weather_load_score": weather_load_score(31, 72, 16, 35),
        "travel_recovery_score": travel_recovery_score(1200, 96, 2, 1800),
        "circadian_load_score": circadian_load_score(2, 18, 3),
        "altitude_load_score": altitude_load_score(500, 200),
        "venue_type_factor": venue_type_factor("retractable_roof"),
        "fan_proximity_score": fan_proximity_score(False, 2400, True),
        "squad_age_resilience_score": 58,
        "uncertainty_score": uncertainty_score([82, 76, 80], 1),
    }
    example_b = {
        "basic_team_strength_score": 70,
        "weather_familiarity_score": 72,
        "weather_load_score": weather_load_score(31, 72, 16, 35),
        "travel_recovery_score": travel_recovery_score(600, 100, 1, 900),
        "circadian_load_score": circadian_load_score(1, 20, 2),
        "altitude_load_score": altitude_load_score(500, 150),
        "venue_type_factor": venue_type_factor("retractable_roof"),
        "fan_proximity_score": fan_proximity_score(False, 5200, False),
        "squad_age_resilience_score": 62,
        "uncertainty_score": uncertainty_score([80, 74, 72], 1),
    }
    print(json.dumps(predict_match(example_a, example_b), indent=2, ensure_ascii=False))
