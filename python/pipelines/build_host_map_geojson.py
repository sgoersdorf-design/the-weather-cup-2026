"""Build a browser-readable host-country GeoJSON bundle for the MVP map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HOST_COUNTRIES = {
    "Canada": "Kanada",
    "United States of America": "USA",
    "Mexico": "Mexiko",
}


def build_host_map_geojson(input_path: str, output_path: str = "website/mvp/map-data.js") -> dict[str, Any]:
    """Filter a world GeoJSON file to Canada, USA and Mexico."""

    source_path = Path(input_path)
    data = json.loads(source_path.read_text(encoding="utf-8"))
    features = []
    for feature in data.get("features", []):
        name = feature.get("properties", {}).get("name")
        if name not in HOST_COUNTRIES:
            continue
        feature = {
            "type": "Feature",
            "properties": {
                "name": name,
                "name_de": HOST_COUNTRIES[name],
            },
            "geometry": feature["geometry"],
        }
        features.append(feature)

    payload = {
        "type": "FeatureCollection",
        "source": {
            "name": "world.geo.json / Natural Earth",
            "url": "https://github.com/johan/world.geo.json",
            "note": "Filtered to 2026 host countries for local MVP rendering.",
        },
        "features": features,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"window.WM_HOST_GEOJSON = {json.dumps(payload, ensure_ascii=False)};\n", encoding="utf-8")
    return {"output": str(output), "features": len(features)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build host-country map data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="website/mvp/map-data.js")
    args = parser.parse_args(argv)
    print(json.dumps(build_host_map_geojson(args.input, args.output), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
