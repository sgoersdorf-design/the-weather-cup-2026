"""Timezone helpers for local and perceived kickoff calculations."""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def timezone_offset_hours(timezone_name: str | None, moment: datetime) -> float | None:
    """Return UTC offset in hours for a timezone at a given datetime."""

    if not timezone_name:
        return None
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return None
    base = moment if moment.tzinfo is not None else moment.replace(tzinfo=timezone.utc)
    aware = base.astimezone(zone)
    offset = aware.utcoffset()
    if offset is None:
        return None
    return offset.total_seconds() / 3600


def timezone_shift_hours(from_timezone: str | None, to_timezone: str | None, moment: datetime) -> float | None:
    """Return target offset minus source offset in hours."""

    from_offset = timezone_offset_hours(from_timezone, moment)
    to_offset = timezone_offset_hours(to_timezone, moment)
    if from_offset is None or to_offset is None:
        return None
    return to_offset - from_offset


def perceived_kickoff_time(local_kickoff: datetime, venue_timezone: str | None, reference_timezone: str | None) -> time | None:
    """Convert a venue-local kickoff into the team's reference timezone."""

    if not venue_timezone or not reference_timezone:
        return None
    try:
        venue_dt = local_kickoff.replace(tzinfo=ZoneInfo(venue_timezone))
        reference_dt = venue_dt.astimezone(ZoneInfo(reference_timezone))
    except ZoneInfoNotFoundError:
        return None
    return reference_dt.time().replace(microsecond=0)
