"""Geographic helpers used by context metrics."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometers."""

    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def estimate_travel_time_hours(distance_km: float | None) -> float | None:
    """Estimate football-team travel time using MVP formula distance / 750 + 3."""

    if distance_km is None:
        return None
    return distance_km / 750 + 3
