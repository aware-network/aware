from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from typing import Any
from uuid import UUID

from .projector import ServiceOntologyProjectionStore


@dataclass(frozen=True, slots=True)
class ProjectedClassInstance:
    branch_id: UUID
    projection_hash: str
    class_instance_id: UUID
    class_config_id: UUID | None
    object_instance_graph_id: UUID | None
    root_object_id: UUID | None
    attributes: Mapping[str, object]
    deleted: bool
    updated_commit_id: UUID
    updated_at_unix_ms: int


@dataclass(frozen=True, slots=True)
class ProjectedRelationship:
    branch_id: UUID
    projection_hash: str
    class_config_relationship_id: UUID
    source_class_instance_id: UUID
    target_class_instance_id: UUID
    deleted: bool
    updated_commit_id: UUID
    updated_at_unix_ms: int


@dataclass(frozen=True, slots=True)
class ServiceOntologyReplicaQuery:
    """Typed read facade over the Service-owned ontology projection DB."""

    projection_store: ServiceOntologyProjectionStore

    def get_class_instance(
        self,
        *,
        instance_id: UUID,
        include_deleted: bool = False,
    ) -> ProjectedClassInstance | None:
        row = self.projection_store.fetch_class_instance(class_instance_id=instance_id)
        if row is None:
            return None
        projected = _class_instance_from_row(row)
        if projected.deleted and not include_deleted:
            return None
        return projected

    def list_class_instances(
        self,
        *,
        class_config_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[ProjectedClassInstance, ...]:
        return tuple(
            _class_instance_from_row(row)
            for row in self.projection_store.list_class_instances(
                class_config_id=class_config_id,
                projection_hash=projection_hash,
                include_deleted=include_deleted,
            )
        )

    def get_attribute(
        self,
        *,
        instance_id: UUID,
        key: str,
        include_deleted: bool = False,
    ) -> object | None:
        instance = self.get_class_instance(
            instance_id=instance_id,
            include_deleted=include_deleted,
        )
        if instance is None:
            return None
        return dict(instance.attributes).get(_attribute_key(key))

    def find_by_attribute(
        self,
        *,
        key: str,
        value: object,
        class_config_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[ProjectedClassInstance, ...]:
        return tuple(
            _class_instance_from_row(row)
            for row in self.projection_store.find_class_instances_by_attribute(
                key=_attribute_key(key),
                value=value,
                class_config_id=class_config_id,
                projection_hash=projection_hash,
                include_deleted=include_deleted,
            )
        )

    def list_relationships(
        self,
        *,
        source_id: UUID | None = None,
        target_id: UUID | None = None,
        relationship_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[ProjectedRelationship, ...]:
        return tuple(
            _relationship_from_row(row)
            for row in self.projection_store.list_relationships(
                class_config_relationship_id=relationship_id,
                source_class_instance_id=source_id,
                target_class_instance_id=target_id,
                projection_hash=projection_hash,
                include_deleted=include_deleted,
            )
        )


def _class_instance_from_row(row: Mapping[str, Any]) -> ProjectedClassInstance:
    return ProjectedClassInstance(
        branch_id=_required_uuid(row.get("branch_id"), "branch_id"),
        projection_hash=_required_text(row.get("projection_hash"), "projection_hash"),
        class_instance_id=_required_uuid(
            row.get("class_instance_id"),
            "class_instance_id",
        ),
        class_config_id=_optional_uuid(row.get("class_config_id")),
        object_instance_graph_id=_optional_uuid(row.get("object_instance_graph_id")),
        root_object_id=_optional_uuid(row.get("root_object_id")),
        attributes=_attributes(row.get("attributes_json")),
        deleted=bool(row.get("deleted")),
        updated_commit_id=_required_uuid(
            row.get("updated_commit_id"),
            "updated_commit_id",
        ),
        updated_at_unix_ms=int(row.get("updated_at_unix_ms") or 0),
    )


def _relationship_from_row(row: Mapping[str, Any]) -> ProjectedRelationship:
    return ProjectedRelationship(
        branch_id=_required_uuid(row.get("branch_id"), "branch_id"),
        projection_hash=_required_text(row.get("projection_hash"), "projection_hash"),
        class_config_relationship_id=_required_uuid(
            row.get("class_config_relationship_id"),
            "class_config_relationship_id",
        ),
        source_class_instance_id=_required_uuid(
            row.get("source_class_instance_id"),
            "source_class_instance_id",
        ),
        target_class_instance_id=_required_uuid(
            row.get("target_class_instance_id"),
            "target_class_instance_id",
        ),
        deleted=bool(row.get("deleted")),
        updated_commit_id=_required_uuid(
            row.get("updated_commit_id"),
            "updated_commit_id",
        ),
        updated_at_unix_ms=int(row.get("updated_at_unix_ms") or 0),
    )


def _attributes(value: object) -> Mapping[str, object]:
    if not isinstance(value, str) or not value.strip():
        return {}
    decoded = json.loads(value)
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def _attribute_key(value: object) -> str:
    token = str(value or "").strip()
    if not token:
        raise ValueError("Service ontology replica attribute key must be non-empty.")
    return token


def _required_uuid(value: object, field_name: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise ValueError(f"Service ontology projection row missing {field_name}.")
    return parsed


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _required_text(value: object, field_name: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise ValueError(f"Service ontology projection row missing {field_name}.")
    return token


__all__ = [
    "ProjectedClassInstance",
    "ProjectedRelationship",
    "ServiceOntologyReplicaQuery",
]
