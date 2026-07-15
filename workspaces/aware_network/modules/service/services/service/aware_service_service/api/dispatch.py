from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, ContextManager, cast
from uuid import UUID

from aware_meta_service.local_sdk import MaterializationLaneContext
from aware_service_runtime.api_ingress.execution import (
    ExecutedServiceApiDispatch,
    ServiceApiStreamEventSink,
)
from aware_service_runtime.api_ingress.economy_settlement import (
    ServiceOperationEconomySettlementAdapter,
)
from aware_service_runtime.api_ingress.execution_context import (
    ServiceApiExecutionBackend,
    ServiceApiExecutionBackendMode,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceEnvironmentCommitReceiptSource,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    ServiceOntologyReplicaQueryProtocol,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    ServiceOntologyReplicaOrmSessionProtocol,
)
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    ServiceApiDispatchRequest,
    ServiceGraphGateway,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
)
from aware_service_runtime.implementation_package import (
    execute_activated_service_api_dispatch_request,
    load_committed_service_lane_session,
)
from aware_types import JsonObject


async def execute_service_api_dispatch(
    *,
    service_name: str,
    dispatch_request: ServiceApiDispatchRequest,
    actor_id: UUID | None = None,
    execution_backend: ServiceApiExecutionBackend | None = None,
    execution_backend_mode: ServiceApiExecutionBackendMode | None = None,
    stream_requested: bool = False,
    stream_event_sink: ServiceApiStreamEventSink | None = None,
    invocation_context: JsonObject | dict[str, object] | None = None,
    environment_api_client: object | None,
    resolve_activated_implementation_package: Callable[..., Any],
    resolve_dispatch_runtime_context: Callable[[], Any],
    build_economy_settlement_adapter: Callable[
        ..., ServiceOperationEconomySettlementAdapter | None
    ],
    ontology_orm_package_path_context: Callable[..., ContextManager[None]],
    graph_gateway_for_activated_package: Callable[..., ServiceGraphGateway],
    workspace_root: Path,
    ontology_authority_package_names: tuple[str, ...],
    ontology_authority_source_kind: str,
    ontology_authority_root: Path | None,
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...],
    meta_temporal_graph_route: MetaTemporalGraphRoute | None,
    build_environment_commit_receipt_source: Callable[
        [], ServiceEnvironmentCommitReceiptSource | None
    ],
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None,
    build_ontology_replica_orm_session: Callable[
        ..., ServiceOntologyReplicaOrmSessionProtocol | None
    ],
    resolve_activated_service_lane: Callable[..., MaterializationLaneContext],
    service_package_name_for_activated_binding: Callable[..., str | None],
) -> ExecutedServiceApiDispatch:
    effective_invocation_context: dict[str, object] = dict(
        cast(Mapping[str, object], invocation_context or {})
    )
    if environment_api_client is not None:
        effective_invocation_context.setdefault(
            "environment_api_client",
            environment_api_client,
        )
    activated_package = resolve_activated_implementation_package(
        service_name=service_name,
    )
    runtime_context = await resolve_dispatch_runtime_context()
    harness = runtime_context.runtime
    index = runtime_context.index
    lanes = runtime_context.lanes
    service_config_lane = resolve_activated_service_lane(
        activated=activated_package.binding,
        service_name=service_name,
        lane_attr="service_config_lanes_by_name",
        fallback=lanes.service_config,
    )
    service_lane = resolve_activated_service_lane(
        activated=activated_package.binding,
        service_name=service_name,
        lane_attr="service_lanes_by_name",
        fallback=lanes.service,
    )
    session = await load_committed_service_lane_session(
        index=index,
        lane=service_config_lane,
        error_context="Service host API dispatch",
    )
    economy_settlement_adapter = build_economy_settlement_adapter(
        actor_id=actor_id,
    )
    with ontology_orm_package_path_context(activated_package=activated_package):
        service_package_id = activated_package.service_package_id
        service_package_name = service_package_name_for_activated_binding(
            activated_package.binding
        )
        return await execute_activated_service_api_dispatch_request(
            activated=activated_package.binding,
            runtime=harness,
            index=index,
            session=cast(Any, session),
            actor_id=actor_id,
            target_lane=service_lane,
            service_package_id=service_package_id,
            service_package_name=service_package_name,
            service_name=service_name,
            dispatch_request=dispatch_request,
            execution_backend=execution_backend,
            execution_backend_mode=(
                execution_backend_mode
                if execution_backend_mode is not None
                else ServiceApiExecutionBackendMode.auto
            ),
            graph_gateway=graph_gateway_for_activated_package(
                activated_package=activated_package,
                service_name=service_name,
            ),
            meta_temporal_graph_route=meta_temporal_graph_route,
            workspace_root=workspace_root,
            stream_requested=stream_requested,
            stream_event_sink=stream_event_sink,
            economy_settlement_adapter=economy_settlement_adapter,
            invocation_context=effective_invocation_context,
            ontology_authority_package_names=ontology_authority_package_names,
            ontology_authority_source_kind=ontology_authority_source_kind,
            ontology_authority_root=ontology_authority_root,
            service_api_dependency_routes=service_api_dependency_routes,
            service_view_provider_routes=service_view_provider_routes,
            environment_commit_receipt_source=build_environment_commit_receipt_source(),
            ontology_replica_query=ontology_replica_query,
            ontology_replica_orm_session=build_ontology_replica_orm_session(
                branch_id=None,
            ),
        )


__all__ = ["execute_service_api_dispatch"]
