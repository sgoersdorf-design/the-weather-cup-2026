"""Post-match result updates, prediction evaluation and update texts."""

from __future__ import annotations

import argparse
import json
from typing import Any

from python.db import get_engine
from python.pipelines.generate_texts import SafeFormatDict, load_templates


def _load_dependencies():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc
    return text


def _result_category(result_team_a: int, result_team_b: int) -> str:
    if result_team_a > result_team_b:
        return "team_a_win"
    if result_team_b > result_team_a:
        return "team_b_win"
    return "draw"


def update_match_result(match_id: str, result_team_a: int, result_team_b: int) -> dict[str, Any]:
    """Update a match result and mark the match finished."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                update matches
                set result_team_a = :result_team_a,
                    result_team_b = :result_team_b,
                    match_status = 'finished'
                where match_id = :match_id
                """
            ),
            {"match_id": match_id, "result_team_a": result_team_a, "result_team_b": result_team_b},
        )
    return {"match_id": match_id, "result_team_a": result_team_a, "result_team_b": result_team_b, "match_status": "finished"}


def evaluate_prediction(match_id: str) -> dict[str, Any]:
    """Compare prediction, result and available weather data, then upsert evaluation."""

    text = _load_dependencies()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                select
                  m.match_id, m.result_team_a, m.result_team_b,
                  ta.iso3 as team_a_iso3, tb.iso3 as team_b_iso3,
                  p.predicted_result_category,
                  wf.forecast_temp, wf.forecast_humidity,
                  wa.actual_temp, wa.actual_humidity
                from matches m
                join teams ta on ta.id = m.team_a_id
                join teams tb on tb.id = m.team_b_id
                left join predictions p on p.match_id = m.match_id
                left join weather_forecast wf on wf.match_id = m.match_id
                left join weather_actual wa on wa.match_id = m.match_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings().first()
        if row is None:
            raise ValueError(f"Unknown match_id: {match_id}")
        if row["result_team_a"] is None or row["result_team_b"] is None:
            raise ValueError(f"Match result missing for {match_id}")

        actual_category = _result_category(row["result_team_a"], row["result_team_b"])
        prediction_correct = row["predicted_result_category"] == actual_category
        correct_de = "traf die Ergebniskategorie" if prediction_correct else "traf die Ergebniskategorie nicht"
        correct_en = "matched the result category" if prediction_correct else "did not match the result category"

        if row["forecast_temp"] is not None and row["actual_temp"] is not None:
            temp_delta = round(float(row["actual_temp"]) - float(row["forecast_temp"]), 1)
            weather_de = f"Die Ist-Temperatur lag {temp_delta:+.1f} Grad von der Forecast-Temperatur entfernt."
            weather_en = f"Actual temperature was {temp_delta:+.1f} degrees away from the forecast temperature."
        else:
            weather_de = "Forecast- oder Ist-Wetterdaten fehlen noch."
            weather_en = "Forecast or actual weather data is still missing."

        learning_de = "Die Bewertung bleibt auf Datenqualitaet, Unsicherheit und transparente Kontextfaktoren begrenzt."
        learning_en = "The evaluation remains limited to data quality, uncertainty and transparent context factors."

        payload = {
            "match_id": match_id,
            "prediction_correct_boolean": prediction_correct,
            "prediction_vs_reality_de": f"Die Prognose {correct_de}: erwartet {row['predicted_result_category']}, tatsaechlich {actual_category}.",
            "prediction_vs_reality_en": f"The prediction {correct_en}: expected {row['predicted_result_category']}, actual {actual_category}.",
            "weather_check_de": weather_de,
            "weather_check_en": weather_en,
            "model_learning_note_de": learning_de,
            "model_learning_note_en": learning_en,
        }
        conn.execute(
            text(
                """
                insert into post_match_evaluations (
                  match_id, prediction_correct_boolean, prediction_vs_reality_de,
                  prediction_vs_reality_en, weather_check_de, weather_check_en,
                  model_learning_note_de, model_learning_note_en
                )
                values (
                  :match_id, :prediction_correct_boolean, :prediction_vs_reality_de,
                  :prediction_vs_reality_en, :weather_check_de, :weather_check_en,
                  :model_learning_note_de, :model_learning_note_en
                )
                on conflict (match_id) do update set
                  prediction_correct_boolean = excluded.prediction_correct_boolean,
                  prediction_vs_reality_de = excluded.prediction_vs_reality_de,
                  prediction_vs_reality_en = excluded.prediction_vs_reality_en,
                  weather_check_de = excluded.weather_check_de,
                  weather_check_en = excluded.weather_check_en,
                  model_learning_note_de = excluded.model_learning_note_de,
                  model_learning_note_en = excluded.model_learning_note_en
                """
            ),
            payload,
        )
    return payload


def regenerate_post_match_content(match_id: str) -> dict[str, Any]:
    """Generate website/social post-match copy from the stored evaluation."""

    text = _load_dependencies()
    templates = load_templates()["match_card"]["post_match"]
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                select
                  m.match_id, m.result_team_a, m.result_team_b,
                  ta.iso3 as team_a_iso3, tb.iso3 as team_b_iso3,
                  p.predicted_result_category,
                  e.prediction_correct_boolean,
                  e.weather_check_de, e.weather_check_en,
                  e.model_learning_note_de, e.model_learning_note_en
                from matches m
                join teams ta on ta.id = m.team_a_id
                join teams tb on tb.id = m.team_b_id
                left join predictions p on p.match_id = m.match_id
                left join post_match_evaluations e on e.match_id = m.match_id
                where m.match_id = :match_id
                """
            ),
            {"match_id": match_id},
        ).mappings().first()
        if row is None:
            raise ValueError(f"Unknown match_id: {match_id}")
        context = dict(row)
        context["prediction_correct_text_de"] = "eine passende Ergebniskategorie" if row["prediction_correct_boolean"] else "eine Abweichung"
        context["prediction_correct_text_en"] = "a matching result category" if row["prediction_correct_boolean"] else "a mismatch"

        outputs = {
            "de": {
                "headline": templates["de"]["headline"].format_map(SafeFormatDict(context)),
                "body": templates["de"]["body"].format_map(SafeFormatDict(context)),
            },
            "en": {
                "headline": templates["en"]["headline"].format_map(SafeFormatDict(context)),
                "body": templates["en"]["body"].format_map(SafeFormatDict(context)),
            },
        }

        for language, item in outputs.items():
            conn.execute(
                text(
                    """
                    insert into generated_texts (
                      match_id, language, content_type, headline, body, social_hook,
                      generated_from_data_hash
                    )
                    values (
                      :match_id, :language, 'post_match_update', :headline, :body,
                      :social_hook, :generated_from_data_hash
                    )
                    on conflict (match_id, language, content_type) do update set
                      headline = excluded.headline,
                      body = excluded.body,
                      social_hook = excluded.social_hook,
                      generated_from_data_hash = excluded.generated_from_data_hash
                    """
                ),
                {
                    "match_id": match_id,
                    "language": language,
                    "headline": item["headline"],
                    "body": item["body"],
                    "social_hook": item["headline"],
                    "generated_from_data_hash": "post_match_evaluation",
                },
            )
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Post-match update pipeline")
    parser.add_argument("--match-id", default=None)
    parser.add_argument("--result-a", type=int, default=None)
    parser.add_argument("--result-b", type=int, default=None)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--regenerate-content", action="store_true")
    args = parser.parse_args(argv)

    if not args.match_id:
        print("Post-match pipeline ready. Pass --match-id plus --result-a/--result-b, --evaluate or --regenerate-content.")
        return 0

    try:
        outputs = []
        if args.result_a is not None and args.result_b is not None:
            outputs.append(update_match_result(args.match_id, args.result_a, args.result_b))
        if args.evaluate:
            outputs.append(evaluate_prediction(args.match_id))
        if args.regenerate_content:
            outputs.append(regenerate_post_match_content(args.match_id))
        print(json.dumps(outputs, indent=2, ensure_ascii=False, default=str))
    except (RuntimeError, ValueError) as exc:
        print(f"Post-match update not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
