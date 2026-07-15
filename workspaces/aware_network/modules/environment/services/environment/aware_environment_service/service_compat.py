from __future__ import annotations

from typing import Protocol
from uuid import UUID, uuid4

from aware_network_service_dto.comms.models.network import (
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
)
from aware_network_service_dto.comms.models.network_node import (
    CloseStreamRequest,
    NetworkNodeOperation,
)
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperation,
)
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperationRequest,
)
from aware_service_runtime.adapters.environment import (
    build_environment_service_operation_request,
)
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    ServiceGraphGateway,
    ServiceOperationRequest,
    ServiceOperationResponse,
)


class EnvironmentNodeTransportPort(Protocol):
    def extract_node_id_from_request_hop(
        self, network_op: NetworkOperation
    ) -> UUID: ...

    def build_env_to_node_hop(
        self, *, environment_id: UUID, node_id: UUID
    ) -> NetworkOperationHop: ...

    async def send_notification_to_node(
        self, *, environment_id: UUID, payload_json: str
    ) -> None: ...


class EnvironmentServiceHostPort(Protocol):
    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse: ...

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None: ...


class EnvironmentServicePluginTransport:
    """Plugin transport rail exposed to ServiceRuntimeHost inside Environment."""

    def __init__(
        self,
        *,
        graph_gateway: ServiceGraphGateway,
        meta_temporal_graph_route: MetaTemporalGraphRoute | None = None,
        node_transport: EnvironmentNodeTransportPort,
    ) -> None:
        self._graph_gateway = graph_gateway
        self._meta_temporal_graph_route = meta_temporal_graph_route
        self._node_transport = node_transport

    async def send_service_operation_stream(
        self,
        *,
        node_id: UUID,
        network_operation_id: UUID,
        env_req: EnvironmentServiceOperationRequest,
        service_operation: EnvironmentServiceOperation,
    ) -> None:
        _ = (node_id, network_operation_id, env_req, service_operation)
        raise RuntimeError(
            "Environment service stream responses over "
            "NetworkOperation.environment_operation are removed; publish through "
            "the generated service API stream contract."
        )

    async def close_stream(
        self,
        *,
        node_id: UUID,
        network_operation_id: UUID,
        env_req: EnvironmentServiceOperationRequest,
    ) -> None:
        hop = self._node_transport.build_env_to_node_hop(
            environment_id=env_req.environment_id, node_id=node_id
        )
        close_req = CloseStreamRequest(
            actor_id=env_req.actor_id,
            node_id=node_id,
            network_operation_id=network_operation_id,
        )
        close_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.notification,
            type=NetworkOperationType.network_node,
            network_node_operation=NetworkNodeOperation(request=close_req),
            network_operation_hop_list=[hop],
        )
        await self._node_transport.send_notification_to_node(
            environment_id=env_req.environment_id,
            payload_json=close_op.model_dump_json(),
        )

    async def send_service_response(
        self,
        *,
        request: ServiceOperationRequest,
        response: ServiceOperationResponse,
    ) -> None:
        _ = (request, response)
        raise RuntimeError(
            "Environment service stream responses over "
            "NetworkOperation.environment_operation are removed; publish through "
            "the generated service API stream contract."
        )

    async def close_service_stream(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        node_id = request.stream_target_id
        network_operation_id = request.stream_correlation_id
        if node_id is None or network_operation_id is None:
            raise RuntimeError(
                "Environment service host requires stream_target_id and "
                "stream_correlation_id for stream close operations."
            )
        host_context = current_service_api_host_context()
        environment_context = (
            host_context.environment_context if host_context is not None else None
        )
        await self.close_stream(
            node_id=node_id,
            network_operation_id=network_operation_id,
            env_req=build_environment_service_operation_request(
                request=request,
                environment_context=environment_context,
            ),
        )

    async def get_graph_gateway(self) -> ServiceGraphGateway:
        return self._graph_gateway

    async def get_meta_temporal_graph_route(self) -> MetaTemporalGraphRoute:
        if self._meta_temporal_graph_route is None:
            raise RuntimeError(
                "Environment service plugin transport requires an explicit Meta "
                "temporal graph route for temporal overlay invocations."
            )
        return self._meta_temporal_graph_route

__all__ = [
    "EnvironmentServiceHostPort",
    "EnvironmentNodeTransportPort",
    "EnvironmentServicePluginTransport",
]
