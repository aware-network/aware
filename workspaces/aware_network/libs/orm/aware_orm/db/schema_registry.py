"""Canonical DB schema-registry contract and resolution helpers.

The registry is compiler-emitted metadata consumed by runtime/local installers to
resolve SQL roots without host-side filesystem guessing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Sequence
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError


DBBackendTarget = Literal["postgres", "sqlite"]
DBPackageKind = Literal["ontology", "state"]


class DBSchemaRegistryError(RuntimeError):
    """Base registry error."""


class DBSchemaRegistryNotFoundError(DBSchemaRegistryError):
    """Registry artifact path is missing."""


class DBSchemaRegistryValidationError(DBSchemaRegistryError):
    """Registry payload is invalid or inconsistent."""


class DBSchemaRegistryResolutionError(DBSchemaRegistryError):
    """Registry filter/resolution failed."""


class DBSchemaRegistryEntry(BaseModel):
    package_kind: DBPackageKind
    backend_targets: list[DBBackendTarget] = Field(default_factory=list)
    sql_root: str
    source_hash: str
    source_label: str | None = None


class DBSchemaRegistry(BaseModel):
    schema_registry_version: int = 1
    environment_id: UUID
    entries: list[DBSchemaRegistryEntry] = Field(default_factory=list)


def compute_db_schema_registry_payload_hash(*, registry: DBSchemaRegistry) -> str:
    """Compute deterministic payload hash for a registry object."""
    payload = registry.model_dump(mode="json", exclude_none=True)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def iter_registry_sql_files(*, sql_root: Path) -> list[Path]:
    """Return canonical SQL files for hashing/resolution."""
    if not sql_root.exists() or not sql_root.is_dir():
        return []
    out: list[Path] = []
    for sql_file in sorted(sql_root.rglob("*.sql"), key=lambda p: str(p)):
        rel = sql_file.relative_to(sql_root)
        if any(part.startswith("_") for part in rel.parts[:-1]):
            continue
        out.append(sql_file)
    return out


def compute_sql_root_source_hash(*, sql_root: Path) -> str:
    """Compute deterministic source hash for one SQL root."""
    resolved_root = Path(sql_root).resolve()
    files = iter_registry_sql_files(sql_root=resolved_root)

    hasher = hashlib.sha256()
    hasher.update(b"aware:db-schema-registry-entry:v1\n")
    hasher.update(str(resolved_root).encode("utf-8"))
    hasher.update(b"\n")
    if not files:
        hasher.update(b"sql_root:missing_or_empty\n")
    else:
        for sql_file in files:
            rel = sql_file.relative_to(resolved_root).as_posix()
            file_hash = hashlib.sha256(sql_file.read_bytes()).hexdigest()
            hasher.update(rel.encode("utf-8"))
            hasher.update(b":")
            hasher.update(file_hash.encode("utf-8"))
            hasher.update(b"\n")
    return "sha256:" + hasher.hexdigest()


def build_db_schema_registry_entry(
    *,
    package_kind: DBPackageKind,
    backend_targets: Sequence[DBBackendTarget],
    sql_root: Path,
    source_label: str | None = None,
    relative_to: Path | None = None,
) -> DBSchemaRegistryEntry:
    """Build one registry entry with deterministic source hash."""
    resolved_root = Path(sql_root).resolve()
    sql_root_token = resolved_root.as_posix()
    if relative_to is not None:
        relative_base = Path(relative_to).resolve()
        try:
            sql_root_token = resolved_root.relative_to(relative_base).as_posix()
        except Exception:
            sql_root_token = resolved_root.as_posix()

    targets: list[DBBackendTarget] = []
    seen_targets: set[DBBackendTarget] = set()
    for target in backend_targets:
        token: DBBackendTarget = "postgres" if target == "postgres" else "sqlite"
        if token in seen_targets:
            continue
        seen_targets.add(token)
        targets.append(token)
    if not targets:
        raise DBSchemaRegistryValidationError("backend_targets must be non-empty")

    return DBSchemaRegistryEntry(
        package_kind=package_kind,
        backend_targets=targets,
        sql_root=sql_root_token,
        source_hash=compute_sql_root_source_hash(sql_root=resolved_root),
        source_label=(str(source_label).strip() or None),
    )


def write_db_schema_registry(*, path: Path, registry: DBSchemaRegistry) -> str:
    """Write registry payload and return payload hash."""
    payload = registry.model_dump(mode="json", exclude_none=True)
    payload_hash = compute_db_schema_registry_payload_hash(registry=registry)

    out_path = Path(path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload_hash


def load_db_schema_registry(*, path: Path) -> DBSchemaRegistry:
    registry_path = Path(path).resolve()
    if not registry_path.exists():
        raise DBSchemaRegistryNotFoundError(f"DB schema registry not found: {registry_path}")
    try:
        return DBSchemaRegistry.model_validate_json(registry_path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise DBSchemaRegistryValidationError(
            f"Invalid DB schema registry payload: {registry_path}: {exc}"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive I/O guard
        raise DBSchemaRegistryValidationError(
            f"Failed to read DB schema registry payload: {registry_path}: {exc}"
        ) from exc


def resolve_db_schema_registry_sql_roots(
    *,
    registry_path: Path,
    environment_id: UUID,
    package_kind: DBPackageKind,
    backend_target: DBBackendTarget,
    require_non_empty_sql: bool = True,
) -> tuple[Path, ...]:
    """Resolve filtered SQL roots from a registry artifact."""
    resolved_registry_path = Path(registry_path).resolve()
    registry = load_db_schema_registry(path=resolved_registry_path)
    if registry.environment_id != environment_id:
        raise DBSchemaRegistryResolutionError(
            "DB schema registry environment_id mismatch: "
            f"registry={registry.environment_id} requested={environment_id}"
        )

    filtered = [
        entry
        for entry in registry.entries
        if entry.package_kind == package_kind and backend_target in entry.backend_targets
    ]
    if not filtered:
        raise DBSchemaRegistryResolutionError(
            "DB schema registry filter returned no entries: "
            f"package_kind={package_kind} backend_target={backend_target}"
        )

    sql_roots: list[Path] = []
    seen: set[Path] = set()
    registry_dir = resolved_registry_path.parent
    for entry in filtered:
        sql_root_token = Path(entry.sql_root)
        sql_root = (registry_dir / sql_root_token).resolve() if not sql_root_token.is_absolute() else sql_root_token
        sql_root = sql_root.resolve()
        if sql_root in seen:
            continue
        seen.add(sql_root)

        if not sql_root.exists() or not sql_root.is_dir():
            raise DBSchemaRegistryResolutionError(
                "DB schema registry entry resolved to missing SQL root: "
                f"sql_root={sql_root} source_label={entry.source_label!r}"
            )

        expected_hash = entry.source_hash
        actual_hash = compute_sql_root_source_hash(sql_root=sql_root)
        if actual_hash != expected_hash:
            raise DBSchemaRegistryResolutionError(
                "DB schema registry source hash mismatch: "
                f"sql_root={sql_root} expected={expected_hash} actual={actual_hash}"
            )

        if require_non_empty_sql and not iter_registry_sql_files(sql_root=sql_root):
            raise DBSchemaRegistryResolutionError(
                "DB schema registry entry resolved to empty SQL root: "
                f"sql_root={sql_root} source_label={entry.source_label!r}"
            )
        sql_roots.append(sql_root)

    return tuple(sql_roots)


__all__ = [
    "DBBackendTarget",
    "DBPackageKind",
    "DBSchemaRegistry",
    "DBSchemaRegistryEntry",
    "DBSchemaRegistryError",
    "DBSchemaRegistryNotFoundError",
    "DBSchemaRegistryResolutionError",
    "DBSchemaRegistryValidationError",
    "build_db_schema_registry_entry",
    "compute_db_schema_registry_payload_hash",
    "compute_sql_root_source_hash",
    "iter_registry_sql_files",
    "load_db_schema_registry",
    "resolve_db_schema_registry_sql_roots",
    "write_db_schema_registry",
]
