"""Postgres DB boot adapter rail.

Owns postgres-specific install semantics:
- schema creation/search_path handling
- FK deferral via table rewrite
- bootstrap marker table semantics
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha1
import re
from typing import cast
from uuid import UUID

from aware_orm.db.contracts import (
    DBBootConnection,
    DBBootExecutionError,
    DBBootResult,
    DBBootstrapMarker,
    SQLBootPlan,
    SQLBootStep,
)

from ..base import DBBootAdapterName


_RE_CREATE_TYPE = re.compile(
    r"^\s*CREATE\s+TYPE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"?[a-zA-Z0-9_]+\"?\.)?\"?([a-zA-Z0-9_]+)\"?\s+",
    re.IGNORECASE | re.MULTILINE,
)
_RE_CREATE_TABLE = re.compile(
    r'^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?([a-zA-Z0-9_]+)\"?\s*\(',
    re.IGNORECASE | re.MULTILINE,
)
_RE_INLINE_REFERENCE = re.compile(
    r"\bREFERENCES\s+\"?([a-zA-Z0-9_]+)\"?\s*\(\s*\"?([a-zA-Z0-9_]+)\"?\s*\)",
    re.IGNORECASE,
)
_RE_TABLE_FK_REFERENCE = re.compile(
    r"\bFOREIGN\s+KEY\s*\(\s*([^)]+?)\s*\)\s+REFERENCES\s+"
    r"(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE,
)
_RE_COLUMN_NAME = re.compile(r'^\s*\"?([a-zA-Z0-9_]+)\"?\s+')
_RE_PRIMARY_KEY = re.compile(r"\bPRIMARY\s+KEY\s*\(\s*([^)]+?)\s*\)", re.IGNORECASE | re.DOTALL)

_RUNTIME_IDENTITY_COLUMNS = ("branch_id", "projection_hash", "id")
_POSTGRES_MAX_IDENTIFIER_BYTES = 63

_MARKER_TABLE_FQN = "public.aware_bootstrap_marker"
_MARKER_TABLE_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS {_MARKER_TABLE_FQN} (
  environment_id UUID PRIMARY KEY NOT NULL,
  ocg_hash TEXT NOT NULL,
  ocg_head_commit_id UUID,
  installed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip()

_MARKER_TABLE_ALTER_SQL = f"""
ALTER TABLE {_MARKER_TABLE_FQN}
  ADD COLUMN IF NOT EXISTS ocg_head_commit_id UUID;
""".strip()


def _parse_uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value)
        except Exception:
            return None
    return None


async def ensure_db_bootstrap_marker_table(*, connection: DBBootConnection) -> None:
    _ = await connection.execute(_MARKER_TABLE_CREATE_SQL)
    _ = await connection.execute(_MARKER_TABLE_ALTER_SQL)


async def fetch_db_bootstrap_marker(
    *,
    connection: DBBootConnection,
    environment_id: UUID,
) -> DBBootstrapMarker | None:
    row = await connection.fetchrow(
        f"SELECT ocg_hash, ocg_head_commit_id FROM {_MARKER_TABLE_FQN} WHERE environment_id=$1",
        environment_id,
    )
    if row is None:
        return None
    ocg_hash = row.get("ocg_hash")
    if not isinstance(ocg_hash, str) or not ocg_hash.strip():
        return None
    return DBBootstrapMarker(
        environment_id=environment_id,
        ocg_hash=ocg_hash,
        ocg_head_commit_id=_parse_uuid_or_none(row.get("ocg_head_commit_id")),
    )


async def upsert_db_bootstrap_marker(
    *,
    connection: DBBootConnection,
    environment_id: UUID,
    ocg_hash: str,
    ocg_head_commit_id: UUID | None,
) -> None:
    _ = await connection.execute(
        f"""
INSERT INTO {_MARKER_TABLE_FQN} (environment_id, ocg_hash, ocg_head_commit_id)
VALUES ($1, $2, $3)
ON CONFLICT (environment_id) DO UPDATE SET
  ocg_hash=EXCLUDED.ocg_hash,
  ocg_head_commit_id=EXCLUDED.ocg_head_commit_id,
  installed_at=NOW();
""".strip(),
        environment_id,
        ocg_hash,
        ocg_head_commit_id,
    )


def _quote_ident(name: str) -> str:
    if not name:
        raise DBBootExecutionError("Empty identifier is not allowed")
    return '"' + name.replace('"', '""') + '"'


def _postgres_stored_identifier_name(name: str) -> str:
    raw = _normalize_ident(name)
    encoded = raw.encode("utf-8")
    if len(encoded) <= _POSTGRES_MAX_IDENTIFIER_BYTES:
        return raw
    return encoded[:_POSTGRES_MAX_IDENTIFIER_BYTES].decode("utf-8", errors="ignore")


def _search_path_for_step(*, step_schema: str, all_schemas: Sequence[str]) -> str:
    ordered = [step_schema, *[s for s in all_schemas if s != step_schema], "public"]
    return ", ".join(_quote_ident(s) for s in ordered)


def _created_type_names(sql_text: str) -> list[str]:
    return [m.group(1) for m in _RE_CREATE_TYPE.finditer(sql_text)]


def _created_table_names(sql_text: str) -> list[str]:
    return [m.group(1) for m in _RE_CREATE_TABLE.finditer(sql_text)]


def _created_column_names(sql_text: str) -> set[str]:
    column_names: set[str] = set()
    for line in sql_text.splitlines():
        col_match = _RE_COLUMN_NAME.match(line)
        if not col_match:
            continue
        column_names.add(_normalize_ident(col_match.group(1)))
    return column_names


def _normalize_ident(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        raw = raw[1:-1]
    return raw.strip()


def _normalized_ident_list(raw: str) -> tuple[str, ...]:
    return tuple(_normalize_ident(part) for part in raw.split(",") if _normalize_ident(part))


def _primary_key_columns(sql_text: str) -> tuple[str, ...] | None:
    match = _RE_PRIMARY_KEY.search(sql_text)
    if match is None:
        return None
    columns = _normalized_ident_list(match.group(1))
    return columns or None


def _needs_runtime_identity_unique_index(sql_text: str) -> bool:
    column_names = _created_column_names(sql_text)
    if not all(column in column_names for column in _RUNTIME_IDENTITY_COLUMNS):
        return False
    return _primary_key_columns(sql_text) != _RUNTIME_IDENTITY_COLUMNS


def _runtime_identity_unique_index_sql(*, schema: str, table_name: str) -> str:
    digest = sha1(f"{schema}.{table_name}".encode("utf-8")).hexdigest()[:16]
    index_name = f"aware_oid_{digest}"
    columns = ", ".join(_quote_ident(column) for column in _RUNTIME_IDENTITY_COLUMNS)
    return (
        f"CREATE UNIQUE INDEX IF NOT EXISTS {_quote_ident(index_name)} "
        f"ON {_quote_ident(schema)}.{_quote_ident(table_name)} ({columns});"
    )


def _strip_trailing_comma_before_close(lines: list[str]) -> None:
    create_idx = None
    close_idx = None
    for idx, line in enumerate(lines):
        if create_idx is None and _RE_CREATE_TABLE.search(line):
            create_idx = idx
            continue
        if create_idx is None:
            continue
        stripped = line.strip()
        if stripped.startswith(");") or stripped == ")":
            close_idx = idx
            break

    search_end = close_idx if close_idx is not None else len(lines)
    search_start = create_idx if create_idx is not None else 0

    for idx in range(search_end - 1, search_start - 1, -1):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.startswith(");") or stripped == ")":
            continue
        line = lines[idx]
        newline = ""
        body = line
        if body.endswith("\r\n"):
            newline = "\r\n"
            body = body[:-2]
        elif body.endswith("\n"):
            newline = "\n"
            body = body[:-1]
        body = re.sub(r",\s*$", "", body)
        lines[idx] = body + newline
        break


def _split_type_token(token: str) -> tuple[str, str]:
    if token.endswith("[]"):
        return token[:-2], "[]"
    if "(" in token:
        base, rest = token.split("(", 1)
        return base, "(" + rest
    return token, ""


def _qualify_custom_types_in_create_table_sql(
    sql_text: str,
    *,
    type_schema_by_name: Mapping[str, str],
) -> str:
    if not type_schema_by_name:
        return sql_text

    create_match = _RE_CREATE_TABLE.search(sql_text)
    if not create_match:
        return sql_text

    lines = sql_text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("--"):
            continue
        if _RE_CREATE_TABLE.search(line):
            continue
        if stripped.startswith(")"):
            continue

        col_match = _RE_COLUMN_NAME.match(line)
        if not col_match:
            continue

        rest = line[col_match.end():]
        rest_stripped = rest.lstrip()
        if not rest_stripped:
            continue

        token = rest_stripped.split(None, 1)[0]
        if "." in token:
            continue

        base_token, suffix = _split_type_token(token)
        base = base_token
        if base.startswith('"') and base.endswith('"'):
            base = base[1:-1]
        schema = type_schema_by_name.get(base)
        if not schema:
            continue

        qualified = f"{_quote_ident(schema)}.{_quote_ident(base)}{suffix}"
        leading_ws = rest[: len(rest) - len(rest_stripped)]
        after_token = rest_stripped[len(token):]
        lines[idx] = line[:col_match.end()] + leading_ws + qualified + after_token

    return "".join(lines)


def _strip_inline_foreign_keys_from_create_table_sql(
    sql_text: str,
    *,
    source_schema: str,
    table_schema_by_name: Mapping[str, str],
) -> tuple[str, list[str]]:
    create_match = _RE_CREATE_TABLE.search(sql_text)
    if not create_match:
        return sql_text, []

    table_name = create_match.group(1)
    source_fqn = f"{_quote_ident(source_schema)}.{_quote_ident(table_name)}"

    fk_statements: list[str] = []
    removed_any = False

    lines = sql_text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        fk_match = _RE_TABLE_FK_REFERENCE.search(line)
        if fk_match:
            fk_cols_raw = fk_match.group(1)
            ref_schema_raw = fk_match.group(2)
            ref_table_raw = fk_match.group(3)
            ref_cols_raw = fk_match.group(4)

            fk_cols = [_normalize_ident(c) for c in fk_cols_raw.split(",") if _normalize_ident(c)]
            ref_cols = [_normalize_ident(c) for c in ref_cols_raw.split(",") if _normalize_ident(c)]
            if not fk_cols or not ref_cols:
                raise DBBootExecutionError(
                    f"Invalid FOREIGN KEY constraint columns (table={table_name} line={line.strip()!r})"
                )
            if len(fk_cols) != len(ref_cols):
                raise DBBootExecutionError(
                    "FOREIGN KEY column count mismatch while stripping FK constraints "
                    f"(table={table_name} fk_cols={fk_cols} ref={ref_table_raw} ref_cols={ref_cols})"
                )

            ref_table = _normalize_ident(ref_table_raw)
            if not ref_table:
                raise DBBootExecutionError(
                    f"Invalid referenced table name while stripping FK constraints (table={table_name})"
                )

            if ref_schema_raw is not None:
                ref_schema = _normalize_ident(ref_schema_raw)
            else:
                ref_schema = table_schema_by_name.get(ref_table)
            if not ref_schema:
                raise DBBootExecutionError(
                    "Failed to resolve referenced table schema while stripping FK constraints "
                    f"(table={table_name} references={ref_table})"
                )

            ref_fqn = f"{_quote_ident(ref_schema)}.{_quote_ident(ref_table)}"
            fk_statements.append(
                "ALTER TABLE "
                f"{source_fqn} "
                "ADD FOREIGN KEY "
                f"({', '.join(_quote_ident(c) for c in fk_cols)}) "
                f"REFERENCES {ref_fqn} ({', '.join(_quote_ident(c) for c in ref_cols)});"
            )

            lines[idx] = ""
            removed_any = True
            continue

        ref_match = _RE_INLINE_REFERENCE.search(line)
        if not ref_match:
            continue

        col_match = _RE_COLUMN_NAME.match(line)
        if not col_match:
            continue

        column_name = col_match.group(1)
        ref_table = ref_match.group(1)
        ref_column = ref_match.group(2)
        ref_schema = table_schema_by_name.get(ref_table)
        if not ref_schema:
            raise DBBootExecutionError(
                "Failed to resolve referenced table schema while stripping inline FK "
                f"(table={table_name} column={column_name} references={ref_table}({ref_column}))"
            )

        ref_fqn = f"{_quote_ident(ref_schema)}.{_quote_ident(ref_table)}"
        fk_statements.append(
            "ALTER TABLE "
            f"{source_fqn} "
            "ADD FOREIGN KEY "
            f"({_quote_ident(column_name)}) "
            f"REFERENCES {ref_fqn} ({_quote_ident(ref_column)});"
        )

        lines[idx] = _RE_INLINE_REFERENCE.sub("", line)
        removed_any = True

    if removed_any:
        _strip_trailing_comma_before_close(lines)

    return "".join(lines), fk_statements


def _split_generated_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql_text.splitlines(keepends=True):
        current.append(line)
        if line.strip().endswith(";"):
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
    remainder = "".join(current).strip()
    if remainder:
        statements.append(remainder)
    return statements


def _rewrite_create_table_statements(
    sql_text: str,
    *,
    source_schema: str,
    type_schema_by_name: Mapping[str, str],
    table_schema_by_name: Mapping[str, str],
) -> tuple[str, list[str], list[str]]:
    statements = _split_generated_sql_statements(sql_text)
    if not statements:
        return sql_text, [], []

    rewritten: list[str] = []
    fk_statements: list[str] = []
    identity_index_statements: list[str] = []
    for statement in statements:
        if not _RE_CREATE_TABLE.search(statement):
            rewritten.append(statement)
            continue

        statement = _qualify_custom_types_in_create_table_sql(
            statement,
            type_schema_by_name=type_schema_by_name,
        )
        statement, extracted = _strip_inline_foreign_keys_from_create_table_sql(
            statement,
            source_schema=source_schema,
            table_schema_by_name=table_schema_by_name,
        )
        rewritten.append(statement)
        fk_statements.extend(extracted)
        if _needs_runtime_identity_unique_index(statement):
            table_names = _created_table_names(statement)
            if len(table_names) != 1:
                raise DBBootExecutionError(
                    f"Expected one CREATE TABLE statement while creating runtime identity index, got: {table_names}"
                )
            identity_index_statements.append(
                _runtime_identity_unique_index_sql(schema=source_schema, table_name=table_names[0])
            )

    return "\n\n".join(rewritten) + ("\n" if sql_text.endswith("\n") else ""), fk_statements, identity_index_statements


def _is_effective_sql_empty(sql_text: str) -> bool:
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        return False
    return True


def _is_postgres_boot_connection(connection: object) -> bool:
    # Structural check only; do not use isinstance against a non-runtime-checkable protocol.
    return all(callable(getattr(connection, attr, None)) for attr in ("transaction", "execute", "fetchrow"))


async def _pg_type_exists(
    *,
    connection: DBBootConnection,
    schema: str,
    name: str,
) -> bool:
    stored_name = _postgres_stored_identifier_name(name)
    row = await connection.fetchrow(
        """
SELECT 1
FROM pg_type t
JOIN pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname::text=$1::text AND t.typname::text=$2::text
LIMIT 1
""".strip(),
        schema,
        stored_name,
    )
    return row is not None


async def _pg_table_exists(
    *,
    connection: DBBootConnection,
    schema: str,
    name: str,
) -> bool:
    stored_name = _postgres_stored_identifier_name(name)
    row = await connection.fetchrow(
        """
SELECT 1
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname::text=$1::text
  AND c.relname::text=$2::text
  AND c.relkind IN ('r', 'p')
LIMIT 1
""".strip(),
        schema,
        stored_name,
    )
    return row is not None


async def _missing_steps_for_same_hash_marker(
    *,
    connection: DBBootConnection,
    plan: SQLBootPlan,
) -> tuple[SQLBootStep, ...]:
    missing_steps: list[SQLBootStep] = []
    for step in plan.steps:
        sql_text = step.path.read_text(encoding="utf-8")
        if _is_effective_sql_empty(sql_text):
            continue

        if step.kind == "type":
            type_names = _created_type_names(sql_text)
            if not type_names:
                raise DBBootExecutionError(
                    f"Failed to parse type names for marker reconciliation: {step.path}"
                )
            existing = [
                await _pg_type_exists(connection=connection, schema=step.schema, name=name)
                for name in type_names
            ]
            if all(existing):
                continue
            if any(existing):
                raise DBBootExecutionError(
                    "DB bootstrap marker matched but SQL type file is partially installed; "
                    f"cannot safely reconcile file={step.path}"
                )
            missing_steps.append(step)
            continue

        if step.kind == "table":
            table_names = _created_table_names(sql_text)
            if not table_names:
                raise DBBootExecutionError(
                    f"Failed to parse table names for marker reconciliation: {step.path}"
                )
            existing = [
                await _pg_table_exists(connection=connection, schema=step.schema, name=name)
                for name in table_names
            ]
            if all(existing):
                continue
            if any(existing):
                raise DBBootExecutionError(
                    "DB bootstrap marker matched but SQL table file is partially installed; "
                    f"cannot safely reconcile file={step.path}"
                )
            missing_steps.append(step)
            continue

        # Other DDL files do not have a stable object identity in the generated
        # SQL contract, so a same-hash marker treats them as already applied.
    return tuple(missing_steps)


def _type_schema_by_name_from_plan(*, plan: SQLBootPlan) -> dict[str, str]:
    type_schema_by_name: dict[str, str] = {}
    for step in plan.steps:
        if step.kind != "type":
            continue
        sql_text = step.path.read_text(encoding="utf-8")
        type_names = _created_type_names(sql_text)
        if not type_names:
            raise DBBootExecutionError(f"Failed to parse type names for qualification: {step.path}")
        for name in type_names:
            prev = type_schema_by_name.get(name)
            if prev is not None and prev != step.schema:
                raise DBBootExecutionError(
                    "Duplicate type name across schemas is ambiguous for unqualified columns: "
                    f"type={name} seen_in=({prev}) and ({step.schema})"
                )
            type_schema_by_name[name] = step.schema
    return type_schema_by_name


def _table_schema_by_name_from_plan(*, plan: SQLBootPlan) -> dict[str, str]:
    table_schema_by_name: dict[str, str] = {}
    for step in plan.steps:
        if step.kind != "table":
            continue
        sql_text = step.path.read_text(encoding="utf-8")
        table_names = _created_table_names(sql_text)
        if not table_names:
            raise DBBootExecutionError(f"Failed to parse table name for FK install: {step.path}")
        for table_name in table_names:
            table_schema_by_name[table_name] = step.schema
    return table_schema_by_name


async def _apply_plan_steps(
    *,
    connection: DBBootConnection,
    plan: SQLBootPlan,
    steps: Sequence[SQLBootStep],
    environment_id: UUID,
    ocg_hash: str,
    ocg_head_commit_id: UUID | None,
    type_schema_by_name: Mapping[str, str],
    table_schema_by_name: Mapping[str, str],
) -> None:
    all_schemas = plan.schemas
    async with connection.transaction():
        for schema in all_schemas:
            _ = await connection.execute(f"CREATE SCHEMA IF NOT EXISTS {_quote_ident(schema)};")

        fk_statements: list[str] = []
        identity_index_statements: list[str] = []

        for step in steps:
            sql_text = step.path.read_text(encoding="utf-8")
            if _is_effective_sql_empty(sql_text):
                continue

            search_path = _search_path_for_step(step_schema=step.schema, all_schemas=all_schemas)
            _ = await connection.execute(f"SET LOCAL search_path TO {search_path};")
            if step.kind == "table":
                try:
                    sql_text, extracted, identity_indexes = _rewrite_create_table_statements(
                        sql_text,
                        source_schema=step.schema,
                        type_schema_by_name=type_schema_by_name,
                        table_schema_by_name=table_schema_by_name,
                    )
                except DBBootExecutionError as exc:
                    raise DBBootExecutionError(f"{exc} file={step.path}") from exc
                fk_statements.extend(extracted)
                identity_index_statements.extend(identity_indexes)
            try:
                _ = await connection.execute(sql_text)
            except Exception as exc:  # pragma: no cover - depends on DB backend
                raise DBBootExecutionError(
                    f"Failed to execute DDL step (kind={step.kind} schema={step.schema} file={step.path}): {exc}"
                ) from exc

        for stmt in identity_index_statements:
            try:
                _ = await connection.execute(stmt)
            except Exception as exc:  # pragma: no cover - depends on DB backend
                raise DBBootExecutionError(
                    f"Failed to create runtime identity unique index: {exc} sql={stmt}"
                ) from exc

        for stmt in fk_statements:
            try:
                _ = await connection.execute(stmt)
            except Exception as exc:  # pragma: no cover - depends on DB backend
                raise DBBootExecutionError(f"Failed to execute FK statement: {exc} sql={stmt}") from exc

        await upsert_db_bootstrap_marker(
            connection=connection,
            environment_id=environment_id,
            ocg_hash=ocg_hash,
            ocg_head_commit_id=ocg_head_commit_id,
        )


@dataclass(frozen=True, slots=True)
class PostgresDBBootAdapter:
    """Postgres DB install execution adapter."""

    name: DBBootAdapterName = "postgres"

    async def ensure_schema_installed(
        self,
        *,
        connection: object,
        plan: SQLBootPlan,
        environment_id: UUID,
        ocg_hash: str,
        ocg_head_commit_id: UUID | None = None,
    ) -> DBBootResult:
        if not _is_postgres_boot_connection(connection):
            raise DBBootExecutionError(
                "Postgres DB boot adapter requires connection implementing transaction/execute/fetchrow"
            )
        if not plan.sql_roots:
            raise DBBootExecutionError("sql_roots must be non-empty")

        pg_connection = cast(DBBootConnection, connection)
        await ensure_db_bootstrap_marker_table(connection=pg_connection)
        marker = await fetch_db_bootstrap_marker(connection=pg_connection, environment_id=environment_id)
        type_schema_by_name = _type_schema_by_name_from_plan(plan=plan)
        table_schema_by_name = _table_schema_by_name_from_plan(plan=plan)

        if marker is not None and marker.ocg_hash != ocg_hash:
            raise DBBootExecutionError(
                "DB already bootstrapped with a different ocg_hash; migrations are not implemented. "
                f"environment_id={environment_id} existing_ocg_hash={marker.ocg_hash} requested_ocg_hash={ocg_hash}"
            )

        steps_to_apply: Sequence[SQLBootStep]
        marker_head_commit_id = marker.ocg_head_commit_id if marker is not None else None
        if marker is not None:
            steps_to_apply = await _missing_steps_for_same_hash_marker(
                connection=pg_connection,
                plan=plan,
            )
            if not steps_to_apply:
                return DBBootResult(
                    installed=False,
                    environment_id=environment_id,
                    ocg_hash=ocg_hash,
                    ocg_head_commit_id=marker_head_commit_id,
                    sql_roots=plan.sql_roots,
                    schema_count=0,
                    step_count=0,
                )
        else:
            steps_to_apply = plan.steps

        await _apply_plan_steps(
            connection=pg_connection,
            plan=plan,
            steps=steps_to_apply,
            environment_id=environment_id,
            ocg_hash=ocg_hash,
            ocg_head_commit_id=ocg_head_commit_id or marker_head_commit_id,
            type_schema_by_name=type_schema_by_name,
            table_schema_by_name=table_schema_by_name,
        )

        return DBBootResult(
            installed=True,
            environment_id=environment_id,
            ocg_hash=ocg_hash,
            ocg_head_commit_id=ocg_head_commit_id or marker_head_commit_id,
            sql_roots=plan.sql_roots,
            schema_count=len(plan.schemas),
            step_count=len(steps_to_apply),
        )


POSTGRES_DB_BOOT_ADAPTER = PostgresDBBootAdapter()


__all__ = [
    "POSTGRES_DB_BOOT_ADAPTER",
    "PostgresDBBootAdapter",
    "ensure_db_bootstrap_marker_table",
    "fetch_db_bootstrap_marker",
    "upsert_db_bootstrap_marker",
]
