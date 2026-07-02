"""Small helpers for transparent data-quality scoring."""

from __future__ import annotations


def quality_from_required_fields(row: dict[str, object], required_fields: list[str]) -> float:
    """Return 0..100 based on present required fields."""

    if not required_fields:
        return 100.0
    present = sum(1 for field in required_fields if row.get(field) not in (None, ""))
    return round((present / len(required_fields)) * 100, 2)


def uncertainty_level(score: float | None) -> str:
    """Map uncertainty score to a label used by website and text templates."""

    if score is None:
        return "unknown"
    if score < 35:
        return "low"
    if score < 70:
        return "medium"
    return "high"
