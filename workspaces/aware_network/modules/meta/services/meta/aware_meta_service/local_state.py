from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    iter_registry_sql_files,
    write_db_schema_registry,
)
from aware_orm.session import Session
from aware_orm.session.backends import SqlitePersistenceConfig


_SERVICE_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_LOCAL_STATE_SQLITE_ROOT = _SERVICE_PACKAGE_ROOT / "db" / "sqlite"
_DEFAULT_REGISTRY_RELATIVE_PATH = (
    Path("meta-service-local-state") / "db.schema.registry.json"
)
_DEFAULT_DATABASE_RELATIVE_PATH = Path("meta-service-local-state") / "temporal.sqlite"


@dataclass(frozen=True, slots=True)
class MetaLocalStateConfig:
    registry_path: Path
    database_path: Path | str
    environment_id: UUID

    def sqlite_backend_config(self) -> SqlitePersistenceConfig:
        return SqlitePersistenceConfig(
            database_path=self.database_path,
            registry_path=self.registry_path,
            environment_id=self.environment_id,
        )

    def open_session(self) -> Session:
        return Session(
            backend_name="sqlite",
            sqlite_backend_config=self.sqlite_backend_config(),
        )


@dataclass(frozen=True, slots=True)
class MetaTemporalSessionStateStore:
    config: MetaLocalStateConfig

    @classmethod
    def from_paths(
        cls,
        *,
        repository_root: Path,
        state_home: Path,
        runtime_manifest_path: str | Path | None = None,
        registry_path: str | Path | None = None,
        database_path: str | Path | None = None,
        sql_root: str | Path | None = None,
    ) -> "MetaTemporalSessionStateStore":
        resolved_registry_path = ensure_meta_service_local_state_registry(
            repository_root=repository_root,
            state_home=state_home,
            runtime_manifest_path=runtime_manifest_path,
            registry_path=registry_path,
            sql_root=sql_root,
        )
        environment_id = _load_environment_id(
            _resolve_runtime_manifest_path(
                repository_root=repository_root,
                runtime_manifest_path=runtime_manifest_path,
            )
        )
        resolved_database_path = _resolve_database_path(
            state_home=state_home,
            database_path=database_path,
        )
        return cls(
            config=MetaLocalStateConfig(
                registry_path=resolved_registry_path,
                database_path=resolved_database_path,
                environment_id=environment_id,
            )
        )

    async def record_session_opened(
        self,
        *,
        session_id: UUID,
        branch_id: UUID,
        projection_hash: str,
        environment_id: UUID,
        process_id: UUID,
        thread_id: UUID,
        base_commit_id: UUID,
        base_graph_hash_post: str,
        overlay_graph_hash_post: str | None,
        overlay_oig_json: str | None,
        revision: int,
        status: str,
        writer_actor_id: UUID | None,
        writer_lease_expires_at: datetime | None,
        created_at: datetime,
        last_activity_at: datetime,
        last_apply_at: datetime | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        session = self.config.open_session()
        session.add_insert(
            """
            INSERT INTO temporal_session(
                id,
                branch_id,
                projection_hash,
                environment_id,
                process_id,
                thread_id,
                base_commit_id,
                base_graph_hash_post,
                overlay_graph_hash_post,
                overlay_oig_json,
                revision,
                status,
                writer_actor_id,
                writer_lease_expires_at_unix_ms,
                created_at_unix_ms,
                last_activity_at_unix_ms,
                last_apply_at_unix_ms,
                closed_at_unix_ms,
                finalized_commit_id,
                metadata_json,
                v
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, NULL, NULL, $18, 1
            )
            ON CONFLICT(id) DO UPDATE SET
                branch_id = excluded.branch_id,
                projection_hash = excluded.projection_hash,
                environment_id = excluded.environment_id,
                process_id = excluded.process_id,
                thread_id = excluded.thread_id,
                base_commit_id = excluded.base_commit_id,
                base_graph_hash_post = excluded.base_graph_hash_post,
                overlay_graph_hash_post = excluded.overlay_graph_hash_post,
                overlay_oig_json = excluded.overlay_oig_json,
                revision = excluded.revision,
                status = excluded.status,
                writer_actor_id = excluded.writer_actor_id,
                writer_lease_expires_at_unix_ms = excluded.writer_lease_expires_at_unix_ms,
                last_activity_at_unix_ms = excluded.last_activity_at_unix_ms,
                last_apply_at_unix_ms = excluded.last_apply_at_unix_ms,
                metadata_json = excluded.metadata_json
            """,
            (
                str(session_id),
                str(branch_id),
                projection_hash,
                str(environment_id),
                str(process_id),
                str(thread_id),
                str(base_commit_id),
                base_graph_hash_post,
                overlay_graph_hash_post,
                overlay_oig_json,
                int(revision),
                status,
                str(writer_actor_id) if writer_actor_id is not None else None,
                _datetime_to_unix_ms(writer_lease_expires_at),
                _datetime_to_unix_ms(created_at),
                _datetime_to_unix_ms(last_activity_at),
                _datetime_to_unix_ms(last_apply_at),
                _json_dumps(metadata or {}),
            ),
        )
        await session.commit()

    async def record_frame(
        self,
        *,
        session_id: UUID,
        frame_id: str,
        branch_id: UUID,
        projection_hash: str,
        revision: int,
        actor_id: UUID,
        function_id: UUID | None,
        object_id: UUID | None,
        idempotency_key: str | None,
        request_hash: str | None,
        graph_hash_pre: str | None,
        graph_hash_post: str | None,
        changes: list[Any],
        payload: dict[str, Any],
        created_at: datetime,
        overlay_graph_hash_post: str | None,
        overlay_oig_json: str | None,
        writer_actor_id: UUID | None,
        writer_lease_expires_at: datetime | None,
    ) -> None:
        session = self.config.open_session()
        session.add_insert(
            """
            INSERT INTO temporal_frame(
                id,
                session_id,
                branch_id,
                projection_hash,
                revision,
                operation,
                actor_id,
                function_id,
                object_id,
                idempotency_key,
                request_hash,
                graph_hash_pre,
                graph_hash_post,
                changes_json,
                payload_json,
                created_at_unix_ms,
                status,
                v
            ) VALUES (
                $1, $2, $3, $4, $5, 'stream_frame', $6, $7, $8, $9,
                $10, $11, $12, $13, $14, $15, 'accepted', 1
            )
            ON CONFLICT(id) DO UPDATE SET
                graph_hash_pre = excluded.graph_hash_pre,
                graph_hash_post = excluded.graph_hash_post,
                changes_json = excluded.changes_json,
                payload_json = excluded.payload_json,
                status = excluded.status
            """,
            (
                frame_id,
                str(session_id),
                str(branch_id),
                projection_hash,
                int(revision),
                str(actor_id),
                str(function_id) if function_id is not None else None,
                str(object_id) if object_id is not None else None,
                idempotency_key,
                request_hash,
                graph_hash_pre,
                graph_hash_post,
                _json_dumps(changes),
                _json_dumps(payload),
                _datetime_to_unix_ms(created_at),
            ),
        )
        session.add_update(
            """
            UPDATE temporal_session
            SET revision = $1,
                overlay_graph_hash_post = $2,
                overlay_oig_json = $3,
                writer_actor_id = $4,
                writer_lease_expires_at_unix_ms = $5,
                last_apply_at_unix_ms = $6,
                last_activity_at_unix_ms = $7
            WHERE id = $8
            """,
            (
                int(revision),
                overlay_graph_hash_post,
                overlay_oig_json,
                str(writer_actor_id) if writer_actor_id is not None else None,
                _datetime_to_unix_ms(writer_lease_expires_at),
                _datetime_to_unix_ms(created_at),
                _datetime_to_unix_ms(created_at),
                str(session_id),
            ),
        )
        await session.commit()

    async def record_session_tombstone(
        self,
        *,
        session_id: UUID,
        tombstone_id: str,
        branch_id: UUID,
        projection_hash: str,
        revision: int,
        operation: str,
        actor_id: UUID | None,
        finalized_commit_id: UUID | None,
        final_graph_hash_post: str | None,
        reason: str | None,
        closed_at: datetime,
        ttl_cleanup_at: datetime | None,
        payload: dict[str, Any],
    ) -> None:
        session = self.config.open_session()
        session.add_insert(
            """
            INSERT INTO temporal_session_tombstone(
                id,
                session_id,
                branch_id,
                projection_hash,
                revision,
                operation,
                actor_id,
                finalized_commit_id,
                final_graph_hash_post,
                reason,
                closed_at_unix_ms,
                ttl_cleanup_at_unix_ms,
                payload_json,
                v
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 1
            )
            ON CONFLICT(id) DO UPDATE SET
                revision = excluded.revision,
                actor_id = excluded.actor_id,
                finalized_commit_id = excluded.finalized_commit_id,
                final_graph_hash_post = excluded.final_graph_hash_post,
                reason = excluded.reason,
                closed_at_unix_ms = excluded.closed_at_unix_ms,
                ttl_cleanup_at_unix_ms = excluded.ttl_cleanup_at_unix_ms,
                payload_json = excluded.payload_json
            """,
            (
                tombstone_id,
                str(session_id),
                str(branch_id),
                projection_hash,
                int(revision),
                operation,
                str(actor_id) if actor_id is not None else None,
                str(finalized_commit_id) if finalized_commit_id is not None else None,
                final_graph_hash_post,
                reason,
                _datetime_to_unix_ms(closed_at),
                _datetime_to_unix_ms(ttl_cleanup_at),
                _json_dumps(payload),
            ),
        )
        session.add_update(
            """
            UPDATE temporal_session
            SET status = $1,
                closed_at_unix_ms = $2,
                finalized_commit_id = $3,
                last_activity_at_unix_ms = $4
            WHERE id = $5
            """,
            (
                "finalized" if finalized_commit_id is not None else "closed",
                _datetime_to_unix_ms(closed_at),
                str(finalized_commit_id) if finalized_commit_id is not None else None,
                _datetime_to_unix_ms(closed_at),
                str(session_id),
            ),
        )
        await session.commit()

    async def load_session_row(self, *, session_id: UUID) -> dict[str, Any] | None:
        session = self.config.open_session()
        rows = await session.execute_query(
            "SELECT * FROM temporal_session WHERE id = $1",
            str(session_id),
        )
        return rows[0] if rows else None

    async def load_frame_rows(self, *, session_id: UUID) -> list[dict[str, Any]]:
        session = self.config.open_session()
        return await session.execute_query(
            """
            SELECT *
            FROM temporal_frame
            WHERE session_id = $1
            ORDER BY revision ASC
            """,
            str(session_id),
        )


def ensure_meta_service_local_state_registry(
    *,
    repository_root: Path,
    state_home: Path,
    runtime_manifest_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    sql_root: str | Path | None = None,
) -> Path:
    resolved_manifest_path = _resolve_runtime_manifest_path(
        repository_root=repository_root,
        runtime_manifest_path=runtime_manifest_path,
    )
    environment_id = _load_environment_id(resolved_manifest_path)
    resolved_registry_path = _resolve_registry_path(
        state_home=state_home,
        registry_path=registry_path,
    )
    resolved_sql_root = Path(sql_root or _SERVICE_LOCAL_STATE_SQLITE_ROOT).resolve()
    if not resolved_sql_root.is_dir() or not iter_registry_sql_files(
        sql_root=resolved_sql_root
    ):
        raise RuntimeError(
            "Meta service temporal local-state SQL materialization is missing: "
            f"sql_root={resolved_sql_root}"
        )
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=resolved_sql_root,
        source_label="services/meta/db/aware.toml",
        relative_to=resolved_registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=resolved_registry_path,
        registry=DBSchemaRegistry(
            environment_id=environment_id,
            entries=[entry],
        ),
    )
    return resolved_registry_path


def _resolve_runtime_manifest_path(
    *,
    repository_root: Path,
    runtime_manifest_path: str | Path | None,
) -> Path:
    if runtime_manifest_path is not None:
        return Path(runtime_manifest_path).expanduser().resolve()
    return (
        repository_root
        / ".aware"
        / "environment"
        / "runtime"
        / "environment.manifest.json"
    ).resolve()


def _resolve_registry_path(
    *,
    state_home: Path,
    registry_path: str | Path | None,
) -> Path:
    if registry_path is not None:
        return Path(registry_path).expanduser().resolve()
    return (state_home / _DEFAULT_REGISTRY_RELATIVE_PATH).resolve()


def _resolve_database_path(
    *,
    state_home: Path,
    database_path: str | Path | None,
) -> Path | str:
    if database_path is not None:
        token = str(database_path)
        if token == ":memory:":
            return token
        return Path(database_path).expanduser().resolve()
    return (state_home / _DEFAULT_DATABASE_RELATIVE_PATH).resolve()


def _load_environment_id(manifest_path: Path) -> UUID:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        environment_payload = payload["environment"]
        environment_id = environment_payload["id"]
        return UUID(str(environment_id))
    except Exception as exc:
        raise RuntimeError(
            "Runtime manifest has invalid environment id: "
            f"manifest_path={manifest_path}"
        ) from exc


def _datetime_to_unix_ms(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


def _json_dumps(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )


def _json_default(value: object) -> str:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


__all__ = [
    "MetaLocalStateConfig",
    "MetaTemporalSessionStateStore",
    "ensure_meta_service_local_state_registry",
]
