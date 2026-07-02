"""Run a local sanity check for the generated standalone MVP HTML."""

from __future__ import annotations

import argparse
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


def browser_check_local(path: str = "website/mvp/wm-2026-weather-fit-mvp.html") -> dict[str, Any]:
    html_path = Path(path)
    html = html_path.read_text(encoding="utf-8")
    payload = _extract_payload(html)
    metadata = payload.get("metadata") or {}
    analysis = payload.get("analysis") or {}
    tournament = analysis.get("tournament") or {}
    matches = payload.get("matches") or []
    schedule_tab = payload.get("ui") or {}
    latest_export = metadata.get("generated_at") or metadata.get("exported_at")

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
    }
    ok = all(checks.values()) and int(metadata.get("matches") or 0) > 0
    return {
        "status": "ok" if ok else "failed",
        "path": str(html_path),
        "metadata": metadata,
        "tournament": tournament,
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
