from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable
from uuid import UUID


class ServiceOntologyProjectedClassInstance(Protocol):
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


class ServiceOntologyProjectedRelationship(Protocol):
    branch_id: UUID
    projection_hash: str
    class_config_relationship_id: UUID
    source_class_instance_id: UUID
    target_class_instance_id: UUID
    deleted: bool
    updated_commit_id: UUID
    updated_at_unix_ms: int


class ServiceOntologyReplicaQueryProtocol(Protocol):
    def get_class_instance(
        self,
        *,
        instance_id: UUID,
        include_deleted: bool = False,
    ) -> ServiceOntologyProjectedClassInstance | None: ...

    def list_class_instances(
        self,
        *,
        class_config_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[ServiceOntologyProjectedClassInstance, ...]: ...

    def get_attribute(
        self,
        *,
        instance_id: UUID,
        key: str,
        include_deleted: bool = False,
    ) -> object | None: ...

    def find_by_attribute(
        self,
        *,
        key: str,
        value: object,
        class_config_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[ServiceOntologyProjectedClassInstance, ...]: ...

    def list_relationships(
        self,
        *,
        source_id: UUID | None = None,
        target_id: UUID | None = None,
        relationship_id: UUID | None = None,
        projection_hash: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[ServiceOntologyProjectedRelationship, ...]: ...


@runtime_checkable
class ServiceOntologyReplicaCommitSink(Protocol):
    async def mirror_committed_lane(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        actor_id: UUID | None = None,
    ) -> None: ...


def current_service_ontology_replica_query() -> (
    ServiceOntologyReplicaQueryProtocol | None
):
    from aware_service_runtime.api_ingress.host_context import (
        current_service_api_host_context,
    )

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return host_context.ontology_replica_query


def require_service_ontology_replica_query() -> ServiceOntologyReplicaQueryProtocol:
    query = current_service_ontology_replica_query()
    if query is None:
        raise RuntimeError(
            "Service ontology replica query requires an active Service API host "
            "context with ontology replica projection configured."
        )
    return query


def current_service_ontology_replica_commit_sink() -> (
    ServiceOntologyReplicaCommitSink | None
):
    from aware_service_runtime.api_ingress.host_context import (
        current_service_api_host_context,
    )

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return host_context.ontology_replica_commit_sink


def require_service_ontology_replica_commit_sink() -> ServiceOntologyReplicaCommitSink:
    sink = current_service_ontology_replica_commit_sink()
    if sink is None:
        raise RuntimeError(
            "Service ontology replica commit mirroring requires an active Service "
            "API host context with a local replica commit sink."
        )
    return sink


__all__ = [
    "ServiceOntologyProjectedClassInstance",
    "ServiceOntologyProjectedRelationship",
    "ServiceOntologyReplicaCommitSink",
    "ServiceOntologyReplicaQueryProtocol",
    "current_service_ontology_replica_commit_sink",
    "current_service_ontology_replica_query",
    "require_service_ontology_replica_commit_sink",
    "require_service_ontology_replica_query",
]
