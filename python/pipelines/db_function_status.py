"""Inspect database function metadata relevant to Supabase advisors."""

from __future__ import annotations

import argparse
import json

from python.db import get_engine


def _load_sqlalchemy():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def get_function_status(schema: str = "public", function_name: str = "set_updated_at") -> dict[str, object]:
    text = _load_sqlalchemy()
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                select
                  n.nspname as schema_name,
                  p.proname as function_name,
                  pg_get_function_identity_arguments(p.oid) as identity_args,
                  pg_get_functiondef(p.oid) as function_def,
                  p.prosecdef as security_definer,
                  p.proconfig as proconfig
                from pg_proc p
                join pg_namespace n on n.oid = p.pronamespace
                where n.nspname = :schema
                  and p.proname = :function_name
                order by p.oid desc
                limit 1
                """
            ),
            {"schema": schema, "function_name": function_name},
        ).mappings().first()
    if row is None:
        return {"found": False, "schema": schema, "function_name": function_name}
    return {"found": True, **dict(row)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a Postgres function definition")
    parser.add_argument("--schema", default="public")
    parser.add_argument("--function", default="set_updated_at")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(get_function_status(args.schema, args.function), indent=2, ensure_ascii=False, default=str))
    except RuntimeError as exc:
        print(f"Function status not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
