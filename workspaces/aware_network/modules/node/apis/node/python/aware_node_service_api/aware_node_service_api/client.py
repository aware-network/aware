# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF,
    NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF,
    NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF,
    NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
    NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF,
    NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF,
    NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF,
    NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF,
)
from aware_node_service_dto.node.host import (
    DescribeHostedRuntimesRequest,
    DescribeHostedRuntimesResponse,
    DescribeHostedServiceRuntimesRequest,
    DescribeHostedServiceRuntimesResponse,
    DiscoverApiRoutesRequest,
    DiscoverApiRoutesResponse,
    DiscoverEnvironmentConfigsRequest,
    DiscoverEnvironmentConfigsResponse,
    GetBootEnvironmentDescriptorRequest,
    GetBootEnvironmentDescriptorResponse,
    GetEnvironmentStatusRequest,
    GetEnvironmentStatusResponse,
    ProvisionEnvironmentRequest,
    ProvisionEnvironmentResponse,
    RestartHostedRuntimeRequest,
    RestartHostedRuntimeResponse,
)


class NodeHostCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_hosted_runtimes(self, request: DescribeHostedRuntimesRequest) -> DescribeHostedRuntimesResponse:
        """Read generic Node-owned hosted runtime lifecycle status from the supervising Node."""
        return cast(
            DescribeHostedRuntimesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def describe_hosted_service_runtimes(
        self, request: DescribeHostedServiceRuntimesRequest
    ) -> DescribeHostedServiceRuntimesResponse:
        """Read live Node-owned hosted-service runtime status from the supervising Node."""
        return cast(
            DescribeHostedServiceRuntimesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def discover_environment_configs(
        self, request: DiscoverEnvironmentConfigsRequest
    ) -> DiscoverEnvironmentConfigsResponse:
        """Discover Node-managed EnvironmentConfig descriptors available for live provisioning."""
        return cast(
            DiscoverEnvironmentConfigsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def discover_service_api_dependency_routes(
        self, request: DiscoverApiRoutesRequest
    ) -> DiscoverApiRoutesResponse:
        """Discover Node-bound service API dependency routes for live service-to-service calls."""
        return cast(
            DiscoverApiRoutesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def get_boot_environment_descriptor(
        self, request: GetBootEnvironmentDescriptorRequest
    ) -> GetBootEnvironmentDescriptorResponse:
        """Read the Node-managed BOOT environment descriptor without client-side kernel heuristics."""
        return cast(
            GetBootEnvironmentDescriptorResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def get_environment_status(self, request: GetEnvironmentStatusRequest) -> GetEnvironmentStatusResponse:
        """Read live Node-owned status for one Environment provisioned on this node."""
        return cast(
            GetEnvironmentStatusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def provision_environment(self, request: ProvisionEnvironmentRequest) -> ProvisionEnvironmentResponse:
        """Provision or resume one Environment through live Node host authority."""
        return cast(
            ProvisionEnvironmentResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def restart_hosted_runtime(self, request: RestartHostedRuntimeRequest) -> RestartHostedRuntimeResponse:
        """Request a generic Node-owned hosted runtime restart through the supervising Node."""
        return cast(
            RestartHostedRuntimeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NodeApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.host = NodeHostCapabilityClient(client)


class AwareNodeServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.node = NodeApiClient(client)


__all__ = [
    "AwareNodeServiceApiClient",
    "NodeApiClient",
    "NodeHostCapabilityClient",
]
