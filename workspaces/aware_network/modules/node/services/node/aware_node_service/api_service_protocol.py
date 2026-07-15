from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from aware_node.host_control_plane import NodeHostControlPlaneService
from aware_node_service_dto.node.host import DescribeHostedRuntimesRequest
from aware_node_service_dto.node.host import DescribeHostedRuntimesResponse
from aware_node_service_dto.node.host import DiscoverApiRoutesRequest
from aware_node_service_dto.node.host import DiscoverApiRoutesResponse
from aware_node_service_dto.node.host import DescribeHostedServiceRuntimesRequest
from aware_node_service_dto.node.host import DescribeHostedServiceRuntimesResponse
from aware_node_service_dto.node.host import HostedServiceRuntimeStatus
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsRequest
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsResponse
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorRequest
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorResponse
from aware_node_service_dto.node.host import GetEnvironmentStatusRequest
from aware_node_service_dto.node.host import GetEnvironmentStatusResponse
from aware_node_service_dto.node.host import NodeHostOperationRequest
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_node_service_dto.node.host import ProvisionEnvironmentResponse
from aware_node_service_dto.node.host import RestartHostedRuntimeRequest
from aware_node_service_dto.node.host import RestartHostedRuntimeResponse
from aware_node_service_protocol.protocols import (
    ENDPOINT_BINDINGS as NODE_SERVICE_PROTOCOL_ENDPOINT_BINDINGS,
    AwareNodeServiceProtocol,
    NodeApiServiceProtocol,
    NodeHostCapabilityServiceProtocol,
)


def build_aware_node_service_protocol_handler(
    *,
    control_plane: NodeHostControlPlaneService,
) -> AwareNodeServiceProtocol:
    return _AwareNodeServiceProtocolHandler(control_plane=control_plane)


class _NodeHostCapabilityHandler:
    def __init__(self, *, control_plane: NodeHostControlPlaneService) -> None:
        self._control_plane = control_plane

    async def discover_environment_configs(
        self,
        request: DiscoverEnvironmentConfigsRequest,
    ) -> DiscoverEnvironmentConfigsResponse:
        return await self._handle_request(
            request,
            request_model=DiscoverEnvironmentConfigsRequest,
            response_model=DiscoverEnvironmentConfigsResponse,
        )

    async def discover_service_api_dependency_routes(
        self,
        request: DiscoverApiRoutesRequest,
    ) -> DiscoverApiRoutesResponse:
        return await self._handle_request(
            request,
            request_model=DiscoverApiRoutesRequest,
            response_model=DiscoverApiRoutesResponse,
        )

    async def describe_hosted_service_runtimes(
        self,
        request: DescribeHostedServiceRuntimesRequest,
    ) -> DescribeHostedServiceRuntimesResponse:
        statuses = [
            HostedServiceRuntimeStatus.model_validate(item)
            for item in self._control_plane.describe_hosted_service_runtime_statuses()
        ]
        return DescribeHostedServiceRuntimesResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="succeeded",
            hosted_service_runtimes=statuses,
        )

    async def describe_hosted_runtimes(
        self,
        request: DescribeHostedRuntimesRequest,
    ) -> DescribeHostedRuntimesResponse:
        return await self._handle_request(
            request,
            request_model=DescribeHostedRuntimesRequest,
            response_model=DescribeHostedRuntimesResponse,
        )

    async def restart_hosted_runtime(
        self,
        request: RestartHostedRuntimeRequest,
    ) -> RestartHostedRuntimeResponse:
        return await self._handle_request(
            request,
            request_model=RestartHostedRuntimeRequest,
            response_model=RestartHostedRuntimeResponse,
        )

    async def get_boot_environment_descriptor(
        self,
        request: GetBootEnvironmentDescriptorRequest,
    ) -> GetBootEnvironmentDescriptorResponse:
        return await self._handle_request(
            request,
            request_model=GetBootEnvironmentDescriptorRequest,
            response_model=GetBootEnvironmentDescriptorResponse,
        )

    async def get_environment_status(
        self,
        request: GetEnvironmentStatusRequest,
    ) -> GetEnvironmentStatusResponse:
        return await self._handle_request(
            request,
            request_model=GetEnvironmentStatusRequest,
            response_model=GetEnvironmentStatusResponse,
        )

    async def provision_environment(
        self,
        request: ProvisionEnvironmentRequest,
    ) -> ProvisionEnvironmentResponse:
        return await self._handle_request(
            request,
            request_model=ProvisionEnvironmentRequest,
            response_model=ProvisionEnvironmentResponse,
        )

    async def _handle_request(
        self,
        request: BaseModel,
        *,
        request_model: type[NodeHostOperationRequest],
        response_model: type[BaseModel],
    ) -> Any:
        module_request = _convert_model(request, model_cls=request_model)
        result = await self._control_plane.handle_request(module_request)
        return _convert_model(result.response, model_cls=response_model)


class _NodeApiServiceProtocolHandler:
    def __init__(self, *, control_plane: NodeHostControlPlaneService) -> None:
        self.host: NodeHostCapabilityServiceProtocol = _NodeHostCapabilityHandler(
            control_plane=control_plane
        )


class _AwareNodeServiceProtocolHandler:
    def __init__(self, *, control_plane: NodeHostControlPlaneService) -> None:
        self.node: NodeApiServiceProtocol = _NodeApiServiceProtocolHandler(
            control_plane=control_plane
        )


def _convert_model(
    value: object,
    *,
    model_cls: type[BaseModel],
) -> Any:
    payload = value
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    return model_cls.model_validate(payload)


__all__ = [
    "NODE_SERVICE_PROTOCOL_ENDPOINT_BINDINGS",
    "build_aware_node_service_protocol_handler",
]
