"""Execute the PostgreSQL/Supabase schema via SQLAlchemy."""

from __future__ import annotations

import argparse
from pathlib import Path

from python.db import get_engine


def _load_sqlalchemy():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def execute_schema(schema_path: str = "sql/001_schema.sql", dry_run: bool = False) -> dict[str, object]:
    """Execute the project schema against DATABASE_URL."""

    path = Path(schema_path)
    sql = path.read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
    if dry_run:
        return {"schema_path": str(path), "statements": len(statements), "executed": False}

    text = _load_sqlalchemy()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql))
    return {"schema_path": str(path), "statements": len(statements), "executed": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute PostgreSQL/Supabase schema")
    parser.add_argument("--schema", default="sql/001_schema.sql")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(execute_schema(args.schema, dry_run=args.dry_run))
    except RuntimeError as exc:
        print(f"Schema setup not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
