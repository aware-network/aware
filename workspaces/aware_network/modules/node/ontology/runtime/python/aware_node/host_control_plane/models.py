from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_types import JsonObject
from aware_node_service_dto.node.host import BootEnvironmentDescriptor
from aware_node_service_dto.node.host import EnvironmentConfigDescriptor
from aware_node_service_dto.node.host import NodeHostOperationResponse
from aware_node_service_dto.node.host import NodeServiceApiDependencyRouteDescriptor
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest


@dataclass(frozen=True, slots=True)
class NodeHostedEnvironmentState:
    environment_id: UUID
    status: str
    error: str | None = None
    environment_config_id: UUID | None = None
    environment_config_title: str | None = None
    environment_title: str | None = None
    environment_endpoint: str | None = None
    runtime_artifact_refs_json: str | None = None
    service_api_provider_refs_json: str | None = None
    ocg_hash: str | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    opg_hashes: tuple[str, ...] = ()
    outer_wrapper_kind: str | None = None
    environment_handle: str | None = None
    workspace_root: str | None = None
    workspace_toml_path: str | None = None
    workspace_id: str | None = None
    workspace_package_id: str | None = None
    workspace_build_invocation_id: str | None = None
    workspace_build_receipt_path: str | None = None
    workspace_build_latest_path: str | None = None
    workspace_target_latest_path: str | None = None
    workspace_target_ref: str | None = None
    readiness_receipt: JsonObject | None = None
    network_node_environment_receipt: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class NodeHostBootEnvironmentReadResult:
    response_status: str
    response_error: str | None = None
    descriptor: BootEnvironmentDescriptor | None = None
    request_status: str = "succeeded"
    request_error: str | None = None


@dataclass(frozen=True, slots=True)
class NodeHostControlPlaneResult:
    response: NodeHostOperationResponse
    request_status: str = "succeeded"
    request_error: str | None = None


class NodeHostControlPlanePorts(Protocol):
    async def bootstrap_kernel_environment(self) -> None: ...

    def discover_environment_config_descriptors(
        self,
    ) -> list[EnvironmentConfigDescriptor]: ...

    def discover_service_api_dependency_route_descriptors(
        self,
        *,
        consumer_service_package_id: UUID | None = None,
        api_package_id: UUID | None = None,
    ) -> list[NodeServiceApiDependencyRouteDescriptor]: ...

    def describe_hosted_service_runtime_statuses(self) -> list[dict[str, object]]: ...

    def describe_hosted_runtime_lifecycle_statuses(
        self,
        *,
        runtime_kind: str | None = None,
        runtime_key: str | None = None,
    ) -> list[dict[str, object]]: ...

    async def restart_hosted_runtime(
        self,
        *,
        runtime_key: str,
        reason: str | None = None,
        evidence: JsonObject | None = None,
    ) -> dict[str, object]: ...

    def read_boot_environment_descriptor(
        self, *, node_id: UUID
    ) -> NodeHostBootEnvironmentReadResult: ...

    async def provision_environment(
        self,
        *,
        request: ProvisionEnvironmentRequest,
        node_id: UUID,
    ) -> NodeHostedEnvironmentState: ...

    def read_environment_status(
        self,
        *,
        environment_id: UUID,
    ) -> NodeHostedEnvironmentState | None: ...


__all__ = [
    "NodeHostBootEnvironmentReadResult",
    "NodeHostControlPlanePorts",
    "NodeHostControlPlaneResult",
    "NodeHostedEnvironmentState",
]
