"""Central configuration for the WM 2026 Context Lab MVP."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    database_url: str | None = os.getenv("DATABASE_URL") or None
    open_meteo_base_url: str = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1")
    open_meteo_ensemble_url: str = os.getenv("OPEN_METEO_ENSEMBLE_URL", "https://ensemble-api.open-meteo.com/v1")
    open_meteo_archive_url: str = os.getenv("OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1")
    open_meteo_geocoding_url: str = os.getenv("OPEN_METEO_GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1")
    model_version: str = os.getenv("MODEL_VERSION", "mvp_0_1")


settings = Settings()
