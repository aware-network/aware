"""Postgres DDL render helpers for commit-keyed migrations.

Owned by: `languages/sql/grammar` (dialect + SQL surface area).

Notes:
- These helpers intentionally accept only primitive inputs (strings/iterables) so they can be
  reused by compiler rails without importing compiler-specific schema IR types.
"""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
from uuid import UUID


def quote_ident(name: str) -> str:
    """Quote an identifier with double quotes and escape embedded quotes.

    This is the conservative choice for migration DDL because identifiers may collide with
    reserved words, casing, or require stable behavior across environments.
    """
    if not name:
        raise ValueError("Empty identifier")
    return '"' + name.replace('"', '""') + '"'


def escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


def stable_index_name(*, table_name: str, view_id: UUID, prefix: str = "idx") -> str:
    """Deterministic index name within Postgres identifier limits (63 bytes)."""
    suffix = view_id.hex[:12]
    return stable_index_name_with_suffix(
        table_name=table_name,
        suffix=suffix,
        prefix=prefix,
    )


def stable_index_name_for_storage(
    *,
    table_name: str,
    column_names: Iterable[str],
    unique: bool = False,
    annotation_name: str | None = None,
    prefix: str = "idx",
) -> str:
    """Deterministic storage index name from semantic physical identity."""
    clean_columns = tuple(column.strip() for column in column_names if column.strip())
    if not clean_columns:
        raise ValueError("stable_index_name_for_storage requires at least one column")
    clean_annotation_name = (annotation_name or "").strip()
    label = table_name
    if clean_annotation_name:
        label = f"{table_name}_{clean_annotation_name}"
    digest_key = "\x1f".join(
        (
            table_name,
            "unique" if unique else "index",
            clean_annotation_name,
            *clean_columns,
        )
    )
    suffix = sha256(digest_key.encode("utf-8")).hexdigest()[:12]
    return stable_index_name_with_suffix(
        table_name=label,
        suffix=suffix,
        prefix=prefix,
    )


def stable_index_name_with_suffix(*, table_name: str, suffix: str, prefix: str = "idx") -> str:
    """Deterministic index name within Postgres identifier limits (63 bytes)."""
    clean_suffix = (suffix or "").strip()
    if not clean_suffix:
        raise ValueError("stable_index_name_with_suffix requires a suffix")
    prefix_str = (prefix or "idx").strip("_") + "_"
    # Reserve: prefix + "_" + suffix
    max_table_len = 63 - len(prefix_str) - 1 - len(clean_suffix)
    table_part = (table_name or "t")[: max_table_len if max_table_len > 0 else 1]
    return f"{prefix_str}{table_part}_{clean_suffix}"


def render_create_enum_type(*, type_name: str, values: Iterable[str]) -> str:
    opts = ", ".join("'" + escape_sql_literal(v) + "'" for v in values)
    return f"CREATE TYPE {quote_ident(type_name)} AS ENUM ({opts});"


def render_alter_enum_add_value(
    *,
    type_name: str,
    value: str,
    before: str | None = None,
    after: str | None = None,
) -> str:
    if before is not None and after is not None:
        raise ValueError("render_alter_enum_add_value requires at most one of before/after")

    stmt = f"ALTER TYPE {quote_ident(type_name)} ADD VALUE '{escape_sql_literal(value)}'"
    if before is not None:
        stmt += f" BEFORE '{escape_sql_literal(before)}'"
    elif after is not None:
        stmt += f" AFTER '{escape_sql_literal(after)}'"
    return stmt + ";"


def render_create_table(*, table_name: str, column_defs: Iterable[str], primary_key_cols: Iterable[str]) -> str:
    cols = list(column_defs)
    pk = ", ".join(quote_ident(c) for c in primary_key_cols)
    cols.append(f"PRIMARY KEY ({pk})")
    body = ",\n  ".join(cols)
    return f"CREATE TABLE {quote_ident(table_name)} (\n  {body}\n);"


def render_add_column(*, table_name: str, column_name: str, sql_type: str) -> str:
    return f"ALTER TABLE {quote_ident(table_name)} ADD COLUMN {quote_ident(column_name)} {sql_type};"


def render_drop_column(*, table_name: str, column_name: str) -> str:
    return f"ALTER TABLE {quote_ident(table_name)} DROP COLUMN IF EXISTS {quote_ident(column_name)};"


def render_drop_not_null(*, table_name: str, column_name: str) -> str:
    """Render a statement that relaxes column nullability to optional."""
    return "ALTER TABLE " f"{quote_ident(table_name)} ALTER COLUMN {quote_ident(column_name)} DROP NOT NULL;"


def render_add_not_null_column_if_table_empty(*, table_name: str, column_name: str, sql_type: str) -> str:
    """Add a NOT NULL column only when the target table is empty.

    This keeps additive migrations safe for fresh/sparse environments while still failing fast
    when a data backfill is required.
    """
    table_q = quote_ident(table_name)
    column_q = quote_ident(column_name)
    alter_stmt = (f"ALTER TABLE {table_q} ADD COLUMN {column_q} {sql_type} NOT NULL;").replace("'", "''")
    message = escape_sql_literal(
        f"cannot add NOT NULL column without backfill/default on non-empty table: {table_name}.{column_name}"
    )
    return "\n".join(
        [
            "DO $$",
            "BEGIN",
            f"  IF EXISTS (SELECT 1 FROM {table_q} LIMIT 1) THEN",
            f"    RAISE EXCEPTION '{message}';",
            "  END IF;",
            f"  EXECUTE '{alter_stmt}';",
            "END;",
            "$$;",
            "",
        ]
    )


def render_add_unique(*, table_name: str, column_name: str) -> str:
    return f"ALTER TABLE {quote_ident(table_name)} ADD UNIQUE ({quote_ident(column_name)});"


def render_add_foreign_key(
    *,
    table_name: str,
    column_name: str,
    target_table: str,
    scope_cols: tuple[str, str] = ("branch_id", "projection_hash"),
    target_pk: str = "id",
) -> str:
    scope = ", ".join(quote_ident(c) for c in scope_cols)
    return " ".join(
        [
            f"ALTER TABLE {quote_ident(table_name)} ADD FOREIGN KEY (",
            f"{scope}, {quote_ident(column_name)}",
            ") REFERENCES",
            f"{quote_ident(target_table)}({scope}, {quote_ident(target_pk)});",
        ]
    )


def render_create_index(*, index_name: str, table_name: str, column_names: Iterable[str]) -> str:
    cols = ", ".join(quote_ident(c) for c in column_names)
    return f"CREATE INDEX {quote_ident(index_name)} ON {quote_ident(table_name)} ({cols});"


def render_failfast_sql(*, reasons: Iterable[str], commit_id: UUID | None = None) -> str:
    """Return a Postgres migration script that fails with a clear reason."""
    reason_lines = [r.strip() for r in reasons if (r or "").strip()]
    message = " | ".join(reason_lines) or "unsupported schema change"
    prefix = f"commit_id={commit_id} " if commit_id is not None else ""
    msg = (prefix + message)[:900]
    escaped = msg.replace("'", "''")
    return "\n".join(
        [
            "DO $$",
            "BEGIN",
            f"  RAISE EXCEPTION '{escaped}';",
            "END;",
            "$$;",
            "",
        ]
    )


__all__ = [
    "escape_sql_literal",
    "quote_ident",
    "stable_index_name",
    "stable_index_name_for_storage",
    "stable_index_name_with_suffix",
    "render_add_column",
    "render_drop_column",
    "render_add_not_null_column_if_table_empty",
    "render_add_foreign_key",
    "render_add_unique",
    "render_alter_enum_add_value",
    "render_create_index",
    "render_create_enum_type",
    "render_create_table",
    "render_drop_not_null",
    "render_failfast_sql",
]
