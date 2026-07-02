"""Build a full team CSV from group snapshot plus REST Countries metadata."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/alpha/{code}?fields=cca2,cca3,flag,capital,capitalInfo,continents,translations"

REST_ALPHA_MAP = {
    "ENG": "GB",
    "SCO": "GB",
}

REFERENCE_TIMEZONE_OVERRIDES = {
    "ARG": "America/Argentina/Buenos_Aires",
    "AUS": "Australia/Canberra",
    "AUT": "Europe/Vienna",
    "BEL": "Europe/Brussels",
    "BIH": "Europe/Sarajevo",
    "BRA": "America/Sao_Paulo",
    "CAN": "America/Toronto",
    "CHE": "Europe/Zurich",
    "CIV": "Africa/Abidjan",
    "COD": "Africa/Kinshasa",
    "COL": "America/Bogota",
    "CPV": "Atlantic/Cape_Verde",
    "CUW": "America/Curacao",
    "CZE": "Europe/Prague",
    "DEU": "Europe/Berlin",
    "DZA": "Africa/Algiers",
    "ECU": "America/Guayaquil",
    "EGY": "Africa/Cairo",
    "ENG": "Europe/London",
    "ESP": "Europe/Madrid",
    "FRA": "Europe/Paris",
    "GHA": "Africa/Accra",
    "HRV": "Europe/Zagreb",
    "HTI": "America/Port-au-Prince",
    "IRN": "Asia/Tehran",
    "IRQ": "Asia/Baghdad",
    "JOR": "Asia/Amman",
    "JPN": "Asia/Tokyo",
    "KOR": "Asia/Seoul",
    "MAR": "Africa/Casablanca",
    "MEX": "America/Mexico_City",
    "NLD": "Europe/Amsterdam",
    "NOR": "Europe/Oslo",
    "NZL": "Pacific/Auckland",
    "PAN": "America/Panama",
    "PRT": "Europe/Lisbon",
    "PRY": "America/Asuncion",
    "QAT": "Asia/Qatar",
    "SAU": "Asia/Riyadh",
    "SCO": "Europe/London",
    "SEN": "Africa/Dakar",
    "SWE": "Europe/Stockholm",
    "TUN": "Africa/Tunis",
    "TUR": "Europe/Istanbul",
    "URY": "America/Montevideo",
    "USA": "America/New_York",
    "UZB": "Asia/Tashkent",
    "ZAF": "Africa/Johannesburg",
}

CAPITAL_OVERRIDES = {
    "ENG": ("London", 51.5074, -0.1278),
    "SCO": ("Edinburgh", 55.9533, -3.1883),
}


def _load_requests():
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("requests missing. Run: pip install -r requirements.txt") from exc
    return requests


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _fetch_country(code: str) -> dict[str, Any]:
    requests = _load_requests()
    response = requests.get(RESTCOUNTRIES_URL.format(code=code), timeout=30)
    response.raise_for_status()
    data = response.json()
    return data[0] if isinstance(data, list) else data


def build_teams(groups_path: str = "data/world_cup_2026_groups.csv") -> list[dict[str, Any]]:
    rows = []
    for group_row in _read_csv(Path(groups_path)):
        team_code = group_row["team_code"]
        alpha_code = REST_ALPHA_MAP.get(team_code, team_code)
        country = _fetch_country(alpha_code)
        capital = country.get("capital", [group_row["team_name_en"]])[0]
        lat, lon = ((country.get("capitalInfo") or {}).get("latlng") or [None, None])[:2]
        if team_code in CAPITAL_OVERRIDES:
            capital, lat, lon = CAPITAL_OVERRIDES[team_code]
        rows.append(
            {
                "name_de": group_row["team_name_de"],
                "name_en": group_row["team_name_en"],
                "iso2": group_row["team_code"][:2] if team_code in {"ENG", "SCO"} else country.get("cca2", ""),
                "iso3": team_code,
                "flag_emoji": country.get("flag", ""),
                "confederation": group_row["confederation"],
                "continent": (country.get("continents") or [group_row.get("continent", "")])[0],
                "capital_city": capital,
                "capital_latitude": lat,
                "capital_longitude": lon,
                "reference_timezone": REFERENCE_TIMEZONE_OVERRIDES.get(team_code, "UTC"),
                "reference_timezone_method": "restcountries_capital_with_overrides",
                "data_quality_score": 78 if team_code not in {"ENG", "SCO"} else 65,
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch REST Countries metadata for World Cup teams")
    parser.add_argument("--groups", default="data/world_cup_2026_groups.csv")
    parser.add_argument("--output", default="data/full_teams_restcountries.csv")
    args = parser.parse_args(argv)
    try:
        rows = build_teams(args.groups)
        write_csv(rows, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"REST Countries team fetch not completed: {exc}")
        return 1
    print({"output": args.output, "teams": len(rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
