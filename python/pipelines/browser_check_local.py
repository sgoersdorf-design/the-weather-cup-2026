"""Run a local sanity check for the generated standalone MVP HTML."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _extract_payload(html: str) -> dict[str, Any]:
    prefix = "window.WM_MVP_DATA = "
    start = html.find(prefix)
    if start == -1:
        raise ValueError("Embedded WM_MVP_DATA payload not found in standalone HTML")
    start += len(prefix)
    end = html.find("</script>", start)
    if end == -1:
        raise ValueError("Embedded WM_MVP_DATA payload is not terminated correctly")
    payload = html[start:end].strip()
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


def _local_event_coverage() -> dict[str, int]:
    events_path = Path("data/match_events.csv")
    appearances_path = Path("data/match_player_appearances.csv")
    if not events_path.exists() and not appearances_path.exists():
        return {}

    matches_with_goal_events: set[str] = set()
    matches_with_substitutions: set[str] = set()
    matches_with_hydration_markers: set[str] = set()
    if events_path.exists():
        with events_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                match_id = str(row.get("match_id") or "")
                event_type = str(row.get("event_type") or "")
                if not match_id:
                    continue
                if event_type in {"goal", "own_goal", "penalty_goal"}:
                    matches_with_goal_events.add(match_id)
                if event_type in {"sub_in", "sub_out"}:
                    matches_with_substitutions.add(match_id)
                if event_type in {"hydration_break_start", "hydration_break_end"}:
                    matches_with_hydration_markers.add(match_id)

    lineup_counts: dict[str, int] = {}
    if appearances_path.exists():
        with appearances_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("appearance_role") != "starter":
                    continue
                match_id = str(row.get("match_id") or "")
                if not match_id:
                    continue
                lineup_counts[match_id] = lineup_counts.get(match_id, 0) + 1

    return {
        "matches_with_goal_events": len(matches_with_goal_events),
        "matches_with_complete_lineups": len([match_id for match_id, starters in lineup_counts.items() if starters >= 22]),
        "matches_with_substitutions": len(matches_with_substitutions),
        "matches_with_hydration_markers": len(matches_with_hydration_markers),
    }


def browser_check_local(path: str = "website/mvp/wm-2026-weather-fit-mvp.html") -> dict[str, Any]:
    html_path = Path(path)
    html = html_path.read_text(encoding="utf-8")
    payload = _extract_payload(html)
    metadata = payload.get("metadata") or {}
    analysis = payload.get("analysis") or {}
    tournament = analysis.get("tournament") or {}
    matches = payload.get("matches") or []
    event_stats = payload.get("event_stats") or {}
    event_coverage = event_stats.get("coverage") or {}
    schedule_tab = payload.get("ui") or {}
    latest_export = metadata.get("generated_at") or metadata.get("exported_at")
    local_event_coverage = _local_event_coverage()

    coverage_not_behind_local = True
    if local_event_coverage:
        coverage_not_behind_local = all(
            int(event_coverage.get(key) or 0) >= value for key, value in local_event_coverage.items()
        )

    checks = {
        "has_inlined_css": "<style>" in html,
        "has_inlined_data": "window.WM_MVP_DATA =" in html,
        "has_inlined_app": "const source = window.WM_MVP_DATA" in html,
        "no_external_data_js": './data.js' not in html,
        "no_external_app_js": './app.js' not in html,
        "contains_actual_weather_pending_copy": "Ist-Wetter noch nicht verfügbar" in html,
        "contains_schedule_jumpbar": "schedule-jumpbar" in html,
        "contains_current_focus_copy": "scheduleSmart" in html and "jumpCurrent" in html,
        "contains_full_timeline_toggle": "scheduleFull" in html or "Full timeline from the opening match." in html,
        "has_matches_payload": len(matches) > 0,
        "has_metadata_timestamp": bool(latest_export),
        "event_coverage_not_behind_local_csv": coverage_not_behind_local,
    }
    ok = all(checks.values()) and int(metadata.get("matches") or 0) > 0
    return {
        "status": "ok" if ok else "failed",
        "path": str(html_path),
        "metadata": metadata,
        "tournament": tournament,
        "event_coverage": event_coverage,
        "local_event_coverage": local_event_coverage,
        "match_count": len(matches),
        "ui_payload_keys": sorted(schedule_tab.keys()) if isinstance(schedule_tab, dict) else [],
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local standalone HTML sanity check")
    parser.add_argument("--file", default="website/mvp/wm-2026-weather-fit-mvp.html")
    args = parser.parse_args(argv)
    result = browser_check_local(args.file)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
