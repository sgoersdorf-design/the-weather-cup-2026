"""Report row-level security coverage for public tables."""

from __future__ import annotations

import json

from python.db import get_engine


def _load_sqlalchemy():
    try:
        from sqlalchemy import text
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SQLAlchemy missing. Run: pip install -r requirements.txt") from exc
    return text


def get_db_rls_status() -> dict[str, object]:
    text = _load_sqlalchemy()
    engine = get_engine()
    with engine.connect() as conn:
        table_rows = conn.execute(
            text(
                """
                select
                  c.relname as table_name,
                  c.relrowsecurity as rls_enabled,
                  c.relforcerowsecurity as rls_forced,
                  coalesce(
                    (
                      select json_agg(json_build_object(
                        'policy_name', p.policyname,
                        'command', p.cmd,
                        'roles', p.roles,
                        'qual', p.qual,
                        'with_check', p.with_check
                      ) order by p.policyname)
                      from pg_policies p
                      where p.schemaname = 'public'
                        and p.tablename = c.relname
                    ),
                    '[]'::json
                  ) as policies
                from pg_class c
                join pg_namespace n on n.oid = c.relnamespace
                where n.nspname = 'public'
                  and c.relkind = 'r'
                order by c.relname
                """
            )
        ).mappings()

    tables = [dict(row) for row in table_rows]
    open_tables = [row["table_name"] for row in tables if not row["rls_enabled"]]
    unforced_tables = [row["table_name"] for row in tables if not row["rls_forced"]]
    public_read_tables = [
        row["table_name"]
        for row in tables
        if any(policy.get("command") == "SELECT" for policy in row["policies"])
    ]
    return {
        "tables": tables,
        "summary": {
            "table_count": len(tables),
            "tables_without_rls": open_tables,
            "tables_without_forced_rls": unforced_tables,
            "public_select_policy_tables": public_read_tables,
        },
    }


def main() -> int:
    try:
        print(json.dumps(get_db_rls_status(), indent=2, ensure_ascii=False, default=str))
    except RuntimeError as exc:
        print(f"RLS status not completed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
