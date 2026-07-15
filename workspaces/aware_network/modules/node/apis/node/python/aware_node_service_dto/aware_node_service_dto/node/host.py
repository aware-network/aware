from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

# Types
from aware_types import JsonObject


class NodeHostOperationContext(BaseModel):
    """
    Transport-neutral DTOs for the live Node-owned host/provisioning control plane.
    SSOT: `node-service-dto` generated from `apis/node/dto`.
    IMPORTANT:
    - This contract is a peer rail to `NodeDeployOperation` and
    `NetworkNodeOperation`.
    - It owns live host/provisioning work after the node runtime is already up.
    - The first extraction preserves the current environment-bridge request
    family names while moving ownership from Network to Node.
    """

    # Attributes
    actor_id: UUID | None = Field(default=None)
    node_id: UUID | None = Field(default=None)


class NodeHostOperation(BaseModel):
    # Attributes
    request: NodeHostOperationRequest | None = Field(default=None)
    response: NodeHostOperationResponse | None = Field(default=None)

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


class NodeHostOperationRequest(NodeHostOperationContext):
    # Attributes
    operation: str


class NodeHostOperationResponse(NodeHostOperationContext):
    # Attributes
    operation: str
    status: str = Field(default="pending")
    error: str | None = Field(default=None)


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


class NodeEnvironmentProvisioningReceipt(BaseModel):
    """
    Product receipt for a Node-provisioned Environment.
    The nested `readiness_receipt` is the public Environment API receipt payload.
    Node keeps it as JSON so NodeHost DTOs do not import Environment Environment
    DTOs while still exposing the full provenance evidence to operators.
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


class NodeServiceApiDependencyRouteDescriptor(BaseModel):
    """
    Live descriptor for a service-to-service API dependency route bound by Node.
    This is transport-neutral NodeHost API DTO truth. Node derives these routes
    from selected ServicePackage required/provided ApiPackage bridges plus live
    ServiceHost handshakes; consumers query them instead of reopening package
    manifests or depending on launch-time env injection.
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


class HostedServiceRuntimeServiceStatus(BaseModel):
    """
    Typed per-service view of one supervised hosted-Service runtime.
    This is Node-owned runtime-status truth, not routing-only advertisement.
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
    - It is intentionally separate from Network hosted-service advertisements,
    which remain routing/discovery truth.
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


class HostedRuntimeRecoveryCapability(BaseModel):
    """
    Generic Node-owned recovery capability for any supervised hosted runtime.
    Node owns whether an operation is available and why. Provider-specific
    meaning remains outside this DTO; consumers map these keys into their own
    API/UX contracts.
    """

    # Attributes
    key: str
    enabled: bool = Field(default=False)
    reason: str | None = Field(default=None)
    action_key: str | None = Field(default=None)


class HostedRuntimeLifecycleStatus(BaseModel):
    """
    Generic Node-owned lifecycle view for any supervised hosted runtime.
    IMPORTANT:
    - `runtime_kind` is an open string, not an enum. Current values such as
    `service`, `interface`, `environment`, or `ontology` are provider keys,
    not Node-owned type variants.
    - Node reports lifecycle/process/readiness/recovery truth only.
    - Provider-specific status must live behind provider APIs and may be
    exposed here only as opaque JSON metadata/refs.
    """

    # Attributes
    runtime_key: str
    runtime_kind: str
    status: str = Field(default="unknown")
    is_ready: bool = Field(default=False)
    is_alive: bool = Field(default=False)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    pid: int | None = Field(default=None)
    returncode: int | None = Field(default=None)
    endpoint: str | None = Field(default=None)
    socket_path: str | None = Field(default=None)
    manifest_ref: str | None = Field(default=None)
    provider_ref: str | None = Field(default=None)
    provider_package: str | None = Field(default=None)
    provider_api_ref: str | None = Field(default=None)
    provider_metadata: JsonObject | None = Field(default=None)
    recovery_capabilities: list[HostedRuntimeRecoveryCapability] = Field(default_factory=list)


class NodeRunManifestHostedServiceSpec(BaseModel):
    """
    Node-owned runtime input consumed by `aware_node_service.app`.
    This is product run truth. Producers may be local source manifest tooling or
    artifact-backed Workspace/Hub flows, but Node consumes this contract instead
    of inferring runtime policy from source roots or legacy deploy env names.
    """

    # Attributes
    name: str | None = Field(default=None)
    bootstrap_config_path: str
    launch_command: list[str] = Field(default_factory=list)
    ready_timeout_s: float | None = Field(default=None)
    request_timeout_s: float | None = Field(default=None)
    socket_root: str | None = Field(default=None)


class NodeRunManifestHostedInterfaceSpec(BaseModel):
    # Attributes
    name: str | None = Field(default=None)
    bootstrap_config_path: str
    launch_command: list[str] = Field(default_factory=list)
    ready_timeout_s: float | None = Field(default=None)


class NodeRunManifestRouteInputs(BaseModel):
    # Attributes
    service_api_dependency_package_refs_json: str | None = Field(default=None)
    service_api_dependency_package_refs_path: str | None = Field(default=None)
    remote_service_api_provider_refs_json: str | None = Field(default=None)
    remote_service_api_provider_refs_path: str | None = Field(default=None)


class NodeRunManifestAuthInputs(BaseModel):
    # Attributes
    token_authority_manifest_path: str | None = Field(default=None)
    token_seed_receipt_path: str | None = Field(default=None)


class NodeRunManifestReadinessPolicy(BaseModel):
    # Attributes
    node_http_ready_timeout_s: float = Field(default=600.0)
    environment_service_ready_timeout_s: float = Field(default=600.0)
    environment_ready_timeout_s: float = Field(default=600.0)
    hosted_service_ready_timeout_s: float = Field(default=180.0)
    hosted_interface_ready_timeout_s: float = Field(default=180.0)
    hosted_service_request_timeout_s: float = Field(default=5.0)


class NodeRunManifestProvenance(BaseModel):
    # Attributes
    source_kind: str
    workspace_root: str | None = Field(default=None)
    workspace_revision_id: str | None = Field(default=None)
    workspace_source_revision_id: str | None = Field(default=None)
    workspace_source_revision_kind: str | None = Field(default=None)
    workspace_deployment_revision_id: str | None = Field(default=None)
    environment_runtime_revision_id: str | None = Field(default=None)
    materialized_workspace_root: str | None = Field(default=None)
    workspace_revision_manifest_path: str | None = Field(default=None)
    deployment_payload_path: str | None = Field(default=None)
    artifact_refs_json: str | None = Field(default=None)


class NodeRunManifest(BaseModel):
    # Attributes
    version: str = Field(default="aware.node.run_manifest.v1")
    node_package: str
    node_id: UUID | None = Field(default=None)
    display_name: str | None = Field(default=None)
    host: str
    port: int
    node_base_url: str | None = Field(default=None)
    node_websocket_path: str = Field(default="/interface/network_node")
    run_dir: str
    aware_root: str | None = Field(default=None)
    node_host_root: str | None = Field(default=None)
    env_file_path: str | None = Field(default=None)
    command_file_path: str | None = Field(default=None)
    log_path: str | None = Field(default=None)
    pid_file_path: str | None = Field(default=None)
    status_file_path: str | None = Field(default=None)
    python_project_path: str | None = Field(default=None)
    python_execution_closure_manifest_path: str | None = Field(default=None)
    deployment_payload_path: str | None = Field(default=None)
    persistence_backend: str | None = Field(default=None)
    database_url: str | None = Field(default=None)
    registry_path: str | None = Field(default=None)
    secrets_dir: str | None = Field(default=None)
    environment_provision_mode: str | None = Field(default=None)
    environment_manifest_path: str | None = Field(default=None)
    runtime_base_environment_manifest_path: str | None = Field(default=None)
    environment_service_port: int | None = Field(default=None)
    environment_api_endpoint: str | None = Field(default=None)
    hosted_services: list[NodeRunManifestHostedServiceSpec] = Field(default_factory=list)
    hosted_interfaces: list[NodeRunManifestHostedInterfaceSpec] = Field(default_factory=list)
    route_inputs: NodeRunManifestRouteInputs | None = Field(default=None)
    auth_inputs: NodeRunManifestAuthInputs | None = Field(default=None)
    readiness: NodeRunManifestReadinessPolicy | None = Field(default=None)
    provenance: NodeRunManifestProvenance | None = Field(default=None)


class ProvisionEnvironmentRequest(NodeHostOperationRequest):
    # Attributes
    operation: str = Field(default="provision_environment")
    environment_config_id: UUID
    environment_title: str | None = Field(default=None)
    environment_description: str | None = Field(default=None)
    environment_port: int | None = Field(default=None)
    database_url: str | None = Field(default=None)
    persistence_backend: str | None = Field(default=None)
    eager_ready: bool = Field(default=True)


class ProvisionEnvironmentResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="provision_environment")
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


class GetEnvironmentStatusRequest(NodeHostOperationRequest):
    # Attributes
    operation: str = Field(default="get_environment_status")
    environment_id: UUID


class GetEnvironmentStatusResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="get_environment_status")
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


class GetBootEnvironmentDescriptorRequest(NodeHostOperationRequest):
    # Attributes
    operation: str = Field(default="get_boot_environment_descriptor")


class GetBootEnvironmentDescriptorResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="get_boot_environment_descriptor")
    status: str
    error: str | None = Field(default=None)
    descriptor: BootEnvironmentDescriptor | None = Field(default=None)


class DiscoverEnvironmentConfigsRequest(NodeHostOperationRequest):
    # Attributes
    operation: str = Field(default="discover_environment_configs")


class DiscoverEnvironmentConfigsResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="discover_environment_configs")
    configs: list[EnvironmentConfigDescriptor] = Field(default_factory=list)


class DiscoverApiRoutesRequest(NodeHostOperationRequest):
    # Attributes
    operation: str = Field(default="discover_service_api_dependency_routes")
    consumer_service_package_id: UUID | None = Field(default=None)
    api_package_id: UUID | None = Field(default=None)


class DiscoverApiRoutesResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="discover_service_api_dependency_routes")
    routes: list[NodeServiceApiDependencyRouteDescriptor] = Field(default_factory=list)


class DescribeHostedServiceRuntimesRequest(NodeHostOperationRequest):
    """Describe supervised hosted-Service runtime health/status currently visible to this Node."""

    # Attributes
    operation: str = Field(default="describe_hosted_service_runtimes")


class DescribeHostedServiceRuntimesResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="describe_hosted_service_runtimes")
    hosted_service_runtimes: list[HostedServiceRuntimeStatus] = Field(default_factory=list)


class DescribeHostedRuntimesRequest(NodeHostOperationRequest):
    """
    Describe generic supervised hosted-runtime lifecycle status currently
    visible to this Node.
    """

    # Attributes
    operation: str = Field(default="describe_hosted_runtimes")
    runtime_kind: str | None = Field(default=None)
    runtime_key: str | None = Field(default=None)


class DescribeHostedRuntimesResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="describe_hosted_runtimes")
    hosted_runtimes: list[HostedRuntimeLifecycleStatus] = Field(default_factory=list)


class RestartHostedRuntimeRequest(NodeHostOperationRequest):
    """
    Request a Node-owned lifecycle restart for a supervised hosted runtime.
    v0 is intentionally generic and fail-closed. Runtime-specific restart
    mechanics must be owned by the supervisor for the selected `runtime_key`;
    provider clients must not infer restartability from paths or labels.
    """

    # Attributes
    operation: str = Field(default="restart_hosted_runtime")
    runtime_key: str
    reason: str | None = Field(default=None)
    evidence: JsonObject | None = Field(default=None)


class RestartHostedRuntimeResponse(NodeHostOperationResponse):
    # Attributes
    operation: str = Field(default="restart_hosted_runtime")
    runtime_key: str
    runtime_kind: str | None = Field(default=None)
    hosted_runtime: HostedRuntimeLifecycleStatus | None = Field(default=None)
    operation_receipt: JsonObject | None = Field(default=None)
