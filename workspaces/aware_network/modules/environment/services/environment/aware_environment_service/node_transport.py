from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequestStatus,
)
from aware_network_service_dto.comms.models.network_node import (
    DiscoverServiceApiDependencyRoutesRequest,
    DiscoverServiceApiDependencyRoutesResponse,
    NetworkNodeOperation,
)
from aware_comms.duplex.collection import DuplexCollection
from aware_network.communications.duplex.duplex import NetworkDuplex
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    service_api_dependency_routes_from_payload,
)


class EnvironmentNodeTransport:
    """Node-facing transport rail for Environment node binding and route discovery."""

    def __init__(self, *, duplex_collection: DuplexCollection) -> None:
        self._duplex_collection = duplex_collection
        self._node_id_by_environment_id: dict[UUID, UUID] = {}

    def remember_node_binding(self, network_op: NetworkOperation) -> None:
        """Record which node is connected for a given environment_id."""

        try:
            if len(network_op.network_operation_hop_list) != 1:
                return
            hop = network_op.network_operation_hop_list[0]
            if hop.source_app_type != NetworkAppType.network_node:
                return
            if hop.source_node_id is None:
                return
            if hop.target_app_type != NetworkAppType.environment:
                return
            if hop.target_environment_id is None:
                return
            self._node_id_by_environment_id[hop.target_environment_id] = (
                hop.source_node_id
            )
        except Exception:
            return

    def extract_node_id_from_request_hop(self, network_op: NetworkOperation) -> UUID:
        if len(network_op.network_operation_hop_list) != 1:
            raise ValueError("NetworkOperation hop_list must contain exactly 1 hop")
        hop = network_op.network_operation_hop_list[0]
        if hop.source_app_type.value != NetworkAppType.network_node.value:
            raise ValueError(
                f"Unsupported source_app_type for environment service: {hop.source_app_type}"
            )
        if hop.source_node_id is None:
            raise ValueError(
                "source_node_id is required when source_app_type is NETWORK_NODE"
            )
        return hop.source_node_id

    def build_env_to_node_hop(
        self, *, environment_id: UUID, node_id: UUID
    ) -> NetworkOperationHop:
        return NetworkOperationHop(
            source_app_type=NetworkAppType.environment,
            source_environment_id=environment_id,
            target_app_type=NetworkAppType.network_node,
            target_node_id=node_id,
        )

    def get_node_duplex_server(self) -> NetworkDuplex[Any, Any]:
        duplex = self._duplex_collection.get_server(NetworkAppType.network_node)
        if duplex is None:
            raise RuntimeError("Missing duplex server for NETWORK_NODE")
        if not isinstance(duplex, NetworkDuplex):
            raise RuntimeError(f"Invalid duplex type for NETWORK_NODE: {type(duplex)}")
        return duplex

    async def send_notification_to_node(
        self, *, environment_id: UUID, payload_json: str
    ) -> None:
        duplex = self.get_node_duplex_server()
        await duplex.send_notification(
            connection_id=environment_id, data_serialized=payload_json
        )

    async def discover_service_api_dependency_routes(
        self,
        *,
        environment_id: UUID,
        node_id: UUID,
        consumer_service_package_id: UUID | None = None,
        api_package_id: UUID | None = None,
        timeout_s: float | None = None,
    ) -> tuple[ServiceApiDependencyRouteDescriptor, ...]:
        """Query the hosting Node route registry over the existing duplex."""

        duplex = self.get_node_duplex_server()
        hop = self.build_env_to_node_hop(
            environment_id=environment_id,
            node_id=node_id,
        )
        request = DiscoverServiceApiDependencyRoutesRequest(
            actor_id=None,
            node_id=node_id,
            consumer_service_package_id=consumer_service_package_id,
            api_package_id=api_package_id,
        )
        network_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.network_node,
            network_operation_hop_list=[hop],
            network_node_operation=NetworkNodeOperation(request=request),
        )
        raw_response = await duplex.send_request(
            connection_id=environment_id,
            data_serialized=network_op.model_dump_json(),
            timeout_s=timeout_s,
        )
        response_op = self._parse_node_response(raw_response)
        if (
            response_op.network_response is not None
            and response_op.network_response.status == NetworkRequestStatus.failed
        ):
            error = response_op.network_response.error or "unknown error"
            raise RuntimeError(
                "Node service API dependency route discovery failed: " f"{error}"
            )
        node_operation = response_op.network_node_operation
        if node_operation is None or node_operation.response is None:
            raise RuntimeError(
                "Node service API dependency route discovery returned no "
                "NetworkNode response."
            )
        if not isinstance(
            node_operation.response,
            DiscoverServiceApiDependencyRoutesResponse,
        ):
            raise RuntimeError(
                "Node service API dependency route discovery returned unexpected "
                f"response type: {type(node_operation.response)}"
            )
        return service_api_dependency_routes_from_payload(
            [
                route.model_dump(mode="json")
                for route in node_operation.response.routes
            ],
            base_dir=Path.cwd(),
        )

    @staticmethod
    def _parse_node_response(raw_response: object) -> NetworkOperation:
        if raw_response is None:
            raise RuntimeError("No response received from node service")
        if isinstance(raw_response, str):
            return NetworkOperation.model_validate_json(raw_response)
        if isinstance(raw_response, dict):
            return NetworkOperation.model_validate(raw_response)
        raise TypeError(f"Unexpected node response type: {type(raw_response)}")


__all__ = ["EnvironmentNodeTransport"]
