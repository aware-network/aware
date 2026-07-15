from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Protocol
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
    LaneCommitReceiptNotification,
)
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    ServiceGraphContextLike,
    ServiceGraphContextProvider,
    ServiceGraphGateway,
    ServiceLaneSubscriptionBinding,
    ServiceOperationContext,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    ServiceOntologyReplicaCommitSink,
    ServiceOntologyReplicaQueryProtocol,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    ServiceOntologyReplicaOrmSessionProtocol,
)
from aware_service_runtime.api_ingress.settlement import (
    ServiceOperationMeteringContextV1,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
)


class ServiceEnvironmentCommitReceiptSource(Protocol):
    """Environment-facing commit receipt source available to hosted API handlers."""

    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]: ...


class ServiceEnvironmentCommitReader(Protocol):
    """Environment-facing OIG commit readback port for hosted API handlers."""

    async def get_object_instance_graph_commit(
        self,
        *,
        commit_id: UUID,
        actor_id: UUID | None = None,
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class ServiceApiHostContext:
    operation_context: ServiceOperationContext
    environment_context: EnvironmentOperationContext | None = None
    workspace_root: Path | None = None
    graph_gateway: ServiceGraphGateway | None = None
    meta_temporal_graph_route: MetaTemporalGraphRoute | None = None
    graph_context_provider: ServiceGraphContextProvider | None = None
    service_name: str | None = None
    service_package_id: UUID | None = None
    service_package_name: str | None = None
    lane_subscriptions: tuple[ServiceLaneSubscriptionBinding, ...] = ()
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = ()
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...] = ()
    environment_commit_receipt_source: ServiceEnvironmentCommitReceiptSource | None = (
        None
    )
    environment_commit_reader: ServiceEnvironmentCommitReader | None = None
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] = field(
        default_factory=dict
    )
    invocation_context: Mapping[str, object] | None = None
    operation_metering_context: ServiceOperationMeteringContextV1 | None = None
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None = None
    ontology_replica_commit_sink: ServiceOntologyReplicaCommitSink | None = None
    ontology_replica_orm_session: ServiceOntologyReplicaOrmSessionProtocol | None = None
    ontology_authority_package_names: tuple[str, ...] = ()
    ontology_authority_source_kind: str | None = None
    ontology_authority_root: Path | None = None
    materialization: "ServiceApiMaterializationContext | None" = None


@dataclass(frozen=True, slots=True)
class ServiceApiMaterializationContext:
    runtime: object
    graph_context: ServiceGraphContextLike
    target_lane: MaterializationLaneContext


_current_service_api_host_context: ContextVar[ServiceApiHostContext | None] = (
    ContextVar(
        "service_api_host_context",
        default=None,
    )
)


@contextmanager
def service_api_host_context(
    *,
    operation_context: ServiceOperationContext,
    environment_context: EnvironmentOperationContext | None = None,
    workspace_root: Path | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    meta_temporal_graph_route: MetaTemporalGraphRoute | None = None,
    graph_context_provider: ServiceGraphContextProvider | None = None,
    service_name: str | None = None,
    service_package_id: UUID | None = None,
    service_package_name: str | None = None,
    lane_subscriptions: tuple[ServiceLaneSubscriptionBinding, ...] = (),
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = (),
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...] = (),
    environment_commit_receipt_source: ServiceEnvironmentCommitReceiptSource | None = (
        None
    ),
    environment_commit_reader: ServiceEnvironmentCommitReader | None = None,
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    invocation_context: Mapping[str, object] | None = None,
    operation_metering_context: ServiceOperationMeteringContextV1 | None = None,
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None = None,
    ontology_replica_orm_session: (
        ServiceOntologyReplicaOrmSessionProtocol | None
    ) = None,
    ontology_authority_package_names: tuple[str, ...] = (),
    ontology_authority_source_kind: str | None = None,
    ontology_authority_root: Path | None = None,
    materialization: ServiceApiMaterializationContext | None = None,
) -> Iterator[ServiceApiHostContext]:
    context = ServiceApiHostContext(
        operation_context=operation_context,
        environment_context=environment_context,
        workspace_root=workspace_root,
        graph_gateway=graph_gateway,
        meta_temporal_graph_route=meta_temporal_graph_route,
        graph_context_provider=graph_context_provider,
        service_name=service_name,
        service_package_id=service_package_id,
        service_package_name=service_package_name,
        lane_subscriptions=lane_subscriptions,
        service_api_dependency_routes=service_api_dependency_routes,
        service_view_provider_routes=service_view_provider_routes,
        environment_commit_receipt_source=environment_commit_receipt_source,
        environment_commit_reader=environment_commit_reader,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name or {}
        ),
        invocation_context=invocation_context,
        operation_metering_context=operation_metering_context,
        ontology_replica_query=ontology_replica_query,
        ontology_replica_commit_sink=(
            graph_gateway
            if isinstance(graph_gateway, ServiceOntologyReplicaCommitSink)
            else None
        ),
        ontology_replica_orm_session=ontology_replica_orm_session,
        ontology_authority_package_names=ontology_authority_package_names,
        ontology_authority_source_kind=ontology_authority_source_kind,
        ontology_authority_root=ontology_authority_root,
        materialization=materialization,
    )
    token = _current_service_api_host_context.set(context)
    try:
        if ontology_replica_orm_session is None:
            yield context
        else:
            from aware_orm.session.current_session_ctx import set_session

            with set_session(ontology_replica_orm_session):
                yield context
    finally:
        _current_service_api_host_context.reset(token)


def current_service_api_host_context() -> ServiceApiHostContext | None:
    return _current_service_api_host_context.get()


def require_current_service_api_materialization_context() -> (
    ServiceApiMaterializationContext
):
    host_context = current_service_api_host_context()
    if host_context is None or host_context.materialization is None:
        raise RuntimeError(
            "Service API handler requires an active materialization context."
        )
    return host_context.materialization


__all__ = [
    "ServiceApiHostContext",
    "ServiceApiMaterializationContext",
    "ServiceEnvironmentCommitReader",
    "ServiceEnvironmentCommitReceiptSource",
    "current_service_api_host_context",
    "require_current_service_api_materialization_context",
    "service_api_host_context",
]
