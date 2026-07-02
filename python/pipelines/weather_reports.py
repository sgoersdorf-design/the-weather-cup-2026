"""Post-match Weather Fit analysis and reporting."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from python.pipelines.weather_matchup import build_local_weather_matchups


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


def _result_category(result_team_a: int, result_team_b: int) -> str:
    if result_team_a > result_team_b:
        return "team_a"
    if result_team_b > result_team_a:
        return "team_b"
    return "draw"


def _edge_alignment(edge: str, result: str) -> str:
    if edge == "balanced":
        return "balanced_no_weather_edge"
    if result == "draw":
        return "draw_after_weather_edge"
    if edge == result:
        return "weather_edge_team_won"
    return "weather_edge_team_did_not_win"


def _forecast_actual_delta(forecast: dict[str, Any], actual: dict[str, Any]) -> dict[str, float | None]:
    forecast_weather = forecast["match"]
    actual_weather = actual["match"]
    temp_delta = None
    humidity_delta = None
    if forecast_weather.get("weather_temp_c") is not None and actual_weather.get("weather_temp_c") is not None:
        temp_delta = round(float(actual_weather["weather_temp_c"]) - float(forecast_weather["weather_temp_c"]), 2)
    if forecast_weather.get("weather_humidity") is not None and actual_weather.get("weather_humidity") is not None:
        humidity_delta = round(float(actual_weather["weather_humidity"]) - float(forecast_weather["weather_humidity"]), 2)
    return {"temp_delta_c": temp_delta, "humidity_delta": humidity_delta}


def build_local_match_reviews() -> list[dict[str, Any]]:
    """Build match-level post-match Weather Fit reviews from sample files."""

    forecast_matchups = {item["match"]["match_id"]: item for item in build_local_weather_matchups("forecast")}
    actual_matchups = {item["match"]["match_id"]: item for item in build_local_weather_matchups("actual")}
    results = {row["match_id"]: row for row in _read_csv(Path("data/sample_results.csv"))}

    reviews: list[dict[str, Any]] = []
    for match_id, forecast in forecast_matchups.items():
        actual = actual_matchups.get(match_id)
        result = results.get(match_id)
        if not actual or not result:
            continue
        result_a = int(result["result_team_a"])
        result_b = int(result["result_team_b"])
        result_category = _result_category(result_a, result_b)
        edge = forecast["match"]["weather_fit_edge"]
        alignment = _edge_alignment(edge, result_category)
        delta = _forecast_actual_delta(forecast, actual)
        reviews.append(
            {
                "match_id": match_id,
                "matchday": forecast["match"].get("matchday"),
                "tournament_stage": forecast["match"].get("tournament_stage"),
                "group_name": forecast["match"].get("group_name"),
                "team_a_iso3": forecast["match"]["team_a_iso3"],
                "team_b_iso3": forecast["match"]["team_b_iso3"],
                "result_team_a": result_a,
                "result_team_b": result_b,
                "forecast_weather_edge": edge,
                "forecast_weather_edge_team_iso3": forecast["match"]["weather_fit_edge_team_iso3"],
                "forecast_weather_edge_gap": forecast["match"]["weather_fit_edge_gap"],
                "actual_weather_edge": actual["match"]["weather_fit_edge"],
                "actual_weather_edge_team_iso3": actual["match"]["weather_fit_edge_team_iso3"],
                "forecast_weather_load_score": forecast["match"]["weather_load_score"],
                "actual_weather_load_score": actual["match"]["weather_load_score"],
                "temp_delta_c": delta["temp_delta_c"],
                "humidity_delta": delta["humidity_delta"],
                "result_category": result_category,
                "edge_alignment": alignment,
                "analysis_note_de": _match_note_de(forecast, actual, result_a, result_b, alignment),
                "analysis_note_en": _match_note_en(forecast, actual, result_a, result_b, alignment),
            }
        )
    return reviews


def _match_note_de(forecast: dict[str, Any], actual: dict[str, Any], result_a: int, result_b: int, alignment: str) -> str:
    match = forecast["match"]
    return (
        f"{match['team_a_iso3']} {result_a}:{result_b} {match['team_b_iso3']}. "
        f"Vor dem Spiel lag der Weather-Fit-Vorteil bei {match['weather_fit_edge_team_iso3'] or 'ausgeglichen'} "
        f"mit {match['weather_fit_edge_gap']}/100 Punkten Abstand. Nach Ist-Wetter lautet die Einordnung "
        f"{actual['match']['weather_fit_edge_team_iso3'] or 'ausgeglichen'}. Alignment: {alignment}. "
        f"Das ist eine Kontextauswertung, keine Ursachenbehauptung."
    )


def _match_note_en(forecast: dict[str, Any], actual: dict[str, Any], result_a: int, result_b: int, alignment: str) -> str:
    match = forecast["match"]
    return (
        f"{match['team_a_iso3']} {result_a}:{result_b} {match['team_b_iso3']}. "
        f"Before the match, the Weather Fit edge was {match['weather_fit_edge_team_iso3'] or 'balanced'} "
        f"with a {match['weather_fit_edge_gap']}/100 point gap. Based on actual weather, the edge is "
        f"{actual['match']['weather_fit_edge_team_iso3'] or 'balanced'}. Alignment: {alignment}. "
        f"This is context analysis, not a causality claim."
    )


def aggregate_reviews(reviews: list[dict[str, Any]], scope_key: str) -> dict[str, dict[str, Any]]:
    """Aggregate match reviews by matchday, phase or tournament."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        if scope_key == "tournament":
            key = "tournament"
        else:
            key = str(review.get(scope_key) or "unknown")
        groups[key].append(review)

    aggregates: dict[str, dict[str, Any]] = {}
    for key, rows in groups.items():
        forecast_loads = [_as_float(row["forecast_weather_load_score"]) for row in rows if _as_float(row["forecast_weather_load_score"]) is not None]
        actual_loads = [_as_float(row["actual_weather_load_score"]) for row in rows if _as_float(row["actual_weather_load_score"]) is not None]
        edge_gaps = [_as_float(row["forecast_weather_edge_gap"]) for row in rows if _as_float(row["forecast_weather_edge_gap"]) is not None]
        alignment_counts: dict[str, int] = defaultdict(int)
        for row in rows:
            alignment_counts[row["edge_alignment"]] += 1
        aggregates[key] = {
            "matches": len(rows),
            "avg_forecast_weather_load_score": round(sum(forecast_loads) / len(forecast_loads), 2) if forecast_loads else None,
            "avg_actual_weather_load_score": round(sum(actual_loads) / len(actual_loads), 2) if actual_loads else None,
            "avg_forecast_weather_edge_gap": round(sum(edge_gaps) / len(edge_gaps), 2) if edge_gaps else None,
            "high_actual_weather_load_matches": len([value for value in actual_loads if value >= 50]),
            "alignment_counts": dict(alignment_counts),
        }
    return aggregates


def build_weather_report() -> dict[str, Any]:
    """Build full report payload for match, matchday, phase and tournament scopes."""

    reviews = build_local_match_reviews()
    return {
        "scope": "sample_tournament",
        "disclaimer_de": "Weather Fit ist ein datenjournalistischer Kontextindikator, kein Beweis für Ergebnisursachen.",
        "disclaimer_en": "Weather Fit is a data-journalistic context indicator, not proof of match-result causality.",
        "matches": reviews,
        "matchday": aggregate_reviews(reviews, "matchday"),
        "phase": aggregate_reviews(reviews, "tournament_stage"),
        "tournament": aggregate_reviews(reviews, "tournament"),
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render a compact German/English Markdown report."""

    lines = [
        "# WM 2026 Context Lab - Weather Fit Sample Report",
        "",
        f"DE Disclaimer: {report['disclaimer_de']}",
        f"EN Disclaimer: {report['disclaimer_en']}",
        "",
        "## Match Reviews",
        "",
    ]
    for row in report["matches"]:
        lines.extend(
            [
                f"### {row['match_id']} - {row['team_a_iso3']} vs {row['team_b_iso3']}",
                "",
                f"- Result: {row['team_a_iso3']} {row['result_team_a']}:{row['result_team_b']} {row['team_b_iso3']}",
                f"- Forecast Weather Fit edge: {row['forecast_weather_edge_team_iso3'] or 'balanced'} ({row['forecast_weather_edge_gap']}/100 gap)",
                f"- Actual Weather Fit edge: {row['actual_weather_edge_team_iso3'] or 'balanced'}",
                f"- Forecast/actual weather load: {row['forecast_weather_load_score']} -> {row['actual_weather_load_score']}",
                f"- Forecast delta: temp {row['temp_delta_c']} C, humidity {row['humidity_delta']} points",
                f"- DE: {row['analysis_note_de']}",
                f"- EN: {row['analysis_note_en']}",
                "",
            ]
        )

    for title, key in [("Matchday Aggregates", "matchday"), ("Phase Aggregates", "phase"), ("Tournament Aggregate", "tournament")]:
        lines.extend([f"## {title}", ""])
        for scope, metrics in report[key].items():
            lines.extend(
                [
                    f"### {scope}",
                    "",
                    f"- Matches: {metrics['matches']}",
                    f"- Avg forecast weather load: {metrics['avg_forecast_weather_load_score']}",
                    f"- Avg actual weather load: {metrics['avg_actual_weather_load_score']}",
                    f"- Avg Weather Fit edge gap: {metrics['avg_forecast_weather_edge_gap']}",
                    f"- High actual weather load matches: {metrics['high_actual_weather_load_matches']}",
                    f"- Alignment counts: {json.dumps(metrics['alignment_counts'], ensure_ascii=False)}",
                    "",
                ]
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Weather Fit analysis report")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    report = build_weather_report()
    text = json.dumps(report, indent=2, ensure_ascii=False) if args.format == "json" else render_markdown_report(report)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
