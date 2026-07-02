"""Database helpers for PostgreSQL/Supabase access."""

from __future__ import annotations

import socket
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from python.config import settings


def _load_sqlalchemy():
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
    except ImportError as exc:  # pragma: no cover - only hit without requirements
        raise RuntimeError("SQLAlchemy is not installed. Run: pip install -r requirements.txt") from exc
    return create_engine, text, sessionmaker


@lru_cache(maxsize=1)
def _candidate_database_urls() -> list[str]:
    """Return primary and derived fallback database URLs."""

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill DATABASE_URL.")
    if "REPLACE_WITH_DATABASE_PASSWORD" in settings.database_url:
        raise RuntimeError("DATABASE_URL still contains the password placeholder. Replace it in .env with the Supabase database password.")

    candidates = [settings.database_url]
    parsed = urlsplit(settings.database_url)
    hostname = parsed.hostname or ""
    username = parsed.username or ""
    if hostname.endswith(".pooler.supabase.com") and username.startswith("postgres."):
        project_ref = username.removeprefix("postgres.")
        password = quote(parsed.password or "", safe="")
        port = parsed.port or 5432
        query = dict(parse_qsl(parsed.query))
        query.setdefault("sslmode", "require")
        direct_netloc = f"postgres:{password}@db.{project_ref}.supabase.co:{port}"
        candidates.append(
            urlunsplit(
                (
                    parsed.scheme,
                    direct_netloc,
                    parsed.path or "/postgres",
                    urlencode(query),
                    parsed.fragment,
                )
            )
        )
    deduped: list[str] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _resolves(url: str) -> bool:
    host = urlsplit(url).hostname
    if not host:
        return False
    try:
        socket.getaddrinfo(host, None)
    except OSError:
        return False
    return True


@lru_cache(maxsize=1)
def get_engine():
    """Return a SQLAlchemy engine or raise a clear setup error."""

    create_engine, _, _ = _load_sqlalchemy()
    selected_url = next((candidate for candidate in _candidate_database_urls() if _resolves(candidate)), settings.database_url)
    return create_engine(
        selected_url,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
    )


@contextmanager
def session_scope() -> Iterator[object]:
    """Provide a transactional SQLAlchemy session."""

    _, _, sessionmaker = _load_sqlalchemy()
    engine = get_engine()
    session = sessionmaker(bind=engine, future=True)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Run a minimal connection test."""

    _, text, _ = _load_sqlalchemy()
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    return True


if __name__ == "__main__":
    try:
        ok = test_connection()
    except RuntimeError as exc:
        print(f"Database not ready: {exc}")
    else:
        print(f"Database connection ok: {ok}")
