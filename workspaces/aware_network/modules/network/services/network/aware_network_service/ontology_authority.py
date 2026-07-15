from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_network_ontology.stable_ids import (
    stable_network_node_id,
    stable_network_node_peer_id,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverTerritoryRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverTerritoryResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkEnvironmentDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkHostedServiceDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListEnvironmentsRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListEnvironmentsResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListHostedServicesRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListHostedServicesResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListPeersRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListPeersResponse,
)
from aware_network_service_dto.comms.models.network_service import NetworkPeerDescriptor
from aware_network_service_dto.comms.models.network_service import (
    NetworkPeerFanoutRuleDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationCommitReceipt,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationCoverage,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishEnvironmentRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishEnvironmentResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishHostedServiceRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishHostedServiceResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkRegisterNodeRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkRegisterNodeResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkReconcileNodePublicationRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkReconcileNodePublicationResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkResolveHostedServiceRoutesRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkResolveHostedServiceRoutesResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkUpsertPeerRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkUpsertPeerResponse,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    ServiceOntologyReplicaQueryProtocol,
    require_service_ontology_replica_query,
)
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceOperationContext,
)

from .topology_authority import (
    InMemoryNetworkTopologyAuthority,
    NetworkTopologyAuthority,
)


@dataclass(frozen=True, slots=True)
class NetworkOntologyRuntimeContext:
    graph_gateway: ServiceGraphGateway
    operation_context: ServiceOperationContext
    environment_context: EnvironmentOperationContext
    runtime_index: MetaGraphRuntimeIndex
    network_node_opg_id: UUID
    network_node_projection_hash: str
    network_node_class_config_id: UUID
    network_node_environment_class_config_id: UUID
    network_node_environment_portal_relationship_id: UUID
    network_node_service_class_config_id: UUID
    network_node_service_package_portal_relationship_id: UUID
    network_node_register_function_id: UUID
    network_node_upsert_environment_function_id: UUID
    network_node_attach_service_function_id: UUID
    network_node_peer_opg_id: UUID
    network_node_peer_projection_hash: str
    network_node_peer_create_function_id: UUID


@dataclass(slots=True)
class NetworkOntologyTopologyAuthority:
    """Commit-backed Network authority.

    Mutations go through the hosted Service graph gateway and produce OIG commits.
    Convergence is verified against the Service-owned committed ontology replica;
    the bounded DTO mirror only supplies richer response descriptors.
    """

    graph_gateway: ServiceGraphGateway
    operation_context: ServiceOperationContext
    environment_context: EnvironmentOperationContext | None
    read_model: InMemoryNetworkTopologyAuthority
    _runtime_context: NetworkOntologyRuntimeContext | None = None

    async def reconcile_node_publication(
        self,
        request: NetworkReconcileNodePublicationRequest,
    ) -> NetworkReconcileNodePublicationResponse:
        intent = request.intent
        runtime_context = await self.runtime_context()
        actor_id = (
            request.actor_id
            or self.operation_context.actor_id
            or runtime_context.environment_context.actor_id
        )
        if actor_id is None:
            raise RuntimeError(
                "Network publication reconciliation requires a Node system Actor."
            )
        if not intent.publication_digest.strip():
            raise RuntimeError(
                "Network publication intent requires publication_digest."
            )
        if (
            intent.environment.environment_id
            != runtime_context.environment_context.environment_id
        ):
            raise RuntimeError(
                "Network publication intent Environment does not match the accepted "
                "Service operation context."
            )
        service_package_ids = [
            service.service_package_id for service in intent.hosted_services
        ]
        if len(service_package_ids) != len(set(service_package_ids)):
            raise RuntimeError(
                "Network publication intent contains duplicate service_package_id values."
            )

        receipts: list[NetworkNodePublicationCommitReceipt] = []
        node_response = await _invoke_constructor(
            runtime_context=runtime_context,
            branch_id=intent.node.node_id,
            object_projection_graph_id=runtime_context.network_node_opg_id,
            projection_hash=runtime_context.network_node_projection_hash,
            function_id=runtime_context.network_node_register_function_id,
            actor_id=actor_id,
            kwargs={
                "public_key": intent.node.public_key,
                "hostname": intent.node.hostname,
                "port": intent.node.port,
                "base_url": intent.node.base_url,
                "node_id": intent.node.node_id,
                "system_actor_id": actor_id,
                "status": intent.node.status,
            },
            context="network.publication.reconcile_node",
        )
        receipts.append(_publication_commit_receipt("register_node", node_response))

        environment_response = await _invoke_instance(
            runtime_context=runtime_context,
            branch_id=intent.node.node_id,
            object_id=UUID(str(node_response.root_object_id or intent.node.node_id)),
            projection_hash=runtime_context.network_node_projection_hash,
            function_id=runtime_context.network_node_upsert_environment_function_id,
            actor_id=actor_id,
            kwargs={
                "environment_id": intent.environment.environment_id,
                "role": intent.environment.role,
                "is_active": intent.environment.is_active,
                "priority": intent.environment.priority,
            },
            context="network.publication.reconcile_environment",
        )
        receipts.append(
            _publication_commit_receipt("upsert_environment", environment_response)
        )

        for service in intent.hosted_services:
            service_response = await _invoke_instance(
                runtime_context=runtime_context,
                branch_id=intent.node.node_id,
                object_id=UUID(
                    str(node_response.root_object_id or intent.node.node_id)
                ),
                projection_hash=runtime_context.network_node_projection_hash,
                function_id=runtime_context.network_node_attach_service_function_id,
                actor_id=actor_id,
                kwargs={
                    "service_package_id": service.service_package_id,
                    "service_id": service.service_id,
                    "service_name": service.service_name,
                    "host_id": service.host_id,
                    "protocol_version": service.protocol_version,
                    "endpoint_refs": service.endpoint_refs,
                    "stream_endpoint_refs": service.stream_endpoint_refs,
                    "host_version": service.host_version,
                    "supports_stream_events": service.supports_stream_events,
                },
                context="network.publication.reconcile_hosted_service",
            )
            receipts.append(
                _publication_commit_receipt(
                    f"attach_service:{service.service_package_id}", service_response
                )
            )

        response_view = await self.read_model.reconcile_node_publication(request)
        coverage = _committed_publication_coverage(
            replica=require_service_ontology_replica_query(),
            runtime_context=runtime_context,
            request=request,
        )
        converged = (
            coverage.node_registered
            and coverage.environment_published
            and not coverage.missing_hosted_service_package_ids
            and not coverage.unexpected_hosted_service_package_ids
        )
        return response_view.model_copy(
            update={
                "success": True,
                "status": "converged" if converged else "progressed",
                "error": None,
                "coverage": coverage,
                "commit_receipts": receipts,
            }
        )

    async def register_node(
        self,
        request: NetworkRegisterNodeRequest,
    ) -> NetworkRegisterNodeResponse:
        runtime_context = await self.runtime_context()
        branch_id = request.node_id or stable_network_node_id(
            public_key=request.public_key.strip()
        )
        response = await _invoke_constructor(
            runtime_context=runtime_context,
            branch_id=branch_id,
            object_projection_graph_id=runtime_context.network_node_opg_id,
            projection_hash=runtime_context.network_node_projection_hash,
            function_id=runtime_context.network_node_register_function_id,
            actor_id=request.actor_id,
            kwargs={
                "public_key": request.public_key,
                "hostname": request.hostname,
                "port": request.port,
                "base_url": request.base_url,
                "node_id": request.node_id,
                "system_actor_id": request.actor_id,
                "status": request.status,
            },
            context="network.node.register",
        )
        committed_node_id = UUID(str(response.root_object_id or branch_id))
        return await self.read_model.register_node(
            request.model_copy(update={"node_id": committed_node_id})
        )

    async def upsert_peer(
        self,
        request: NetworkUpsertPeerRequest,
    ) -> NetworkUpsertPeerResponse:
        runtime_context = await self.runtime_context()
        branch_id = stable_network_node_peer_id(
            source_peer_node_id=request.source_node_id,
            target_peer_node_id=request.target_node_id,
        )
        await _invoke_constructor(
            runtime_context=runtime_context,
            branch_id=branch_id,
            object_projection_graph_id=runtime_context.network_node_peer_opg_id,
            projection_hash=runtime_context.network_node_peer_projection_hash,
            function_id=runtime_context.network_node_peer_create_function_id,
            actor_id=request.actor_id,
            kwargs={
                "network_node_id": request.source_node_id,
                "peer_node_id": request.target_node_id,
                "peer_http_base_url": request.target_base_url,
            },
            context="network.peer.upsert",
        )
        return await self.read_model.upsert_peer(request)

    async def list_peers(
        self,
        request: NetworkListPeersRequest,
    ) -> NetworkListPeersResponse:
        return await self.read_model.list_peers(request)

    async def publish_hosted_service(
        self,
        request: NetworkPublishHostedServiceRequest,
    ) -> NetworkPublishHostedServiceResponse:
        if request.service_package_id is None:
            return NetworkPublishHostedServiceResponse(
                request_id=request.request_id,
                success=False,
                error=(
                    "Network hosted-service publication requires " "service_package_id."
                ),
            )
        runtime_context = await self.runtime_context()
        await _invoke_instance(
            runtime_context=runtime_context,
            branch_id=request.node_id,
            object_id=request.node_id,
            projection_hash=runtime_context.network_node_projection_hash,
            function_id=runtime_context.network_node_attach_service_function_id,
            actor_id=request.actor_id,
            kwargs={
                "service_package_id": request.service_package_id,
                "service_id": request.service_id,
                "host_id": request.host_id,
                "protocol_version": request.protocol_version,
                "endpoint_refs": request.endpoint_refs,
                "stream_endpoint_refs": request.stream_endpoint_refs,
                "host_version": request.host_version,
                "supports_stream_events": request.supports_stream_events,
            },
            context="network.hosted_service.publish",
        )
        return await self.read_model.publish_hosted_service(request)

    async def list_hosted_services(
        self,
        request: NetworkListHostedServicesRequest,
    ) -> NetworkListHostedServicesResponse:
        return await self.read_model.list_hosted_services(request)

    async def publish_environment(
        self,
        request: NetworkPublishEnvironmentRequest,
    ) -> NetworkPublishEnvironmentResponse:
        runtime_context = await self.runtime_context()
        await _invoke_instance(
            runtime_context=runtime_context,
            branch_id=request.node_id,
            object_id=request.node_id,
            projection_hash=runtime_context.network_node_projection_hash,
            function_id=runtime_context.network_node_upsert_environment_function_id,
            actor_id=request.actor_id,
            kwargs={
                "environment_id": request.environment_id,
                "role": request.role,
                "is_active": request.is_active,
                "priority": request.priority,
            },
            context="network.environment.publish",
        )
        return await self.read_model.publish_environment(request)

    async def list_environments(
        self,
        request: NetworkListEnvironmentsRequest,
    ) -> NetworkListEnvironmentsResponse:
        return await self.read_model.list_environments(request)

    async def resolve_hosted_service_routes(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> NetworkResolveHostedServiceRoutesResponse:
        return await self.read_model.resolve_hosted_service_routes(request)

    async def discover_territory(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> NetworkDiscoverTerritoryResponse:
        return await self.read_model.discover_territory(request)

    async def discover_experience_territory(
        self,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> NetworkDiscoverExperienceTerritoryResponse:
        return await self.read_model.discover_experience_territory(request)

    async def runtime_context(self) -> NetworkOntologyRuntimeContext:
        if self._runtime_context is not None:
            return self._runtime_context
        runtime_index = cast(
            MetaGraphRuntimeIndex, await self.graph_gateway.resolve_graph_context()
        )
        context = resolve_network_ontology_runtime_context(
            graph_gateway=self.graph_gateway,
            operation_context=self.operation_context,
            environment_context=self.environment_context,
            runtime_index=runtime_index,
        )
        self._runtime_context = context
        return context


@dataclass(slots=True)
class HostContextNetworkTopologyAuthority:
    """Select graph-backed authority inside ServiceHost, fallback outside it."""

    fallback: InMemoryNetworkTopologyAuthority = field(
        default_factory=InMemoryNetworkTopologyAuthority
    )

    def _authority(self) -> NetworkTopologyAuthority:
        host_context = current_service_api_host_context()
        if host_context is None:
            return self.fallback
        if host_context.graph_gateway is None:
            raise RuntimeError(
                "Network service protocol requires a Service graph gateway in host context."
            )
        return NetworkOntologyTopologyAuthority(
            graph_gateway=host_context.graph_gateway,
            operation_context=host_context.operation_context,
            environment_context=host_context.environment_context,
            read_model=self.fallback,
        )

    async def reconcile_node_publication(
        self,
        request: NetworkReconcileNodePublicationRequest,
    ) -> NetworkReconcileNodePublicationResponse:
        return await self._authority().reconcile_node_publication(request)

    async def register_node(
        self,
        request: NetworkRegisterNodeRequest,
    ) -> NetworkRegisterNodeResponse:
        return await self._authority().register_node(request)

    async def upsert_peer(
        self,
        request: NetworkUpsertPeerRequest,
    ) -> NetworkUpsertPeerResponse:
        return await self._authority().upsert_peer(request)

    async def list_peers(
        self,
        request: NetworkListPeersRequest,
    ) -> NetworkListPeersResponse:
        return await self._authority().list_peers(request)

    async def publish_hosted_service(
        self,
        request: NetworkPublishHostedServiceRequest,
    ) -> NetworkPublishHostedServiceResponse:
        return await self._authority().publish_hosted_service(request)

    async def list_hosted_services(
        self,
        request: NetworkListHostedServicesRequest,
    ) -> NetworkListHostedServicesResponse:
        return await self._authority().list_hosted_services(request)

    async def publish_environment(
        self,
        request: NetworkPublishEnvironmentRequest,
    ) -> NetworkPublishEnvironmentResponse:
        return await self._authority().publish_environment(request)

    async def list_environments(
        self,
        request: NetworkListEnvironmentsRequest,
    ) -> NetworkListEnvironmentsResponse:
        return await self._authority().list_environments(request)

    async def resolve_hosted_service_routes(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> NetworkResolveHostedServiceRoutesResponse:
        return await self._authority().resolve_hosted_service_routes(request)

    async def discover_territory(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> NetworkDiscoverTerritoryResponse:
        return await self._authority().discover_territory(request)

    async def discover_experience_territory(
        self,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> NetworkDiscoverExperienceTerritoryResponse:
        return await self._authority().discover_experience_territory(request)


def resolve_network_ontology_runtime_context(
    *,
    graph_gateway: ServiceGraphGateway,
    operation_context: ServiceOperationContext,
    environment_context: EnvironmentOperationContext | None,
    runtime_index: MetaGraphRuntimeIndex,
) -> NetworkOntologyRuntimeContext:
    if environment_context is None:
        raise RuntimeError(
            "Network service ontology mutations require an Environment operation "
            "context in the Service API host context."
        )
    network_node_projection, network_node_class_config = (
        _resolve_projection_and_root_class(
            runtime_index=runtime_index,
            projection_name="NetworkNode",
            root_class_name="NetworkNode",
        )
    )
    network_node_environment_class_config = _resolve_projection_class(
        runtime_index=runtime_index,
        projection=network_node_projection,
        class_name="NetworkNodeEnvironment",
    )
    network_node_service_class_config = _resolve_projection_class(
        runtime_index=runtime_index,
        projection=network_node_projection,
        class_name="NetworkNodeService",
    )
    network_node_peer_projection, network_node_peer_class_config = (
        _resolve_projection_and_root_class(
            runtime_index=runtime_index,
            projection_name="NetworkNodePeer",
            root_class_name="NetworkNodePeer",
        )
    )
    return NetworkOntologyRuntimeContext(
        graph_gateway=graph_gateway,
        operation_context=operation_context,
        environment_context=environment_context,
        runtime_index=runtime_index,
        network_node_opg_id=network_node_projection.id,
        network_node_projection_hash=str(network_node_projection.projection_hash),
        network_node_class_config_id=UUID(str(network_node_class_config.id)),
        network_node_environment_class_config_id=UUID(
            str(network_node_environment_class_config.id)
        ),
        network_node_environment_portal_relationship_id=_resolve_relationship_id(
            class_config=network_node_environment_class_config,
            relationship_key="environment",
        ),
        network_node_service_class_config_id=UUID(
            str(network_node_service_class_config.id)
        ),
        network_node_service_package_portal_relationship_id=(
            _resolve_relationship_id(
                class_config=network_node_service_class_config,
                relationship_key="service_package",
            )
        ),
        network_node_register_function_id=_resolve_function_id(
            class_config=network_node_class_config,
            function_name="register",
        ),
        network_node_upsert_environment_function_id=_resolve_function_id(
            class_config=network_node_class_config,
            function_name="upsert_environment",
        ),
        network_node_attach_service_function_id=_resolve_function_id(
            class_config=network_node_class_config,
            function_name="attach_service",
        ),
        network_node_peer_opg_id=network_node_peer_projection.id,
        network_node_peer_projection_hash=str(
            network_node_peer_projection.projection_hash
        ),
        network_node_peer_create_function_id=_resolve_function_id(
            class_config=network_node_peer_class_config,
            function_name="create",
        ),
    )


async def _invoke_constructor(
    *,
    runtime_context: NetworkOntologyRuntimeContext,
    branch_id: UUID,
    object_projection_graph_id: UUID,
    projection_hash: str,
    function_id: UUID,
    actor_id: UUID | None,
    kwargs: dict[str, object],
    context: str,
) -> InvokeFunctionResponse:
    operation_context = runtime_context.operation_context
    environment_context = runtime_context.environment_context
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id
            or operation_context.actor_id
            or environment_context.actor_id,
            environment_id=environment_context.environment_id,
            process_id=environment_context.process_id,
            thread_id=environment_context.thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.opg_constructor,
            object_projection_graph_id=object_projection_graph_id,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(
                JsonObject,
                {key: value for key, value in kwargs.items() if value is not None},
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(response=response, context=context)
    return response


async def _invoke_instance(
    *,
    runtime_context: NetworkOntologyRuntimeContext,
    branch_id: UUID,
    object_id: UUID,
    projection_hash: str,
    function_id: UUID,
    actor_id: UUID | None,
    kwargs: dict[str, object],
    context: str,
) -> InvokeFunctionResponse:
    operation_context = runtime_context.operation_context
    environment_context = runtime_context.environment_context
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id
            or operation_context.actor_id
            or environment_context.actor_id,
            environment_id=environment_context.environment_id,
            process_id=environment_context.process_id,
            thread_id=environment_context.thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=object_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(JsonObject, kwargs),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(response=response, context=context)
    return response


def _publication_commit_receipt(
    operation: str,
    response: InvokeFunctionResponse,
) -> NetworkNodePublicationCommitReceipt:
    return NetworkNodePublicationCommitReceipt(
        operation=operation,
        domain_commit_id=response.commit_id,
        object_instance_graph_commit_id=response.object_instance_graph_commit_id,
        root_object_id=response.root_object_id,
    )


def _ensure_invoke_succeeded(
    *,
    response: InvokeFunctionResponse,
    context: str,
) -> None:
    if _response_succeeded(response):
        return
    raise RuntimeError(f"{context} failed: {response.error or response.status}")


def _response_succeeded(response: InvokeFunctionResponse) -> bool:
    return (response.status or "").strip().casefold() == "succeeded"


def _committed_publication_coverage(
    *,
    replica: ServiceOntologyReplicaQueryProtocol,
    runtime_context: NetworkOntologyRuntimeContext,
    request: NetworkReconcileNodePublicationRequest,
) -> NetworkNodePublicationCoverage:
    intent = request.intent
    projection_hash = runtime_context.network_node_projection_hash
    node_record = replica.get_class_instance(instance_id=intent.node.node_id)
    node_registered = bool(
        node_record is not None
        and node_record.class_config_id == runtime_context.network_node_class_config_id
        and node_record.projection_hash == projection_hash
        and node_record.branch_id == intent.node.node_id
        and node_record.root_object_id == intent.node.node_id
    )

    environment_ids: set[UUID] = set()
    environment_records = replica.list_class_instances(
        class_config_id=runtime_context.network_node_environment_class_config_id,
        projection_hash=projection_hash,
    )
    for record in environment_records:
        if record.branch_id != intent.node.node_id:
            continue
        environment_ids.update(
            relationship.target_class_instance_id
            for relationship in replica.list_relationships(
                source_id=record.class_instance_id,
                relationship_id=(
                    runtime_context.network_node_environment_portal_relationship_id
                ),
                projection_hash=projection_hash,
            )
        )

    committed_service_package_ids: set[UUID] = set()
    service_records = replica.list_class_instances(
        class_config_id=runtime_context.network_node_service_class_config_id,
        projection_hash=projection_hash,
    )
    for record in service_records:
        if record.branch_id != intent.node.node_id:
            continue
        committed_service_package_ids.update(
            relationship.target_class_instance_id
            for relationship in replica.list_relationships(
                source_id=record.class_instance_id,
                relationship_id=(
                    runtime_context.network_node_service_package_portal_relationship_id
                ),
                projection_hash=projection_hash,
            )
        )

    requested_service_package_ids = {
        service.service_package_id for service in intent.hosted_services
    }
    return NetworkNodePublicationCoverage(
        node_registered=node_registered,
        environment_published=(intent.environment.environment_id in environment_ids),
        hosted_service_package_ids=sorted(
            committed_service_package_ids,
            key=str,
        ),
        missing_hosted_service_package_ids=sorted(
            requested_service_package_ids - committed_service_package_ids,
            key=str,
        ),
        unexpected_hosted_service_package_ids=sorted(
            committed_service_package_ids - requested_service_package_ids,
            key=str,
        ),
    )


def _resolve_projection_and_root_class(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    projection_name: str,
    root_class_name: str,
) -> tuple[Any, Any]:
    norm = projection_name.strip()
    class_configs_by_id = cast(Any, getattr(runtime_index, "class_configs_by_id", {}))
    matches: list[tuple[Any, Any]] = []
    for projection in cast(Any, getattr(runtime_index, "opg_by_hash", {})).values():
        if (getattr(projection, "name", "") or "").strip() != norm:
            continue
        root_class_matches = [
            class_config
            for node in getattr(projection, "object_projection_graph_nodes", []) or []
            if bool(getattr(node, "is_root", False))
            for class_config in [
                class_configs_by_id.get(getattr(node, "class_config_id", None))
            ]
            if class_config is not None
            and (
                (getattr(class_config, "name", "") or "").strip() == root_class_name
                or _class_fqn(class_config).endswith(f".{root_class_name}")
            )
        ]
        for class_config in root_class_matches:
            matches.append((projection, class_config))
    if not matches:
        raise ValueError(
            "Network projection root is missing from runtime index: "
            + f"projection_name={projection_name!r} root_class_name={root_class_name!r}"
        )
    if len(matches) != 1:
        raise ValueError(
            "Network projection root is ambiguous in runtime index: "
            + f"projection_name={projection_name!r} root_class_name={root_class_name!r} "
            + f"matches={len(matches)}"
        )
    return matches[0]


def _resolve_projection_class(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    projection: Any,
    class_name: str,
) -> Any:
    class_configs_by_id = cast(Any, getattr(runtime_index, "class_configs_by_id", {}))
    matches = [
        class_config
        for node in getattr(projection, "object_projection_graph_nodes", []) or []
        for class_config in [
            class_configs_by_id.get(getattr(node, "class_config_id", None))
        ]
        if class_config is not None
        and (
            (getattr(class_config, "name", "") or "").strip() == class_name
            or _class_fqn(class_config).endswith(f".{class_name}")
        )
    ]
    if len(matches) != 1:
        raise ValueError(
            "Network projection class resolution must be unique: "
            + f"projection_name={getattr(projection, 'name', None)!r} "
            + f"class_name={class_name!r} matches={len(matches)}"
        )
    return matches[0]


def _resolve_relationship_id(
    *,
    class_config: Any,
    relationship_key: str,
) -> UUID:
    matches = [
        UUID(str(relationship.id))
        for relationship in getattr(class_config, "class_config_relationships", [])
        or []
        if (getattr(relationship, "relationship_key", "") or "").strip()
        == relationship_key
    ]
    if len(matches) != 1:
        raise ValueError(
            "Network relationship resolution must be unique: "
            + f"class_fqn={_class_fqn(class_config)!r} "
            + f"relationship_key={relationship_key!r} matches={len(matches)}"
        )
    return matches[0]


def _resolve_function_id(
    *,
    class_config: Any,
    function_name: str,
) -> UUID:
    norm = function_name.strip()
    function_ids = [
        function_config.id
        for link in getattr(class_config, "class_config_function_configs", []) or []
        for function_config in [getattr(link, "function_config", None)]
        if function_config is not None
        and (getattr(function_config, "name", "") or "").strip() == norm
    ]
    if not function_ids:
        raise ValueError(
            "Network function missing from runtime index: "
            + f"class_fqn={_class_fqn(class_config)!r} function_name={function_name!r}"
        )
    if len(function_ids) != 1:
        raise ValueError(
            "Network function is ambiguous in runtime index: "
            + f"class_fqn={_class_fqn(class_config)!r} function_name={function_name!r} "
            + f"matches={len(function_ids)}"
        )
    return UUID(str(function_ids[0]))


def _peer_descriptors_from_payload(
    payload: object,
    *,
    request: NetworkListPeersRequest,
) -> list[NetworkPeerDescriptor]:
    peers: list[NetworkPeerDescriptor] = []
    for item in _payload_results(payload, context="network.peer.list"):
        edge_id = _required_uuid(item, "edge_id", context="network.peer.list")
        peer_node_id = _required_uuid(
            item,
            "peer_node_id",
            context="network.peer.list",
        )
        direction = _optional_string(item.get("direction")) or "outgoing"
        if direction.strip().casefold() == "incoming":
            source_node_id = peer_node_id
            target_node_id = request.node_id
            resolved_direction = "incoming"
        else:
            source_node_id = request.node_id
            target_node_id = peer_node_id
            resolved_direction = "outgoing"
        fanout_rules = [
            NetworkPeerFanoutRuleDescriptor(
                id=_optional_uuid(rule.get("id")),
                lane_branch_id=_required_uuid(
                    rule,
                    "lane_branch_id",
                    context="network.peer.list",
                ),
                lane_projection_hash=_required_string(
                    rule,
                    "lane_projection_hash",
                    context="network.peer.list",
                ),
                enabled=_optional_bool(rule.get("enabled"), default=True),
                mode=_enum_or_string(rule.get("mode"), default="notify_pull"),
            )
            for rule in _optional_mapping_list(item.get("fanout_rules"))
        ]
        peers.append(
            NetworkPeerDescriptor(
                edge_id=edge_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                peer_node_id=peer_node_id,
                peer_base_url=_optional_string(item.get("peer_http_base_url")) or "",
                direction=resolved_direction,
                status=_enum_or_string(item.get("status"), default="accepted"),
                trust_score=_optional_float(item.get("trust_score"), default=0.0),
                fanout_rules=fanout_rules,
                connected_at=_optional_string(item.get("connected_at")),
                last_ping_at=_optional_string(item.get("last_ping_at")),
            )
        )
    return peers


def _territory_response_from_directory_payload(
    payload: object,
    *,
    request: NetworkDiscoverTerritoryRequest,
) -> NetworkDiscoverTerritoryResponse:
    data = _payload_object(payload, context="network.discovery.discover_territory")
    return NetworkDiscoverTerritoryResponse.model_validate(
        {
            "request_id": request.request_id,
            "success": True,
            "nodes": data.get("nodes", []),
            "summary": data.get("summary"),
        }
    )


def _experience_territory_response_from_directory_payload(
    payload: object,
    *,
    request: NetworkDiscoverExperienceTerritoryRequest,
) -> NetworkDiscoverExperienceTerritoryResponse:
    data = _payload_object(
        payload,
        context="network.discovery.discover_experience_territory",
    )
    return NetworkDiscoverExperienceTerritoryResponse.model_validate(
        {
            "request_id": request.request_id,
            "success": True,
            "experience_name": data.get("experience_name"),
            "entries": data.get("entries", []),
            "summary": data.get("summary"),
        }
    )


def _hosted_service_descriptors_from_payload(
    payload: object,
    *,
    context: str,
) -> list[NetworkHostedServiceDescriptor]:
    return [
        NetworkHostedServiceDescriptor(
            service_package_id=_optional_uuid(item.get("service_package_id")),
            service_id=_required_uuid(item, "service_id", context=context),
            service_name=_required_string(item, "service_name", context=context),
            service_package_names=_optional_string_list(
                item.get("service_package_names")
            ),
            endpoint_refs=_optional_string_list(item.get("endpoint_refs")),
            stream_endpoint_refs=_optional_string_list(
                item.get("stream_endpoint_refs")
            ),
            host_id=_required_string(item, "host_id", context=context),
            host_version=_optional_string(item.get("host_version")),
            protocol_version=_required_string(
                item, "protocol_version", context=context
            ),
            supports_stream_events=_optional_bool(
                item.get("supports_stream_events"),
                default=False,
            ),
        )
        for item in _payload_results(payload, context=context)
    ]


def _environment_descriptors_from_payload(
    payload: object,
    *,
    node_id: UUID,
    context: str,
) -> list[NetworkEnvironmentDescriptor]:
    return [
        NetworkEnvironmentDescriptor(
            node_id=node_id,
            environment_id=_required_uuid(item, "environment_id", context=context),
            role=_enum_or_string(item.get("role"), default="replica"),
            is_active=_optional_bool(item.get("is_active"), default=True),
            priority=_optional_int(item.get("priority"), default=0),
            status=(
                "active"
                if _optional_bool(item.get("is_active"), default=True)
                else "inactive"
            ),
        )
        for item in _payload_results(payload, context=context)
    ]


def _payload_results(payload: object, *, context: str) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{context} returned malformed payload: expected object")
    results = payload.get("results")
    if not isinstance(results, list):
        raise RuntimeError(
            f"{context} returned malformed payload: expected results list"
        )
    return [item for item in results if isinstance(item, dict)]


def _payload_object(payload: object, *, context: str) -> dict[str, object]:
    if hasattr(payload, "model_dump"):
        payload = cast(Any, payload).model_dump(mode="json")
    if not isinstance(payload, dict):
        raise RuntimeError(f"{context} returned malformed payload: expected object")
    value = payload.get("value")
    if hasattr(value, "model_dump"):
        value = cast(Any, value).model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return payload


def _optional_mapping_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _required_uuid(
    item: dict[str, object],
    key: str,
    *,
    context: str,
) -> UUID:
    value = _optional_uuid(item.get(key))
    if value is None:
        raise RuntimeError(
            f"{context} returned malformed payload: missing UUID {key!r}"
        )
    return value


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def _required_string(
    item: dict[str, object],
    key: str,
    *,
    context: str,
) -> str:
    value = _optional_string(item.get(key))
    if value is None:
        raise RuntimeError(
            f"{context} returned malformed payload: missing string {key!r}"
        )
    return value


def _optional_string(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if value is None:
        return None
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    return str(value)


def _enum_or_string(value: object, *, default: str) -> str:
    return _optional_string(value) or default


def _optional_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _optional_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _optional_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _optional_float(value: object, *, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _class_fqn(class_config: Any) -> str:
    fqn = getattr(class_config, "fqn", None)
    if fqn is not None:
        return str(fqn)
    namespace = str(getattr(class_config, "namespace", "") or "").strip()
    name = str(getattr(class_config, "name", "") or "").strip()
    return ".".join(part for part in (namespace, name) if part)


__all__ = [
    "HostContextNetworkTopologyAuthority",
    "NetworkOntologyRuntimeContext",
    "NetworkOntologyTopologyAuthority",
    "resolve_network_ontology_runtime_context",
]
