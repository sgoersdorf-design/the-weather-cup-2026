"""Open-Meteo weather pipeline for forecast, historical and actual match weather."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import socket
import subprocess
from statistics import mean
from typing import Any
from urllib.parse import urlencode, urlsplit

from python.config import settings
from python.db import get_engine
from python.scoring.scores import calculate_heat_index

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "precipitation_probability",
    "wind_speed_10m",
    "weather_code",
]
DAILY_VARS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"]
_forecast_primary_failed = False
_dns_resolution_cache: dict[str, bool] = {}


def _load_dependencies():
    try:
        import requests
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc
    return requests, text


def _endpoint(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """Request JSON with a fixed timeout and readable errors."""

    hostname = urlsplit(url).hostname or ""
    if hostname:
        cached = _dns_resolution_cache.get(hostname)
        if cached is None:
            try:
                socket.getaddrinfo(hostname, None)
            except OSError:
                _dns_resolution_cache[hostname] = False
            else:
                _dns_resolution_cache[hostname] = True
            cached = _dns_resolution_cache[hostname]
        if not cached:
            raise RuntimeError(f"DNS resolution failed for {hostname}")

    query_url = f"{url}?{urlencode(params)}"
    completed = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--retry",
            "5",
            "--retry-all-errors",
            "--retry-delay",
            "2",
            "--max-time",
            "30",
            query_url,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"HTTP request failed: {url}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from {url}") from exc


def _average(values: list[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return round(mean(clean), 2) if clean else None


def _select_hourly_for_date(data: dict[str, Any], target_date: str, preferred_hour: int = 15) -> dict[str, Any]:
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    candidates: list[tuple[int, int]] = []
    for index, value in enumerate(times):
        if str(value).startswith(target_date):
            hour = int(str(value)[11:13])
            candidates.append((abs(hour - preferred_hour), index))
    if not candidates:
        return {}
    _, selected = min(candidates)
    return {key: values[selected] for key, values in hourly.items() if key != "time" and selected < len(values)}


def _ensemble_precipitation_probability(selected: dict[str, Any]) -> float | None:
    """Estimate precipitation probability from ensemble members with measurable rain."""

    member_values = [
        float(value)
        for key, value in selected.items()
        if key.startswith("precipitation_member") and value is not None
    ]
    if not member_values:
        return None
    wet_members = sum(value >= 0.1 for value in member_values)
    return round(100 * wet_members / len(member_values))


def fetch_forecast_data(latitude: float, longitude: float, timezone: str) -> tuple[dict[str, Any], str, int]:
    """Fetch one 16-day forecast payload for a venue."""

    global _forecast_primary_failed

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "hourly": ",".join(HOURLY_VARS),
        "daily": ",".join(DAILY_VARS),
        "forecast_days": 16,
    }
    source_name = "Open-Meteo Forecast API"
    quality_score = 85
    if not _forecast_primary_failed:
        try:
            data = request_json(_endpoint(settings.open_meteo_base_url, "forecast"), params)
        except Exception:  # noqa: BLE001 - use Open-Meteo's official ensemble service as fallback
            _forecast_primary_failed = True
            data = request_json(_endpoint(settings.open_meteo_ensemble_url, "ensemble"), params)
            source_name = "Open-Meteo Ensemble API (fallback)"
            quality_score = 75
    else:
        data = request_json(_endpoint(settings.open_meteo_ensemble_url, "ensemble"), params)
        source_name = "Open-Meteo Ensemble API (fallback)"
        quality_score = 75

    return data, source_name, quality_score


def normalize_forecast_weather(
    data: dict[str, Any],
    date: str,
    source_name: str,
    quality_score: int,
) -> dict[str, Any]:
    """Normalize one match date from a previously fetched venue forecast."""

    selected = _select_hourly_for_date(data, date)
    temp = selected.get("temperature_2m")
    humidity = selected.get("relative_humidity_2m")
    precipitation_probability = selected.get("precipitation_probability")
    if precipitation_probability is None and "Ensemble" in source_name:
        precipitation_probability = _ensemble_precipitation_probability(selected)
    heat_index = calculate_heat_index(temp, humidity)
    daily = data.get("daily", {})
    target_index = daily.get("time", []).index(date) if date in daily.get("time", []) else None
    return {
        "forecast_temp": temp,
        "forecast_min_temp": daily.get("temperature_2m_min", [None])[target_index] if target_index is not None else None,
        "forecast_max_temp": daily.get("temperature_2m_max", [None])[target_index] if target_index is not None else None,
        "forecast_precipitation_probability": precipitation_probability,
        "forecast_humidity": humidity,
        "forecast_wind_speed": selected.get("wind_speed_10m"),
        "forecast_heat_index": heat_index,
        "forecast_weather_code": selected.get("weather_code"),
        "forecast_data_source": source_name,
        "data_quality_score": quality_score if temp is not None and humidity is not None else 30,
    }


def fetch_forecast_weather(latitude: float, longitude: float, date: str, timezone: str) -> dict[str, Any]:
    """Fetch forecast weather for a venue/date and return normalized fields."""

    data, source_name, quality_score = fetch_forecast_data(latitude, longitude, timezone)
    return normalize_forecast_weather(data, date, source_name, quality_score)


def fetch_historical_weather(latitude: float, longitude: float, start_date: str, end_date: str, timezone: str) -> dict[str, Any]:
    """Fetch historical weather and compute average values over the requested window."""

    url = _endpoint(settings.open_meteo_archive_url, "archive")
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]),
        "daily": ",".join(DAILY_VARS),
    }
    data = request_json(url, params)
    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    avg_temp = _average(hourly.get("temperature_2m", []))
    avg_humidity = _average(hourly.get("relative_humidity_2m", []))
    return {
        "historical_avg_temp": avg_temp,
        "historical_min_temp": _average(daily.get("temperature_2m_min", [])),
        "historical_max_temp": _average(daily.get("temperature_2m_max", [])),
        "historical_precipitation": _average(daily.get("precipitation_sum", [])),
        "historical_humidity": avg_humidity,
        "historical_wind_speed": _average(daily.get("wind_speed_10m_max", [])),
        "historical_heat_index": calculate_heat_index(avg_temp, avg_humidity),
        "historical_weather_years_count": 1,
        "historical_data_source": "Open-Meteo Archive API",
        "data_quality_score": 80 if daily else 25,
    }


def fetch_actual_weather_after_match(latitude: float, longitude: float, match_date: str, timezone: str) -> dict[str, Any]:
    """Fetch actual weather after a match via the archive endpoint."""

    historical = fetch_historical_weather(latitude, longitude, match_date, match_date, timezone)
    return {
        "actual_temp": historical["historical_avg_temp"],
        "actual_humidity": historical["historical_humidity"],
        "actual_precipitation": historical["historical_precipitation"],
        "actual_wind_speed": historical["historical_wind_speed"],
        "actual_heat_index": historical["historical_heat_index"],
        "actual_weather_code": None,
        "actual_data_source": "Open-Meteo Archive API",
        "data_quality_score": historical["data_quality_score"],
    }


def update_weather_for_match(match_id: str) -> dict[str, Any]:
    """Load match and venue, fetch available weather data and upsert it."""

    _, text = _load_dependencies()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                select m.match_id, m.local_date, m.date_utc, v.latitude, v.longitude, v.timezone
                from matches m
                join venues v on v.id = m.venue_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings().first()
        if row is None:
            raise ValueError(f"Unknown match_id: {match_id}")

        match_date = row["local_date"].isoformat()
        today = dt.date.today()
        target_date = row["local_date"]
        result: dict[str, Any] = {"match_id": match_id}

        try:
            if 0 <= (target_date - today).days <= 16:
                forecast = fetch_forecast_weather(row["latitude"], row["longitude"], match_date, row["timezone"])
                conn.execute(
                    text(
                        """
                        insert into weather_forecast (
                          match_id, forecast_temp, forecast_min_temp, forecast_max_temp,
                          forecast_precipitation_probability, forecast_humidity, forecast_wind_speed,
                          forecast_heat_index, forecast_weather_code, forecast_data_source,
                          data_quality_score
                        )
                        values (
                          :match_id, :forecast_temp, :forecast_min_temp, :forecast_max_temp,
                          :forecast_precipitation_probability, :forecast_humidity, :forecast_wind_speed,
                          :forecast_heat_index, :forecast_weather_code, :forecast_data_source,
                          :data_quality_score
                        )
                        on conflict (match_id) do update set
                          forecast_temp = excluded.forecast_temp,
                          forecast_min_temp = excluded.forecast_min_temp,
                          forecast_max_temp = excluded.forecast_max_temp,
                          forecast_precipitation_probability = excluded.forecast_precipitation_probability,
                          forecast_humidity = excluded.forecast_humidity,
                          forecast_wind_speed = excluded.forecast_wind_speed,
                          forecast_heat_index = excluded.forecast_heat_index,
                          forecast_weather_code = excluded.forecast_weather_code,
                          forecast_data_source = excluded.forecast_data_source,
                          forecast_last_updated = now(),
                          data_quality_score = excluded.data_quality_score
                        """
                    ),
                    {"match_id": match_id, **forecast},
                )
                result["forecast"] = forecast
            elif target_date < today:
                actual = fetch_actual_weather_after_match(row["latitude"], row["longitude"], match_date, row["timezone"])
                conn.execute(
                    text(
                        """
                        insert into weather_actual (
                          match_id, actual_temp, actual_humidity, actual_precipitation,
                          actual_wind_speed, actual_heat_index, actual_weather_code,
                          actual_data_source, data_quality_score
                        )
                        values (
                          :match_id, :actual_temp, :actual_humidity, :actual_precipitation,
                          :actual_wind_speed, :actual_heat_index, :actual_weather_code,
                          :actual_data_source, :data_quality_score
                        )
                        on conflict (match_id) do update set
                          actual_temp = excluded.actual_temp,
                          actual_humidity = excluded.actual_humidity,
                          actual_precipitation = excluded.actual_precipitation,
                          actual_wind_speed = excluded.actual_wind_speed,
                          actual_heat_index = excluded.actual_heat_index,
                          actual_weather_code = excluded.actual_weather_code,
                          actual_data_source = excluded.actual_data_source,
                          actual_weather_last_updated = now(),
                          data_quality_score = excluded.data_quality_score
                        """
                    ),
                    {"match_id": match_id, **actual},
                )
                result["actual"] = actual
            else:
                result["status"] = "forecast_not_available_yet"
        except Exception as exc:  # noqa: BLE001
            result["status"] = "weather_fetch_failed"
            result["error"] = str(exc)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update Open-Meteo weather for a match")
    parser.add_argument("--match-id", default=None)
    args = parser.parse_args(argv)
    if not args.match_id:
        print("Weather pipeline ready. Pass --match-id M001 to update a database match.")
        return 0
    try:
        print(update_weather_for_match(args.match_id))
    except (RuntimeError, ValueError) as exc:
        print(f"Weather update not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
