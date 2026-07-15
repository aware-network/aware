from __future__ import annotations

from dataclasses import dataclass

from aware_interface.local_db import InterfaceLocalDb


@dataclass(frozen=True, slots=True)
class LocalCommitRecord:
    branch_id: str
    id: str
    commit_id: str
    projection_hash: str
    payload_json: str
    parent_commit_id: str | None = None
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
    object_instance_graph_id: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class LocalCommitActionRecord:
    id: str
    branch_id: str
    projection_hash: str
    commit_id: str
    operation_label: str
    call_target: str | None = None
    function_id: str | None = None
    object_id: str | None = None
    class_instance_identity_id: str | None = None
    actor_id: str | None = None


@dataclass(frozen=True, slots=True)
class LocalLaneCommitRecord:
    id: str
    branch_id: str
    projection_hash: str
    commit_id: str


@dataclass(frozen=True, slots=True)
class LocalLaneHeadRecord:
    id: str
    branch_id: str
    projection_hash: str
    head_commit_id: str | None = None
    graph_hash_post: str | None = None
    object_instance_graph_id: str | None = None
    root_object_instance_id: str | None = None
    v: int = 1


@dataclass(frozen=True, slots=True)
class LocalProjectionCursorRecord:
    id: str
    branch_id: str
    projection_hash: str
    head_commit_id: str
    projector_id: str
    graph_hash_post: str | None = None
    v: int = 1


@dataclass(frozen=True, slots=True)
class LocalSnapshotRecord:
    id: str
    branch_id: str
    projection_hash: str
    commit_id: str
    oig_json: str
    indexes_json: str
    v: int = 1


class InterfaceLaneStores:
    """Persistence-only runtime surface for local lane-state artifacts."""

    _db: InterfaceLocalDb

    def __init__(self, *, db: InterfaceLocalDb) -> None:
        self._db = db

    @property
    def db(self) -> InterfaceLocalDb:
        return self._db

    async def save_commit(self, record: LocalCommitRecord) -> None:
        await self._execute_upsert(
            """
            INSERT INTO commit_store.local_oig_commit (
              branch_id,
              id,
              commit_id,
              projection_hash,
              parent_commit_id,
              graph_hash_pre,
              graph_hash_post,
              object_instance_graph_id,
              object_instance_graph_commit_id,
              payload_json
            ) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT(id) DO UPDATE SET
              branch_id = excluded.branch_id,
              commit_id = excluded.commit_id,
              projection_hash = excluded.projection_hash,
              parent_commit_id = excluded.parent_commit_id,
              graph_hash_pre = excluded.graph_hash_pre,
              graph_hash_post = excluded.graph_hash_post,
              object_instance_graph_id = excluded.object_instance_graph_id,
              object_instance_graph_commit_id = excluded.object_instance_graph_commit_id,
              payload_json = excluded.payload_json
            """,
            (
                record.branch_id,
                record.id,
                record.commit_id,
                record.projection_hash,
                record.parent_commit_id,
                record.graph_hash_pre,
                record.graph_hash_post,
                record.object_instance_graph_id,
                record.object_instance_graph_commit_id,
                record.payload_json,
            ),
        )

    async def load_commit(self, *, branch_id: str, commit_id: str, projection_hash: str) -> LocalCommitRecord | None:
        row = await self._fetch_optional(
            """
            SELECT
              branch_id,
              id,
              commit_id,
              projection_hash,
              parent_commit_id,
              graph_hash_pre,
              graph_hash_post,
              object_instance_graph_id,
              object_instance_graph_commit_id,
              payload_json
            FROM commit_store.local_oig_commit
            WHERE branch_id = $1 AND id = $2 AND projection_hash = $3
            """,
            branch_id,
            commit_id,
            projection_hash,
        )
        if row is None:
            return None
        return _commit_record_from_row(row)

    async def list_commits(self, *, branch_id: str, projection_hash: str) -> tuple[LocalCommitRecord, ...]:
        rows = await self._fetch_rows(
            """
            SELECT
              branch_id,
              id,
              commit_id,
              projection_hash,
              parent_commit_id,
              graph_hash_pre,
              graph_hash_post,
              object_instance_graph_id,
              object_instance_graph_commit_id,
              payload_json
            FROM commit_store.local_oig_commit
            WHERE branch_id = $1 AND projection_hash = $2
            ORDER BY id ASC
            """,
            branch_id,
            projection_hash,
        )
        return tuple(_commit_record_from_row(row) for row in rows)

    async def save_commit_action(self, record: LocalCommitActionRecord) -> None:
        await self._execute_upsert(
            """
            INSERT INTO commit_store.local_oig_commit_action (
              id,
              branch_id,
              projection_hash,
              commit_id,
              operation_label,
              call_target,
              function_id,
              object_id,
              class_instance_identity_id,
              actor_id
            ) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT(id) DO UPDATE SET
              branch_id = excluded.branch_id,
              projection_hash = excluded.projection_hash,
              commit_id = excluded.commit_id,
              operation_label = excluded.operation_label,
              call_target = excluded.call_target,
              function_id = excluded.function_id,
              object_id = excluded.object_id,
              class_instance_identity_id = excluded.class_instance_identity_id,
              actor_id = excluded.actor_id
            """,
            (
                record.id,
                record.branch_id,
                record.projection_hash,
                record.commit_id,
                record.operation_label,
                record.call_target,
                record.function_id,
                record.object_id,
                record.class_instance_identity_id,
                record.actor_id,
            ),
        )

    async def load_commit_action(
        self,
        *,
        branch_id: str,
        action_id: str,
        projection_hash: str,
    ) -> LocalCommitActionRecord | None:
        row = await self._fetch_optional(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              commit_id,
              operation_label,
              call_target,
              function_id,
              object_id,
              class_instance_identity_id,
              actor_id
            FROM commit_store.local_oig_commit_action
            WHERE id = $1 AND branch_id = $2 AND projection_hash = $3
            """,
            action_id,
            branch_id,
            projection_hash,
        )
        if row is None:
            return None
        return _commit_action_record_from_row(row)

    async def list_commit_actions(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str | None = None,
    ) -> tuple[LocalCommitActionRecord, ...]:
        params: list[object] = [branch_id, projection_hash]
        commit_filter = ""
        if commit_id is not None:
            params.append(commit_id)
            commit_filter = " AND commit_id = $3"
        rows = await self._fetch_rows(
            f"""
            SELECT
              id,
              branch_id,
              projection_hash,
              commit_id,
              operation_label,
              call_target,
              function_id,
              object_id,
              class_instance_identity_id,
              actor_id
            FROM commit_store.local_oig_commit_action
            WHERE branch_id = $1 AND projection_hash = $2{commit_filter}
            ORDER BY id ASC
            """,
            *params,
        )
        return tuple(_commit_action_record_from_row(row) for row in rows)

    async def save_lane_commit(self, record: LocalLaneCommitRecord) -> None:
        await self._execute_upsert(
            """
            INSERT INTO commit_store.local_oig_lane_commit (
              id,
              branch_id,
              projection_hash,
              commit_id
            ) VALUES($1, $2, $3, $4)
            ON CONFLICT(id) DO UPDATE SET
              branch_id = excluded.branch_id,
              projection_hash = excluded.projection_hash,
              commit_id = excluded.commit_id
            """,
            (record.id, record.branch_id, record.projection_hash, record.commit_id),
        )

    async def load_lane_commit(
        self,
        *,
        branch_id: str,
        lane_commit_id: str,
        projection_hash: str,
    ) -> LocalLaneCommitRecord | None:
        row = await self._fetch_optional(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              commit_id
            FROM commit_store.local_oig_lane_commit
            WHERE id = $1 AND branch_id = $2 AND projection_hash = $3
            """,
            lane_commit_id,
            branch_id,
            projection_hash,
        )
        if row is None:
            return None
        return _lane_commit_record_from_row(row)

    async def list_lane_commits(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str | None = None,
    ) -> tuple[LocalLaneCommitRecord, ...]:
        params: list[object] = [branch_id, projection_hash]
        commit_filter = ""
        if commit_id is not None:
            params.append(commit_id)
            commit_filter = " AND commit_id = $3"
        rows = await self._fetch_rows(
            f"""
            SELECT
              id,
              branch_id,
              projection_hash,
              commit_id
            FROM commit_store.local_oig_lane_commit
            WHERE branch_id = $1 AND projection_hash = $2{commit_filter}
            ORDER BY id ASC
            """,
            *params,
        )
        return tuple(_lane_commit_record_from_row(row) for row in rows)

    async def save_lane_head(self, record: LocalLaneHeadRecord) -> None:
        await self._execute_upsert(
            """
            INSERT INTO commit_store.local_oig_lane_head (
              id,
              branch_id,
              projection_hash,
              head_commit_id,
              graph_hash_post,
              object_instance_graph_id,
              root_object_instance_id,
              v
            ) VALUES($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT(id) DO UPDATE SET
              branch_id = excluded.branch_id,
              projection_hash = excluded.projection_hash,
              head_commit_id = excluded.head_commit_id,
              graph_hash_post = excluded.graph_hash_post,
              object_instance_graph_id = excluded.object_instance_graph_id,
              root_object_instance_id = excluded.root_object_instance_id,
              v = excluded.v
            """,
            (
                record.id,
                record.branch_id,
                record.projection_hash,
                record.head_commit_id,
                record.graph_hash_post,
                record.object_instance_graph_id,
                record.root_object_instance_id,
                record.v,
            ),
        )

    async def load_lane_head(self, *, branch_id: str, lane_id: str, projection_hash: str) -> LocalLaneHeadRecord | None:
        row = await self._fetch_optional(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              head_commit_id,
              graph_hash_post,
              object_instance_graph_id,
              root_object_instance_id,
              v
            FROM commit_store.local_oig_lane_head
            WHERE id = $1 AND branch_id = $2 AND projection_hash = $3
            """,
            lane_id,
            branch_id,
            projection_hash,
        )
        if row is None:
            return None
        return _lane_head_record_from_row(row)

    async def list_lane_heads(self, *, branch_id: str, projection_hash: str) -> tuple[LocalLaneHeadRecord, ...]:
        rows = await self._fetch_rows(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              head_commit_id,
              graph_hash_post,
              object_instance_graph_id,
              root_object_instance_id,
              v
            FROM commit_store.local_oig_lane_head
            WHERE branch_id = $1 AND projection_hash = $2
            ORDER BY id ASC
            """,
            branch_id,
            projection_hash,
        )
        return tuple(_lane_head_record_from_row(row) for row in rows)

    async def save_projection_cursor(self, record: LocalProjectionCursorRecord) -> None:
        await self._execute_upsert(
            """
            INSERT INTO commit_store.local_oig_projection_cursor (
              id,
              branch_id,
              projection_hash,
              head_commit_id,
              projector_id,
              graph_hash_post,
              v
            ) VALUES($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT(id) DO UPDATE SET
              branch_id = excluded.branch_id,
              projection_hash = excluded.projection_hash,
              head_commit_id = excluded.head_commit_id,
              projector_id = excluded.projector_id,
              graph_hash_post = excluded.graph_hash_post,
              v = excluded.v
            """,
            (
                record.id,
                record.branch_id,
                record.projection_hash,
                record.head_commit_id,
                record.projector_id,
                record.graph_hash_post,
                record.v,
            ),
        )

    async def load_projection_cursor(
        self,
        *,
        branch_id: str,
        cursor_id: str,
        projection_hash: str,
    ) -> LocalProjectionCursorRecord | None:
        row = await self._fetch_optional(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              head_commit_id,
              projector_id,
              graph_hash_post,
              v
            FROM commit_store.local_oig_projection_cursor
            WHERE id = $1 AND branch_id = $2 AND projection_hash = $3
            """,
            cursor_id,
            branch_id,
            projection_hash,
        )
        if row is None:
            return None
        return _projection_cursor_record_from_row(row)

    async def list_projection_cursors(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        projector_id: str | None = None,
    ) -> tuple[LocalProjectionCursorRecord, ...]:
        params: list[object] = [branch_id, projection_hash]
        projector_filter = ""
        if projector_id is not None:
            params.append(projector_id)
            projector_filter = " AND projector_id = $3"
        rows = await self._fetch_rows(
            f"""
            SELECT
              id,
              branch_id,
              projection_hash,
              head_commit_id,
              projector_id,
              graph_hash_post,
              v
            FROM commit_store.local_oig_projection_cursor
            WHERE branch_id = $1 AND projection_hash = $2{projector_filter}
            ORDER BY id ASC
            """,
            *params,
        )
        return tuple(_projection_cursor_record_from_row(row) for row in rows)

    async def save_snapshot(self, record: LocalSnapshotRecord) -> None:
        await self._execute_upsert(
            """
            INSERT INTO commit_store.local_oig_snapshot (
              id,
              branch_id,
              projection_hash,
              commit_id,
              oig_json,
              indexes_json,
              v
            ) VALUES($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT(id) DO UPDATE SET
              branch_id = excluded.branch_id,
              projection_hash = excluded.projection_hash,
              commit_id = excluded.commit_id,
              oig_json = excluded.oig_json,
              indexes_json = excluded.indexes_json,
              v = excluded.v
            """,
            (
                record.id,
                record.branch_id,
                record.projection_hash,
                record.commit_id,
                record.oig_json,
                record.indexes_json,
                record.v,
            ),
        )

    async def load_snapshot(self, *, branch_id: str, snapshot_id: str, projection_hash: str) -> LocalSnapshotRecord | None:
        row = await self._fetch_optional(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              commit_id,
              oig_json,
              indexes_json,
              v
            FROM commit_store.local_oig_snapshot
            WHERE id = $1 AND branch_id = $2 AND projection_hash = $3
            """,
            snapshot_id,
            branch_id,
            projection_hash,
        )
        if row is None:
            return None
        return _snapshot_record_from_row(row)

    async def list_snapshots(self, *, branch_id: str, projection_hash: str) -> tuple[LocalSnapshotRecord, ...]:
        rows = await self._fetch_rows(
            """
            SELECT
              id,
              branch_id,
              projection_hash,
              commit_id,
              oig_json,
              indexes_json,
              v
            FROM commit_store.local_oig_snapshot
            WHERE branch_id = $1 AND projection_hash = $2
            ORDER BY id ASC
            """,
            branch_id,
            projection_hash,
        )
        return tuple(_snapshot_record_from_row(row) for row in rows)

    async def _execute_upsert(self, sql: str, params: tuple[object, ...]) -> None:
        orm_session = self._db.new_session()
        try:
            orm_session.add_insert(sql, params)
            await orm_session.commit()
        finally:
            self._db.close_session(orm_session)

    async def _fetch_optional(self, sql: str, *params: object) -> dict[str, object] | None:
        rows = await self._fetch_rows(sql, *params)
        if not rows:
            return None
        return rows[0]

    async def _fetch_rows(self, sql: str, *params: object) -> list[dict[str, object]]:
        return await self._db.execute_query(sql, *params)


def _required_text(row: dict[str, object], key: str) -> str:
    value = row.get(key)
    if value is None:
        raise ValueError(f"Missing required lane-store column: {key}")
    return str(value)


def _optional_text(row: dict[str, object], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    return str(value)


def _required_int(row: dict[str, object], key: str) -> int:
    value = row.get(key)
    if value is None:
        raise ValueError(f"Missing required lane-store integer column: {key}")
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"Invalid integer value for lane-store column {key}: {value!r}")


def _commit_record_from_row(row: dict[str, object]) -> LocalCommitRecord:
    return LocalCommitRecord(
        branch_id=_required_text(row, "branch_id"),
        id=_required_text(row, "id"),
        commit_id=_required_text(row, "commit_id"),
        projection_hash=_required_text(row, "projection_hash"),
        payload_json=_required_text(row, "payload_json"),
        parent_commit_id=_optional_text(row, "parent_commit_id"),
        graph_hash_pre=_optional_text(row, "graph_hash_pre"),
        graph_hash_post=_optional_text(row, "graph_hash_post"),
        object_instance_graph_id=_optional_text(row, "object_instance_graph_id"),
        object_instance_graph_commit_id=_optional_text(row, "object_instance_graph_commit_id"),
    )


def _commit_action_record_from_row(row: dict[str, object]) -> LocalCommitActionRecord:
    return LocalCommitActionRecord(
        id=_required_text(row, "id"),
        branch_id=_required_text(row, "branch_id"),
        projection_hash=_required_text(row, "projection_hash"),
        commit_id=_required_text(row, "commit_id"),
        operation_label=_required_text(row, "operation_label"),
        call_target=_optional_text(row, "call_target"),
        function_id=_optional_text(row, "function_id"),
        object_id=_optional_text(row, "object_id"),
        class_instance_identity_id=_optional_text(row, "class_instance_identity_id"),
        actor_id=_optional_text(row, "actor_id"),
    )


def _lane_commit_record_from_row(row: dict[str, object]) -> LocalLaneCommitRecord:
    return LocalLaneCommitRecord(
        id=_required_text(row, "id"),
        branch_id=_required_text(row, "branch_id"),
        projection_hash=_required_text(row, "projection_hash"),
        commit_id=_required_text(row, "commit_id"),
    )


def _lane_head_record_from_row(row: dict[str, object]) -> LocalLaneHeadRecord:
    return LocalLaneHeadRecord(
        id=_required_text(row, "id"),
        branch_id=_required_text(row, "branch_id"),
        projection_hash=_required_text(row, "projection_hash"),
        head_commit_id=_optional_text(row, "head_commit_id"),
        graph_hash_post=_optional_text(row, "graph_hash_post"),
        object_instance_graph_id=_optional_text(row, "object_instance_graph_id"),
        root_object_instance_id=_optional_text(row, "root_object_instance_id"),
        v=_required_int(row, "v"),
    )


def _projection_cursor_record_from_row(row: dict[str, object]) -> LocalProjectionCursorRecord:
    return LocalProjectionCursorRecord(
        id=_required_text(row, "id"),
        branch_id=_required_text(row, "branch_id"),
        projection_hash=_required_text(row, "projection_hash"),
        head_commit_id=_required_text(row, "head_commit_id"),
        projector_id=_required_text(row, "projector_id"),
        graph_hash_post=_optional_text(row, "graph_hash_post"),
        v=_required_int(row, "v"),
    )


def _snapshot_record_from_row(row: dict[str, object]) -> LocalSnapshotRecord:
    return LocalSnapshotRecord(
        id=_required_text(row, "id"),
        branch_id=_required_text(row, "branch_id"),
        projection_hash=_required_text(row, "projection_hash"),
        commit_id=_required_text(row, "commit_id"),
        oig_json=_required_text(row, "oig_json"),
        indexes_json=_required_text(row, "indexes_json"),
        v=_required_int(row, "v"),
    )


__all__ = [
    "InterfaceLaneStores",
    "LocalCommitActionRecord",
    "LocalCommitRecord",
    "LocalLaneCommitRecord",
    "LocalLaneHeadRecord",
    "LocalProjectionCursorRecord",
    "LocalSnapshotRecord",
]
