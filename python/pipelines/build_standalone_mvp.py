"""Build one self-contained HTML file for the static website MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
MVP_DIR = ROOT_DIR / "website" / "mvp"


def _read(name: str) -> str:
    return (MVP_DIR / name).read_text(encoding="utf-8")


def _inline_script(source: str) -> str:
    return source.replace("</script", "<\\/script")


def build_standalone_mvp(output: str = "website/mvp/wm-2026-weather-fit-mvp.html") -> dict[str, str | int]:
    """Inline CSS, data and scripts into a single browser-openable HTML file."""

    html = _read("index.html")
    html = html.replace('<link rel="stylesheet" href="./styles.css">', f"<style>\n{_read('styles.css')}\n</style>")
    html = html.replace('<script src="./data.js"></script>', f"<script>\n{_inline_script(_read('data.js'))}\n</script>")
    html = html.replace('<script src="./map-data.js"></script>', f"<script>\n{_inline_script(_read('map-data.js'))}\n</script>")
    html = html.replace('<script src="./experience.js"></script>', f"<script>\n{_inline_script(_read('experience.js'))}\n</script>")
    html = html.replace('<script src="./app.js"></script>', f"<script>\n{_inline_script(_read('app.js'))}\n</script>")

    output_path = ROOT_DIR / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return {"output": str(output_path), "bytes": output_path.stat().st_size}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build standalone website MVP HTML")
    parser.add_argument("--output", default="website/mvp/wm-2026-weather-fit-mvp.html")
    args = parser.parse_args(argv)
    print(build_standalone_mvp(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
