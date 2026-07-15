"""
Network Router for network communication with hop-based routing.
"""

from typing import Any, Iterable, cast
from uuid import UUID, uuid4
import asyncio
import contextlib
from collections.abc import Awaitable, Callable, Mapping
import json
import os

# Logging
from aware_utils.logging import logger

# Core communications
from aware_comms.duplex.websocket.models import WsMessageFrameType, WsMessageFrame

# Network communications
from aware_network.communications.app import NetworkApp
from aware_network.network.node.manager import network_node_manager

# Network Router
from aware_network.communications.duplex.router import NetworkRouter
from aware_network.communications.duplex.duplex import NetworkDuplex
from aware_network_sdk import NetworkSdkClient

# NetworkOperation handling (protocol DTOs; no ORM dependency)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkResponse,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequestStatus,
)
from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    ApiRequestStatus,
    ApiStreamLifecycle,
    InvokeApiEndpointRequest,
    InvokeApiEndpointResponse,
    StreamApiEndpointRequest,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus as ServiceRequestStatus,
    ServiceOperation,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle as ServiceStreamLifecycle,
)
from aware_code.types import JsonObject
from aware_network_service_dto.comms.models.network_node import (
    NetworkNodeOperation,
    UnknownNetworkNodeOperationResponse,
    CloseStreamRequest,
    CloseStreamResponse,
    DescribeHostedServiceRuntimesRequest,
    DescribeHostedServiceRuntimesResponse,
    DiscoverEnvironmentConfigsRequest as NetworkDiscoverEnvironmentConfigsRequest,
    DiscoverEnvironmentConfigsResponse as NetworkDiscoverEnvironmentConfigsResponse,
    DiscoverServiceApiDependencyRoutesRequest as NetworkDiscoverApiRoutesRequest,
    DiscoverServiceApiDependencyRoutesResponse as NetworkDiscoverApiRoutesResponse,
    DiscoverHostedServicesRequest,
    DiscoverHostedServicesResponse,
    GetBootEnvironmentDescriptorRequest as NetworkGetBootEnvironmentDescriptorRequest,
    GetBootEnvironmentDescriptorResponse as NetworkGetBootEnvironmentDescriptorResponse,
    InterfaceSessionHeartbeatRequest,
    InterfaceSessionHeartbeatResponse,
    InterfaceSessionRegisterRequest,
    InterfaceSessionRegisterResponse,
    GetEnvironmentStatusRequest as NetworkGetEnvironmentStatusRequest,
    GetEnvironmentStatusResponse as NetworkGetEnvironmentStatusResponse,
    NodeEnvironmentProvisioningReceipt as NetworkNodeEnvironmentProvisioningReceipt,
    ProvisionEnvironmentRequest as NetworkProvisionEnvironmentRequest,
    ProvisionEnvironmentResponse as NetworkProvisionEnvironmentResponse,
    BootEnvironmentDescriptor as NetworkBootEnvironmentDescriptor,
    EnvironmentConfigDescriptor as NetworkEnvironmentConfigDescriptor,
    ServiceApiDependencyRouteDescriptor as NetworkServiceApiDependencyRouteDescriptor,
)
from aware_network_service_dto.comms.identity.identity_session_operation import (
    IdentityChallengeRequest,
    IdentityChallengeResponse,
    IdentityLoginRequest,
    IdentityLoginResponse,
    TokenLoginRequest,
    TokenLoginResponse,
    WhoamiRequest,
    WhoamiResponse,
)
from aware_network_service_dto.comms.economy.membership_operation import (
    MembershipStatusResponse,
)
from aware_node_service_dto.node.host import (
    BootEnvironmentDescriptor as NodeHostBootEnvironmentDescriptor,
    DescribeHostedServiceRuntimesRequest as NodeHostDescribeHostedServiceRuntimesRequest,
    DescribeHostedServiceRuntimesResponse as NodeHostDescribeHostedServiceRuntimesResponse,
    DiscoverApiRoutesRequest as NodeHostDiscoverApiRoutesRequest,
    DiscoverApiRoutesResponse as NodeHostDiscoverApiRoutesResponse,
    DiscoverEnvironmentConfigsRequest as NodeHostDiscoverEnvironmentConfigsRequest,
    DiscoverEnvironmentConfigsResponse as NodeHostDiscoverEnvironmentConfigsResponse,
    EnvironmentConfigDescriptor as NodeHostEnvironmentConfigDescriptor,
    GetBootEnvironmentDescriptorRequest as NodeHostGetBootEnvironmentDescriptorRequest,
    GetBootEnvironmentDescriptorResponse as NodeHostGetBootEnvironmentDescriptorResponse,
    GetEnvironmentStatusRequest as NodeHostGetEnvironmentStatusRequest,
    GetEnvironmentStatusResponse as NodeHostGetEnvironmentStatusResponse,
    HostedServiceRuntimeStatus as NodeHostHostedServiceRuntimeStatus,
    NodeEnvironmentProvisioningReceipt as NodeHostNodeEnvironmentProvisioningReceipt,
    NodeHostOperationRequest,
    NodeHostOperationResponse,
    NodeServiceApiDependencyRouteDescriptor as NodeHostServiceApiDependencyRouteDescriptor,
    ProvisionEnvironmentRequest as NodeHostProvisionEnvironmentRequest,
    ProvisionEnvironmentResponse as NodeHostProvisionEnvironmentResponse,
)
from aware_node.host_control_plane import (
    NodeHostControlPlaneResult,
    NodeHostControlPlaneService,
)
from aware_node_service.control_plane.environment_registry import environment_registry
from aware_node_service.service_contract_access import (
    SERVICE_CONTRACT_ACCESS_ROLE,
    actor_has_service_contract_access,
    is_actor_contract_access_bypassed,
    read_service_contract_access_status,
    service_contract_access_gate_required,
)

# Identity session manager (transport-only)
from aware_network.communications.identity_session_manager import (
    IdentitySessionManager,
    TokenBinding,
)

# Interface session binding manager (transport-only)
from aware_network.communications.interface_session_binding_manager import (
    InterfaceSessionBindingManager,
)

from aware_node_service.duplex.lane_commit_receipt_bus import LaneCommitReceiptBus
from aware_node_service.auth_tokens import (
    AptTokenValidationError,
    AptTokenValidator,
    load_token_authority_manifest,
)
from aware_node_service.control_plane.bootstrap_service import (
    NetworkNodeBootstrapService,
)
from aware_node_service.control_plane.hosted_environment_service import (
    NetworkNodeHostedEnvironmentService,
)
from aware_node_service.control_plane.node_host_runtime_ports import (
    NodeHostControlPlaneRuntimePorts,
)
from aware_node_service.control_plane.peer_directory import (
    RemoteHostedServiceRoute,
    discover_network_node_peer_endpoints,
    discover_remote_hosted_service_routes,
    discover_remote_hosted_service_routes_for_endpoint_ref,
)
from aware_node_service.host.services import (
    CommittedHostedServiceLookupMiss,
    describe_node_hosted_service_runtime_statuses,
    discover_node_hosted_service_advertisements,
    open_api_ingress_stream_to_hosted_service_runtime,
    open_request_stream_to_hosted_service_runtime,
    route_api_request_to_hosted_service_runtime,
    resolve_node_hosted_service_runtime_for_endpoint_ref,
    resolve_node_hosted_service_runtime_for_service_request,
)
from aware_node_service.network.fanout_pull_hint_bus import (
    FanoutPullHintBus,
    FanoutPullHintNotification,
)
from aware_service_runtime.duplex import ServiceDuplexStreamEventEnvelope
from aware_service_runtime.contracts import ServiceHostApiIngressRequest


_NODE_HOST_API_REQUEST_MODEL_BY_ENDPOINT_REF: Mapping[
    str,
    type[NodeHostOperationRequest],
] = {
    "node.host.describe_hosted_service_runtimes": (
        NodeHostDescribeHostedServiceRuntimesRequest
    ),
    "node.host.discover_environment_configs": (
        NodeHostDiscoverEnvironmentConfigsRequest
    ),
    "node.host.discover_service_api_dependency_routes": (
        NodeHostDiscoverApiRoutesRequest
    ),
    "node.host.get_boot_environment_descriptor": (
        NodeHostGetBootEnvironmentDescriptorRequest
    ),
    "node.host.get_environment_status": NodeHostGetEnvironmentStatusRequest,
    "node.host.provision_environment": NodeHostProvisionEnvironmentRequest,
}
_ENVIRONMENT_API_ENDPOINT_REF_PREFIXES = ("environment.",)


def _dispatch_environment_operation_notification_to_lane_bus(
    *,
    raw_network_op: object,
) -> None:
    if not isinstance(raw_network_op, Mapping):
        return
    raw_environment_op = raw_network_op.get("environment_operation")
    if not isinstance(raw_environment_op, Mapping):
        return
    raw_notification = raw_environment_op.get("notification")
    if not isinstance(raw_notification, Mapping):
        return

    from aware_environment_service_dto.environment.environment import (
        EnvironmentOperationNotification,
    )

    LaneCommitReceiptBus.instance().dispatch(
        EnvironmentOperationNotification.parse(dict(raw_notification))
    )


def _api_invocation_context_payload(
    request: InvokeApiEndpointRequest | StreamApiEndpointRequest,
) -> JsonObject | None:
    invocation_context = request.invocation_context
    if invocation_context is None:
        return None
    return cast(
        JsonObject,
        invocation_context.model_dump(mode="json", exclude_none=True),
    )


def _actor_id_matches_public_key(*, actor_id: UUID, public_key: str) -> bool:
    """Transport-layer anti-claim check for identity sessions.

    The node's websocket session binding currently supplies `actor_id` from the
    client (v0). To prevent impersonation, we must ensure that the claimed
    `actor_id` is derivable from the authenticated Ed25519 public key using the
    stable-id formulas.

    We don't know the identity type at the transport boundary, so we accept a
    match for any known IdentityType value.
    """

    from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
    from aware_identity_ontology.stable_ids import stable_actor_id, stable_identity_id

    canonical_public_key, _ = canonicalize_ed25519_public_key(public_key)
    for identity_type_value in ("human", "agent", "organization", "system"):
        identity_id = stable_identity_id(
            public_key=canonical_public_key,
            type=identity_type_value,
        )
        if stable_actor_id(identity_id=identity_id) == actor_id:
            return True
    return False


def _is_environment_api_endpoint_ref(endpoint_ref: str) -> bool:
    normalized = endpoint_ref.strip()
    return any(
        normalized.startswith(prefix)
        for prefix in _ENVIRONMENT_API_ENDPOINT_REF_PREFIXES
    )


def _runtime_manifest_path_for_token_validation() -> str | None:
    authority_manifest_path = _token_authority_manifest_path_for_token_validation()
    if authority_manifest_path is not None:
        authority_manifest = load_token_authority_manifest(authority_manifest_path)
        if authority_manifest.runtime_manifest_path:
            return authority_manifest.runtime_manifest_path.as_posix()

    manifest_path = str(os.environ.get("AWARE_ENVIRONMENT_MANIFEST") or "").strip()
    if manifest_path:
        return manifest_path
    return None


def _token_authority_manifest_path_for_token_validation() -> str | None:
    manifest_path = str(
        os.environ.get("AWARE_NODE_TOKEN_AUTHORITY_MANIFEST_PATH") or ""
    ).strip()
    return manifest_path or None


class NetworkNodeRouter(NetworkRouter):
    """
    Central router for all network communication using hop-based routing.

    This class:
    1. Routes NetworkOperations using hop-based headers (single hop in hop_list)
    2. Maintains audit trail by persisting hops to database
    3. Handles privacy by stripping interface IDs when crossing node boundaries
    4. Supports path disclosure for compliance/diagnostics when needed
    """

    def __init__(
        self,
        network_app: NetworkApp,
        *,
        network_sdk_client: NetworkSdkClient | None = None,
    ):
        """Initialize the network router"""
        self._network_app = network_app
        self._network_sdk_client = network_sdk_client
        self._bootstrap_service: NetworkNodeBootstrapService | None = None
        self._hosted_environment_service: NetworkNodeHostedEnvironmentService | None = (
            None
        )
        self._node_host_control_plane_service: NodeHostControlPlaneService | None = None
        # Correlate STREAM notifications back to the originating interface connection.
        # Key: NetworkOperation.id (request correlation id) -> interface connection_id (UUID)
        self._stream_origin_by_operation_id: dict[UUID, UUID] = {}
        # Correlate direct remote API STREAM notifications back to the websocket
        # connection that carried the explicit StreamApiEndpointRequest.
        self._api_stream_origin_connection_by_operation_id: dict[UUID, UUID] = {}
        self._stream_close_by_operation_id: dict[
            UUID, Callable[[], Awaitable[None]]
        ] = {}
        self._register_network_operation_handlers()

    def set_bootstrap_service(
        self, bootstrap_service: NetworkNodeBootstrapService
    ) -> None:
        self._bootstrap_service = bootstrap_service
        self._node_host_control_plane_service = None

    def set_hosted_environment_service(
        self, hosted_environment_service: NetworkNodeHostedEnvironmentService
    ) -> None:
        self._hosted_environment_service = hosted_environment_service
        self._node_host_control_plane_service = None

    def set_network_sdk_client(
        self, network_sdk_client: NetworkSdkClient | None
    ) -> None:
        self._network_sdk_client = network_sdk_client

    def _require_hosted_environment_service(
        self,
    ) -> NetworkNodeHostedEnvironmentService:
        service = getattr(self, "_hosted_environment_service", None)
        if service is None:
            service = NetworkNodeHostedEnvironmentService(
                route_to_environment_service=self.route_to_environment_service
            )
            self._hosted_environment_service = service
        return service

    def _require_bootstrap_service(self) -> NetworkNodeBootstrapService:
        service = getattr(self, "_bootstrap_service", None)
        if service is None:
            service = NetworkNodeBootstrapService(
                route_to_environment_service=self.route_to_environment_service,
                hosted_environment_service=self._require_hosted_environment_service(),
            )
            self._bootstrap_service = service
        return service

    def _require_node_host_control_plane_service(self) -> NodeHostControlPlaneService:
        service = getattr(self, "_node_host_control_plane_service", None)
        if service is None:
            service = NodeHostControlPlaneService(
                ports=NodeHostControlPlaneRuntimePorts(
                    bootstrap_service=self._require_bootstrap_service(),
                    hosted_environment_service=self._require_hosted_environment_service(),
                    node_app=self._network_app,
                )
            )
            self._node_host_control_plane_service = service
        return service

    def _build_node_host_request_from_network_request(
        self,
        *,
        request: object,
        node_id: UUID,
    ) -> NodeHostOperationRequest:
        if isinstance(request, NetworkDiscoverEnvironmentConfigsRequest):
            return NodeHostDiscoverEnvironmentConfigsRequest(
                actor_id=request.actor_id,
                node_id=node_id,
                operation=request.operation,
            )
        if isinstance(request, NetworkDiscoverApiRoutesRequest):
            return NodeHostDiscoverApiRoutesRequest(
                actor_id=request.actor_id,
                node_id=node_id,
                operation=request.operation,
                consumer_service_package_id=request.consumer_service_package_id,
                api_package_id=request.api_package_id,
            )
        if isinstance(request, NetworkGetBootEnvironmentDescriptorRequest):
            return NodeHostGetBootEnvironmentDescriptorRequest(
                actor_id=request.actor_id,
                node_id=node_id,
                operation=request.operation,
            )
        if isinstance(request, NetworkProvisionEnvironmentRequest):
            return NodeHostProvisionEnvironmentRequest(
                actor_id=request.actor_id,
                node_id=node_id,
                operation=request.operation,
                environment_config_id=request.environment_config_id,
                environment_title=request.environment_title,
                environment_description=request.environment_description,
                environment_port=request.environment_port,
                database_url=request.database_url,
                persistence_backend=request.persistence_backend,
                eager_ready=request.eager_ready,
            )
        if isinstance(request, NetworkGetEnvironmentStatusRequest):
            return NodeHostGetEnvironmentStatusRequest(
                actor_id=request.actor_id,
                node_id=node_id,
                operation=request.operation,
                environment_id=request.environment_id,
            )
        raise RuntimeError(
            "NetworkNodeOperation.request is not an environment-related bridge request"
        )

    def _build_network_environment_config_descriptor(
        self,
        descriptor: NodeHostEnvironmentConfigDescriptor,
    ) -> NetworkEnvironmentConfigDescriptor:
        return NetworkEnvironmentConfigDescriptor.model_validate(
            descriptor.model_dump(mode="json")
        )

    def _build_network_boot_environment_descriptor(
        self,
        descriptor: NodeHostBootEnvironmentDescriptor,
    ) -> NetworkBootEnvironmentDescriptor:
        return NetworkBootEnvironmentDescriptor.model_validate(
            descriptor.model_dump(mode="json")
        )

    def _build_network_provisioning_receipt(
        self,
        receipt: NodeHostNodeEnvironmentProvisioningReceipt | None,
    ) -> NetworkNodeEnvironmentProvisioningReceipt | None:
        if receipt is None:
            return None
        return NetworkNodeEnvironmentProvisioningReceipt.model_validate(
            receipt.model_dump(mode="json", exclude_none=True)
        )

    def _build_network_service_api_dependency_route_descriptor(
        self,
        descriptor: NodeHostServiceApiDependencyRouteDescriptor,
    ) -> NetworkServiceApiDependencyRouteDescriptor:
        return NetworkServiceApiDependencyRouteDescriptor.model_validate(
            descriptor.model_dump(mode="json")
        )

    def _build_network_node_bridge_response(
        self,
        response: NodeHostOperationResponse,
    ) -> NetworkNodeOperation:
        if isinstance(response, NodeHostDiscoverEnvironmentConfigsResponse):
            return NetworkNodeOperation(
                response=NetworkDiscoverEnvironmentConfigsResponse(
                    actor_id=response.actor_id,
                    node_id=response.node_id,
                    configs=[
                        self._build_network_environment_config_descriptor(config)
                        for config in response.configs
                    ],
                )
            )
        if isinstance(response, NodeHostDiscoverApiRoutesResponse):
            return NetworkNodeOperation(
                response=NetworkDiscoverApiRoutesResponse(
                    actor_id=response.actor_id,
                    node_id=response.node_id,
                    routes=[
                        self._build_network_service_api_dependency_route_descriptor(
                            route
                        )
                        for route in response.routes
                    ],
                )
            )
        if isinstance(response, NodeHostGetBootEnvironmentDescriptorResponse):
            return NetworkNodeOperation(
                response=NetworkGetBootEnvironmentDescriptorResponse(
                    actor_id=response.actor_id,
                    node_id=response.node_id,
                    status=response.status,
                    error=response.error,
                    descriptor=(
                        None
                        if response.descriptor is None
                        else self._build_network_boot_environment_descriptor(
                            response.descriptor
                        )
                    ),
                )
            )
        if isinstance(response, NodeHostProvisionEnvironmentResponse):
            return NetworkNodeOperation(
                response=NetworkProvisionEnvironmentResponse(
                    actor_id=response.actor_id,
                    node_id=response.node_id,
                    status=response.status,
                    error=response.error,
                    environment_id=response.environment_id,
                    environment_config_id=response.environment_config_id,
                    environment_config_title=response.environment_config_title,
                    environment_title=response.environment_title,
                    environment_endpoint=response.environment_endpoint,
                    ocg_hash=response.ocg_hash,
                    process_id=response.process_id,
                    thread_id=response.thread_id,
                    branch_id=response.branch_id,
                    opg_hashes=list(response.opg_hashes),
                    provisioning_receipt=self._build_network_provisioning_receipt(
                        response.provisioning_receipt
                    ),
                )
            )
        if isinstance(response, NodeHostGetEnvironmentStatusResponse):
            return NetworkNodeOperation(
                response=NetworkGetEnvironmentStatusResponse(
                    actor_id=response.actor_id,
                    node_id=response.node_id,
                    status=response.status,
                    error=response.error,
                    environment_id=response.environment_id,
                    environment_config_id=response.environment_config_id,
                    environment_config_title=response.environment_config_title,
                    environment_title=response.environment_title,
                    environment_endpoint=response.environment_endpoint,
                    ocg_hash=response.ocg_hash,
                    process_id=response.process_id,
                    thread_id=response.thread_id,
                    branch_id=response.branch_id,
                    opg_hashes=list(response.opg_hashes),
                    provisioning_receipt=self._build_network_provisioning_receipt(
                        response.provisioning_receipt
                    ),
                )
            )
        raise RuntimeError(
            f"Unsupported NodeHostOperationResponse bridge payload: {type(response)}"
        )

    @staticmethod
    def _build_network_request_status_for_node_host_result(
        result: NodeHostControlPlaneResult,
    ) -> NetworkRequestStatus:
        return (
            NetworkRequestStatus.failed
            if result.request_status == "failed"
            else NetworkRequestStatus.succeeded
        )

    def _build_node_host_request_from_api_request(
        self,
        *,
        request: InvokeApiEndpointRequest,
    ) -> NodeHostOperationRequest | None:
        request_model = _NODE_HOST_API_REQUEST_MODEL_BY_ENDPOINT_REF.get(
            request.endpoint_ref.strip()
        )
        if request_model is None:
            return None
        if not isinstance(request.request_payload, Mapping):
            raise RuntimeError(
                "NodeHost API request_payload must be an object for endpoint_ref "
                f"{request.endpoint_ref!r}"
            )
        payload = dict(request.request_payload)
        if request.actor_id is not None and payload.get("actor_id") is None:
            payload["actor_id"] = request.actor_id
        if payload.get("node_id") is None:
            payload["node_id"] = network_node_manager.hosted_node_id
        return request_model.model_validate(payload)

    async def _route_to_node_host_api(
        self,
        *,
        network_op: NetworkOperation,
        request: InvokeApiEndpointRequest,
    ) -> NetworkOperation | None:
        node_request = self._build_node_host_request_from_api_request(request=request)
        if node_request is None:
            return None

        request_status = "succeeded"
        request_error: str | None = None
        if isinstance(node_request, NodeHostDescribeHostedServiceRuntimesRequest):
            statuses = [
                NodeHostHostedServiceRuntimeStatus.model_validate(
                    status.model_dump(mode="json", exclude_none=True)
                )
                for status in describe_node_hosted_service_runtime_statuses(
                    node_app=self._network_app
                )
            ]
            response = NodeHostDescribeHostedServiceRuntimesResponse(
                actor_id=node_request.actor_id,
                node_id=node_request.node_id,
                status="succeeded",
                hosted_service_runtimes=statuses,
            )
        else:
            result = (
                await self._require_node_host_control_plane_service().handle_request(
                    node_request
                )
            )
            request_status = result.request_status
            request_error = result.request_error
            response = result.response

        api_status = (
            ApiRequestStatus.failed
            if request_status == "failed"
            else ApiRequestStatus.succeeded
        )
        network_status = (
            NetworkRequestStatus.failed
            if request_status == "failed"
            else NetworkRequestStatus.succeeded
        )
        return NetworkOperation(
            id=network_op.id,
            message_type=NetworkOperationMessageType.response,
            type=network_op.type,
            network_response=NetworkResponse(
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request is not None
                    else None
                ),
                status=network_status,
                error=request_error,
            ),
            api_operation=ApiOperation(
                response=InvokeApiEndpointResponse(
                    status=api_status,
                    error=request_error,
                    response_payload=response.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                )
            ),
        )

    async def _route_to_environment_api(
        self,
        *,
        network_op: NetworkOperation,
        request: InvokeApiEndpointRequest,
    ) -> NetworkOperation | None:
        if not _is_environment_api_endpoint_ref(request.endpoint_ref):
            return None
        if not isinstance(request.request_payload, Mapping):
            raise RuntimeError(
                "Environment API request_payload must be an object for endpoint_ref "
                f"{request.endpoint_ref!r}"
            )

        current_hop = self._get_current_header(network_op)
        payload_environment_id = self._uuid_from_api_payload(
            request.request_payload,
            "environment_id",
        )
        environment_id = self._resolve_environment_api_transport_target_id(
            hop_target_environment_id=current_hop.target_environment_id,
            payload_environment_id=payload_environment_id,
        )
        if environment_id is None:
            raise RuntimeError(
                "Environment API routing requires a registered Environment "
                "transport target from the hop, a registered payload "
                "environment_id, or a single registered local Environment for "
                f"endpoint_ref {request.endpoint_ref!r}"
            )

        environment_op = NetworkOperation(
            id=network_op.id,
            message_type=network_op.message_type,
            type=network_op.type,
            network_request=network_op.network_request,
            api_operation=network_op.api_operation,
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=current_hop.source_app_type,
                    source_node_id=current_hop.source_node_id,
                    source_interface_id=current_hop.source_interface_id,
                    source_environment_id=current_hop.source_environment_id,
                    target_app_type=NetworkAppType.environment,
                    target_node_id=current_hop.target_node_id,
                    target_environment_id=environment_id,
                )
            ],
        )
        rejection = await self._maybe_reject_unauthenticated_environment_api_operation(
            network_op=environment_op,
            current_hop=environment_op.network_operation_hop_list[0],
        )
        if rejection is not None:
            return rejection
        return await self._route_to_environment_service(environment_op)

    async def bootstrap_kernel_environment(self) -> None:
        await self._require_bootstrap_service().bootstrap_kernel_environment()

    async def route_to_environment_service(
        self,
        network_op: NetworkOperation,
        *,
        timeout_s: float | None = None,
    ) -> NetworkOperation | None:
        if network_op.type == NetworkOperationType.service:
            return await self._route_to_service_host(network_op)
        return await self._route_to_environment_service(network_op, timeout_s=timeout_s)

    def _register_network_operation_handlers(self):
        """Register handlers for NetworkOperation messages"""
        # Idempotency: if already registered globally, skip
        existing = NetworkDuplex._handlers.get(WsMessageFrameType.REQUEST)
        if existing is not None:
            logger.info(
                "Global REQUEST handler for NetworkOperation already present; skipping registration"
            )
            return

        self.register_handler(
            app_type=NetworkAppType.interface,
            message_type=WsMessageFrameType.REQUEST,
            handler=self._handle_interface_request,
        )

        self.register_handler(
            app_type=NetworkAppType.interface,
            message_type=WsMessageFrameType.NOTIFICATION,
            handler=self._handle_interface_notification,
        )

        # !! TODO: Add Proper handlers for specific ENV | NODE messages, for now assuming they come from interface
        # self.register_handler(
        #     app_type=NetAppType.ENVIRONMENT,
        #     message_type=WsMessageFrameType.REQUEST,
        #     handler=self._handle_environment_request,
        # )

        # self.register_handler(
        #     app_type=NetAppType.ENVIRONMENT,
        #     message_type=WsMessageFrameType.NOTIFICATION,
        #     handler=self._handle_environment_notification,
        # )

        # self.register_handler(
        #     app_type=NetAppType.NETWORK_NODE,
        #     message_type=WsMessageFrameType.REQUEST,
        #     handler=self._handle_node_request,
        # )

        # self.register_handler(
        #     app_type=NetAppType.NETWORK_NODE,
        #     message_type=WsMessageFrameType.NOTIFICATION,
        #     handler=self._handle_node_notification,
        # )

    # ===============================
    # Main Message Handlers
    # ===============================

    async def _handle_interface_request(
        self,
        data: str,
        message_type: WsMessageFrameType,
        *,
        connection_id: UUID | None = None,
    ) -> str | None:
        """
        Handle incoming NetworkOperation requests using hop-based routing

        Args:
            data: Serialized NetworkOperation JSON
            message_type: The message frame type

        Returns:
            Serialized NetworkOperation RESPONSE JSON or None
        """
        network_op: NetworkOperation | None = None
        try:
            # Parse NetworkOperation from data
            network_op = NetworkOperation.model_validate_json(data)

            # Validate hop structure
            current_hop = self._get_current_header(network_op)

            # Allow interface clients to omit target_node_id when directly connected to this node.
            if (
                current_hop.target_app_type == NetworkAppType.network_node
                and current_hop.target_node_id is None
            ):
                from aware_network.network.node.manager import network_node_manager

                current_hop.target_node_id = network_node_manager.hosted_node_id

            # Validate hop constraints
            if not self.validate_hop_constraints(current_hop):
                raise RuntimeError(
                    f"Invalid hop constraints in NetworkOperation {network_op.id}"
                )

            logger.info(
                f"Processing NetworkOperation {network_op.id} from {current_hop.source_app_type} "
                f"to {current_hop.target_app_type}"
            )

            # Record the originating interface connection for downstream STREAM notifications.
            #
            # This now covers both:
            # - canonical `NetworkOperation(type=api)` once public stream helpers exist
            # - canonical `NetworkOperation(type=service)`
            if (
                current_hop.source_app_type == NetworkAppType.interface
                and current_hop.source_interface_id is not None
                and (
                    (
                        network_op.type == NetworkOperationType.api
                        and network_op.api_operation is not None
                        and network_op.api_operation.request is not None
                    )
                    or (
                        network_op.type == NetworkOperationType.service
                        and network_op.service_operation is not None
                        and network_op.service_operation.request is not None
                    )
                )
            ):
                self._stream_origin_by_operation_id[network_op.id] = (
                    current_hop.source_interface_id
                )
            elif (
                current_hop.source_app_type == NetworkAppType.network_node
                and connection_id is not None
                and network_op.type == NetworkOperationType.api
                and network_op.api_operation is not None
                and isinstance(
                    network_op.api_operation.request,
                    StreamApiEndpointRequest,
                )
            ):
                self._api_stream_origin_connections()[network_op.id] = connection_id

            # Update network request status to processing
            if network_op.network_request:
                network_op.network_request.status = NetworkRequestStatus.pending
                if network_op.network_request.id is None:
                    network_op.network_request.id = uuid4()

            response_op: NetworkOperation | None
            if (
                not self._is_target_this_node(current_hop)
                and current_hop.target_app_type != NetworkAppType.environment
            ):
                if (
                    network_op.type
                    in {NetworkOperationType.api, NetworkOperationType.service}
                    and current_hop.target_app_type == NetworkAppType.network_node
                ):
                    response_op = await self._send_request_to_target_node(
                        network_op,
                        target_node_id=current_hop.target_node_id,
                        external_url=await self._resolve_peer_base_url(
                            target_node_id=current_hop.target_node_id
                        ),
                    )
                else:
                    # Forwarding across nodes is not yet implemented in the canonical DTO-only path.
                    raise RuntimeError(
                        "Cross-node forwarding not implemented for interface requests"
                    )
            elif current_hop.target_app_type == NetworkAppType.environment:
                if network_op.type == NetworkOperationType.api:
                    response_op = await self._maybe_reject_unauthenticated_environment_api_operation(
                        network_op=network_op,
                        current_hop=current_hop,
                    )
                    if response_op is None:
                        response_op = await self._route_to_environment_service(
                            network_op
                        )
                else:
                    raise RuntimeError(
                        "Environment targets accept NetworkOperation(type=api) only"
                    )
            elif network_op.type == NetworkOperationType.network_node:
                response_op = await self._route_to_network_node_service(network_op)
            elif network_op.type == NetworkOperationType.api:
                response_op = await self._route_to_api_host(network_op)
            elif network_op.type == NetworkOperationType.service:
                response_op = await self._route_to_service_host(network_op)
            else:
                raise RuntimeError(
                    f"Unsupported NetworkOperation.type: {network_op.type}"
                )

            if response_op is None:
                raise RuntimeError(
                    "Operation did not return a response NetworkOperation"
                )

            # Update network request status using the environment service status.
            if network_op.network_request and response_op.network_response is not None:
                network_op.network_request.status = response_op.network_response.status

            network_response = response_op.network_response or NetworkResponse(
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request
                    else None
                ),
                status=NetworkRequestStatus.failed,
                error="Operation did not return network_response",
            )

            # Build response NetworkOperation with reversed routing (node -> interface).
            response_hop = NetworkOperationHop(
                source_app_type=current_hop.target_app_type,
                source_node_id=current_hop.target_node_id,
                source_interface_id=current_hop.target_interface_id,
                source_environment_id=current_hop.target_environment_id,
                target_app_type=current_hop.source_app_type,
                target_node_id=current_hop.source_node_id,
                target_interface_id=current_hop.source_interface_id,
                target_environment_id=current_hop.source_environment_id,
            )

            response_net_op = NetworkOperation(
                id=network_op.id,  # Same ID for correlation
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=network_response,
                api_operation=response_op.api_operation,
                service_operation=response_op.service_operation,
                network_node_operation=response_op.network_node_operation,
                network_operation_hop_list=[response_hop],
            )

            if network_op.type in {
                NetworkOperationType.api,
                NetworkOperationType.service,
            } and not self._response_keeps_stream_open(response_op):
                self._stream_origin_by_operation_id.pop(network_op.id, None)
                self._api_stream_origin_connections().pop(network_op.id, None)

            # Return serialized Response NetworkOperation
            return response_net_op.model_dump_json()

        except Exception as e:
            if network_op is not None and network_op.type in {
                NetworkOperationType.api,
                NetworkOperationType.service,
            }:
                self._stream_origin_by_operation_id.pop(network_op.id, None)
                self._api_stream_origin_connections().pop(network_op.id, None)
                close_registry = getattr(self, "_stream_close_by_operation_id", None)
                if isinstance(close_registry, dict):
                    close_registry.pop(network_op.id, None)
            logger.error(f"Error handling NetworkOperation request: {e}")
            return self._build_failed_network_operation_response(
                data=data, network_op=network_op, error=e
            )

    @staticmethod
    def _response_keeps_stream_open(response_op: NetworkOperation | None) -> bool:
        if response_op is None:
            return False
        api_response = (
            response_op.api_operation.response
            if response_op.api_operation is not None
            else None
        )
        if isinstance(api_response, InvokeApiEndpointResponse):
            return api_response.stream_lifecycle is ApiStreamLifecycle.started
        service_response = (
            response_op.service_operation.response
            if response_op.service_operation is not None
            else None
        )
        if isinstance(service_response, ServiceOperationResponse):
            return service_response.stream_lifecycle is ServiceStreamLifecycle.started
        return False

    def _stream_close_registry(self) -> dict[UUID, Callable[[], Awaitable[None]]]:
        registry = getattr(self, "_stream_close_by_operation_id", None)
        if not isinstance(registry, dict):
            registry = {}
            self._stream_close_by_operation_id = registry
        return registry

    def _api_stream_origin_connections(self) -> dict[UUID, UUID]:
        registry = getattr(self, "_api_stream_origin_connection_by_operation_id", None)
        if not isinstance(registry, dict):
            registry = {}
            self._api_stream_origin_connection_by_operation_id = registry
        return registry

    async def _maybe_reject_unauthenticated_environment_api_operation(
        self,
        *,
        network_op: NetworkOperation,
        current_hop: NetworkOperationHop,
    ) -> NetworkOperation | None:
        """Identity gate for Environment API endpoint calls from Interface clients."""

        if current_hop.source_app_type != NetworkAppType.interface:
            return None

        api_request = (
            network_op.api_operation.request
            if network_op.api_operation is not None
            else None
        )
        if not isinstance(api_request, InvokeApiEndpointRequest):
            return None

        actor_id = api_request.actor_id
        if actor_id is None:
            actor_id = self._uuid_from_api_payload(
                api_request.request_payload,
                "actor_id",
            )
        if actor_id is None:
            return self._build_environment_api_operation_failure(
                network_op=network_op,
                request=api_request,
                error="unauthenticated: API request missing actor_id",
            )

        connection_id = current_hop.source_interface_id
        if connection_id is None:
            return self._build_environment_api_operation_failure(
                network_op=network_op,
                request=api_request,
                error="unauthenticated: missing source_interface_id",
            )

        binding = await InterfaceSessionBindingManager.instance().get_binding(
            connection_id=connection_id
        )
        if binding is None:
            return self._build_environment_api_operation_failure(
                network_op=network_op,
                request=api_request,
                error="unauthenticated: interface session not registered (send interface_session_register first)",
            )
        if binding.identity_id != actor_id:
            return self._build_environment_api_operation_failure(
                network_op=network_op,
                request=api_request,
                error="unauthenticated: actor_id does not match the registered interface identity",
            )

        session = IdentitySessionManager.instance().get_session(
            connection_id=connection_id
        )
        if session is None:
            return self._build_environment_api_operation_failure(
                network_op=network_op,
                request=api_request,
                error="unauthenticated: identity session required (run identity_challenge + identity_login)",
            )
        if not _actor_id_matches_public_key(
            actor_id=binding.identity_id,
            public_key=session.public_key,
        ):
            return self._build_environment_api_operation_failure(
                network_op=network_op,
                request=api_request,
                error="unauthenticated: actor_id does not match authenticated public key (anti-claim)",
            )

        token_binding = session.token_binding
        if token_binding is not None:
            payload = api_request.request_payload
            if (
                token_binding.context_environment_id is not None
                and self._uuid_from_api_payload(payload, "environment_id")
                != token_binding.context_environment_id
            ):
                return self._build_environment_api_operation_failure(
                    network_op=network_op,
                    request=api_request,
                    error="forbidden: token context binding mismatch (environment_id)",
                )
            if (
                token_binding.context_process_id is not None
                and self._uuid_from_api_payload(payload, "process_id")
                != token_binding.context_process_id
            ):
                return self._build_environment_api_operation_failure(
                    network_op=network_op,
                    request=api_request,
                    error="forbidden: token context binding mismatch (process_id)",
                )
            if (
                token_binding.context_thread_id is not None
                and self._uuid_from_api_payload(payload, "thread_id")
                != token_binding.context_thread_id
            ):
                return self._build_environment_api_operation_failure(
                    network_op=network_op,
                    request=api_request,
                    error="forbidden: token context binding mismatch (thread_id)",
                )

        return None

    @staticmethod
    def _uuid_from_api_payload(payload: Mapping[str, Any], key: str) -> UUID | None:
        raw = payload.get(key)
        if raw is None:
            return None
        if isinstance(raw, UUID):
            return raw
        try:
            return UUID(str(raw))
        except Exception:
            return None

    def _build_environment_api_operation_failure(
        self,
        *,
        network_op: NetworkOperation,
        request: InvokeApiEndpointRequest,
        error: str,
    ) -> NetworkOperation:
        return NetworkOperation(
            id=network_op.id,
            message_type=NetworkOperationMessageType.response,
            type=network_op.type,
            network_response=NetworkResponse(
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request
                    else None
                ),
                status=NetworkRequestStatus.failed,
                error=error,
            ),
            api_operation=ApiOperation(
                response=InvokeApiEndpointResponse(
                    actor_id=request.actor_id,
                    status=ApiRequestStatus.failed,
                    error=error,
                    response_payload=None,
                    stream_lifecycle=ApiStreamLifecycle.auto_close,
                )
            ),
        )

    def _build_failed_network_operation_response(
        self,
        *,
        data: str,
        network_op: NetworkOperation | None,
        error: Exception,
    ) -> str:
        """
        Best-effort fallback: ensure every REQUEST yields a RESPONSE (never timeout),
        even when request DTO validation fails and the payload cannot be parsed.
        """

        raw: dict[str, Any] | None = None
        try:
            raw = json.loads(data)
        except Exception:
            raw = None

        op_id: UUID | None = None
        if network_op is not None:
            op_id = network_op.id
        elif isinstance(raw, dict):
            raw_id = raw.get("id")
            if raw_id is not None:
                try:
                    op_id = UUID(str(raw_id))
                except Exception:
                    op_id = None
        if op_id is None:
            op_id = uuid4()

        op_type: NetworkOperationType | None = (
            network_op.type if network_op is not None else None
        )
        if op_type is None and isinstance(raw, dict):
            raw_type = raw.get("type")
            if raw_type is not None:
                try:
                    op_type = NetworkOperationType(raw_type)
                except Exception:
                    op_type = None
        if op_type is None:
            op_type = NetworkOperationType.network_node

        request_hop: NetworkOperationHop | None = None
        if network_op is not None and network_op.network_operation_hop_list:
            request_hop = network_op.network_operation_hop_list[0]
        elif isinstance(raw, dict):
            hop_list = raw.get("network_operation_hop_list")
            if isinstance(hop_list, list) and hop_list:
                try:
                    request_hop = NetworkOperationHop.model_validate(hop_list[0])
                except Exception:
                    request_hop = None

        response_hops: list[NetworkOperationHop] = []
        if request_hop is not None:
            response_hops.append(
                NetworkOperationHop(
                    source_app_type=request_hop.target_app_type,
                    source_node_id=request_hop.target_node_id,
                    source_interface_id=request_hop.target_interface_id,
                    source_environment_id=request_hop.target_environment_id,
                    target_app_type=request_hop.source_app_type,
                    target_node_id=request_hop.source_node_id,
                    target_interface_id=request_hop.source_interface_id,
                    target_environment_id=request_hop.source_environment_id,
                )
            )

        network_request_id: UUID | None = None
        if network_op is not None and network_op.network_request is not None:
            network_request_id = network_op.network_request.id
        elif isinstance(raw, dict):
            raw_req = raw.get("network_request")
            if isinstance(raw_req, dict):
                raw_req_id = raw_req.get("id")
                if raw_req_id is not None:
                    try:
                        network_request_id = UUID(str(raw_req_id))
                    except Exception:
                        network_request_id = None

        network_response = NetworkResponse(
            network_request_id=network_request_id,
            status=NetworkRequestStatus.failed,
            error=str(error),
        )

        api_op_response: ApiOperation | None = None
        service_op_response: ServiceOperation | None = None
        node_op_response: NetworkNodeOperation | None = None

        try:
            if op_type == NetworkOperationType.network_node:
                node_op_response = self._build_failed_network_node_operation(
                    raw=raw, network_op=network_op, error=error
                )
            elif op_type == NetworkOperationType.api:
                api_op_response = self._build_failed_api_operation(
                    raw=raw, network_op=network_op, error=error
                )
            elif op_type == NetworkOperationType.service:
                service_op_response = self._build_failed_service_operation(
                    raw=raw, network_op=network_op, error=error
                )
        except Exception:
            # Never allow fallback response construction to raise; the transport-level
            # NetworkResponse carries the failure semantics.
            pass

        response_op = NetworkOperation(
            id=op_id,
            message_type=NetworkOperationMessageType.response,
            type=op_type,
            network_response=network_response,
            api_operation=api_op_response,
            service_operation=service_op_response,
            network_node_operation=node_op_response,
            network_operation_hop_list=response_hops,
        )
        return response_op.model_dump_json()

    def _build_failed_api_operation(
        self,
        *,
        raw: dict[str, Any] | None,
        network_op: NetworkOperation | None,
        error: Exception,
    ) -> ApiOperation | None:
        request: InvokeApiEndpointRequest | None = None
        if network_op is not None and network_op.api_operation is not None:
            if isinstance(network_op.api_operation.request, InvokeApiEndpointRequest):
                request = network_op.api_operation.request
        elif isinstance(raw, dict):
            raw_api_op = raw.get("api_operation")
            if isinstance(raw_api_op, dict):
                raw_request = raw_api_op.get("request")
                if isinstance(raw_request, dict):
                    try:
                        request = InvokeApiEndpointRequest.model_validate(raw_request)
                    except Exception:
                        request = None

        if request is None:
            return None

        return ApiOperation(
            response=InvokeApiEndpointResponse(
                actor_id=request.actor_id,
                status=ApiRequestStatus.failed,
                error=str(error),
            )
        )

    def _build_failed_service_operation(
        self,
        *,
        raw: dict[str, Any] | None,
        network_op: NetworkOperation | None,
        error: Exception,
    ) -> ServiceOperation | None:
        service_request_present = False
        if network_op is not None and network_op.service_operation is not None:
            service_request_present = network_op.service_operation.request is not None
        elif isinstance(raw, dict):
            raw_service_op = raw.get("service_operation")
            if isinstance(raw_service_op, dict):
                service_request_present = isinstance(
                    raw_service_op.get("request"), dict
                )

        if not service_request_present:
            return None

        return ServiceOperation(
            response=ServiceOperationResponse(
                status=ServiceRequestStatus.failed,
                error=str(error),
            )
        )

    def _build_failed_network_node_operation(
        self,
        *,
        raw: dict[str, Any] | None,
        network_op: NetworkOperation | None,
        error: Exception,
    ) -> NetworkNodeOperation | None:
        request: dict[str, Any] | None = None
        if network_op is not None and network_op.network_node_operation is not None:
            req = network_op.network_node_operation.request
            if req is not None:
                request = req.model_dump(mode="json", exclude_none=True)
        if request is None and isinstance(raw, dict):
            node_op = raw.get("network_node_operation")
            if isinstance(node_op, dict):
                req = node_op.get("request")
                if isinstance(req, dict):
                    request = req
        if request is None:
            return None

        op_name = str(request.get("operation") or "").strip() or None
        actor_id_raw = request.get("actor_id")
        node_id_raw = request.get("node_id")

        actor_id = UUID(str(actor_id_raw)) if actor_id_raw is not None else uuid4()
        node_id = UUID(str(node_id_raw)) if node_id_raw is not None else None

        if op_name == "provision_environment":
            return self._build_network_node_bridge_response(
                NodeHostProvisionEnvironmentResponse(
                    actor_id=actor_id,
                    node_id=node_id,
                    status="failed",
                    error=str(error),
                    environment_config_id=(
                        UUID(str(request["environment_config_id"]))
                        if request.get("environment_config_id")
                        else None
                    ),
                    environment_title=(
                        str(request.get("environment_title"))
                        if request.get("environment_title")
                        else None
                    ),
                    environment_endpoint=None,
                    environment_id=None,
                    ocg_hash=None,
                    opg_hashes=[],
                )
            )

        if op_name == "get_environment_status":
            env_id_raw = request.get("environment_id")
            env_id = UUID(str(env_id_raw)) if env_id_raw is not None else uuid4()
            return self._build_network_node_bridge_response(
                NodeHostGetEnvironmentStatusResponse(
                    actor_id=actor_id,
                    node_id=node_id,
                    status="failed",
                    error=str(error),
                    environment_id=env_id,
                )
            )

        if op_name == "discover_environment_configs":
            return self._build_network_node_bridge_response(
                NodeHostDiscoverEnvironmentConfigsResponse(
                    actor_id=actor_id,
                    node_id=node_id,
                    configs=[],
                )
            )

        if op_name == "get_boot_environment_descriptor":
            return self._build_network_node_bridge_response(
                NodeHostGetBootEnvironmentDescriptorResponse(
                    actor_id=actor_id,
                    node_id=node_id,
                    status="failed",
                    error=str(error),
                    descriptor=None,
                )
            )

        if op_name == "close_stream":
            op_id_raw = request.get("network_operation_id")
            op_id = UUID(str(op_id_raw)) if op_id_raw is not None else uuid4()
            return NetworkNodeOperation(
                response=CloseStreamResponse(
                    actor_id=actor_id,
                    node_id=node_id,
                    status="failed",
                    error=str(error),
                    network_operation_id=op_id,
                )
            )

        if op_name == "membership_status":
            return NetworkNodeOperation(
                response=MembershipStatusResponse(
                    actor_id=actor_id,
                    node_id=node_id,
                    status="failed",
                    error=str(error),
                    is_active=False,
                    is_bypassed=False,
                    plan_label=None,
                    current_period_end=None,
                )
            )

        # Unknown op: still return a response envelope (client should read NetworkResponse.error).
        # !! TODO: Clarify - Improve UnknownNetworkNodeOperationResponse
        return NetworkNodeOperation(
            response=UnknownNetworkNodeOperationResponse(
                operation=op_name or "unknown",
                actor_id=actor_id,
                node_id=node_id,
                status="failed",
                error=str(error),
            )
        )

    async def _handle_interface_notification(
        self, data: str, message_type: WsMessageFrameType
    ) -> None:
        """
        Handle incoming NetworkOperation notifications using hop-based routing

        Args:
            data: Serialized NetworkOperation JSON
            message_type: The message frame type
        """
        try:
            raw_network_op = json.loads(data)
            # Parse NetworkOperation from data
            network_op = NetworkOperation.model_validate_json(data)

            # Validate hop structure
            current_hop = self._get_current_header(network_op)

            if (
                current_hop.target_app_type == NetworkAppType.network_node
                and current_hop.target_node_id is None
            ):
                from aware_network.network.node.manager import network_node_manager

                current_hop.target_node_id = network_node_manager.hosted_node_id

            # Validate hop constraints
            if not self.validate_hop_constraints(current_hop):
                logger.error(
                    f"Invalid hop constraints in NetworkOperation notification {network_op.id}"
                )
                return

            logger.info(f"Processing NetworkOperation notification {network_op.id}")

            # STREAM payloads are transport-only and should be forwarded to the originating interface.
            if network_op.message_type == NetworkOperationMessageType.stream:
                await self._forward_stream_to_interface(network_op)
                return

            # Route based on target
            if self._is_target_this_node(current_hop):
                if network_op.type == NetworkOperationType.network_node:
                    await self._route_to_network_node_service(network_op)
                elif network_op.type == NetworkOperationType.environment:
                    _dispatch_environment_operation_notification_to_lane_bus(
                        raw_network_op=raw_network_op,
                    )
                else:
                    raise RuntimeError(
                        f"Unsupported NetworkOperation.type for notification: {network_op.type}"
                    )
            else:
                # Forward to target node
                await self._forward_to_target_node(network_op)

        except Exception as e:
            logger.error(f"Error handling NetworkOperation notification: {e}")

    async def _forward_stream_to_interface(self, network_op: NetworkOperation) -> None:
        """Forward a STREAM NetworkOperation to the originating interface connection."""
        origin_interface_id = self._stream_origin_by_operation_id.get(network_op.id)
        if origin_interface_id is None:
            logger.warning(
                "[STREAM] No origin interface recorded for NetworkOperation %s",
                network_op.id,
            )
            return

        from aware_network.network.node.manager import network_node_manager

        node_id = network_node_manager.hosted_node_id
        hop = NetworkOperationHop(
            source_app_type=NetworkAppType.network_node,
            source_node_id=node_id,
            target_app_type=NetworkAppType.interface,
            target_node_id=node_id,
            target_interface_id=origin_interface_id,
        )

        forward_op = NetworkOperation(
            id=network_op.id,
            message_type=NetworkOperationMessageType.stream,
            type=network_op.type,
            network_operation_hop_list=[hop],
            api_operation=network_op.api_operation,
            service_operation=network_op.service_operation,
            network_node_operation=network_op.network_node_operation,
        )

        duplex = self._network_app.get_duplex_server(NetworkAppType.interface)
        await duplex.send_notification(
            connection_id=origin_interface_id,
            data_serialized=forward_op.model_dump_json(),
        )

    # ===============================
    # Routing Implementation
    # ===============================

    async def _route_to_api_host(
        self,
        network_op: NetworkOperation,
    ) -> NetworkOperation | None:
        """Route a canonical API NetworkOperation to one local or remote hosted Service runtime."""

        current_hop = self._get_current_header(network_op)
        await self._persist_hop_for_audit(network_op, current_hop)

        api_op = network_op.api_operation
        if api_op is None:
            raise RuntimeError("NetworkOperation missing api_operation")

        if network_op.message_type == NetworkOperationMessageType.notification:
            raise RuntimeError(
                "NetworkOperation(type=api) notifications are not supported yet"
            )
        if network_op.message_type != NetworkOperationMessageType.request:
            raise RuntimeError(
                f"Unsupported message_type for api routing: {network_op.message_type}"
            )
        if api_op.request is None:
            raise RuntimeError("ApiOperation.request is required")
        if not isinstance(
            api_op.request,
            (InvokeApiEndpointRequest, StreamApiEndpointRequest),
        ):
            raise RuntimeError(
                "NetworkOperation.api_operation.request is not an "
                "InvokeApiEndpointRequest or StreamApiEndpointRequest"
            )

        request = api_op.request
        stream_requested = isinstance(request, StreamApiEndpointRequest)
        if not stream_requested:
            node_host_response = await self._route_to_node_host_api(
                network_op=network_op,
                request=request,
            )
            if node_host_response is not None:
                return node_host_response
            environment_response = await self._route_to_environment_api(
                network_op=network_op,
                request=request,
            )
            if environment_response is not None:
                return environment_response

        try:
            hosted_runtime = await resolve_node_hosted_service_runtime_for_endpoint_ref(
                node_app=self._network_app,
                endpoint_ref=request.endpoint_ref,
            )
        except CommittedHostedServiceLookupMiss as local_error:
            remote_route = await self._resolve_remote_api_route(
                endpoint_ref=request.endpoint_ref,
                actor_id=request.actor_id,
            )
            if remote_route is None:
                raise local_error
            if (
                stream_requested
                and not remote_route.advertisement.supports_stream_events
            ):
                raise RuntimeError(
                    "Remote hosted Service does not advertise stream event support "
                    f"for API endpoint {request.endpoint_ref!r}"
                )
            return await self._send_request_to_target_node(
                network_op,
                target_node_id=remote_route.peer.node_id,
                external_url=remote_route.peer.base_url,
                persist_current_hop=False,
            )

        hosted_request = ServiceHostApiIngressRequest(
            actor_id=request.actor_id,
            endpoint_ref=request.endpoint_ref,
            discriminant=request.discriminant,
            request_payload=request.request_payload,
            invocation_context=_api_invocation_context_payload(request),
            network_request_id=(
                network_op.network_request.id
                if network_op.network_request is not None
                else None
            ),
            stream_requested=False,
        )
        if stream_requested:
            if not self._hosted_runtime_supports_api_stream_endpoint(
                runtime=hosted_runtime,
                endpoint_ref=request.endpoint_ref,
            ):
                raise RuntimeError(
                    "Hosted Service runtime does not advertise API stream support "
                    f"for endpoint {request.endpoint_ref!r}"
                )
            hosted_request = ServiceHostApiIngressRequest(
                actor_id=request.actor_id,
                endpoint_ref=request.endpoint_ref,
                discriminant=request.discriminant,
                request_payload=request.request_payload,
                invocation_context=_api_invocation_context_payload(request),
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request is not None
                    else None
                ),
                stream_requested=True,
            )
            handle = open_api_ingress_stream_to_hosted_service_runtime(
                runtime=hosted_runtime,
                request=hosted_request,
            )
            self._stream_close_registry()[network_op.id] = handle.close
            self._start_api_stream_forwarder(
                request_network_op=network_op,
                current_hop=current_hop,
                actor_id=request.actor_id,
                handle=handle,
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=NetworkOperationType.api,
                network_response=NetworkResponse(
                    network_request_id=(
                        network_op.network_request.id
                        if network_op.network_request is not None
                        else None
                    ),
                    status=NetworkRequestStatus.succeeded,
                ),
                api_operation=ApiOperation(
                    response=InvokeApiEndpointResponse(
                        actor_id=request.actor_id,
                        status=ApiRequestStatus.succeeded,
                        response_payload=None,
                        stream_lifecycle=ApiStreamLifecycle.started,
                    )
                ),
            )

        response = await route_api_request_to_hosted_service_runtime(
            runtime=hosted_runtime,
            request=hosted_request,
        )

        return NetworkOperation(
            id=network_op.id,
            message_type=NetworkOperationMessageType.response,
            type=NetworkOperationType.api,
            network_response=NetworkResponse(
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request is not None
                    else None
                ),
                status=self._network_request_status_from_api_response(response),
                error=response.error,
            ),
            api_operation=ApiOperation(
                response=InvokeApiEndpointResponse(
                    actor_id=request.actor_id,
                    status=self._api_request_status_from_service_response(response),
                    error=response.error,
                    response_payload=response.response_payload,
                    stream_lifecycle=self._api_stream_lifecycle_from_service_response(
                        response
                    ),
                )
            ),
        )

    def _start_api_stream_forwarder(
        self,
        *,
        request_network_op: NetworkOperation,
        current_hop: NetworkOperationHop,
        actor_id: UUID | None,
        handle: Any,
    ) -> None:
        task = asyncio.create_task(
            self._forward_api_stream_from_service_host(
                request_network_op=request_network_op,
                current_hop=current_hop,
                actor_id=actor_id,
                handle=handle,
            )
        )
        task.add_done_callback(
            lambda completed: self._log_api_stream_forwarder_result(
                request_network_op.id,
                completed,
            )
        )

    def _log_api_stream_forwarder_result(
        self,
        operation_id: UUID,
        task: asyncio.Task[None],
    ) -> None:
        if task.cancelled():
            return
        with contextlib.suppress(Exception):
            task.result()
            return
        logger.warning("API stream forwarder failed for operation_id=%s", operation_id)

    async def _forward_api_stream_from_service_host(
        self,
        *,
        request_network_op: NetworkOperation,
        current_hop: NetworkOperationHop,
        actor_id: UUID | None,
        handle: Any,
    ) -> None:
        try:
            async for event in handle.events:
                if event.kind.value == "close":
                    await self._emit_api_stream_close(
                        request_network_op=request_network_op,
                        current_hop=current_hop,
                        actor_id=actor_id,
                    )
                    return
                if event.response is None:
                    continue
                await self._emit_api_stream_response(
                    request_network_op=request_network_op,
                    current_hop=current_hop,
                    actor_id=actor_id,
                    response=event.response.to_contract(),
                )
            with contextlib.suppress(Exception):
                response = await handle.response
                if response.stream_lifecycle is ServiceStreamLifecycle.started:
                    return
                await self._emit_api_stream_response(
                    request_network_op=request_network_op,
                    current_hop=current_hop,
                    actor_id=actor_id,
                    response=response,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._emit_api_stream_response(
                request_network_op=request_network_op,
                current_hop=current_hop,
                actor_id=actor_id,
                response=ServiceOperationResponse(
                    status=ServiceRequestStatus.failed,
                    error=str(exc),
                    stream_lifecycle=ServiceStreamLifecycle.closed,
                ),
            )
        finally:
            self._stream_origin_by_operation_id.pop(request_network_op.id, None)
            self._api_stream_origin_connections().pop(request_network_op.id, None)
            self._stream_close_registry().pop(request_network_op.id, None)
            with contextlib.suppress(Exception):
                await handle.close()

    async def _emit_api_stream_response(
        self,
        *,
        request_network_op: NetworkOperation,
        current_hop: NetworkOperationHop,
        actor_id: UUID | None,
        response: ServiceOperationResponse,
    ) -> None:
        response_payload = response.response_payload
        if response_payload is not None:
            try:
                response_payload = ServiceDuplexStreamEventEnvelope.model_validate(
                    response_payload
                ).payload
            except Exception:
                response_payload = response.response_payload

        stream_op = NetworkOperation(
            id=request_network_op.id,
            message_type=NetworkOperationMessageType.stream,
            type=NetworkOperationType.api,
            network_operation_hop_list=[current_hop.model_copy(deep=True)],
            api_operation=ApiOperation(
                response=InvokeApiEndpointResponse(
                    actor_id=actor_id,
                    status=self._api_request_status_from_service_response(response),
                    error=response.error,
                    response_payload=response_payload,
                    stream_lifecycle=self._api_stream_lifecycle_from_service_response(
                        response
                    ),
                )
            ),
        )

        if current_hop.source_app_type == NetworkAppType.interface:
            await self._forward_stream_to_interface(stream_op)
            return

        if current_hop.source_app_type == NetworkAppType.network_node:
            origin_connection_id = self._api_stream_origin_connections().get(
                request_network_op.id
            )
            if origin_connection_id is not None:
                duplex = self._network_app.get_duplex_server(
                    NetworkAppType.network_node
                )
                await duplex.send_notification(
                    connection_id=origin_connection_id,
                    data_serialized=stream_op.model_dump_json(),
                )
                return
            if current_hop.source_node_id is None:
                raise RuntimeError(
                    "API stream response cannot target source node without source_node_id"
                )
            await self._send_notification_to_target_node(
                stream_op,
                target_node_id=current_hop.source_node_id,
                external_url=await self._resolve_peer_base_url(
                    target_node_id=current_hop.source_node_id
                ),
                persist_current_hop=False,
            )
            return

        raise RuntimeError(
            "API stream response source app type is unsupported for forwarding: "
            f"{current_hop.source_app_type}"
        )

    async def _emit_api_stream_close(
        self,
        *,
        request_network_op: NetworkOperation,
        current_hop: NetworkOperationHop,
        actor_id: UUID | None,
    ) -> None:
        await self._emit_api_stream_response(
            request_network_op=request_network_op,
            current_hop=current_hop,
            actor_id=actor_id,
            response=ServiceOperationResponse(
                status=ServiceRequestStatus.succeeded,
                response_payload=None,
                stream_lifecycle=ServiceStreamLifecycle.closed,
            ),
        )

    async def _route_to_service_host(
        self,
        network_op: NetworkOperation,
    ) -> NetworkOperation | None:
        """Route a canonical Service NetworkOperation to one local or remote hosted Service runtime."""

        current_hop = self._get_current_header(network_op)
        await self._persist_hop_for_audit(network_op, current_hop)

        service_op = network_op.service_operation
        if service_op is None:
            raise RuntimeError("NetworkOperation missing service_operation")

        if network_op.message_type == NetworkOperationMessageType.notification:
            raise RuntimeError(
                "NetworkOperation(type=service) notifications are not supported yet"
            )
        if network_op.message_type != NetworkOperationMessageType.request:
            raise RuntimeError(
                f"Unsupported message_type for service routing: {network_op.message_type}"
            )
        if service_op.request is None:
            raise RuntimeError("ServiceOperation.request is required")

        request = service_op.request
        try:
            hosted_runtime = (
                await resolve_node_hosted_service_runtime_for_service_request(
                    node_app=self._network_app,
                    request=request,
                )
            )
        except CommittedHostedServiceLookupMiss as local_error:
            remote_route = await self._resolve_remote_service_request_route(
                request=request,
                actor_id=(
                    request.context.actor_id if request.context is not None else None
                ),
            )
            if remote_route is None:
                raise local_error
            if (
                self._service_request_declares_stream(request)
                and not remote_route.advertisement.supports_stream_events
            ):
                raise RuntimeError(
                    "Remote hosted Service does not advertise stream event support "
                    f"for {self._service_request_resolution_label(request)!r}"
                )
            return await self._send_request_to_target_node(
                network_op,
                target_node_id=remote_route.peer.node_id,
                external_url=remote_route.peer.base_url,
                timeout_s=self._service_remote_request_timeout_s(),
                persist_current_hop=False,
            )

        handle = open_request_stream_to_hosted_service_runtime(
            runtime=hosted_runtime,
            request=request,
        )
        try:
            async for event in handle.events:
                if event.kind.value == "close":
                    self._stream_origin_by_operation_id.pop(network_op.id, None)
                    self._api_stream_origin_connections().pop(network_op.id, None)
                    close_registry = getattr(
                        self, "_stream_close_by_operation_id", None
                    )
                    if isinstance(close_registry, dict):
                        close_registry.pop(network_op.id, None)
                    continue
                if event.response is None:
                    continue
                await self._emit_service_stream_response(
                    request_network_op=network_op,
                    current_hop=current_hop,
                    response=event.response.to_contract(),
                )
            response = await handle.response
        finally:
            await handle.close()

        return NetworkOperation(
            id=network_op.id,
            message_type=NetworkOperationMessageType.response,
            type=NetworkOperationType.service,
            network_response=NetworkResponse(
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request is not None
                    else None
                ),
                status=self._network_request_status_from_service_response(response),
                error=response.error,
            ),
            service_operation=ServiceOperation(response=response),
        )

    @staticmethod
    def _network_request_status_from_service_response(
        response: ServiceOperationResponse,
    ) -> NetworkRequestStatus:
        if response.status is ServiceRequestStatus.succeeded:
            return NetworkRequestStatus.succeeded
        if response.status is ServiceRequestStatus.pending:
            return NetworkRequestStatus.pending
        return NetworkRequestStatus.failed

    @staticmethod
    def _api_request_status_from_service_response(
        response: ServiceOperationResponse,
    ) -> ApiRequestStatus:
        if response.status is ServiceRequestStatus.succeeded:
            return ApiRequestStatus.succeeded
        if response.status is ServiceRequestStatus.pending:
            return ApiRequestStatus.pending
        return ApiRequestStatus.failed

    @classmethod
    def _network_request_status_from_api_response(
        cls,
        response: ServiceOperationResponse,
    ) -> NetworkRequestStatus:
        api_status = cls._api_request_status_from_service_response(response)
        if api_status is ApiRequestStatus.succeeded:
            return NetworkRequestStatus.succeeded
        if api_status is ApiRequestStatus.pending:
            return NetworkRequestStatus.pending
        return NetworkRequestStatus.failed

    @staticmethod
    def _api_stream_lifecycle_from_service_response(
        response: ServiceOperationResponse,
    ) -> ApiStreamLifecycle:
        if response.stream_lifecycle is ServiceStreamLifecycle.started:
            return ApiStreamLifecycle.started
        if response.stream_lifecycle is ServiceStreamLifecycle.closed:
            return ApiStreamLifecycle.closed
        return ApiStreamLifecycle.auto_close

    @staticmethod
    def _hosted_runtime_supports_api_stream_endpoint(
        *,
        runtime: Any,
        endpoint_ref: str,
    ) -> bool:
        advertised = getattr(
            runtime,
            "advertised_stream_endpoint_refs_by_service",
            None,
        )
        if not callable(advertised):
            return False
        endpoint = endpoint_ref.strip()
        if not endpoint:
            return False
        return any(endpoint in tuple(refs) for refs in advertised().values())

    async def _resolve_peer_base_url(
        self,
        *,
        target_node_id: UUID | None,
    ) -> str:
        if target_node_id is None:
            raise RuntimeError("NetworkOperationHop missing target_node_id")
        peers = await discover_network_node_peer_endpoints(
            route_to_environment_service=self.route_to_environment_service,
            hosted_environment_service=self._require_hosted_environment_service(),
            network_sdk_client=getattr(self, "_network_sdk_client", None),
        )
        peer = next((item for item in peers if item.node_id == target_node_id), None)
        if peer is None:
            raise RuntimeError(
                f"Node peer transport is not registered for target node {target_node_id}"
            )
        return peer.base_url

    async def _resolve_remote_service_route(
        self,
        *,
        service_name: str,
        actor_id: UUID | None,
    ) -> RemoteHostedServiceRoute | None:
        routes = await discover_remote_hosted_service_routes(
            network_app=self._network_app,
            route_to_environment_service=self.route_to_environment_service,
            hosted_environment_service=self._require_hosted_environment_service(),
            service_name=service_name,
            network_sdk_client=getattr(self, "_network_sdk_client", None),
            actor_id=actor_id,
            timeout_s=self._service_remote_discovery_timeout_s(),
        )
        if not routes:
            return None
        service_ids = {
            route.advertisement.service_id
            for route in routes
            if route.advertisement.service_id is not None
        }
        if len(service_ids) != len(routes):
            raise RuntimeError(
                "Remote Node hosted-service advertisements for "
                f"{service_name!r} are missing committed service_id"
            )
        if len(service_ids) != 1:
            committed_service_ids = ", ".join(
                sorted(str(service_id) for service_id in service_ids)
            )
            raise RuntimeError(
                "Multiple remote Nodes advertise conflicting committed service_id "
                f"for hosted service {service_name!r}: [{committed_service_ids}]"
            )
        if len(routes) != 1:
            peer_ids = ", ".join(str(route.peer.node_id) for route in routes)
            committed_service_id = next(iter(service_ids))
            raise RuntimeError(
                "Multiple remote Nodes advertise the same committed hosted service "
                f"{service_name!r} ({committed_service_id}): [{peer_ids}]"
            )
        return routes[0]

    async def _resolve_remote_service_request_route(
        self,
        *,
        request: ServiceOperationRequest,
        actor_id: UUID | None,
    ) -> RemoteHostedServiceRoute | None:
        api_dispatch = request.api_dispatch
        if api_dispatch is None:
            return await self._resolve_remote_service_route(
                service_name=request.service,
                actor_id=actor_id,
            )

        normalized_service_name = request.service.strip()
        if not normalized_service_name:
            raise RuntimeError("ServiceOperationRequest.service is required")
        endpoint_ref = api_dispatch.envelope.endpoint_ref.strip()
        if not endpoint_ref:
            raise RuntimeError(
                "ServiceApiDispatchRequest.envelope.endpoint_ref is required"
            )

        remote_route = await self._resolve_remote_api_route(
            endpoint_ref=endpoint_ref,
            actor_id=actor_id,
        )
        if remote_route is None:
            return None

        advertised_service_name = (
            remote_route.advertisement.service_name or ""
        ).strip()
        if advertised_service_name.casefold() != normalized_service_name.casefold():
            raise RuntimeError(
                "ServiceOperationRequest.service "
                f"{normalized_service_name!r} does not match remote hosted-service "
                "advertisement service_name "
                f"{advertised_service_name!r} for endpoint_ref {endpoint_ref!r}"
            )
        return remote_route

    async def _resolve_remote_api_route(
        self,
        *,
        endpoint_ref: str,
        actor_id: UUID | None,
    ) -> RemoteHostedServiceRoute | None:
        routes = await discover_remote_hosted_service_routes_for_endpoint_ref(
            network_app=self._network_app,
            route_to_environment_service=self.route_to_environment_service,
            hosted_environment_service=self._require_hosted_environment_service(),
            endpoint_ref=endpoint_ref,
            network_sdk_client=getattr(self, "_network_sdk_client", None),
            actor_id=actor_id,
            timeout_s=self._service_remote_discovery_timeout_s(),
        )
        if not routes:
            return None
        service_ids = {
            route.advertisement.service_id
            for route in routes
            if route.advertisement.service_id is not None
        }
        if len(service_ids) != len(routes):
            raise RuntimeError(
                "Remote Node hosted-service advertisements for "
                f"API endpoint {endpoint_ref!r} are missing committed service_id"
            )
        if len(service_ids) != 1:
            committed_service_ids = ", ".join(
                sorted(str(service_id) for service_id in service_ids)
            )
            raise RuntimeError(
                "Multiple remote Nodes advertise conflicting committed service_id "
                f"for hosted API endpoint {endpoint_ref!r}: "
                f"[{committed_service_ids}]"
            )
        if len(routes) != 1:
            peer_ids = ", ".join(str(route.peer.node_id) for route in routes)
            committed_service_id = next(iter(service_ids))
            raise RuntimeError(
                "Multiple remote Nodes advertise the same committed hosted API "
                f"endpoint {endpoint_ref!r} ({committed_service_id}): [{peer_ids}]"
            )
        return routes[0]

    @staticmethod
    def _service_remote_discovery_timeout_s() -> float:
        return float(
            os.environ.get("AWARE_NODE_SERVICE_REMOTE_DISCOVERY_TIMEOUT_S", "5.0")
        )

    @staticmethod
    def _service_remote_request_timeout_s() -> float:
        return float(
            os.environ.get("AWARE_NODE_SERVICE_REMOTE_REQUEST_TIMEOUT_S", "15.0")
        )

    @staticmethod
    def _service_request_declares_stream(request: ServiceOperationRequest) -> bool:
        return (
            request.stream_target_id is not None
            or request.stream_correlation_id is not None
        )

    @staticmethod
    def _service_request_resolution_label(request: ServiceOperationRequest) -> str:
        if request.api_dispatch is not None:
            endpoint_ref = request.api_dispatch.envelope.endpoint_ref.strip()
            if endpoint_ref:
                return f"endpoint_ref {endpoint_ref!r}"
        return f"service {request.service!r}"

    async def _emit_service_stream_response(
        self,
        *,
        request_network_op: NetworkOperation,
        current_hop: NetworkOperationHop,
        response: ServiceOperationResponse,
    ) -> None:
        stream_op = NetworkOperation(
            id=request_network_op.id,
            message_type=NetworkOperationMessageType.stream,
            type=NetworkOperationType.service,
            network_operation_hop_list=[current_hop.model_copy(deep=True)],
            service_operation=ServiceOperation(response=response),
        )

        if current_hop.source_app_type == NetworkAppType.interface:
            await self._forward_stream_to_interface(stream_op)
            return

        if current_hop.source_app_type == NetworkAppType.network_node:
            if current_hop.source_node_id is None:
                raise RuntimeError(
                    "Service stream response cannot target source node without source_node_id"
                )
            await self._send_notification_to_target_node(
                stream_op,
                target_node_id=current_hop.source_node_id,
                external_url=await self._resolve_peer_base_url(
                    target_node_id=current_hop.source_node_id
                ),
                persist_current_hop=False,
            )
            return

        raise RuntimeError(
            "Service stream response source app type is unsupported for forwarding: "
            f"{current_hop.source_app_type}"
        )

    async def _send_request_to_target_node(
        self,
        network_op: NetworkOperation,
        *,
        target_node_id: UUID | None,
        external_url: str | None,
        timeout_s: float | None = None,
        persist_current_hop: bool = True,
    ) -> NetworkOperation:
        current_hop = self._get_current_header(network_op)
        if persist_current_hop:
            await self._persist_hop_for_audit(network_op, current_hop)

        if target_node_id is None:
            raise RuntimeError("NetworkOperationHop missing target_node_id")

        from aware_network.network.node.manager import network_node_manager
        from aware_network_ontology.stable_ids import stable_network_node_peer_id

        local_node_id = network_node_manager.hosted_node_id
        duplex = self._network_app.get_duplex_client(NetworkAppType.network_node)
        connection_id = stable_network_node_peer_id(
            source_peer_node_id=local_node_id,
            target_peer_node_id=target_node_id,
        )
        await duplex.ensure_connection(
            connection_id=connection_id,
            external_url=external_url,
        )

        next_hop = self._create_next_hop(
            current_hop=current_hop,
            target_app_type=NetworkAppType.network_node,
            target_node_id=target_node_id,
            strip_source_interface=True,
        )
        forward_op = network_op.model_copy(deep=True)
        forward_op.network_operation_hop_list = [next_hop]

        raw = await duplex.send_request(
            connection_id=connection_id,
            data_serialized=forward_op.model_dump_json(),
            timeout_s=timeout_s,
        )
        if raw is None:
            raise RuntimeError(
                f"No response received from remote node {target_node_id}"
            )
        if isinstance(raw, str):
            return NetworkOperation.model_validate_json(raw)
        if isinstance(raw, dict):
            return NetworkOperation.model_validate(raw)
        raise TypeError(f"Unexpected remote node response type: {type(raw)}")

    async def _send_notification_to_target_node(
        self,
        network_op: NetworkOperation,
        *,
        target_node_id: UUID | None,
        external_url: str | None,
        persist_current_hop: bool = True,
    ) -> bool:
        current_hop = self._get_current_header(network_op)
        if persist_current_hop:
            await self._persist_hop_for_audit(network_op, current_hop)

        if target_node_id is None:
            raise RuntimeError("NetworkOperationHop missing target_node_id")

        from aware_network.network.node.manager import network_node_manager
        from aware_network_ontology.stable_ids import stable_network_node_peer_id

        local_node_id = network_node_manager.hosted_node_id
        duplex = self._network_app.get_duplex_client(NetworkAppType.network_node)
        connection_id = stable_network_node_peer_id(
            source_peer_node_id=local_node_id,
            target_peer_node_id=target_node_id,
        )
        await duplex.ensure_connection(
            connection_id=connection_id,
            external_url=external_url,
        )

        next_hop = self._create_next_hop(
            current_hop=current_hop,
            target_app_type=NetworkAppType.network_node,
            target_node_id=target_node_id,
            strip_source_interface=True,
        )
        forward_op = network_op.model_copy(deep=True)
        forward_op.network_operation_hop_list = [next_hop]
        return await duplex.send_notification(
            connection_id=connection_id,
            data_serialized=forward_op.model_dump_json(),
        )

    async def _route_to_network_node_service(
        self, network_op: NetworkOperation
    ) -> NetworkOperation | None:
        """Handle a NetworkOperation addressed to the Network Node control-plane."""
        current_hop = self._get_current_header(network_op)
        await self._persist_hop_for_audit(network_op, current_hop)

        node_op = network_op.network_node_operation
        if node_op is None:
            raise RuntimeError("NetworkOperation missing network_node_operation")

        if network_op.message_type == NetworkOperationMessageType.notification:
            # Control-plane notifications are mostly no-ops (v0), but we must support
            # transport-level stream lifecycle without peeking into service payloads.
            if (
                node_op.request is not None
                and node_op.request.operation == "close_stream"
            ):
                if not isinstance(node_op.request, CloseStreamRequest):
                    raise RuntimeError(
                        "NetworkNodeOperation.request is not a CloseStreamRequest"
                    )
                self._stream_origin_by_operation_id.pop(
                    node_op.request.network_operation_id, None
                )
                close_stream = self._stream_close_registry().pop(
                    node_op.request.network_operation_id, None
                )
                if close_stream is not None:
                    await close_stream()
            if (
                node_op.request is not None
                and node_op.request.operation == "fanout_notify_pull"
            ):
                # v0: peers send "notify + pull" hints; the receiver decides how/when to pull commits.
                # This is intentionally transport-only: it MUST NOT execute environment operations directly.
                if current_hop.source_app_type != NetworkAppType.network_node:
                    logger.warning(
                        "fanout_notify_pull received from non-node source; ignoring"
                    )
                    return None
                branch_id_raw = getattr(node_op.request, "branch_id", None)
                projection_hash = getattr(node_op.request, "projection_hash", None)
                commit_id_raw = getattr(node_op.request, "commit_id", None)
                branch_id = branch_id_raw
                if isinstance(branch_id_raw, str):
                    try:
                        branch_id = UUID(branch_id_raw)
                    except ValueError:
                        branch_id = None
                commit_id = commit_id_raw
                if isinstance(commit_id_raw, str):
                    try:
                        commit_id = UUID(commit_id_raw)
                    except ValueError:
                        commit_id = None
                logger.info(
                    "[fanout] notify_pull from peer=%s lane=(%s,%s) head=%s",
                    current_hop.source_node_id,
                    branch_id,
                    projection_hash,
                    commit_id,
                )
                try:
                    FanoutPullHintBus.instance().dispatch(
                        FanoutPullHintNotification(
                            source_node_id=current_hop.source_node_id,
                            branch_id=branch_id,
                            projection_hash=(projection_hash or "").strip(),
                            commit_id=commit_id,
                        )
                    )
                except Exception as exc:
                    logger.warning("[fanout-hint-bus] dispatch failed: %s", exc)
            if (
                node_op.request is not None
                and node_op.request.operation == "interface_session_heartbeat"
            ):
                if not isinstance(node_op.request, InterfaceSessionHeartbeatRequest):
                    raise RuntimeError(
                        "NetworkNodeOperation.request is not a InterfaceSessionHeartbeatRequest"
                    )
                connection_id = current_hop.source_interface_id
                if connection_id is None:
                    logger.warning(
                        "Interface session heartbeat missing source_interface_id; ignoring"
                    )
                    return None

                manager = InterfaceSessionBindingManager.instance()
                binding = await manager.get_binding(connection_id=connection_id)
                if binding is None:
                    logger.warning(
                        "Heartbeat received for unregistered interface connection %s; ignoring",
                        connection_id,
                    )
                    return None
                if binding.interface_session_id != node_op.request.interface_session_id:
                    logger.warning(
                        "Heartbeat interface_session_id mismatch for connection %s: got=%s expected=%s; ignoring",
                        connection_id,
                        node_op.request.interface_session_id,
                        binding.interface_session_id,
                    )
                    return None
                await manager.record_heartbeat(connection_id=connection_id)
            return None

        if network_op.message_type != NetworkOperationMessageType.request:
            raise RuntimeError(
                f"Unsupported message_type for node routing: {network_op.message_type}"
            )

        if node_op.request is None:
            raise RuntimeError("NetworkNodeOperation.request is required")
        request = node_op.request

        from aware_network.network.node.manager import network_node_manager

        node_id = network_node_manager.hosted_node_id
        bridge_node_id = current_hop.target_node_id or node_id
        network_request_id = (
            network_op.network_request.id if network_op.network_request else None
        )

        if request.operation == "interface_session_register":
            if not isinstance(request, InterfaceSessionRegisterRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a InterfaceSessionRegisterRequest"
                )
            if current_hop.source_app_type != NetworkAppType.interface:
                raise RuntimeError(
                    "interface_session_register is only supported from INTERFACE connections"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError(
                    "interface_session_register missing source_interface_id"
                )

            manager = InterfaceSessionBindingManager.instance()
            identity_id = request.actor_id or UUID(int=0)
            try:
                ctx = await manager.register_connection(
                    connection_id=connection_id,
                    payload={
                        "interface_id": str(request.interface_id),
                        "interface_session_id": str(request.interface_session_id),
                        "identity_id": str(identity_id),
                    },
                )
                last_seen_at = ctx.last_seen_at.isoformat().replace("+00:00", "Z")
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.succeeded,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=InterfaceSessionRegisterResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="succeeded",
                            error=None,
                            interface_id=request.interface_id,
                            interface_session_id=request.interface_session_id,
                            interface_identity_network_node_id=ctx.interface_identity_network_node_id,
                            interface_session_network_binding_id=ctx.interface_session_network_binding_id,
                            last_seen_at=last_seen_at,
                            protocol_version=request.protocol_version,
                        )
                    ),
                )
            except Exception as exc:
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=str(exc),
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=InterfaceSessionRegisterResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=str(exc),
                            interface_id=request.interface_id,
                            interface_session_id=request.interface_session_id,
                            interface_identity_network_node_id=None,
                            interface_session_network_binding_id=None,
                            last_seen_at=None,
                            protocol_version=request.protocol_version,
                        )
                    ),
                )

        if request.operation == "interface_session_heartbeat":
            if not isinstance(request, InterfaceSessionHeartbeatRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a InterfaceSessionHeartbeatRequest"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError(
                    "interface_session_heartbeat missing source_interface_id"
                )

            manager = InterfaceSessionBindingManager.instance()
            binding = await manager.get_binding(connection_id=connection_id)
            if binding is None:
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error="interface session not registered",
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=InterfaceSessionHeartbeatResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error="interface session not registered",
                            interface_session_id=request.interface_session_id,
                            last_seen_at=None,
                        )
                    ),
                )

            if binding.interface_session_id != request.interface_session_id:
                err = "interface_session_id does not match the registered session for this connection"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=InterfaceSessionHeartbeatResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            interface_session_id=request.interface_session_id,
                            last_seen_at=None,
                        )
                    ),
                )

            await manager.record_heartbeat(connection_id=connection_id)
            binding = await manager.get_binding(connection_id=connection_id)
            last_seen = None
            if binding is not None:
                last_seen = binding.last_seen_at.isoformat().replace("+00:00", "Z")
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=InterfaceSessionHeartbeatResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        interface_session_id=request.interface_session_id,
                        last_seen_at=last_seen,
                    )
                ),
            )

        if request.operation == "identity_challenge":
            if not isinstance(request, IdentityChallengeRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not an IdentityChallengeRequest"
                )
            if current_hop.source_app_type != NetworkAppType.interface:
                raise RuntimeError(
                    "identity_challenge is only supported from INTERFACE connections"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError("identity_challenge missing source_interface_id")

            binding = await InterfaceSessionBindingManager.instance().get_binding(
                connection_id=connection_id
            )
            if binding is None:
                err = "unauthenticated: interface session not registered (send interface_session_register first)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityChallengeResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=request.public_key,
                            challenge="",
                            expires_at=None,
                        )
                    ),
                )
            if binding.identity_id != request.actor_id:
                err = "unauthenticated: actor_id does not match the registered interface identity"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityChallengeResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=request.public_key,
                            challenge="",
                            expires_at=None,
                        )
                    ),
                )

            err = ""
            try:
                matches_actor = _actor_id_matches_public_key(
                    actor_id=request.actor_id,
                    public_key=request.public_key,
                )
            except Exception as exc:
                matches_actor = False
                err = str(exc)
            if not matches_actor:
                err = (
                    err or "forbidden: actor_id does not match public key (anti-claim)"
                )
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityChallengeResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=request.public_key,
                            challenge="",
                            expires_at=None,
                        )
                    ),
                )

            pending = IdentitySessionManager.instance().issue_challenge(
                connection_id=connection_id,
                public_key=request.public_key,
            )
            expires_at = pending.expires_at.isoformat().replace("+00:00", "Z")
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=IdentityChallengeResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        public_key=request.public_key,
                        challenge=pending.challenge,
                        expires_at=expires_at,
                    )
                ),
            )

        if request.operation == "identity_login":
            if not isinstance(request, IdentityLoginRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not an IdentityLoginRequest"
                )
            if current_hop.source_app_type != NetworkAppType.interface:
                raise RuntimeError(
                    "identity_login is only supported from INTERFACE connections"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError("identity_login missing source_interface_id")

            binding = await InterfaceSessionBindingManager.instance().get_binding(
                connection_id=connection_id
            )
            if binding is None:
                err = "unauthenticated: interface session not registered (send interface_session_register first)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=request.public_key,
                            roles=[],
                        )
                    ),
                )
            if binding.identity_id != request.actor_id:
                err = "unauthenticated: actor_id does not match the registered interface identity"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=request.public_key,
                            roles=[],
                        )
                    ),
                )

            err = ""
            try:
                matches_actor = _actor_id_matches_public_key(
                    actor_id=request.actor_id,
                    public_key=request.public_key,
                )
            except Exception as exc:
                matches_actor = False
                err = str(exc)
            if not matches_actor:
                err = (
                    err or "forbidden: actor_id does not match public key (anti-claim)"
                )
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=request.public_key,
                            roles=[],
                        )
                    ),
                )

            try:
                session = IdentitySessionManager.instance().complete_login(
                    connection_id=connection_id,
                    public_key=request.public_key,
                    challenge=request.challenge,
                    signature=request.signature,
                    roles=[],
                )
            except Exception as exc:
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=str(exc),
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=IdentityLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=str(exc),
                            public_key=request.public_key,
                            roles=[],
                        )
                    ),
                )

            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=IdentityLoginResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        public_key=session.public_key,
                        roles=list(session.roles),
                    )
                ),
            )

        if request.operation == "token_login":
            if not isinstance(request, TokenLoginRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a TokenLoginRequest"
                )
            if current_hop.source_app_type != NetworkAppType.interface:
                raise RuntimeError(
                    "token_login is only supported from INTERFACE connections"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError("token_login missing source_interface_id")

            binding = await InterfaceSessionBindingManager.instance().get_binding(
                connection_id=connection_id
            )
            if binding is None:
                err = "unauthenticated: interface session not registered (send interface_session_register first)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=TokenLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=None,
                            roles=[],
                            token_id=None,
                            token_type=None,
                            scopes=[],
                            context_environment_id=None,
                            context_process_id=None,
                            context_thread_id=None,
                            expires_at=None,
                        )
                    ),
                )

            try:
                token_authority_manifest_path = (
                    _token_authority_manifest_path_for_token_validation()
                )
                manifest_path = _runtime_manifest_path_for_token_validation()
                validator = AptTokenValidator(
                    manifest_path=manifest_path if manifest_path else None,
                    token_authority_manifest_path=(
                        token_authority_manifest_path
                        if token_authority_manifest_path
                        else None
                    ),
                )
                claims = await validator.validate_apt_token(request.token)
            except AptTokenValidationError as exc:
                err = str(exc)
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=TokenLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=None,
                            roles=[],
                            token_id=None,
                            token_type=None,
                            scopes=[],
                            context_environment_id=None,
                            context_process_id=None,
                            context_thread_id=None,
                            expires_at=None,
                        )
                    ),
                )
            except Exception as exc:
                err = str(exc)
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=TokenLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=None,
                            roles=[],
                            token_id=None,
                            token_type=None,
                            scopes=[],
                            context_environment_id=None,
                            context_process_id=None,
                            context_thread_id=None,
                            expires_at=None,
                        )
                    ),
                )

            err = ""
            try:
                matches_actor = _actor_id_matches_public_key(
                    actor_id=claims.actor_id,
                    public_key=claims.public_key,
                )
            except Exception as exc:
                matches_actor = False
                err = str(exc)
            if not matches_actor:
                err = (
                    err
                    or "forbidden: actor_id does not match token public key (anti-claim)"
                )
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=TokenLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=None,
                            roles=[],
                            token_id=None,
                            token_type=None,
                            scopes=[],
                            context_environment_id=None,
                            context_process_id=None,
                            context_thread_id=None,
                            expires_at=None,
                        )
                    ),
                )

            # v1: token-based auth may upgrade an unauthenticated connection (actor_id=nil),
            # but must not let a caller switch identities mid-session.
            unauthenticated_id = UUID(int=0)
            if (
                binding.identity_id != unauthenticated_id
                and binding.identity_id != claims.actor_id
            ):
                err = "unauthenticated: token actor_id does not match the registered interface identity"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=TokenLoginResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            public_key=None,
                            roles=[],
                            token_id=None,
                            token_type=None,
                            scopes=[],
                            context_environment_id=None,
                            context_process_id=None,
                            context_thread_id=None,
                            expires_at=None,
                        )
                    ),
                )

            await InterfaceSessionBindingManager.instance().update_identity(
                connection_id=connection_id,
                identity_id=claims.actor_id,
            )

            token_binding = TokenBinding(
                token_id=claims.token_id,
                token_type="apt",
                scopes=list(claims.scopes),
                context_environment_id=claims.context_environment_id,
                context_process_id=claims.context_process_id,
                context_thread_id=claims.context_thread_id,
                expires_at=claims.expires_at,
            )

            session = IdentitySessionManager.instance().complete_token_login(
                connection_id=connection_id,
                public_key=claims.public_key,
                token_binding=token_binding,
                roles=[],
            )

            expires_at = (
                claims.expires_at.isoformat().replace("+00:00", "Z")
                if claims.expires_at is not None
                else None
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=TokenLoginResponse(
                        actor_id=claims.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        public_key=session.public_key,
                        roles=list(session.roles),
                        token_id=claims.token_id,
                        token_type="apt",
                        scopes=list(claims.scopes),
                        context_environment_id=claims.context_environment_id,
                        context_process_id=claims.context_process_id,
                        context_thread_id=claims.context_thread_id,
                        expires_at=expires_at,
                    )
                ),
            )

        if request.operation == "whoami":
            if not isinstance(request, WhoamiRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a WhoamiRequest"
                )
            if current_hop.source_app_type != NetworkAppType.interface:
                raise RuntimeError(
                    "whoami is only supported from INTERFACE connections"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError("whoami missing source_interface_id")

            binding = await InterfaceSessionBindingManager.instance().get_binding(
                connection_id=connection_id
            )
            if binding is None:
                err = "unauthenticated: interface session not registered (send interface_session_register first)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=WhoamiResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            authenticated=False,
                            public_key=None,
                            roles=[],
                            interface_session_id=None,
                            interface_id=None,
                            last_seen_at=None,
                        )
                    ),
                )
            if binding.identity_id != request.actor_id:
                err = "unauthenticated: actor_id does not match the registered interface identity"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=WhoamiResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            authenticated=False,
                            public_key=None,
                            roles=[],
                            interface_session_id=binding.interface_session_id,
                            interface_id=binding.interface_id,
                            last_seen_at=binding.last_seen_at.isoformat().replace(
                                "+00:00", "Z"
                            ),
                        )
                    ),
                )

            session = IdentitySessionManager.instance().get_session(
                connection_id=connection_id
            )
            if session is not None and not _actor_id_matches_public_key(
                actor_id=request.actor_id,
                public_key=session.public_key,
            ):
                session = None
            authenticated = session is not None
            public_key = session.public_key if session is not None else None
            roles = list(session.roles) if session is not None else []
            if authenticated and await actor_has_service_contract_access(
                actor_id=request.actor_id
            ):
                if SERVICE_CONTRACT_ACCESS_ROLE not in roles:
                    roles.append(SERVICE_CONTRACT_ACCESS_ROLE)
            last_seen_at = binding.last_seen_at.isoformat().replace("+00:00", "Z")

            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=WhoamiResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        authenticated=authenticated,
                        public_key=public_key,
                        roles=roles,
                        interface_session_id=binding.interface_session_id,
                        interface_id=binding.interface_id,
                        last_seen_at=last_seen_at,
                    )
                ),
            )

        if request.operation == "membership_status":
            # Forward-compatible: accept any request payload with `operation=membership_status`.
            # (This op has no additional fields beyond the base request.)
            if current_hop.source_app_type != NetworkAppType.interface:
                raise RuntimeError(
                    "membership_status is only supported from INTERFACE connections"
                )
            connection_id = current_hop.source_interface_id
            if connection_id is None:
                raise RuntimeError("membership_status missing source_interface_id")

            binding = await InterfaceSessionBindingManager.instance().get_binding(
                connection_id=connection_id
            )
            if binding is None:
                err = "unauthenticated: interface session not registered (send interface_session_register first)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=MembershipStatusResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            is_active=False,
                            is_bypassed=False,
                            plan_label=None,
                            current_period_end=None,
                        )
                    ),
                )
            if binding.identity_id != request.actor_id:
                err = "unauthenticated: actor_id does not match the registered interface identity"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=MembershipStatusResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            is_active=False,
                            is_bypassed=False,
                            plan_label=None,
                            current_period_end=None,
                        )
                    ),
                )

            session = IdentitySessionManager.instance().get_session(
                connection_id=connection_id
            )
            if session is None:
                err = "unauthenticated: identity session required (run identity_challenge + identity_login)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=MembershipStatusResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            is_active=False,
                            is_bypassed=False,
                            plan_label=None,
                            current_period_end=None,
                        )
                    ),
                )
            if not _actor_id_matches_public_key(
                actor_id=request.actor_id,
                public_key=session.public_key,
            ):
                err = "unauthenticated: actor_id does not match authenticated public key (anti-claim)"
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=err,
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=MembershipStatusResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=err,
                            is_active=False,
                            is_bypassed=False,
                            plan_label=None,
                            current_period_end=None,
                        )
                    ),
                )

            try:
                membership_status = await read_service_contract_access_status(
                    actor_id=request.actor_id
                )
            except Exception as exc:
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=str(exc),
                    ),
                    network_node_operation=NetworkNodeOperation(
                        response=MembershipStatusResponse(
                            actor_id=request.actor_id,
                            node_id=node_id,
                            status="failed",
                            error=str(exc),
                            is_active=False,
                            is_bypassed=False,
                            plan_label=None,
                            current_period_end=None,
                        )
                    ),
                )

            bypassed = is_actor_contract_access_bypassed(actor_id=request.actor_id)
            is_active = bool(bypassed or membership_status.is_active)

            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=MembershipStatusResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        is_active=is_active,
                        is_bypassed=bypassed,
                        plan_label=membership_status.plan_label,
                        current_period_end=membership_status.current_period_end,
                    )
                ),
            )

        if request.operation == "discover_environment_configs":
            if not isinstance(request, NetworkDiscoverEnvironmentConfigsRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a DiscoverEnvironmentConfigsRequest"
                )

            node_request = self._build_node_host_request_from_network_request(
                request=request,
                node_id=bridge_node_id,
            )
            if not isinstance(node_request, NodeHostDiscoverEnvironmentConfigsRequest):
                raise RuntimeError(
                    "NodeHost bridge request is not a DiscoverEnvironmentConfigsRequest"
                )
            result = (
                await self._require_node_host_control_plane_service().handle_request(
                    node_request
                )
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=self._build_network_request_status_for_node_host_result(
                        result
                    ),
                    error=result.request_error,
                ),
                network_node_operation=self._build_network_node_bridge_response(
                    result.response
                ),
            )

        if request.operation == "discover_service_api_dependency_routes":
            if not isinstance(request, NetworkDiscoverApiRoutesRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a "
                    "DiscoverServiceApiDependencyRoutesRequest"
                )

            node_request = self._build_node_host_request_from_network_request(
                request=request,
                node_id=bridge_node_id,
            )
            if not isinstance(node_request, NodeHostDiscoverApiRoutesRequest):
                raise RuntimeError(
                    "NodeHost bridge request is not a DiscoverApiRoutesRequest"
                )
            result = (
                await self._require_node_host_control_plane_service().handle_request(
                    node_request
                )
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=self._build_network_request_status_for_node_host_result(
                        result
                    ),
                    error=result.request_error,
                ),
                network_node_operation=self._build_network_node_bridge_response(
                    result.response
                ),
            )

        if request.operation == "discover_hosted_services":
            if not isinstance(request, DiscoverHostedServicesRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a DiscoverHostedServicesRequest"
                )

            hosted_services = await discover_node_hosted_service_advertisements(
                node_app=self._network_app
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=DiscoverHostedServicesResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        hosted_services=hosted_services,
                    )
                ),
            )

        if request.operation == "describe_hosted_service_runtimes":
            if not isinstance(request, DescribeHostedServiceRuntimesRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a DescribeHostedServiceRuntimesRequest"
                )

            hosted_service_runtimes = describe_node_hosted_service_runtime_statuses(
                node_app=self._network_app
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=DescribeHostedServiceRuntimesResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        hosted_service_runtimes=hosted_service_runtimes,
                    )
                ),
            )

        if request.operation == "get_boot_environment_descriptor":
            if not isinstance(request, NetworkGetBootEnvironmentDescriptorRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a GetBootEnvironmentDescriptorRequest"
                )

            node_request = self._build_node_host_request_from_network_request(
                request=request,
                node_id=bridge_node_id,
            )
            if not isinstance(
                node_request, NodeHostGetBootEnvironmentDescriptorRequest
            ):
                raise RuntimeError(
                    "NodeHost bridge request is not a GetBootEnvironmentDescriptorRequest"
                )
            try:
                result = await self._require_node_host_control_plane_service().handle_request(
                    node_request
                )
            except Exception as exc:
                node_response = NodeHostGetBootEnvironmentDescriptorResponse(
                    actor_id=node_request.actor_id,
                    node_id=node_request.node_id,
                    status="failed",
                    error=str(exc),
                    descriptor=None,
                )
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=str(exc),
                    ),
                    network_node_operation=self._build_network_node_bridge_response(
                        node_response
                    ),
                )

            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=self._build_network_request_status_for_node_host_result(
                        result
                    ),
                    error=result.request_error,
                ),
                network_node_operation=self._build_network_node_bridge_response(
                    result.response
                ),
            )

        if request.operation == "provision_environment":
            if not isinstance(request, NetworkProvisionEnvironmentRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a ProvisionEnvironmentRequest"
                )
            node_request = self._build_node_host_request_from_network_request(
                request=request,
                node_id=bridge_node_id,
            )
            if not isinstance(node_request, NodeHostProvisionEnvironmentRequest):
                raise RuntimeError(
                    "NodeHost bridge request is not a ProvisionEnvironmentRequest"
                )
            try:
                # Identity gate (M3): provisioning is only allowed from an authenticated identity session.
                if current_hop.source_app_type == NetworkAppType.interface:
                    connection_id = current_hop.source_interface_id
                    if connection_id is None:
                        raise RuntimeError(
                            "unauthenticated: missing source_interface_id for provision_environment"
                        )

                    binding = (
                        await InterfaceSessionBindingManager.instance().get_binding(
                            connection_id=connection_id
                        )
                    )
                    if binding is None:
                        raise RuntimeError(
                            "unauthenticated: interface session not registered (send interface_session_register first)"
                        )
                    if binding.identity_id != request.actor_id:
                        raise RuntimeError(
                            "unauthenticated: actor_id does not match the registered interface identity"
                        )
                    session = IdentitySessionManager.instance().get_session(
                        connection_id=connection_id
                    )
                    if session is None:
                        raise RuntimeError(
                            "unauthenticated: identity session required (run identity_challenge + identity_login)"
                        )
                    if not _actor_id_matches_public_key(
                        actor_id=request.actor_id,
                        public_key=session.public_key,
                    ):
                        raise RuntimeError(
                            "unauthenticated: actor_id does not match authenticated public key (anti-claim)"
                        )

                # Service contract access gate: provisioning requires active contract access (or bypass).
                if service_contract_access_gate_required():
                    if node_request.actor_id is None:
                        raise RuntimeError(
                            "unauthenticated: actor_id is required for contract-access-gated provisioning"
                        )
                    if not await actor_has_service_contract_access(
                        actor_id=node_request.actor_id,
                        fail_closed=True,
                    ):
                        raise RuntimeError(
                            "contract_access_required: active Service contract access required to provision environment"
                        )

                result = await self._require_node_host_control_plane_service().handle_request(
                    node_request
                )

                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=self._build_network_request_status_for_node_host_result(
                            result
                        ),
                        error=result.request_error,
                    ),
                    network_node_operation=self._build_network_node_bridge_response(
                        result.response
                    ),
                )
            except Exception as exc:
                node_response = NodeHostProvisionEnvironmentResponse(
                    actor_id=node_request.actor_id,
                    node_id=node_request.node_id,
                    status="failed",
                    error=str(exc),
                    environment_config_id=node_request.environment_config_id,
                    environment_title=node_request.environment_title,
                )
                return NetworkOperation(
                    id=network_op.id,
                    message_type=NetworkOperationMessageType.response,
                    type=network_op.type,
                    network_response=NetworkResponse(
                        network_request_id=network_request_id,
                        status=NetworkRequestStatus.failed,
                        error=str(exc),
                    ),
                    network_node_operation=self._build_network_node_bridge_response(
                        node_response
                    ),
                )

        if request.operation == "close_stream":
            if not isinstance(request, CloseStreamRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a CloseStreamRequest"
                )

            self._stream_origin_by_operation_id.pop(request.network_operation_id, None)
            close_stream = self._stream_close_registry().pop(
                request.network_operation_id, None
            )
            if close_stream is not None:
                await close_stream()
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=NetworkRequestStatus.succeeded,
                ),
                network_node_operation=NetworkNodeOperation(
                    response=CloseStreamResponse(
                        actor_id=request.actor_id,
                        node_id=node_id,
                        status="succeeded",
                        error=None,
                        network_operation_id=request.network_operation_id,
                    )
                ),
            )

        if request.operation == "get_environment_status":
            if not isinstance(request, NetworkGetEnvironmentStatusRequest):
                raise RuntimeError(
                    "NetworkNodeOperation.request is not a GetEnvironmentStatusRequest"
                )
            node_request = self._build_node_host_request_from_network_request(
                request=request,
                node_id=bridge_node_id,
            )
            if not isinstance(node_request, NodeHostGetEnvironmentStatusRequest):
                raise RuntimeError(
                    "NodeHost bridge request is not a GetEnvironmentStatusRequest"
                )
            result = (
                await self._require_node_host_control_plane_service().handle_request(
                    node_request
                )
            )
            return NetworkOperation(
                id=network_op.id,
                message_type=NetworkOperationMessageType.response,
                type=network_op.type,
                network_response=NetworkResponse(
                    network_request_id=network_request_id,
                    status=self._build_network_request_status_for_node_host_result(
                        result
                    ),
                    error=result.request_error,
                ),
                network_node_operation=self._build_network_node_bridge_response(
                    result.response
                ),
            )

        raise RuntimeError(f"Unsupported network node operation: {request.operation}")

    async def _route_to_environment_service(
        self,
        network_op: NetworkOperation,
        *,
        timeout_s: float | None = None,
    ) -> NetworkOperation | None:
        """Route a NetworkOperation to an environment service (request/notification aware)."""
        current_hop = self._get_current_header(network_op)
        await self._persist_hop_for_audit(network_op, current_hop)

        environment_id = self._resolve_environment_id(network_op)

        from aware_network.network.node.manager import network_node_manager

        forward_hop = NetworkOperationHop(
            source_app_type=NetworkAppType.network_node,
            source_node_id=network_node_manager.hosted_node_id,
            target_app_type=NetworkAppType.environment,
            target_environment_id=environment_id,
        )

        forward_op = NetworkOperation(
            id=network_op.id,
            message_type=network_op.message_type,
            type=network_op.type,
            network_request=network_op.network_request,
            api_operation=network_op.api_operation,
            network_operation_hop_list=[forward_hop],
        )

        duplex = self._network_app.get_duplex_client(NetworkAppType.environment)
        record = environment_registry.get(environment_id)
        await duplex.ensure_connection(
            connection_id=environment_id,
            external_url=record.environment_endpoint if record else None,
        )
        if network_op.message_type == NetworkOperationMessageType.notification:
            await duplex.send_notification(
                connection_id=environment_id,
                data_serialized=forward_op.model_dump_json(),
            )
            return None

        if network_op.message_type != NetworkOperationMessageType.request:
            raise RuntimeError(
                f"Unsupported message_type for environment routing: {network_op.message_type}"
            )

        resolved_timeout_s = timeout_s
        if resolved_timeout_s is None:
            request_endpoint_ref = (
                network_op.api_operation.request.endpoint_ref
                if (
                    network_op.api_operation is not None
                    and isinstance(
                        network_op.api_operation.request, InvokeApiEndpointRequest
                    )
                )
                else None
            )
            if request_endpoint_ref == "environment.function_call.invoke_function":
                resolved_timeout_s = float(
                    os.environ.get("AWARE_NODE_ENVIRONMENT_INVOKE_TIMEOUT_S", "12.0")
                )
            else:
                # Non-invoke operations (e.g. experience upsert/provision) can legitimately take
                # >5s (the duplex default). Fail-closed with an explicit, configurable timeout.
                resolved_timeout_s = self._environment_service_request_timeout_s()

        response = await duplex.send_request(
            connection_id=environment_id,
            data_serialized=forward_op.model_dump_json(),
            timeout_s=resolved_timeout_s,
        )
        if response is None:
            raise RuntimeError("No response received from environment service")
        if isinstance(response, str):
            return NetworkOperation.model_validate_json(response)
        if isinstance(response, dict):
            return NetworkOperation.model_validate(response)
        raise TypeError(
            f"Unexpected environment service response type: {type(response)}"
        )

    @staticmethod
    def _environment_service_request_timeout_s() -> float:
        raw_timeout = (
            os.environ.get("AWARE_NODE_ENVIRONMENT_REQUEST_TIMEOUT_S")
            or os.environ.get("AWARE_NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S")
            or "60.0"
        )
        return float(raw_timeout)

    @staticmethod
    def _resolve_environment_id(network_op: NetworkOperation) -> UUID:
        if len(network_op.network_operation_hop_list) == 1:
            target_environment_id = network_op.network_operation_hop_list[
                0
            ].target_environment_id
            environment_id = NetworkNodeRouter._resolve_environment_transport_target_id(
                target_environment_id=target_environment_id,
            )
            if environment_id is not None:
                return environment_id
        raise RuntimeError(
            "Environment routing requires a registered target Environment id "
            "or a single registered local Environment"
        )

    @staticmethod
    def _resolve_environment_api_transport_target_id(
        *,
        hop_target_environment_id: UUID | None,
        payload_environment_id: UUID | None,
    ) -> UUID | None:
        environment_id = NetworkNodeRouter._resolve_environment_transport_target_id(
            target_environment_id=hop_target_environment_id,
            fallback_environment_id=payload_environment_id,
        )
        if environment_id is not None:
            return environment_id
        return None

    @staticmethod
    def _resolve_environment_transport_target_id(
        *,
        target_environment_id: UUID | None,
        fallback_environment_id: UUID | None = None,
    ) -> UUID | None:
        if (
            target_environment_id is not None
            and environment_registry.get(target_environment_id) is not None
        ):
            return target_environment_id
        if (
            fallback_environment_id is not None
            and environment_registry.get(fallback_environment_id) is not None
        ):
            return fallback_environment_id

        candidates = [
            record
            for record in environment_registry.list_records()
            if record.environment_endpoint and record.status == "ready"
        ]
        if len(candidates) == 1:
            return candidates[0].environment_id
        return None

    async def _forward_to_target_node(self, network_op: NetworkOperation) -> bool:
        """
        Forward NetworkOperation to target node using hop-based routing

        Args:
            network_op: The NetworkOperation to forward

        Returns:
            True if successful, False otherwise
        """
        try:
            current_hop = self._get_current_header(network_op)

            # Persist current hop for audit trail
            await self._persist_hop_for_audit(network_op, current_hop)

            target_node_id = current_hop.target_node_id
            if not target_node_id:
                raise RuntimeError("NetworkOperationHop missing target_node_id")

            duplex = self._get_duplex_for_connection(target_node_id)

            if not duplex:
                raise RuntimeError(f"No connection to target node {target_node_id}")

            # Create hop to target node (source becomes this node, target stays the same)
            next_hop = self._create_next_hop(
                current_hop=current_hop,
                target_app_type=current_hop.target_app_type,
                target_node_id=current_hop.target_node_id,
                target_interface_id=current_hop.target_interface_id,
                strip_source_interface=True,  # Strip interface info for privacy
            )

            # Update hop list with new header
            network_op.network_operation_hop_list = [next_hop]

            # Send NetworkOperation to target node
            response = await duplex.send_request(
                connection_id=target_node_id,
                data_serialized=network_op.model_dump_json(),
            )

            return response is not None

        except Exception as e:
            logger.error(f"Error forwarding NetworkOperation to target node: {e}")
            return False

    async def _get_environment_service_connection(
        self, environment_id: UUID
    ) -> UUID | None:
        """
        Get connection ID for environment service hosting the specified environment

        Args:
            environment_id: The environment ID to find service for

        Returns:
            Connection ID for environment service or None
        """
        # TODO: Implement environment service discovery
        # This would typically involve:
        # 1. Looking up which docker container/service hosts this environment
        # 2. Getting the connection ID for that service
        # 3. Returning the connection ID

        # For now, return a placeholder
        # In real implementation, this would query a service registry
        return environment_id  # Placeholder - assuming connection_id == environment_id

    async def _send_to_environment_service(
        self, connection_id: UUID, network_op: NetworkOperation
    ) -> bool:
        """
        Send FULL NetworkOperation to environment service

        Environment service now receives the full NetworkOperation with network_request
        so it can access identity for ACL without needing shared DB

        Args:
            connection_id: The connection ID for the environment service
            network_op: The FULL NetworkOperation to send

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get duplex for environment service
            duplex = self._get_duplex_for_connection(connection_id)

            if not duplex:
                raise RuntimeError(
                    f"No connection to environment service {connection_id}"
                )

            # Send FULL NetworkOperation to service
            response = await duplex.send_request(
                connection_id=connection_id,
                data_serialized=network_op.model_dump_json(),
            )

            return response is not None

        except Exception as e:
            logger.error(f"Error sending to environment service: {e}")
            return False

    async def send_notifications(
        self,
        identity_ids: Iterable[UUID],
        data_serialized: str,
        notify_local_interfaces: bool = True,
        notify_remote_nodes: bool = False,
        exclude_identity_ids: Iterable[UUID] | None = None,
    ) -> bool:
        """Send notifications to one or more identities with configurable targets

        Args:
            identity_ids: The identities to send the notification to
            data_serialized: The data to send in the notification
            notify_local_interfaces:
                Whether to notify local interfaces, by default True so all nodes
                can notify their interfaces
            notify_remote_nodes:
                Whether to notify remote nodes, by default False as ONLY HOST is
                allowed to send notifications to remote nodes
            exclude_identity_ids: The identities to exclude from the notification
        Returns:
            True if the notification was sent successfully, False otherwise
        """
        # Process exclude_identity_ids set for more efficient lookups
        exclude_set = set(exclude_identity_ids) if exclude_identity_ids else set()

        # Filter out excluded identities
        filtered_identities = [id for id in identity_ids if id not in exclude_set]
        if not filtered_identities:
            return True

        notification_tasks = []

        # Prepare coroutines to gather identity information concurrently
        identity_info_tasks = []
        for identity_id in filtered_identities:
            identity_info_tasks.append(
                (identity_id, self.get_host_node_id(identity_id))
            )

        # Get local identity ids and remote node ids
        local_identity_ids: set[UUID] = set()
        remote_node_ids: set[UUID] = set()

        # Process each identity and classify as local or remote
        for identity_id, host_node_id_future in identity_info_tasks:
            host_node_id = await host_node_id_future
            if host_node_id is None:
                logger.warning(
                    "No host node resolved for identity %s; skipping notification routing",
                    identity_id,
                )
                continue
            if self.is_local_host(host_node_id):
                local_identity_ids.add(identity_id)
            else:
                remote_node_ids.add(host_node_id)

        # Prepare remote node notification tasks
        if notify_remote_nodes and remote_node_ids:
            for node_id in remote_node_ids:
                duplex = self._get_duplex_for_connection(node_id)
                if duplex is None:
                    logger.error(f"No duplex found for connection {node_id}")
                    continue
                # Notify nodes
                notification_tasks.append(
                    duplex.send_notification(
                        connection_id=node_id,
                        data_serialized=data_serialized,
                    )
                )

        # Prepare local interface notification tasks
        if notify_local_interfaces and local_identity_ids:
            for identity_id in local_identity_ids:
                # Get interface IDs
                interface_ids = set(await self.get_interface_ids(identity_id))

                # Add notification tasks for each interface
                for interface_id in interface_ids:
                    duplex = self._get_duplex_for_connection(interface_id)
                    if duplex is None:
                        logger.error(f"No duplex found for connection {interface_id}")
                        continue
                    notification_tasks.append(
                        duplex.send_notification(
                            connection_id=interface_id,
                            data_serialized=data_serialized,
                        )
                    )

        # If no tasks to run, return True (as no failures occurred)
        if not notification_tasks:
            return True

        # Execute all notification tasks concurrently
        results = await asyncio.gather(*notification_tasks, return_exceptions=True)

        # Check if all notifications were successful
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error sending notification: {result}")
                return False
            if not result:
                return False

        return True

    async def send_request(
        self,
        identity_id: UUID,
        data_serialized: str,
    ) -> WsMessageFrame:
        """Send a request"""
        # Get node id and duplex
        node_id = await self.get_node_id(identity_id)
        if node_id is None:
            raise RuntimeError(f"identity {identity_id} has no host-node")
        duplex = self._get_duplex_for_connection(node_id)
        if duplex is None:
            raise RuntimeError(f"no duplex for node {node_id}")
        return await duplex.send_request(node_id, data_serialized)
