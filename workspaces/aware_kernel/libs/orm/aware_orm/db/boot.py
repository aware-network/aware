"""Canonical ORM DB boot planner + adapter orchestrator.

Ownership split:
- Planning/discovery: this module (backend-agnostic)
- Execution semantics: backend adapters under `aware_orm.db.adapters.*`

Compatibility:
- Runtime callsites may import `aware_orm.runtime.db_boot` (thin re-export shim).
- Postgres marker helpers remain exported from this module for existing callers.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import re
from uuid import UUID

from aware_orm.db.adapters import DBBootAdapter, DBBootAdapterName, resolve_db_boot_adapter
from aware_orm.db.adapters.postgres import (
    ensure_db_bootstrap_marker_table as _ensure_db_bootstrap_marker_table_postgres,
)
from aware_orm.db.adapters.postgres import (
    fetch_db_bootstrap_marker as _fetch_db_bootstrap_marker_postgres,
)
from aware_orm.db.adapters.postgres import (
    upsert_db_bootstrap_marker as _upsert_db_bootstrap_marker_postgres,
)
from aware_orm.db.contracts import (
    DBBootConnection,
    DBBootExecutionError,
    DBBootPlanError,
    DBBootResult,
    DBBootstrapMarker,
    SQLBootPlan,
    SQLBootStep,
)
from aware_orm.db.schema_registry import (
    DBBackendTarget,
    DBPackageKind,
    DBSchemaRegistryError,
    compute_db_schema_registry_payload_hash,
    load_db_schema_registry,
    resolve_db_schema_registry_sql_roots,
)


_RE_CREATE_TYPE = re.compile(
    r"^\s*CREATE\s+TYPE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"?[a-zA-Z0-9_]+\"?\.)?\"?([a-zA-Z0-9_]+)\"?\s+",
    re.IGNORECASE | re.MULTILINE,
)
_RE_CREATE_TABLE = re.compile(
    r'^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?([a-zA-Z0-9_]+)\"?\s*\(',
    re.IGNORECASE | re.MULTILINE,
)
_RE_REFERENCES = re.compile(r"\bREFERENCES\s+\"?([a-zA-Z0-9_]+)\"?\s*\(", re.IGNORECASE)


def discover_sql_files(*, sql_root: Path) -> list[Path]:
    """Discover SQL files under supported bundle layouts."""
    if not sql_root.exists() or not sql_root.is_dir():
        raise DBBootPlanError(f"sql_root not found or not a directory: {sql_root}")

    out: list[Path] = []
    for sql_file in sorted(sql_root.rglob("*.sql"), key=lambda p: str(p)):
        rel = sql_file.relative_to(sql_root)
        if any(part.startswith("_") for part in rel.parts[:-1]):
            continue
        if len(rel.parts) < 2:
            raise DBBootPlanError(
                "SQL path must be `<schema>/<...>/<file>.sql` or "
                f"`<domain>/<schema>/<...>/<file>.sql`, got: {rel}"
            )
        out.append(sql_file)
    return out


def _schema_for_path(sql_root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(sql_root)
    except Exception as exc:  # pragma: no cover
        raise DBBootPlanError(f"SQL path is not under sql_root: {path}") from exc

    parts = rel.parts
    if len(parts) < 2:
        raise DBBootPlanError(
            "SQL path must be `<schema>/<...>/<file>.sql` or "
            f"`<domain>/<schema>/<...>/<file>.sql`, got: {rel}"
        )
    if len(parts) == 2:
        schema = parts[0]
    else:
        schema = parts[1]

    if schema in {"class_", "import_"}:
        return schema[:-1]
    return schema


def _created_type_names(sql_text: str) -> list[str]:
    return [m.group(1) for m in _RE_CREATE_TYPE.finditer(sql_text)]


def _created_table_names(sql_text: str) -> list[str]:
    return [m.group(1) for m in _RE_CREATE_TABLE.finditer(sql_text)]


def _referenced_table_names(sql_text: str) -> set[str]:
    return {m.group(1) for m in _RE_REFERENCES.finditer(sql_text)}


def _register_table_file(
    *,
    table_defs: dict[str, tuple[str, Path, set[str]]],
    table_files: list[tuple[str, str, Path]],
    schema: str,
    path: Path,
    table_names: list[str],
    referenced_table_names: set[str],
) -> None:
    if not table_names:
        return

    table_files.append((schema, min(table_names), path))
    for name in table_names:
        prev = table_defs.get(name)
        if prev is not None:
            prev_schema, prev_path, _prev_refs = prev
            raise DBBootPlanError(
                "Duplicate table name across schemas is ambiguous for unqualified REFERENCES: "
                f"table={name} seen_in=({prev_schema}, {prev_path}) and ({schema}, {path})"
            )
        table_defs[name] = (schema, path, referenced_table_names)


def build_sql_boot_plan(*, sql_root: Path) -> SQLBootPlan:
    """Build a deterministic schema install plan from one SQL root."""
    files = discover_sql_files(sql_root=sql_root)
    if not files:
        raise DBBootPlanError(f"No .sql files discovered under {sql_root}")

    schemas = sorted({_schema_for_path(sql_root, p) for p in files})

    type_defs: dict[str, tuple[str, Path]] = {}
    type_files: list[tuple[str, str, Path]] = []
    table_defs: dict[str, tuple[str, Path, set[str]]] = {}
    table_files: list[tuple[str, str, Path]] = []
    other: list[Path] = []

    for p in files:
        schema = _schema_for_path(sql_root, p)
        sql_text = p.read_text(encoding="utf-8")
        type_names = _created_type_names(sql_text)
        table_names = _created_table_names(sql_text)

        if type_names and table_names:
            raise DBBootPlanError(f"SQL file mixes CREATE TYPE and CREATE TABLE statements (unsupported): {p}")

        if type_names:
            type_files.append((schema, min(type_names), p))
            for name in type_names:
                prev = type_defs.get(name)
                if prev is not None:
                    prev_schema, prev_path = prev
                    raise DBBootPlanError(
                        "Duplicate type name across schemas is ambiguous for unqualified columns: "
                        f"type={name} seen_in=({prev_schema}, {prev_path}) and ({schema}, {p})"
                    )
                type_defs[name] = (schema, p)
            continue

        if table_names:
            _register_table_file(
                table_defs=table_defs,
                table_files=table_files,
                schema=schema,
                path=p,
                table_names=table_names,
                referenced_table_names=_referenced_table_names(sql_text),
            )
            continue

        other.append(p)

    steps: list[SQLBootStep] = []

    for schema, _min_name, path in sorted(type_files, key=lambda item: (item[0], item[1], str(item[2]))):
        steps.append(SQLBootStep(schema=schema, path=path, kind="type"))

    for schema, _min_name, path in sorted(table_files, key=lambda item: (item[0], item[1], str(item[2]))):
        steps.append(SQLBootStep(schema=schema, path=path, kind="table"))

    for p in sorted(other, key=lambda x: str(x)):
        steps.append(SQLBootStep(schema=_schema_for_path(sql_root, p), path=p, kind="other"))

    return SQLBootPlan(sql_roots=(sql_root,), schemas=tuple(schemas), steps=tuple(steps))


def build_sql_boot_plan_multi(*, sql_roots: Sequence[Path]) -> SQLBootPlan:
    """Build a deterministic schema install plan from multiple SQL roots."""
    if not sql_roots:
        raise DBBootPlanError("sql_roots must be non-empty")
    roots = tuple(Path(p).resolve() for p in sql_roots)

    files: list[tuple[Path, Path]] = []
    for root in roots:
        for f in discover_sql_files(sql_root=root):
            files.append((root, f))
    if not files:
        raise DBBootPlanError(f"No .sql files discovered under sql_roots={roots}")

    schemas = sorted({_schema_for_path(root, p) for root, p in files})

    type_defs: dict[str, tuple[str, Path]] = {}
    type_files: list[tuple[str, str, Path]] = []
    table_defs: dict[str, tuple[str, Path, set[str]]] = {}
    table_files: list[tuple[str, str, Path]] = []
    other: list[tuple[Path, Path]] = []

    for root, p in files:
        schema = _schema_for_path(root, p)
        sql_text = p.read_text(encoding="utf-8")
        type_names = _created_type_names(sql_text)
        table_names = _created_table_names(sql_text)

        if type_names and table_names:
            raise DBBootPlanError(f"SQL file mixes CREATE TYPE and CREATE TABLE statements (unsupported): {p}")

        if type_names:
            type_files.append((schema, min(type_names), p))
            for name in type_names:
                prev = type_defs.get(name)
                if prev is not None:
                    prev_schema, prev_path = prev
                    raise DBBootPlanError(
                        "Duplicate type name across schemas is ambiguous for unqualified columns: "
                        f"type={name} seen_in=({prev_schema}, {prev_path}) and ({schema}, {p})"
                    )
                type_defs[name] = (schema, p)
            continue

        if table_names:
            _register_table_file(
                table_defs=table_defs,
                table_files=table_files,
                schema=schema,
                path=p,
                table_names=table_names,
                referenced_table_names=_referenced_table_names(sql_text),
            )
            continue

        other.append((root, p))

    steps: list[SQLBootStep] = []

    for schema, _min_name, path in sorted(type_files, key=lambda item: (item[0], item[1], str(item[2]))):
        steps.append(SQLBootStep(schema=schema, path=path, kind="type"))

    for schema, _min_name, path in sorted(table_files, key=lambda item: (item[0], item[1], str(item[2]))):
        steps.append(SQLBootStep(schema=schema, path=path, kind="table"))

    for root, p in sorted(other, key=lambda x: str(x[1])):
        steps.append(SQLBootStep(schema=_schema_for_path(root, p), path=p, kind="other"))

    return SQLBootPlan(sql_roots=roots, schemas=tuple(schemas), steps=tuple(steps))


def build_sql_boot_plan_from_registry(
    *,
    registry_path: Path,
    environment_id: UUID,
    package_kind: DBPackageKind,
    backend_target: DBBackendTarget,
    require_non_empty_sql: bool = True,
) -> SQLBootPlan:
    """Build a deterministic boot plan from compiler-emitted registry entries."""
    try:
        sql_roots = resolve_db_schema_registry_sql_roots(
            registry_path=registry_path,
            environment_id=environment_id,
            package_kind=package_kind,
            backend_target=backend_target,
            require_non_empty_sql=require_non_empty_sql,
        )
    except DBSchemaRegistryError as exc:
        raise DBBootPlanError(
            "DB boot registry resolution failed: "
            f"registry_path={Path(registry_path).resolve()} "
            f"environment_id={environment_id} "
            f"package_kind={package_kind} backend_target={backend_target}: {exc}"
        ) from exc
    return build_sql_boot_plan_multi(sql_roots=sql_roots)


def build_local_plugin_sqlite_boot_plan_from_registry(
    *,
    registry_path: Path,
    environment_id: UUID,
    require_non_empty_sql: bool = True,
) -> SQLBootPlan:
    """Resolve local/plugin sqlite DB install plan from registry (`state` + `sqlite`)."""
    return build_sql_boot_plan_from_registry(
        registry_path=registry_path,
        environment_id=environment_id,
        package_kind="state",
        backend_target="sqlite",
        require_non_empty_sql=require_non_empty_sql,
    )


async def ensure_local_plugin_sqlite_schema_installed_from_registry(
    *,
    connection: object,
    registry_path: Path,
    environment_id: UUID,
    require_non_empty_sql: bool = True,
) -> DBBootResult:
    """Install local/plugin sqlite schema from compiler-emitted registry truth."""
    resolved_registry_path = Path(registry_path).resolve()
    registry = load_db_schema_registry(path=resolved_registry_path)
    plan = build_local_plugin_sqlite_boot_plan_from_registry(
        registry_path=resolved_registry_path,
        environment_id=environment_id,
        require_non_empty_sql=require_non_empty_sql,
    )
    return await resolve_db_boot_adapter("sqlite").ensure_schema_installed(
        connection=connection,
        plan=plan,
        environment_id=environment_id,
        ocg_hash=compute_db_schema_registry_payload_hash(registry=registry),
        ocg_head_commit_id=None,
    )


# Postgres marker helpers remain on the owner rail for compatibility.
async def ensure_db_bootstrap_marker_table(*, connection: DBBootConnection) -> None:
    await _ensure_db_bootstrap_marker_table_postgres(connection=connection)


async def fetch_db_bootstrap_marker(
    *,
    connection: DBBootConnection,
    environment_id: UUID,
) -> DBBootstrapMarker | None:
    return await _fetch_db_bootstrap_marker_postgres(connection=connection, environment_id=environment_id)


async def upsert_db_bootstrap_marker(
    *,
    connection: DBBootConnection,
    environment_id: UUID,
    ocg_hash: str,
    ocg_head_commit_id: UUID | None,
) -> None:
    await _upsert_db_bootstrap_marker_postgres(
        connection=connection,
        environment_id=environment_id,
        ocg_hash=ocg_hash,
        ocg_head_commit_id=ocg_head_commit_id,
    )


async def ensure_db_schema_installed(
    *,
    connection: object,
    sql_root: Path,
    environment_id: UUID,
    ocg_hash: str,
    ocg_head_commit_id: UUID | None = None,
    adapter: DBBootAdapterName | DBBootAdapter | None = None,
) -> DBBootResult:
    return await ensure_db_schema_installed_multi(
        connection=connection,
        sql_roots=(sql_root,),
        environment_id=environment_id,
        ocg_hash=ocg_hash,
        ocg_head_commit_id=ocg_head_commit_id,
        adapter=adapter,
    )


async def ensure_db_schema_installed_multi(
    *,
    connection: object,
    sql_roots: Sequence[Path],
    environment_id: UUID,
    ocg_hash: str,
    ocg_head_commit_id: UUID | None = None,
    adapter: DBBootAdapterName | DBBootAdapter | None = None,
) -> DBBootResult:
    """Ensure schema install using explicit backend adapter execution."""
    if not sql_roots:
        raise DBBootExecutionError("sql_roots must be non-empty")

    plan = build_sql_boot_plan_multi(sql_roots=sql_roots)
    resolved = resolve_db_boot_adapter(adapter)
    return await resolved.ensure_schema_installed(
        connection=connection,
        plan=plan,
        environment_id=environment_id,
        ocg_hash=ocg_hash,
        ocg_head_commit_id=ocg_head_commit_id,
    )


__all__ = [
    "DBBootAdapter",
    "DBBootAdapterName",
    "DBBootConnection",
    "DBBootExecutionError",
    "DBBootPlanError",
    "DBBootResult",
    "DBBootstrapMarker",
    "SQLBootPlan",
    "SQLBootStep",
    "build_local_plugin_sqlite_boot_plan_from_registry",
    "build_sql_boot_plan",
    "build_sql_boot_plan_from_registry",
    "build_sql_boot_plan_multi",
    "discover_sql_files",
    "ensure_db_bootstrap_marker_table",
    "ensure_db_schema_installed",
    "ensure_db_schema_installed_multi",
    "ensure_local_plugin_sqlite_schema_installed_from_registry",
    "fetch_db_bootstrap_marker",
    "upsert_db_bootstrap_marker",
    "resolve_db_boot_adapter",
]
