from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import sqlite3
from time import time
from typing import Any, Protocol, get_args
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_environment_service_dto.environment.environment import (
    GetObjectInstanceGraphCommitRequest,
)
from aware_meta.graph.instance.commit.body_codec import (
    object_instance_graph_changes_from_body,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.config.stable_ids import stable_enum_option_id

from .state import ServiceOntologyReplicaCommitReceipt


@dataclass(frozen=True, slots=True)
class ServiceOntologyProjectionApplyStats:
    class_row_count: int = 0
    association_row_count: int = 0
    mutation_row_count: int = 0
    duplicate: bool = False


class ServiceOntologyCommitSource(Protocol):
    async def get_object_instance_graph_commit(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class EnvironmentApiServiceOntologyCommitSource:
    api_client: object
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None

    async def get_object_instance_graph_commit(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
    ) -> object:
        response = await self.api_client.environment.object_instance_graph_commit.get_object_instance_graph_commit(
            GetObjectInstanceGraphCommitRequest(
                actor_id=receipt.actor_id,
                environment_id=self.environment_id,
                process_id=self.process_id,
                thread_id=self.thread_id,
                branch_id=receipt.branch_id,
                projection_hash=receipt.projection_hash,
                commit_id=receipt.commit_id,
            )
        )
        status = str(getattr(response, "status", "") or "").strip().casefold()
        if status not in {"succeeded", "success", "ok"}:
            raise RuntimeError(
                "Environment OIG commit read failed: "
                f"{getattr(response, 'error', None) or status or 'unknown'}"
            )
        commit = getattr(response, "commit", None)
        if commit is None:
            raise RuntimeError(
                "Environment OIG commit read returned no commit payload: "
                f"commit_id={receipt.commit_id}"
            )
        return commit


@dataclass(frozen=True, slots=True)
class MetaLaneStoreServiceOntologyCommitSource:
    meta_lane_store: object

    async def get_object_instance_graph_commit(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
    ) -> object:
        commit = await self.meta_lane_store.object_instance_graph_commit(
            branch_id=receipt.branch_id,
            projection_hash=receipt.projection_hash,
            commit_id=receipt.commit_id,
        )
        if commit is None:
            raise RuntimeError(
                "Meta lane store returned no OIG commit payload: "
                f"branch_id={receipt.branch_id} "
                f"projection_hash={receipt.projection_hash} "
                f"commit_id={receipt.commit_id}"
            )
        return commit


@dataclass(frozen=True, slots=True)
class LocalFsServiceOntologyCommitSource:
    commit_store: FSCommitStore = field(default_factory=FSCommitStore)

    async def get_object_instance_graph_commit(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
    ) -> object:
        commit = await self.commit_store.get_commit(
            branch_id=receipt.branch_id,
            projection_hash=receipt.projection_hash,
            commit_id=receipt.commit_id,
        )
        if commit is None:
            raise RuntimeError(
                "Local Meta store returned no OIG commit envelope: "
                f"branch_id={receipt.branch_id} "
                f"projection_hash={receipt.projection_hash} "
                f"commit_id={receipt.commit_id}"
            )
        body = await self.commit_store.get_commit_body(
            branch_id=receipt.branch_id,
            projection_hash=receipt.projection_hash,
            commit_id=receipt.commit_id,
        )
        if body is None:
            raise RuntimeError(
                "Local Meta store returned no OIG commit body: "
                f"branch_id={receipt.branch_id} "
                f"projection_hash={receipt.projection_hash} "
                f"commit_id={receipt.commit_id}"
            )
        return commit.model_copy(
            update={
                "object_instance_graph_changes": list(
                    object_instance_graph_changes_from_body(body)
                )
            }
        )


class ServiceOntologyProjectionStore:
    """Service-owned generic OIG projection DB for local read queries."""

    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        db_path: Path,
    ) -> None:
        self._connection = connection
        self.db_path = db_path

    @classmethod
    def open(cls, *, db_path: Path) -> "ServiceOntologyProjectionStore":
        resolved_db_path = Path(db_path).expanduser().resolve()
        resolved_db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(resolved_db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SCHEMA_SQL)
        return cls(connection=connection, db_path=resolved_db_path)

    def close(self) -> None:
        self._connection.close()

    def apply_commit(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
        commit: object,
    ) -> ServiceOntologyProjectionApplyStats:
        if self.has_commit(commit_id=receipt.commit_id):
            return ServiceOntologyProjectionApplyStats(duplicate=True)

        payload = _payload_dict(commit)
        class_row_count = 0
        association_row_count = 0
        mutation_row_count = 0
        now_ms = _unix_ms()
        class_change_payloads = tuple(
            _payload_dict(class_change)
            for change in _as_list(payload.get("object_instance_graph_changes"))
            for class_change in _as_list(
                _payload_dict(change).get("class_instance_changes")
            )
        )
        unresolved_class_instance_ids = tuple(
            class_instance_id
            for class_change in class_change_payloads
            if (
                class_instance_id := _required_uuid(
                    class_change.get("class_instance_id")
                )
            )
            and self._current_class_config_id(class_instance_id=class_instance_id)
            is None
            and _class_config_id_from_change(class_change) is None
        )
        root_fallback_class_instance_id = (
            unresolved_class_instance_ids[0]
            if len(unresolved_class_instance_ids) == 1
            else None
        )
        root_class_config_id = _optional_text(payload.get("root_class_config_id"))
        with self._connection:
            for change in _as_list(payload.get("object_instance_graph_changes")):
                change_payload = _payload_dict(change)
                for class_change in _as_list(
                    change_payload.get("class_instance_changes")
                ):
                    class_stats = self._apply_class_instance_change(
                        receipt=receipt,
                        commit_payload=payload,
                        class_change=_payload_dict(class_change),
                        fallback_class_config_id=(
                            root_class_config_id
                            if _required_uuid(
                                _payload_dict(class_change).get("class_instance_id")
                            )
                            == root_fallback_class_instance_id
                            else None
                        ),
                        observed_at_unix_ms=now_ms,
                    )
                    class_row_count += class_stats.class_row_count
                    mutation_row_count += class_stats.mutation_row_count
                for relationship_change in _as_list(
                    change_payload.get("class_instance_relationship_changes")
                ):
                    relationship_stats = self._apply_relationship_change(
                        receipt=receipt,
                        relationship_change=_payload_dict(relationship_change),
                        observed_at_unix_ms=now_ms,
                    )
                    association_row_count += relationship_stats.association_row_count
                    mutation_row_count += relationship_stats.mutation_row_count
            self._connection.execute(
                """
INSERT INTO service_ontology_projection_commit (
  id,
  branch_id,
  projection_hash,
  commit_id,
  object_instance_graph_commit_id,
  graph_hash_post,
  object_instance_graph_id,
  root_object_id,
  applied_at_unix_ms,
  payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""".strip(),
                (
                    str(_commit_row_id(commit_id=receipt.commit_id)),
                    str(receipt.branch_id),
                    _projection_hash(receipt.projection_hash),
                    str(receipt.commit_id),
                    _optional_text(receipt.object_instance_graph_commit_id)
                    or _optional_text(payload.get("id")),
                    receipt.graph_hash_post
                    or _optional_text(payload.get("graph_hash_post")),
                    _optional_text(receipt.object_instance_graph_id)
                    or _optional_text(payload.get("object_instance_graph_id")),
                    _optional_text(receipt.root_object_id)
                    or _optional_text(payload.get("root_source_object_id")),
                    now_ms,
                    _json_dump(payload),
                ),
            )
        return ServiceOntologyProjectionApplyStats(
            class_row_count=class_row_count,
            association_row_count=association_row_count,
            mutation_row_count=mutation_row_count,
            duplicate=False,
        )

    def has_commit(self, *, commit_id: UUID) -> bool:
        cursor = self._connection.execute(
            "SELECT 1 FROM service_ontology_projection_commit WHERE commit_id = ?;",
            (str(commit_id),),
        )
        return cursor.fetchone() is not None

    def fetch_class_instance(
        self,
        *,
        class_instance_id: UUID,
    ) -> dict[str, Any] | None:
        cursor = self._connection.execute(
            "SELECT * FROM service_ontology_projection_class_instance WHERE class_instance_id = ?;",
            (str(class_instance_id),),
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def list_class_instances(
        self,
        *,
        class_config_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[dict[str, Any], ...]:
        conditions: list[str] = []
        params: list[object] = []
        if class_config_id is not None:
            conditions.append("class_config_id = ?")
            params.append(str(class_config_id))
        if projection_hash is not None:
            conditions.append("projection_hash = ?")
            params.append(_projection_hash(projection_hash))
        if not include_deleted:
            conditions.append("deleted = 0")
        where_sql = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor = self._connection.execute(
            (
                "SELECT * FROM service_ontology_projection_class_instance"
                f"{where_sql} ORDER BY class_config_id, class_instance_id;"
            ),
            tuple(params),
        )
        return tuple(dict(row) for row in cursor.fetchall())

    def find_class_instances_by_attribute(
        self,
        *,
        key: str,
        value: object,
        class_config_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[dict[str, Any], ...]:
        attribute_key = str(key or "").strip()
        if not attribute_key:
            raise ValueError(
                "Service ontology replica attribute key must be non-empty."
            )
        rows = self.list_class_instances(
            class_config_id=class_config_id,
            projection_hash=projection_hash,
            include_deleted=include_deleted,
        )
        matches: list[dict[str, Any]] = []
        for row in rows:
            attributes = _json_object(row.get("attributes_json"))
            if attributes.get(attribute_key) == value:
                matches.append(row)
        return tuple(matches)

    def fetch_relationship(
        self,
        *,
        class_config_relationship_id: UUID,
        source_class_instance_id: UUID,
        target_class_instance_id: UUID,
    ) -> dict[str, Any] | None:
        row_id = _relationship_row_id(
            class_config_relationship_id=class_config_relationship_id,
            source_class_instance_id=source_class_instance_id,
            target_class_instance_id=target_class_instance_id,
        )
        cursor = self._connection.execute(
            "SELECT * FROM service_ontology_projection_relationship WHERE id = ?;",
            (str(row_id),),
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def list_relationships(
        self,
        *,
        class_config_relationship_id: UUID | None = None,
        source_class_instance_id: UUID | None = None,
        target_class_instance_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[dict[str, Any], ...]:
        conditions: list[str] = []
        params: list[object] = []
        if class_config_relationship_id is not None:
            conditions.append("class_config_relationship_id = ?")
            params.append(str(class_config_relationship_id))
        if source_class_instance_id is not None:
            conditions.append("source_class_instance_id = ?")
            params.append(str(source_class_instance_id))
        if target_class_instance_id is not None:
            conditions.append("target_class_instance_id = ?")
            params.append(str(target_class_instance_id))
        if projection_hash is not None:
            conditions.append("projection_hash = ?")
            params.append(_projection_hash(projection_hash))
        if not include_deleted:
            conditions.append("deleted = 0")
        where_sql = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor = self._connection.execute(
            (
                "SELECT * FROM service_ontology_projection_relationship"
                f"{where_sql} ORDER BY class_config_relationship_id, "
                "source_class_instance_id, target_class_instance_id;"
            ),
            tuple(params),
        )
        return tuple(dict(row) for row in cursor.fetchall())

    def count_rows(self, *, table: str) -> int:
        if table not in _PROJECTION_TABLES:
            raise ValueError(
                f"Unsupported Service ontology projection table: {table!r}"
            )
        cursor = self._connection.execute(f"SELECT COUNT(*) FROM {table};")
        return int(cursor.fetchone()[0])

    def _apply_class_instance_change(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
        commit_payload: Mapping[str, object],
        class_change: Mapping[str, object],
        fallback_class_config_id: str | None,
        observed_at_unix_ms: int,
    ) -> ServiceOntologyProjectionApplyStats:
        class_instance_id = _required_uuid(class_change.get("class_instance_id"))
        change_payload = _payload_dict(class_change.get("change"))
        change_type = _enum_value(change_payload.get("type"))
        deleted = 1 if change_type == "delete" else 0
        deltas = tuple(_as_list(change_payload.get("change_deltas")))
        attributes = self._current_attributes(class_instance_id=class_instance_id)
        class_config_id = self._current_class_config_id(
            class_instance_id=class_instance_id
        )
        mutation_count = 0
        for delta in deltas:
            delta_payload = _payload_dict(delta)
            property_name = _optional_text(delta_payload.get("property"))
            if not property_name:
                continue
            value = _delta_value(delta_payload.get("payload"))
            if property_name == "class_config_id":
                class_config_id = _optional_text(value)
                mutation_count += 1
                continue
            attributes[property_name] = value
            mutation_count += 1
        if class_config_id is None:
            class_config_id = fallback_class_config_id
        if (
            fallback_class_config_id is not None
            and "source_object_id" not in attributes
        ):
            root_source_object_id = _optional_text(
                receipt.root_object_id
            ) or _optional_text(commit_payload.get("root_source_object_id"))
            if root_source_object_id is not None:
                attributes["source_object_id"] = root_source_object_id
        attribute_projection_by_id = _attribute_projection_by_id_for_class_config(
            class_config_id=class_config_id
        )
        for attribute_change in _as_list(class_change.get("attribute_changes")):
            attribute_change_payload = _payload_dict(attribute_change)
            attribute_id = _attribute_config_id_for_attribute_change(
                attribute_change_payload
            ) or _optional_text(attribute_change_payload.get("attribute_id"))
            if not attribute_id:
                continue
            attribute_projection = attribute_projection_by_id.get(attribute_id)
            if attribute_projection is None:
                continue
            attributes[attribute_projection.name] = _attribute_change_value(
                attribute_change_payload,
                projection=attribute_projection,
            )
            mutation_count += 1
        self._connection.execute(
            """
INSERT INTO service_ontology_projection_class_instance (
  id,
  branch_id,
  projection_hash,
  class_instance_id,
  class_config_id,
  object_instance_graph_id,
  root_object_id,
  attributes_json,
  deleted,
  updated_commit_id,
  updated_at_unix_ms
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(class_instance_id) DO UPDATE SET
  branch_id=excluded.branch_id,
  projection_hash=excluded.projection_hash,
  class_config_id=excluded.class_config_id,
  object_instance_graph_id=excluded.object_instance_graph_id,
  root_object_id=excluded.root_object_id,
  attributes_json=excluded.attributes_json,
  deleted=excluded.deleted,
  updated_commit_id=excluded.updated_commit_id,
  updated_at_unix_ms=excluded.updated_at_unix_ms;
""".strip(),
            (
                str(_class_instance_row_id(class_instance_id=class_instance_id)),
                str(receipt.branch_id),
                _projection_hash(receipt.projection_hash),
                str(class_instance_id),
                class_config_id,
                _optional_text(receipt.object_instance_graph_id)
                or _optional_text(commit_payload.get("object_instance_graph_id")),
                _optional_text(receipt.root_object_id)
                or _optional_text(commit_payload.get("root_source_object_id")),
                _json_dump(attributes),
                deleted,
                str(receipt.commit_id),
                observed_at_unix_ms,
            ),
        )
        return ServiceOntologyProjectionApplyStats(
            class_row_count=1,
            mutation_row_count=mutation_count,
        )

    def _apply_relationship_change(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
        relationship_change: Mapping[str, object],
        observed_at_unix_ms: int,
    ) -> ServiceOntologyProjectionApplyStats:
        change_payload = _payload_dict(relationship_change.get("change"))
        change_type = _enum_value(change_payload.get("type"))
        class_config_relationship_id = _required_uuid(
            relationship_change.get("class_config_relationship_id")
        )
        source_class_instance_id = _required_uuid(
            relationship_change.get("source_class_instance_id")
        )
        target_class_instance_id = _required_uuid(
            relationship_change.get("target_class_instance_id")
        )
        row_id = _relationship_row_id(
            class_config_relationship_id=class_config_relationship_id,
            source_class_instance_id=source_class_instance_id,
            target_class_instance_id=target_class_instance_id,
        )
        self._connection.execute(
            """
INSERT INTO service_ontology_projection_relationship (
  id,
  branch_id,
  projection_hash,
  class_config_relationship_id,
  source_class_instance_id,
  target_class_instance_id,
  deleted,
  updated_commit_id,
  updated_at_unix_ms
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  branch_id=excluded.branch_id,
  projection_hash=excluded.projection_hash,
  deleted=excluded.deleted,
  updated_commit_id=excluded.updated_commit_id,
  updated_at_unix_ms=excluded.updated_at_unix_ms;
""".strip(),
            (
                str(row_id),
                str(receipt.branch_id),
                _projection_hash(receipt.projection_hash),
                str(class_config_relationship_id),
                str(source_class_instance_id),
                str(target_class_instance_id),
                1 if change_type == "delete" else 0,
                str(receipt.commit_id),
                observed_at_unix_ms,
            ),
        )
        foreign_key_mutation_count = self._apply_relationship_foreign_key(
            receipt=receipt,
            class_config_relationship_id=class_config_relationship_id,
            source_class_instance_id=source_class_instance_id,
            target_class_instance_id=target_class_instance_id,
            deleted=change_type == "delete",
            observed_at_unix_ms=observed_at_unix_ms,
        )
        return ServiceOntologyProjectionApplyStats(
            association_row_count=1,
            mutation_row_count=1 + foreign_key_mutation_count,
        )

    def _apply_relationship_foreign_key(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
        class_config_relationship_id: UUID,
        source_class_instance_id: UUID,
        target_class_instance_id: UUID,
        deleted: bool,
        observed_at_unix_ms: int,
    ) -> int:
        source_row = self.fetch_class_instance(
            class_instance_id=source_class_instance_id
        )
        target_row = self.fetch_class_instance(
            class_instance_id=target_class_instance_id
        )
        if source_row is None or target_row is None:
            return 0
        projection = _relationship_foreign_key_projection(
            class_config_relationship_id=class_config_relationship_id,
            source_class_config_id=source_row.get("class_config_id"),
            target_class_config_id=target_row.get("class_config_id"),
        )
        if projection is None:
            return 0
        owner_row = source_row if projection.owner_is_source else target_row
        referenced_row = target_row if projection.owner_is_source else source_row
        referenced_attributes = _json_object(referenced_row.get("attributes_json"))
        referenced_source_object_id = _optional_text(
            referenced_attributes.get("source_object_id")
        )
        if referenced_source_object_id is None:
            return 0
        owner_class_instance_id = _required_uuid(owner_row.get("class_instance_id"))
        owner_attributes = _json_object(owner_row.get("attributes_json"))
        current_value = _optional_text(owner_attributes.get(projection.name))
        if deleted:
            if current_value != referenced_source_object_id:
                return 0
            owner_attributes.pop(projection.name, None)
        else:
            if current_value == referenced_source_object_id:
                return 0
            owner_attributes[projection.name] = referenced_source_object_id
        self._connection.execute(
            """
UPDATE service_ontology_projection_class_instance
SET attributes_json = ?, updated_commit_id = ?, updated_at_unix_ms = ?
WHERE class_instance_id = ?;
""".strip(),
            (
                _json_dump(owner_attributes),
                str(receipt.commit_id),
                observed_at_unix_ms,
                str(owner_class_instance_id),
            ),
        )
        return 1

    def _current_attributes(self, *, class_instance_id: UUID) -> dict[str, object]:
        row = self.fetch_class_instance(class_instance_id=class_instance_id)
        if row is None:
            return {}
        raw = row.get("attributes_json")
        if not isinstance(raw, str) or not raw.strip():
            return {}
        decoded = json.loads(raw)
        return dict(decoded) if isinstance(decoded, dict) else {}

    def _current_class_config_id(self, *, class_instance_id: UUID) -> str | None:
        row = self.fetch_class_instance(class_instance_id=class_instance_id)
        if row is None:
            return None
        return _optional_text(row.get("class_config_id"))


def _class_config_id_from_change(
    class_change: Mapping[str, object],
) -> str | None:
    change_payload = _payload_dict(class_change.get("change"))
    for delta in _as_list(change_payload.get("change_deltas")):
        delta_payload = _payload_dict(delta)
        if _optional_text(delta_payload.get("property")) != "class_config_id":
            continue
        return _optional_text(_delta_value(delta_payload.get("payload")))
    return None


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS service_ontology_projection_commit (
  id TEXT NOT NULL PRIMARY KEY,
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  commit_id TEXT NOT NULL UNIQUE,
  object_instance_graph_commit_id TEXT,
  graph_hash_post TEXT,
  object_instance_graph_id TEXT,
  root_object_id TEXT,
  applied_at_unix_ms INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS service_ontology_projection_class_instance (
  id TEXT NOT NULL PRIMARY KEY,
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  class_instance_id TEXT NOT NULL UNIQUE,
  class_config_id TEXT,
  object_instance_graph_id TEXT,
  root_object_id TEXT,
  attributes_json TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0,
  updated_commit_id TEXT NOT NULL,
  updated_at_unix_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS service_ontology_projection_relationship (
  id TEXT NOT NULL PRIMARY KEY,
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  class_config_relationship_id TEXT NOT NULL,
  source_class_instance_id TEXT NOT NULL,
  target_class_instance_id TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0,
  updated_commit_id TEXT NOT NULL,
  updated_at_unix_ms INTEGER NOT NULL
);
""".strip()

_PROJECTION_TABLES = {
    "service_ontology_projection_commit",
    "service_ontology_projection_class_instance",
    "service_ontology_projection_relationship",
}


def _payload_dict(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json", exclude_none=True)
        return dict(dumped) if isinstance(dumped, Mapping) else {}
    return {
        key: attr
        for key in dir(value)
        if not key.startswith("_")
        for attr in (getattr(value, key, None),)
        if not callable(attr)
    }


def _as_list(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def _delta_value(value: object) -> object:
    payload = _payload_dict(value)
    if "value" in payload:
        return payload["value"]
    return payload if payload else value


@dataclass(frozen=True, slots=True)
class _AttributeProjection:
    name: str
    enum_value_by_option_id: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _RelationshipForeignKeyProjection:
    name: str
    owner_is_source: bool


def _relationship_foreign_key_projection(
    *,
    class_config_relationship_id: UUID,
    source_class_config_id: object,
    target_class_config_id: object,
) -> _RelationshipForeignKeyProjection | None:
    try:
        from aware_orm.registry import ORMModelRegistry
    except Exception:
        return None
    class_config_ids: list[UUID] = []
    for raw_class_config_id in (
        source_class_config_id,
        target_class_config_id,
    ):
        try:
            class_config_id = UUID(str(raw_class_config_id))
        except (TypeError, ValueError):
            continue
        if class_config_id not in class_config_ids:
            class_config_ids.append(class_config_id)
    for class_config_id in class_config_ids:
        model_class = ORMModelRegistry.get_class_by_class_config_id(class_config_id)
        if model_class is None:
            continue
        get_class_config = getattr(model_class, "get_class_config", None)
        if not callable(get_class_config):
            continue
        class_config = get_class_config()
        if class_config is None:
            continue
        relationships = tuple(
            getattr(class_config, "class_config_relationships", ()) or ()
        )
        for relationship in relationships:
            if getattr(relationship, "id", None) != class_config_relationship_id:
                continue
            for binding in tuple(
                getattr(
                    relationship,
                    "class_config_relationship_attributes",
                    (),
                )
                or ()
            ):
                if _enum_value(getattr(binding, "role", None)) != "foreign_key":
                    continue
                direction = _enum_value(getattr(binding, "direction", None))
                if direction not in {"forward", "reverse"}:
                    continue
                owner_class_config_id = (
                    source_class_config_id
                    if direction == "forward"
                    else target_class_config_id
                )
                projections = _attribute_projection_by_id_for_class_config(
                    class_config_id=_optional_text(owner_class_config_id)
                )
                projection = projections.get(
                    str(getattr(binding, "attribute_config_id", ""))
                )
                if projection is None:
                    continue
                return _RelationshipForeignKeyProjection(
                    name=projection.name,
                    owner_is_source=direction == "forward",
                )
    return None


def _attribute_projection_by_id_for_class_config(
    *, class_config_id: str | None
) -> dict[str, _AttributeProjection]:
    if class_config_id is None:
        return {}
    try:
        class_config_uuid = UUID(str(class_config_id))
    except (TypeError, ValueError):
        return {}
    try:
        from aware_orm.registry import ORMModelRegistry
    except Exception:
        return {}
    model_class = ORMModelRegistry.get_class_by_class_config_id(class_config_uuid)
    if model_class is None:
        return {}
    get_class_config = getattr(model_class, "get_class_config", None)
    if not callable(get_class_config):
        return {}
    class_config = get_class_config()
    if class_config is None:
        return {}
    out: dict[str, _AttributeProjection] = {}
    for binding in tuple(getattr(class_config, "field_bindings", ()) or ()):
        field = getattr(binding, "field", None)
        name = _optional_text(getattr(field, "name", None))
        if not name:
            continue
        projection = _AttributeProjection(
            name=name,
            enum_value_by_option_id=_enum_value_by_option_id(
                model_class=model_class,
                field=field,
                field_name=name,
            ),
        )
        for raw_field_id in (
            getattr(binding, "field_id", None),
            getattr(field, "id", None),
        ):
            field_id = _optional_text(raw_field_id)
            if field_id:
                out[field_id] = projection
    return out


def _enum_value_by_option_id(
    *,
    model_class: type[object],
    field: object,
    field_name: str,
) -> dict[str, object]:
    value_type = getattr(field, "value_type", None)
    enum_config_id = getattr(value_type, "enum_id", None)
    if not isinstance(enum_config_id, UUID):
        try:
            enum_config_id = UUID(str(enum_config_id))
        except (TypeError, ValueError):
            return {}
    model_fields = getattr(model_class, "model_fields", {})
    model_field = model_fields.get(field_name)
    annotation = getattr(model_field, "annotation", None)
    enum_class = _enum_class_from_annotation(annotation)
    if enum_class is None:
        return {}
    return {
        str(
            stable_enum_option_id(
                enum_config_id=enum_config_id,
                value=str(member.value),
            )
        ): member.value
        for member in enum_class
    }


def _enum_class_from_annotation(annotation: object) -> type[Enum] | None:
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation
    for candidate in get_args(annotation):
        enum_class = _enum_class_from_annotation(candidate)
        if enum_class is not None:
            return enum_class
    return None


@dataclass(frozen=True, slots=True)
class _PayloadChangeDelta:
    found: bool
    value: object = None


@dataclass(frozen=True, slots=True)
class _EnumOptionReference:
    option_id: str


def _attribute_change_value(
    attribute_change: Mapping[str, object],
    *,
    projection: _AttributeProjection,
) -> object:
    value_root_change = _payload_dict(attribute_change.get("value_root_change"))
    value_root_value = _decode_attribute_value_change(value_root_change)
    if isinstance(value_root_value, _EnumOptionReference):
        if value_root_value.option_id not in projection.enum_value_by_option_id:
            raise ValueError(
                "Service ontology replica could not resolve enum option: "
                f"field={projection.name} option_id={value_root_value.option_id}"
            )
        return projection.enum_value_by_option_id[value_root_value.option_id]
    if value_root_change:
        return value_root_value

    attribute_delta = _payload_change_delta(
        attribute_change.get("change"),
        property_name="value",
    )
    if attribute_delta.found:
        return attribute_delta.value
    return None


def _decode_attribute_value_change(value_change: Mapping[str, object]) -> object:
    change = value_change.get("change")
    for property_name in (
        "primitive_value",
        "class_instance_id",
        "inline_value_instance_id",
    ):
        delta = _payload_change_delta(change, property_name=property_name)
        if delta.found:
            return delta.value
    enum_delta = _payload_change_delta(change, property_name="enum_option_id")
    if enum_delta.found:
        option_id = _optional_text(enum_delta.value)
        if option_id is None:
            return None
        return _EnumOptionReference(option_id=option_id)

    children: list[tuple[str, int, str, object]] = []
    for link_change in _as_list(value_change.get("attribute_value_link_changes")):
        link_payload = _payload_dict(link_change)
        link_change_payload = link_payload.get("change")
        if _enum_value(_payload_dict(link_change_payload).get("type")) == "delete":
            continue
        role_delta = _payload_change_delta(link_change_payload, property_name="role")
        position_delta = _payload_change_delta(
            link_change_payload,
            property_name="position",
        )
        identity_delta = _payload_change_delta(
            link_change_payload,
            property_name="identity_key",
        )
        child = _payload_dict(link_payload.get("child_attribute_value_change"))
        if not child:
            continue
        role = _optional_text(role_delta.value) if role_delta.found else None
        position = position_delta.value if position_delta.found else None
        identity_key = (
            _optional_text(identity_delta.value) if identity_delta.found else None
        )
        children.append(
            (
                (role or "").casefold(),
                position if isinstance(position, int) else 10_000,
                identity_key or "",
                _decode_attribute_value_change(child),
            )
        )
    if not children:
        return None

    children.sort(key=lambda item: (item[0], item[1], item[2]))
    roles = {item[0] for item in children}
    if roles <= {"key", "value"}:
        grouped: dict[str, dict[str, object]] = {}
        for role, _position, identity_key, value in children:
            grouped.setdefault(identity_key, {})[role] = value
        return {
            pair["key"]: pair["value"]
            for identity_key in sorted(grouped)
            for pair in (grouped[identity_key],)
            if "key" in pair and "value" in pair
        }
    values = [item[3] for item in children]
    if roles == {"member"} and len(values) == 1:
        return values[0]
    return values


def _attribute_config_id_for_attribute_change(
    attribute_change: Mapping[str, object],
) -> str | None:
    attribute_config_delta = _payload_change_delta(
        attribute_change.get("change"),
        property_name="attribute_config_id",
    )
    if attribute_config_delta.found:
        return _optional_text(attribute_config_delta.value)
    return None


def _payload_change_delta(
    change: object,
    *,
    property_name: str,
) -> _PayloadChangeDelta:
    change_payload = _payload_dict(change)
    for delta in _as_list(change_payload.get("change_deltas")):
        delta_payload = _payload_dict(delta)
        if _optional_text(delta_payload.get("property")) != property_name:
            continue
        return _PayloadChangeDelta(
            found=True,
            value=_delta_value(delta_payload.get("payload")),
        )
    return _PayloadChangeDelta(found=False)


def _required_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    raise ValueError(f"Expected UUID value, got {value!r}")


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _enum_value(value: object) -> str:
    enum_value = getattr(value, "value", value)
    return str(enum_value or "").strip().casefold()


def _projection_hash(value: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise ValueError("projection_hash must be non-empty")
    return token


def _json_dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, str) or not value.strip():
        return {}
    decoded = json.loads(value)
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def _unix_ms() -> int:
    return int(time() * 1000)


def _stable_uuid(*tokens: str) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        "aware.service.ontology_projection:" + ":".join(tokens),
    )


def _commit_row_id(*, commit_id: UUID) -> UUID:
    return _stable_uuid("commit", str(commit_id))


def _class_instance_row_id(*, class_instance_id: UUID) -> UUID:
    return _stable_uuid("class_instance", str(class_instance_id))


def _relationship_row_id(
    *,
    class_config_relationship_id: UUID,
    source_class_instance_id: UUID,
    target_class_instance_id: UUID,
) -> UUID:
    return _stable_uuid(
        "relationship",
        str(class_config_relationship_id),
        str(source_class_instance_id),
        str(target_class_instance_id),
    )


__all__ = [
    "EnvironmentApiServiceOntologyCommitSource",
    "LocalFsServiceOntologyCommitSource",
    "MetaLaneStoreServiceOntologyCommitSource",
    "ServiceOntologyCommitSource",
    "ServiceOntologyProjectionApplyStats",
    "ServiceOntologyProjectionStore",
]
