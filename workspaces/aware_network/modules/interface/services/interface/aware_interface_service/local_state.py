from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    iter_registry_sql_files,
    write_db_schema_registry,
)


_SERVICE_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_LOCAL_STATE_SQLITE_ROOT = _SERVICE_PACKAGE_ROOT / "db" / "sqlite"
_DEFAULT_REGISTRY_RELATIVE_PATH = (
    Path("interface-service-local-state") / "db.schema.registry.json"
)


def ensure_interface_service_local_state_registry(
    *,
    repository_root: Path,
    state_home: Path,
    environment_id: UUID | str | None = None,
    runtime_manifest_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    sql_root: str | Path | None = None,
) -> Path:
    resolved_environment_id = _resolve_environment_id(
        repository_root=repository_root,
        environment_id=environment_id,
        runtime_manifest_path=runtime_manifest_path,
    )
    resolved_registry_path = _resolve_registry_path(
        state_home=state_home,
        registry_path=registry_path,
    )
    resolved_sql_root = Path(sql_root or _SERVICE_LOCAL_STATE_SQLITE_ROOT).resolve()
    if not resolved_sql_root.is_dir() or not iter_registry_sql_files(
        sql_root=resolved_sql_root
    ):
        raise RuntimeError(
            "Interface service local-state SQL materialization is missing: "
            f"sql_root={resolved_sql_root}"
        )
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=resolved_sql_root,
        source_label="workspaces/aware_network/modules/interface/services/interface/db/aware.toml",
        relative_to=resolved_registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=resolved_registry_path,
        registry=DBSchemaRegistry(
            environment_id=resolved_environment_id,
            entries=[entry],
        ),
    )
    return resolved_registry_path


def _resolve_registry_path(
    *,
    state_home: Path,
    registry_path: str | Path | None,
) -> Path:
    if registry_path is not None:
        return Path(registry_path).expanduser().resolve()
    return (state_home / _DEFAULT_REGISTRY_RELATIVE_PATH).resolve()


def _resolve_environment_id(
    *,
    repository_root: Path,
    environment_id: UUID | str | None,
    runtime_manifest_path: str | Path | None,
) -> UUID:
    _ = repository_root, runtime_manifest_path
    if environment_id is not None:
        return UUID(str(environment_id))
    raise RuntimeError(
        "Interface service local-state registry requires an explicit "
        "environment_id. Inferring it from Environment runtime manifests is retired."
    )


__all__ = ["ensure_interface_service_local_state_registry"]
