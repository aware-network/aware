from __future__ import annotations

# Standard
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)

# Types
from aware_types import JsonObject


class NetworkNodeOperationContext(BaseModel):
    """Wire DTOs for Network Node operations (control-plane; graph/ORM agnostic)."""

    # Attributes
    actor_id: UUID | None = Field(default=None)
    node_id: UUID | None = Field(default=None)


class NetworkNodeOperation(BaseModel):
    """NetworkNodeOperation is either a request or a response."""

    # Attributes
    request: SerializeAsAny[NetworkNodeOperationRequest] | None = Field(default=None)
    response: SerializeAsAny[NetworkNodeOperationResponse] | None = Field(default=None)

    @field_validator("request", mode="before")
    @classmethod
    def _parse_request(cls, v):
        if v is None:
            return None
        return NetworkNodeOperationRequest.parse(v)

    @field_validator("response", mode="before")
    @classmethod
    def _parse_response(cls, v):
        if v is None:
            return None
        return NetworkNodeOperationResponse.parse(v)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.request,
                    self.response,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of request, response must be set")
        return self


class NetworkNodeOperationRequest(NetworkNodeOperationContext):
    """Request union base (operation + context)."""

    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "identity_challenge": "aware_network_service_dto.comms.identity.identity_session_operation.IdentityChallengeRequest",
        "identity_login": "aware_network_service_dto.comms.identity.identity_session_operation.IdentityLoginRequest",
        "token_login": "aware_network_service_dto.comms.identity.identity_session_operation.TokenLoginRequest",
        "whoami": "aware_network_service_dto.comms.identity.identity_session_operation.WhoamiRequest",
        "membership_status": "aware_network_service_dto.comms.economy.membership_operation.MembershipStatusRequest",
        "membership_checkout_session_create": "aware_network_service_dto.comms.economy.membership_operation.MembershipCheckoutSessionCreateRequest",
        "membership_purchase_prepare": "aware_network_service_dto.comms.economy.membership_operation.MembershipPurchasePrepareRequest",
        "membership_purchase_claim": "aware_network_service_dto.comms.economy.membership_operation.MembershipPurchaseClaimRequest",
        "provision_environment": "aware_network_service_dto.comms.models.network_node.ProvisionEnvironmentRequest",
        "get_boot_environment_descriptor": "aware_network_service_dto.comms.models.network_node.GetBootEnvironmentDescriptorRequest",
        "discover_environment_configs": "aware_network_service_dto.comms.models.network_node.DiscoverEnvironmentConfigsRequest",
        "discover_service_api_dependency_routes": "aware_network_service_dto.comms.models.network_node.DiscoverServiceApiDependencyRoutesRequest",
        "discover_hosted_services": "aware_network_service_dto.comms.models.network_node.DiscoverHostedServicesRequest",
        "describe_hosted_service_runtimes": "aware_network_service_dto.comms.models.network_node.DescribeHostedServiceRuntimesRequest",
        "get_environment_status": "aware_network_service_dto.comms.models.network_node.GetEnvironmentStatusRequest",
        "close_stream": "aware_network_service_dto.comms.models.network_node.CloseStreamRequest",
        "interface_session_register": "aware_network_service_dto.comms.models.network_node.InterfaceSessionRegisterRequest",
        "interface_session_heartbeat": "aware_network_service_dto.comms.models.network_node.InterfaceSessionHeartbeatRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownNetworkNodeOperationRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownNetworkNodeOperationRequest(NetworkNodeOperationRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class NetworkNodeOperationResponse(NetworkNodeOperationContext):
    """Response union base (operation + context)."""

    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "identity_challenge": "aware_network_service_dto.comms.identity.identity_session_operation.IdentityChallengeResponse",
        "identity_login": "aware_network_service_dto.comms.identity.identity_session_operation.IdentityLoginResponse",
        "token_login": "aware_network_service_dto.comms.identity.identity_session_operation.TokenLoginResponse",
        "whoami": "aware_network_service_dto.comms.identity.identity_session_operation.WhoamiResponse",
        "membership_status": "aware_network_service_dto.comms.economy.membership_operation.MembershipStatusResponse",
        "membership_checkout_session_create": "aware_network_service_dto.comms.economy.membership_operation.MembershipCheckoutSessionCreateResponse",
        "membership_purchase_prepare": "aware_network_service_dto.comms.economy.membership_operation.MembershipPurchasePrepareResponse",
        "membership_purchase_claim": "aware_network_service_dto.comms.economy.membership_operation.MembershipPurchaseClaimResponse",
        "provision_environment": "aware_network_service_dto.comms.models.network_node.ProvisionEnvironmentResponse",
        "get_boot_environment_descriptor": "aware_network_service_dto.comms.models.network_node.GetBootEnvironmentDescriptorResponse",
        "discover_environment_configs": "aware_network_service_dto.comms.models.network_node.DiscoverEnvironmentConfigsResponse",
        "discover_service_api_dependency_routes": "aware_network_service_dto.comms.models.network_node.DiscoverServiceApiDependencyRoutesResponse",
        "discover_hosted_services": "aware_network_service_dto.comms.models.network_node.DiscoverHostedServicesResponse",
        "describe_hosted_service_runtimes": "aware_network_service_dto.comms.models.network_node.DescribeHostedServiceRuntimesResponse",
        "get_environment_status": "aware_network_service_dto.comms.models.network_node.GetEnvironmentStatusResponse",
        "close_stream": "aware_network_service_dto.comms.models.network_node.CloseStreamResponse",
        "interface_session_register": "aware_network_service_dto.comms.models.network_node.InterfaceSessionRegisterResponse",
        "interface_session_heartbeat": "aware_network_service_dto.comms.models.network_node.InterfaceSessionHeartbeatResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownNetworkNodeOperationResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownNetworkNodeOperationResponse(NetworkNodeOperationResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ProvisionEnvironmentRequest(NetworkNodeOperationRequest):
    # Discriminator Tag
    operation: Literal["provision_environment"] = "provision_environment"

    # Attributes
    environment_config_id: UUID
    environment_title: str | None = Field(default=None)
    environment_description: str | None = Field(default=None)
    environment_port: int | None = Field(default=None)
    database_url: str | None = Field(default=None)
    persistence_backend: str | None = Field(default=None)
    eager_ready: bool = Field(default=True)


class NodeEnvironmentProvisioningReceipt(BaseModel):
    """
    Product receipt for a NetworkNode-provisioned Environment.
    The nested `readiness_receipt` is the public Environment API receipt payload.
    Network keeps it as JSON so Network control-plane DTOs stay decoupled from
    Environment Environment DTO packages while exposing full provenance evidence.
    """

    # Attributes
    status: str
    error: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    node_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_title: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    environment_endpoint: str | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    runtime_artifact_refs_json: str | None = Field(default=None)
    service_api_provider_refs_json: str | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    outer_wrapper_kind: str | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    workspace_toml_path: str | None = Field(default=None)
    workspace_id: str | None = Field(default=None)
    workspace_package_id: str | None = Field(default=None)
    workspace_build_invocation_id: str | None = Field(default=None)
    workspace_build_receipt_path: str | None = Field(default=None)
    workspace_build_latest_path: str | None = Field(default=None)
    workspace_target_latest_path: str | None = Field(default=None)
    workspace_target_ref: str | None = Field(default=None)
    readiness_receipt: JsonObject | None = Field(default=None)
    network_node_environment_receipt: JsonObject | None = Field(default=None)


class ProvisionEnvironmentResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["provision_environment"] = "provision_environment"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_title: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    environment_endpoint: str | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    provisioning_receipt: NodeEnvironmentProvisioningReceipt | None = Field(default=None)


class GetEnvironmentStatusRequest(NetworkNodeOperationRequest):
    # Discriminator Tag
    operation: Literal["get_environment_status"] = "get_environment_status"

    # Attributes
    environment_id: UUID


class GetEnvironmentStatusResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["get_environment_status"] = "get_environment_status"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    environment_id: UUID
    environment_config_id: UUID | None = Field(default=None)
    environment_config_title: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    environment_endpoint: str | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    provisioning_receipt: NodeEnvironmentProvisioningReceipt | None = Field(default=None)


class CloseStreamRequest(NetworkNodeOperationRequest):
    """
    Close a previously-registered STREAM correlation on the node (control-plane).
    This is transport-only and must not embed service payload semantics.
    It allows callers (ENVIRONMENT or INTERFACE) to stop forwarding STREAM frames
    for a given `NetworkOperation.id` correlation key.
    """

    # Discriminator Tag
    operation: Literal["close_stream"] = "close_stream"

    # Attributes
    network_operation_id: UUID


class CloseStreamResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["close_stream"] = "close_stream"

    # Attributes
    status: str = Field(default="succeeded")
    error: str | None = Field(default=None)
    network_operation_id: UUID


class InterfaceSessionRegisterRequest(NetworkNodeOperationRequest):
    """
    Canonical interface session registration (DTO-only).
    This replaces the legacy `channel="interface_control"` control frames.
    The node uses this to bind the active websocket connection (hop.source_interface_id)
    to an identity for routing + gating.
    """

    # Discriminator Tag
    operation: Literal["interface_session_register"] = "interface_session_register"

    # Attributes
    interface_id: UUID
    interface_session_id: UUID
    session_label: str | None = Field(default=None)
    capabilities: list[str] = Field(default_factory=list)
    protocol_version: int = Field(default=1)


class InterfaceSessionRegisterResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["interface_session_register"] = "interface_session_register"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    interface_id: UUID
    interface_session_id: UUID
    interface_identity_network_node_id: UUID | None = Field(default=None)
    interface_session_network_binding_id: UUID | None = Field(default=None)
    last_seen_at: str | None = Field(default=None)
    protocol_version: int


class InterfaceSessionHeartbeatRequest(NetworkNodeOperationRequest):
    """
    Interface session heartbeat (DTO-only).
    Optional v0 keepalive so the node can expire stale sessions deterministically
    without relying on transport TCP timeouts.
    """

    # Discriminator Tag
    operation: Literal["interface_session_heartbeat"] = "interface_session_heartbeat"

    # Attributes
    interface_session_id: UUID
    timestamp: str | None = Field(default=None)


class InterfaceSessionHeartbeatResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["interface_session_heartbeat"] = "interface_session_heartbeat"

    # Attributes
    status: str = Field(default="succeeded")
    error: str | None = Field(default=None)
    interface_session_id: UUID
    last_seen_at: str | None = Field(default=None)


class EnvironmentConfigDescriptor(BaseModel):
    """Describe an environment config (template/map) available for provisioning."""

    # Attributes
    environment_config_id: UUID
    title: str | None = Field(default=None)
    canonical_language: str | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    outer_wrapper_kind: str | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    workspace_target_ref: str | None = Field(default=None)


class BootEnvironmentDescriptor(BaseModel):
    """
    Descriptor for the node-managed BOOT environment (v0).
    IMPORTANT:
    - The "kernel" is an EnvironmentConfig (module mount set).
    - The "boot environment" is an Environment instance derived from that config.
    - This DTO exists to avoid client-side heuristics for selecting the kernel config.
    """

    # Attributes
    kernel_environment_config_id: UUID
    boot_environment_id: UUID
    kernel_environment_config_title: str | None = Field(default=None)
    boot_environment_title: str | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)


class GetBootEnvironmentDescriptorRequest(NetworkNodeOperationRequest):
    """Return the node's BOOT environment descriptor (kernel config + boot environment instance)."""

    # Discriminator Tag
    operation: Literal["get_boot_environment_descriptor"] = "get_boot_environment_descriptor"


class GetBootEnvironmentDescriptorResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["get_boot_environment_descriptor"] = "get_boot_environment_descriptor"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    descriptor: BootEnvironmentDescriptor | None = Field(default=None)


class DiscoverEnvironmentConfigsRequest(NetworkNodeOperationRequest):
    # Discriminator Tag
    operation: Literal["discover_environment_configs"] = "discover_environment_configs"


class DiscoverEnvironmentConfigsResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["discover_environment_configs"] = "discover_environment_configs"

    # Attributes
    configs: list[EnvironmentConfigDescriptor] = Field(default_factory=list)


class ServiceApiDependencyRouteDescriptor(BaseModel):
    """
    Node-owned route descriptor for one bound service-to-service API dependency.
    This is the network transport DTO for NodeHost route-registry truth. Node
    derives it from selected ServicePackage required/provided ApiPackage bridges
    plus live ServiceHost handshakes; remote/subprocess consumers must not
    reopen package manifests or infer provider routes locally.
    """

    # Attributes
    consumer_service_package_id: UUID
    consumer_service_package_name: str
    provider_service_package_id: UUID
    provider_service_package_name: str
    api_package_id: UUID
    api_package_name: str | None = Field(default=None)
    route_kind: str
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    socket_path: str | None = Field(default=None)
    consumer_node_id: UUID | None = Field(default=None)
    provider_node_id: UUID | None = Field(default=None)
    provider_node_base_url: str | None = Field(default=None)
    route_connection_id: UUID | None = Field(default=None)
    request_timeout_s: float
    service_names: list[str] = Field(default_factory=list)
    endpoint_refs_by_service: JsonObject = Field(default_factory=JsonObject)
    stream_endpoint_refs_by_service: JsonObject = Field(default_factory=JsonObject)


class DiscoverServiceApiDependencyRoutesRequest(NetworkNodeOperationRequest):
    """Discover live service API dependency routes bound by the target Node."""

    # Discriminator Tag
    operation: Literal["discover_service_api_dependency_routes"] = "discover_service_api_dependency_routes"

    # Attributes
    consumer_service_package_id: UUID | None = Field(default=None)
    api_package_id: UUID | None = Field(default=None)


class DiscoverServiceApiDependencyRoutesResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["discover_service_api_dependency_routes"] = "discover_service_api_dependency_routes"

    # Attributes
    routes: list[ServiceApiDependencyRouteDescriptor] = Field(default_factory=list)


class HostedServiceAdvertisement(BaseModel):
    """
    Node-owned advertisement for one supervised hosted generic Service.
    This is control-plane discovery truth derived by the hosting Node from its
    private Service-host handshake/runtime registry. Remote Nodes consume this
    DTO; they do not consume the raw Service-host handshake contract directly.
    """

    # Attributes
    service_package_id: UUID | None = Field(default=None)
    service_id: UUID | None = Field(default=None)
    service_name: str
    service_package_names: list[str] = Field(default_factory=list)
    endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    supports_stream_events: bool = Field(default=False)


class HostedServiceRuntimeServiceStatus(BaseModel):
    """
    Typed per-service view of one supervised hosted-Service runtime.
    This is runtime-status truth, not routing-only advertisement.
    """

    # Attributes
    service_name: str
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)


class HostedServiceRuntimeStatus(BaseModel):
    """
    Node-owned runtime status for one supervised hosted-Service host/runtime.
    IMPORTANT:
    - This remains control-plane truth owned by the supervising Node.
    - It is derived from private Service-host handshake + process supervision.
    - It is intentionally separate from `HostedServiceAdvertisement`, which
    remains routing/discovery-only.
    """

    # Attributes
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    readiness_status: str = Field(default="unknown")
    is_ready: bool = Field(default=False)
    is_alive: bool = Field(default=False)
    supports_stream_events: bool = Field(default=False)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    services: list[HostedServiceRuntimeServiceStatus] = Field(default_factory=list)


class DiscoverHostedServicesRequest(NetworkNodeOperationRequest):
    """Discover generic hosted Services currently supervised by this Node."""

    # Discriminator Tag
    operation: Literal["discover_hosted_services"] = "discover_hosted_services"


class DiscoverHostedServicesResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["discover_hosted_services"] = "discover_hosted_services"

    # Attributes
    hosted_services: list[HostedServiceAdvertisement] = Field(default_factory=list)


class DescribeHostedServiceRuntimesRequest(NetworkNodeOperationRequest):
    """Describe supervised hosted-Service runtime health/status currently visible to this Node."""

    # Discriminator Tag
    operation: Literal["describe_hosted_service_runtimes"] = "describe_hosted_service_runtimes"


class DescribeHostedServiceRuntimesResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_hosted_service_runtimes"] = "describe_hosted_service_runtimes"

    # Attributes
    hosted_service_runtimes: list[HostedServiceRuntimeStatus] = Field(default_factory=list)
