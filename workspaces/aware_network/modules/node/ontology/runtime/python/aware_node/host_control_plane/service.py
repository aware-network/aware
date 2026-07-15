from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_node_service_dto.node.host import DiscoverApiRoutesRequest
from aware_node_service_dto.node.host import DiscoverApiRoutesResponse
from aware_node_service_dto.node.host import DescribeHostedRuntimesRequest
from aware_node_service_dto.node.host import DescribeHostedRuntimesResponse
from aware_node_service_dto.node.host import HostedRuntimeLifecycleStatus
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsRequest
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsResponse
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorRequest
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorResponse
from aware_node_service_dto.node.host import GetEnvironmentStatusRequest
from aware_node_service_dto.node.host import GetEnvironmentStatusResponse
from aware_node_service_dto.node.host import NodeEnvironmentProvisioningReceipt
from aware_node_service_dto.node.host import NodeHostOperationRequest
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_node_service_dto.node.host import ProvisionEnvironmentResponse
from aware_node_service_dto.node.host import RestartHostedRuntimeRequest
from aware_node_service_dto.node.host import RestartHostedRuntimeResponse

from aware_node.host_control_plane.models import (
    NodeHostControlPlanePorts,
    NodeHostControlPlaneResult,
    NodeHostedEnvironmentState,
)


def _require_node_id(request: NodeHostOperationRequest) -> UUID:
    if request.node_id is None:
        raise RuntimeError("NodeHostOperationRequest.node_id is required")
    return request.node_id


@dataclass(slots=True)
class NodeHostControlPlaneService:
    ports: NodeHostControlPlanePorts

    async def handle_request(
        self,
        request: NodeHostOperationRequest,
    ) -> NodeHostControlPlaneResult:
        if isinstance(request, DiscoverEnvironmentConfigsRequest):
            return await self.handle_discover_environment_configs(request)
        if isinstance(request, DiscoverApiRoutesRequest):
            return await self.handle_discover_service_api_dependency_routes(request)
        if isinstance(request, DescribeHostedRuntimesRequest):
            return await self.handle_describe_hosted_runtimes(request)
        if isinstance(request, GetBootEnvironmentDescriptorRequest):
            return await self.handle_get_boot_environment_descriptor(request)
        if isinstance(request, ProvisionEnvironmentRequest):
            return await self.handle_provision_environment(request)
        if isinstance(request, GetEnvironmentStatusRequest):
            return await self.handle_get_environment_status(request)
        if isinstance(request, RestartHostedRuntimeRequest):
            return await self.handle_restart_hosted_runtime(request)
        raise RuntimeError(f"Unsupported NodeHostOperationRequest: {type(request)}")

    async def handle_discover_environment_configs(
        self,
        request: DiscoverEnvironmentConfigsRequest,
    ) -> NodeHostControlPlaneResult:
        return NodeHostControlPlaneResult(
            response=DiscoverEnvironmentConfigsResponse(
                actor_id=request.actor_id,
                node_id=_require_node_id(request),
                configs=self.ports.discover_environment_config_descriptors(),
            )
        )

    async def handle_discover_service_api_dependency_routes(
        self,
        request: DiscoverApiRoutesRequest,
    ) -> NodeHostControlPlaneResult:
        return NodeHostControlPlaneResult(
            response=DiscoverApiRoutesResponse(
                actor_id=request.actor_id,
                node_id=_require_node_id(request),
                status="succeeded",
                routes=self.ports.discover_service_api_dependency_route_descriptors(
                    consumer_service_package_id=request.consumer_service_package_id,
                    api_package_id=request.api_package_id,
                ),
            )
        )

    async def handle_get_boot_environment_descriptor(
        self,
        request: GetBootEnvironmentDescriptorRequest,
    ) -> NodeHostControlPlaneResult:
        node_id = _require_node_id(request)
        await self.ports.bootstrap_kernel_environment()
        result = self.ports.read_boot_environment_descriptor(node_id=node_id)
        return NodeHostControlPlaneResult(
            response=GetBootEnvironmentDescriptorResponse(
                actor_id=request.actor_id,
                node_id=node_id,
                status=result.response_status,
                error=result.response_error,
                descriptor=result.descriptor,
            ),
            request_status=result.request_status,
            request_error=result.request_error,
        )

    async def handle_describe_hosted_runtimes(
        self,
        request: DescribeHostedRuntimesRequest,
    ) -> NodeHostControlPlaneResult:
        node_id = _require_node_id(request)
        statuses = [
            HostedRuntimeLifecycleStatus.model_validate(item)
            for item in self.ports.describe_hosted_runtime_lifecycle_statuses(
                runtime_kind=request.runtime_kind,
                runtime_key=request.runtime_key,
            )
        ]
        return NodeHostControlPlaneResult(
            response=DescribeHostedRuntimesResponse(
                actor_id=request.actor_id,
                node_id=node_id,
                status="succeeded",
                hosted_runtimes=statuses,
            )
        )

    async def handle_restart_hosted_runtime(
        self,
        request: RestartHostedRuntimeRequest,
    ) -> NodeHostControlPlaneResult:
        node_id = _require_node_id(request)
        payload = await self.ports.restart_hosted_runtime(
            runtime_key=request.runtime_key,
            reason=request.reason,
            evidence=request.evidence,
        )
        runtime_payload = payload.get("hosted_runtime")
        runtime = (
            HostedRuntimeLifecycleStatus.model_validate(runtime_payload)
            if runtime_payload is not None
            else None
        )
        return NodeHostControlPlaneResult(
            response=RestartHostedRuntimeResponse(
                actor_id=request.actor_id,
                node_id=node_id,
                status=str(payload.get("status") or "failed"),
                error=(
                    str(payload["error"]) if payload.get("error") is not None else None
                ),
                runtime_key=request.runtime_key,
                runtime_kind=(
                    str(payload["runtime_kind"])
                    if payload.get("runtime_kind") is not None
                    else None
                ),
                hosted_runtime=runtime,
                operation_receipt=payload.get("operation_receipt"),
            )
        )

    async def handle_provision_environment(
        self,
        request: ProvisionEnvironmentRequest,
    ) -> NodeHostControlPlaneResult:
        node_id = _require_node_id(request)
        record = await self.ports.provision_environment(
            request=request, node_id=node_id
        )
        return NodeHostControlPlaneResult(
            response=self._build_provision_environment_response(
                request=request,
                node_id=node_id,
                record=record,
            )
        )

    async def handle_get_environment_status(
        self,
        request: GetEnvironmentStatusRequest,
    ) -> NodeHostControlPlaneResult:
        node_id = _require_node_id(request)
        record = self.ports.read_environment_status(
            environment_id=request.environment_id
        )
        if record is None:
            return NodeHostControlPlaneResult(
                response=GetEnvironmentStatusResponse(
                    actor_id=request.actor_id,
                    node_id=node_id,
                    status="not_found",
                    error="Environment is not registered on this node",
                    environment_id=request.environment_id,
                )
            )
        return NodeHostControlPlaneResult(
            response=self._build_environment_status_response(
                request=request,
                node_id=node_id,
                record=record,
            )
        )

    def describe_hosted_service_runtime_statuses(self) -> list[dict[str, object]]:
        return self.ports.describe_hosted_service_runtime_statuses()

    @staticmethod
    def _build_provision_environment_response(
        *,
        request: ProvisionEnvironmentRequest,
        node_id: UUID,
        record: NodeHostedEnvironmentState,
    ) -> ProvisionEnvironmentResponse:
        return ProvisionEnvironmentResponse(
            actor_id=request.actor_id,
            node_id=node_id,
            status=record.status,
            error=record.error,
            environment_id=record.environment_id,
            environment_config_id=record.environment_config_id,
            environment_config_title=record.environment_config_title,
            environment_title=record.environment_title,
            environment_endpoint=record.environment_endpoint,
            ocg_hash=record.ocg_hash,
            process_id=record.process_id,
            thread_id=record.thread_id,
            branch_id=record.branch_id,
            opg_hashes=list(record.opg_hashes),
            provisioning_receipt=NodeHostControlPlaneService._build_provisioning_receipt(
                actor_id=request.actor_id,
                node_id=node_id,
                record=record,
            ),
        )

    @staticmethod
    def _build_environment_status_response(
        *,
        request: GetEnvironmentStatusRequest,
        node_id: UUID,
        record: NodeHostedEnvironmentState,
    ) -> GetEnvironmentStatusResponse:
        return GetEnvironmentStatusResponse(
            actor_id=request.actor_id,
            node_id=node_id,
            status=record.status,
            error=record.error,
            environment_id=record.environment_id,
            environment_config_id=record.environment_config_id,
            environment_config_title=record.environment_config_title,
            environment_title=record.environment_title,
            environment_endpoint=record.environment_endpoint,
            ocg_hash=record.ocg_hash,
            process_id=record.process_id,
            thread_id=record.thread_id,
            branch_id=record.branch_id,
            opg_hashes=list(record.opg_hashes),
            provisioning_receipt=NodeHostControlPlaneService._build_provisioning_receipt(
                actor_id=request.actor_id,
                node_id=node_id,
                record=record,
            ),
        )

    @staticmethod
    def _build_provisioning_receipt(
        *,
        actor_id: UUID | None,
        node_id: UUID,
        record: NodeHostedEnvironmentState,
    ) -> NodeEnvironmentProvisioningReceipt:
        return NodeEnvironmentProvisioningReceipt(
            status=record.status,
            error=record.error,
            actor_id=actor_id,
            node_id=node_id,
            environment_id=record.environment_id,
            environment_config_id=record.environment_config_id,
            environment_config_title=record.environment_config_title,
            environment_title=record.environment_title,
            environment_endpoint=record.environment_endpoint,
            runtime_artifact_refs_json=record.runtime_artifact_refs_json,
            service_api_provider_refs_json=record.service_api_provider_refs_json,
            ocg_hash=record.ocg_hash,
            opg_hashes=list(record.opg_hashes),
            process_id=record.process_id,
            thread_id=record.thread_id,
            branch_id=record.branch_id,
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
            readiness_receipt=record.readiness_receipt,
            network_node_environment_receipt=record.network_node_environment_receipt,
        )


__all__ = ["NodeHostControlPlaneService"]
