from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from aware_network_service_dto.comms.models.network import NetworkRequestStatus
from aware_types import JsonObject
from aware_node.host_control_plane import (
    NodeHostBootEnvironmentReadResult,
    NodeHostedEnvironmentState,
)
from aware_node_service_dto.node.host import EnvironmentConfigDescriptor
from aware_node_service_dto.node.host import NodeServiceApiDependencyRouteDescriptor
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_node_service.control_plane.bootstrap_service import (
    NetworkNodeBootstrapService,
)
from aware_node_service.control_plane.environment_registry import (
    HostedEnvironmentRecord,
)
from aware_node_service.control_plane.hosted_environment_service import (
    NetworkNodeHostedEnvironmentService,
)
from aware_node_service.host.services import (
    describe_node_hosted_runtime_lifecycle_statuses,
    describe_node_hosted_service_runtime_statuses,
)


def _build_hosted_environment_state(
    record: HostedEnvironmentRecord,
) -> NodeHostedEnvironmentState:
    return NodeHostedEnvironmentState(
        environment_id=record.environment_id,
        status=record.status,
        error=record.error,
        environment_config_id=record.environment_config_id,
        environment_config_title=record.environment_config_title,
        environment_title=record.environment_title,
        environment_endpoint=record.environment_endpoint,
        runtime_artifact_refs_json=record.runtime_artifact_refs_json,
        service_api_provider_refs_json=record.service_api_provider_refs_json,
        ocg_hash=record.ocg_hash,
        process_id=record.process_id,
        thread_id=record.thread_id,
        branch_id=record.branch_id,
        opg_hashes=tuple(record.opg_hashes),
        outer_wrapper_kind=record.outer_wrapper_kind,
        environment_handle=record.environment_handle,
        workspace_root=record.workspace_root,
        workspace_toml_path=record.workspace_toml_path,
        workspace_id=record.workspace_id,
        workspace_package_id=record.workspace_package_id,
        workspace_build_invocation_id=record.workspace_build_invocation_id,
        workspace_build_receipt_path=record.workspace_build_receipt_path,
        workspace_build_latest_path=record.workspace_build_latest_path,
        workspace_target_latest_path=record.workspace_target_latest_path,
        workspace_target_ref=record.workspace_target_ref,
        readiness_receipt=(
            JsonObject(cast(Any, record.readiness_receipt))
            if record.readiness_receipt is not None
            else None
        ),
        network_node_environment_receipt=(
            JsonObject(cast(Any, record.network_node_environment_receipt))
            if record.network_node_environment_receipt is not None
            else None
        ),
    )


@dataclass(slots=True)
class NodeHostControlPlaneRuntimePorts:
    bootstrap_service: NetworkNodeBootstrapService
    hosted_environment_service: NetworkNodeHostedEnvironmentService
    node_app: object | None = None

    async def bootstrap_kernel_environment(self) -> None:
        await self.bootstrap_service.bootstrap_kernel_environment()

    def discover_environment_config_descriptors(
        self,
    ) -> list[EnvironmentConfigDescriptor]:
        return self.hosted_environment_service.list_environment_config_descriptors()

    def discover_service_api_dependency_route_descriptors(
        self,
        *,
        consumer_service_package_id: UUID | None = None,
        api_package_id: UUID | None = None,
    ) -> list[NodeServiceApiDependencyRouteDescriptor]:
        assembly = getattr(self.node_app, "_host_services_runtime", None)
        raw_routes: Any = getattr(assembly, "service_api_dependency_routes", ())
        descriptors: list[NodeServiceApiDependencyRouteDescriptor] = []
        for route in raw_routes or ():
            if (
                consumer_service_package_id is not None
                and route.consumer_service_package_id != consumer_service_package_id
            ):
                continue
            if api_package_id is not None and route.api_package_id != api_package_id:
                continue
            descriptors.append(_build_service_api_dependency_route_descriptor(route))
        return descriptors

    def describe_hosted_service_runtime_statuses(self) -> list[dict[str, object]]:
        if self.node_app is None:
            return []
        return [
            cast(dict[str, object], status.model_dump(mode="json", exclude_none=True))
            for status in describe_node_hosted_service_runtime_statuses(
                node_app=self.node_app
            )
        ]

    def describe_hosted_runtime_lifecycle_statuses(
        self,
        *,
        runtime_kind: str | None = None,
        runtime_key: str | None = None,
    ) -> list[dict[str, object]]:
        if self.node_app is None:
            return []
        return [
            cast(dict[str, object], status.model_dump(mode="json", exclude_none=True))
            for status in describe_node_hosted_runtime_lifecycle_statuses(
                node_app=self.node_app,
                runtime_kind=runtime_kind,
                runtime_key=runtime_key,
            )
        ]

    async def restart_hosted_runtime(
        self,
        *,
        runtime_key: str,
        reason: str | None = None,
        evidence: JsonObject | None = None,
    ) -> dict[str, object]:
        assembly = getattr(self.node_app, "_host_services_runtime", None)
        restart = getattr(assembly, "restart_hosted_runtime", None)
        if callable(restart):
            return cast(
                dict[str, object],
                await restart(
                    runtime_key=runtime_key,
                    reason=reason,
                    evidence=evidence,
                ),
            )
        return {
            "status": "failed",
            "error": (
                "NodeHost runtime assembly does not expose hosted runtime restart."
            ),
            "runtime_kind": None,
            "hosted_runtime": None,
            "operation_receipt": JsonObject(
                {
                    "runtime_key": runtime_key,
                    "reason": reason,
                    "evidence": dict(evidence or {}),
                    "restart_enabled": False,
                }
            ),
        }

    def read_boot_environment_descriptor(
        self,
        *,
        node_id: UUID,
    ) -> NodeHostBootEnvironmentReadResult:
        result = self.hosted_environment_service.read_boot_environment_descriptor(
            node_id=node_id
        )
        request_status = (
            "failed"
            if result.network_status == NetworkRequestStatus.failed
            else "succeeded"
        )
        request_error = result.network_error if request_status == "failed" else None
        return NodeHostBootEnvironmentReadResult(
            response_status=result.response_status,
            response_error=result.response_error,
            descriptor=result.descriptor,
            request_status=request_status,
            request_error=request_error,
        )

    async def provision_environment(
        self,
        *,
        request: ProvisionEnvironmentRequest,
        node_id: UUID,
    ) -> NodeHostedEnvironmentState:
        record = await self.hosted_environment_service.provision_environment(
            request=request,
            node_id=node_id,
        )
        return _build_hosted_environment_state(record)

    def read_environment_status(
        self,
        *,
        environment_id: UUID,
    ) -> NodeHostedEnvironmentState | None:
        record = self.hosted_environment_service.read_environment_record(environment_id)
        if record is None:
            return None
        return _build_hosted_environment_state(record)


def _build_service_api_dependency_route_descriptor(
    route: Any,
) -> NodeServiceApiDependencyRouteDescriptor:
    route_kind = getattr(route.route_kind, "value", route.route_kind)
    return NodeServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=route.consumer_service_package_id,
        consumer_service_package_name=route.consumer_service_package_name,
        provider_service_package_id=route.provider_service_package_id,
        provider_service_package_name=route.provider_service_package_name,
        api_package_id=route.api_package_id,
        api_package_name=route.api_package_name,
        route_kind=str(route_kind),
        host_id=route.host_id,
        host_version=route.host_version,
        protocol_version=route.protocol_version,
        socket_path=(str(route.socket_path) if route.socket_path is not None else None),
        consumer_node_id=getattr(route, "consumer_node_id", None),
        provider_node_id=getattr(route, "provider_node_id", None),
        provider_node_base_url=getattr(route, "provider_node_base_url", None),
        route_connection_id=getattr(route, "route_connection_id", None),
        request_timeout_s=route.request_timeout_s,
        service_names=list(route.service_names),
        endpoint_refs_by_service=JsonObject(
            cast(Any, _route_map_payload(route.endpoint_refs_by_service))
        ),
        stream_endpoint_refs_by_service=JsonObject(
            cast(Any, _route_map_payload(route.stream_endpoint_refs_by_service))
        ),
    )


def _route_map_payload(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    payload: dict[str, list[str]] = {}
    for raw_key, raw_refs in value.items():
        if not isinstance(raw_key, str):
            continue
        refs = _string_sequence_payload(raw_refs)
        if refs:
            payload[raw_key] = refs
    return payload


def _string_sequence_payload(value: object) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            refs.append(item)
    return refs


__all__ = ["NodeHostControlPlaneRuntimePorts"]
