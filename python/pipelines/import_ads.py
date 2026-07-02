"""Import ad inventory, campaigns and placements from a CSV file."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from python.db import get_engine

REQUIRED_COLUMNS = {
    "slot_key",
    "section_key",
    "placement_key",
    "display_name",
    "partner_key",
    "partner_name",
    "campaign_key",
    "campaign_name",
    "creative_key",
    "creative_name",
}


def _load_sql():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _clean(row: dict[str, Any]) -> dict[str, Any]:
    return {key: (None if value == "" else value) for key, value in row.items()}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "ja"}


def _parse_int(value: Any, default: int | None = None) -> int | None:
    if value in ("", None):
        return default
    return int(value)


def _parse_json(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {"raw": value}


def validate_ads(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    columns = set(rows[0].keys()) if rows else set()
    missing = REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
        return errors
    if not rows:
        errors.append("CSV contains no rows")
        return errors
    valid_devices = {"all", "mobile", "desktop", ""}
    valid_types = {"html", "image", "native", "network_tag", ""}
    for row in rows:
        if row.get("device_targeting", "") not in valid_devices:
            errors.append(f"Invalid device_targeting for {row.get('slot_key')}")
        if row.get("creative_type", "") not in valid_types:
            errors.append(f"Invalid creative_type for {row.get('creative_key')}")
    return errors


def import_ads(csv_path: str, dry_run: bool = False) -> dict[str, int]:
    """Import ad inventory CSV into the ad tables."""

    path = Path(csv_path)
    rows = _read_rows(path)
    errors = validate_ads(rows)
    if errors:
        raise ValueError("; ".join(errors))

    if dry_run:
        return {"rows_processed": len(rows), "rows_failed": 0}

    text = _load_sql()
    engine = get_engine()
    rows_failed = 0
    with engine.begin() as conn:
        for row in rows:
            payload = _clean(
                {
                    **row,
                    "partner_type": row.get("partner_type") or "direct",
                    "booking_status": row.get("booking_status") or "active",
                    "creative_type": row.get("creative_type") or "native",
                    "label": row.get("label") or "Anzeige",
                    "device_targeting": row.get("device_targeting") or "all",
                    "priority": _parse_int(row.get("priority"), 50),
                    "weight": _parse_int(row.get("weight"), 100),
                    "max_width": _parse_int(row.get("max_width")),
                    "min_height": _parse_int(row.get("min_height")),
                    "width": _parse_int(row.get("width")),
                    "height": _parse_int(row.get("height")),
                    "is_active": _parse_bool(row.get("is_active", True)),
                    "targeting_json": _parse_json(row.get("targeting_json")),
                }
            )
            try:
                partner_id = conn.execute(
                    text(
                        """
                        insert into ad_partners (
                          partner_key, partner_name, contact_email, partner_type, status, notes
                        )
                        values (
                          :partner_key, :partner_name, :contact_email, :partner_type, 'active', :notes
                        )
                        on conflict (partner_key) do update set
                          partner_name = excluded.partner_name,
                          contact_email = excluded.contact_email,
                          partner_type = excluded.partner_type,
                          notes = excluded.notes
                        returning id
                        """
                    ),
                    payload,
                ).scalar_one()

                campaign_id = conn.execute(
                    text(
                        """
                        insert into ad_campaigns (
                          campaign_key, partner_id, campaign_name, booking_status,
                          starts_at, ends_at, priority, targeting_json, notes
                        )
                        values (
                          :campaign_key, :partner_id, :campaign_name, :booking_status,
                          :starts_at, :ends_at, :priority, :targeting_json, :notes
                        )
                        on conflict (campaign_key) do update set
                          partner_id = excluded.partner_id,
                          campaign_name = excluded.campaign_name,
                          booking_status = excluded.booking_status,
                          starts_at = excluded.starts_at,
                          ends_at = excluded.ends_at,
                          priority = excluded.priority,
                          targeting_json = excluded.targeting_json,
                          notes = excluded.notes
                        returning id
                        """
                    ),
                    {**payload, "partner_id": partner_id},
                ).scalar_one()

                creative_id = conn.execute(
                    text(
                        """
                        insert into ad_creatives (
                          creative_key, campaign_id, creative_name, creative_type, label,
                          headline, body, call_to_action, image_url, click_url,
                          tracking_pixel_url, alt_text, background_color, text_color,
                          width, height, is_active
                        )
                        values (
                          :creative_key, :campaign_id, :creative_name, :creative_type, :label,
                          :headline, :body, :call_to_action, :image_url, :click_url,
                          :tracking_pixel_url, :alt_text, :background_color, :text_color,
                          :width, :height, :is_active
                        )
                        on conflict (creative_key) do update set
                          campaign_id = excluded.campaign_id,
                          creative_name = excluded.creative_name,
                          creative_type = excluded.creative_type,
                          label = excluded.label,
                          headline = excluded.headline,
                          body = excluded.body,
                          call_to_action = excluded.call_to_action,
                          image_url = excluded.image_url,
                          click_url = excluded.click_url,
                          tracking_pixel_url = excluded.tracking_pixel_url,
                          alt_text = excluded.alt_text,
                          background_color = excluded.background_color,
                          text_color = excluded.text_color,
                          width = excluded.width,
                          height = excluded.height,
                          is_active = excluded.is_active
                        returning id
                        """
                    ),
                    {**payload, "campaign_id": campaign_id},
                ).scalar_one()

                slot_id = conn.execute(
                    text(
                        """
                        insert into ad_slots (
                          slot_key, section_key, placement_key, display_name, allowed_sizes,
                          max_width, min_height, device_targeting, is_active
                        )
                        values (
                          :slot_key, :section_key, :placement_key, :display_name, :allowed_sizes,
                          :max_width, :min_height, :device_targeting, :is_active
                        )
                        on conflict (slot_key) do update set
                          section_key = excluded.section_key,
                          placement_key = excluded.placement_key,
                          display_name = excluded.display_name,
                          allowed_sizes = excluded.allowed_sizes,
                          max_width = excluded.max_width,
                          min_height = excluded.min_height,
                          device_targeting = excluded.device_targeting,
                          is_active = excluded.is_active
                        returning id
                        """
                    ),
                    payload,
                ).scalar_one()

                conn.execute(
                    text(
                        """
                        insert into ad_placements (
                          slot_id, creative_id, starts_at, ends_at, priority, weight, is_active
                        )
                        values (
                          :slot_id, :creative_id, :starts_at, :ends_at, :priority, :weight, :is_active
                        )
                        on conflict (slot_id, creative_id) do update set
                          starts_at = excluded.starts_at,
                          ends_at = excluded.ends_at,
                          priority = excluded.priority,
                          weight = excluded.weight,
                          is_active = excluded.is_active
                        """
                    ),
                    {**payload, "slot_id": slot_id, "creative_id": creative_id},
                )
            except Exception as exc:  # noqa: BLE001
                rows_failed += 1
                print(f"Failed ad row {row.get('creative_key')}: {exc}", file=sys.stderr)

        conn.execute(
            text(
                """
                insert into import_logs(
                  import_type, source_file, rows_processed, rows_inserted, rows_updated,
                  rows_failed, status, error_message
                )
                values (
                  'ads_csv', :source_file, :rows_processed, :rows_inserted, :rows_updated,
                  :rows_failed, :status, :error_message
                )
                """
            ),
            {
                "source_file": str(path),
                "rows_processed": len(rows),
                "rows_inserted": len(rows) - rows_failed,
                "rows_updated": 0,
                "rows_failed": rows_failed,
                "status": "completed" if rows_failed == 0 else "partial",
                "error_message": None if rows_failed == 0 else "Some rows failed; see stderr.",
            },
        )

    return {"rows_processed": len(rows), "rows_failed": rows_failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import ad inventory CSV")
    parser.add_argument("--file", default="data/ad_inventory.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(import_ads(args.file, dry_run=args.dry_run))
    except (RuntimeError, ValueError) as exc:
        print(f"Ad import not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
