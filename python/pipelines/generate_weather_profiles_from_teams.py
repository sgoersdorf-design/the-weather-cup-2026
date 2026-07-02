"""Generate MVP weather profiles for all teams from team metadata.

This is a pragmatic fallback, not a licensed performance dataset. It uses
capital latitude and continent as transparent proxy inputs until a richer
climate-profile source is connected.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _as_float(value: Any, fallback: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _profile_for_team(row: dict[str, str]) -> dict[str, Any]:
    latitude = abs(_as_float(row.get("capital_latitude")))
    continent = row.get("continent", "")
    tropical_bonus = 10 if continent in {"Africa", "South America", "North America", "Asia"} and latitude < 25 else 0
    cool_bonus = 10 if continent == "Europe" and latitude > 45 else 0
    heat = _clamp(88 - latitude * 0.85 + tropical_bonus)
    humidity = _clamp(72 - latitude * 0.35 + tropical_bonus / 2)
    rain = _clamp(55 + (8 if continent in {"Europe", "South America", "Africa"} else 0) - max(0, latitude - 45) * 0.35)
    wind = _clamp(52 + (8 if continent in {"Europe", "Oceania"} else 0))
    reference_temp = round(_clamp(29 - latitude * 0.28, 8, 30), 1)
    reference_humidity = round(_clamp(72 - latitude * 0.18 + tropical_bonus / 2, 45, 82), 1)
    return {
        "iso3": row["iso3"],
        "reference_temp_c": reference_temp,
        "reference_humidity": reference_humidity,
        "heat_tolerance_score": round(heat, 1),
        "humidity_tolerance_score": round(humidity, 1),
        "rain_tolerance_score": round(rain, 1),
        "wind_tolerance_score": round(wind, 1),
        "profile_method": "capital_latitude_continent_proxy",
        "data_source_name": "REST Countries metadata plus transparent MVP heuristic",
        "is_active": "true",
        "data_quality_score": 52 if row["iso3"] not in {"ENG", "SCO"} else 45,
    }


def generate_profiles(teams_path: str, output_path: str) -> dict[str, int]:
    rows = [_profile_for_team(row) for row in _read_csv(Path(teams_path))]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return {"teams": len(rows), "output": output_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate fallback Weather Fit profiles from team CSV")
    parser.add_argument("--teams", default="data/full_teams_restcountries.csv")
    parser.add_argument("--output", default="data/full_team_weather_profiles.csv")
    args = parser.parse_args(argv)
    print(generate_profiles(args.teams, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
