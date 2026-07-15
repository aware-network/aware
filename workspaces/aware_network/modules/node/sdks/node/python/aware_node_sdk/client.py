from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from aware_node_service_dto.node.host import BootEnvironmentDescriptor
from aware_node_service_dto.node.host import DescribeHostedRuntimesRequest
from aware_node_service_dto.node.host import DescribeHostedRuntimesResponse
from aware_node_service_dto.node.host import DiscoverApiRoutesRequest
from aware_node_service_dto.node.host import DiscoverApiRoutesResponse
from aware_node_service_dto.node.host import DescribeHostedServiceRuntimesRequest
from aware_node_service_dto.node.host import DescribeHostedServiceRuntimesResponse
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsRequest
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsResponse
from aware_node_service_dto.node.host import EnvironmentConfigDescriptor
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorRequest
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorResponse
from aware_node_service_dto.node.host import GetEnvironmentStatusRequest
from aware_node_service_dto.node.host import GetEnvironmentStatusResponse
from aware_node_service_dto.node.host import HostedRuntimeLifecycleStatus
from aware_node_service_dto.node.host import HostedServiceRuntimeStatus
from aware_node_service_dto.node.host import NodeServiceApiDependencyRouteDescriptor
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_node_service_dto.node.host import ProvisionEnvironmentResponse
from aware_node_service_dto.node.host import RestartHostedRuntimeRequest
from aware_node_service_dto.node.host import RestartHostedRuntimeResponse

from aware_node_sdk.package_run import NodePackageRunClient


class _NodeHostCapabilityClient(Protocol):
    async def discover_environment_configs(
        self,
        request: DiscoverEnvironmentConfigsRequest,
    ) -> DiscoverEnvironmentConfigsResponse: ...

    async def discover_service_api_dependency_routes(
        self,
        request: DiscoverApiRoutesRequest,
    ) -> DiscoverApiRoutesResponse: ...

    async def describe_hosted_service_runtimes(
        self,
        request: DescribeHostedServiceRuntimesRequest,
    ) -> DescribeHostedServiceRuntimesResponse: ...

    async def describe_hosted_runtimes(
        self,
        request: DescribeHostedRuntimesRequest,
    ) -> DescribeHostedRuntimesResponse: ...

    async def restart_hosted_runtime(
        self,
        request: RestartHostedRuntimeRequest,
    ) -> RestartHostedRuntimeResponse: ...

    async def get_boot_environment_descriptor(
        self,
        request: GetBootEnvironmentDescriptorRequest,
    ) -> GetBootEnvironmentDescriptorResponse: ...

    async def get_environment_status(
        self,
        request: GetEnvironmentStatusRequest,
    ) -> GetEnvironmentStatusResponse: ...

    async def provision_environment(
        self,
        request: ProvisionEnvironmentRequest,
    ) -> ProvisionEnvironmentResponse: ...


class _NodeApiNamespaceClient(Protocol):
    @property
    def host(self) -> _NodeHostCapabilityClient: ...


class NodeGeneratedApiClient(Protocol):
    @property
    def node(self) -> _NodeApiNamespaceClient: ...


class NodeSdkError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class NodeApiRoutesQuery:
    consumer_service_package_id: UUID | None = None
    api_package_id: UUID | None = None


@dataclass(slots=True)
class NodeSdkCache:
    environment_configs: tuple[EnvironmentConfigDescriptor, ...] = ()
    boot_environment_descriptor: BootEnvironmentDescriptor | None = None
    service_api_dependency_routes_by_query: dict[
        NodeApiRoutesQuery,
        tuple[NodeServiceApiDependencyRouteDescriptor, ...],
    ] = field(default_factory=dict)
    hosted_service_runtimes: tuple[HostedServiceRuntimeStatus, ...] = ()
    hosted_runtimes: tuple[HostedRuntimeLifecycleStatus, ...] = ()
    environment_status_by_id: dict[
        UUID,
        GetEnvironmentStatusResponse,
    ] = field(default_factory=dict)
    provisioned_environments_by_id: dict[
        UUID,
        ProvisionEnvironmentResponse,
    ] = field(default_factory=dict)

    def record_environment_configs(
        self,
        configs: tuple[EnvironmentConfigDescriptor, ...],
    ) -> None:
        self.environment_configs = configs

    def record_service_api_dependency_routes(
        self,
        *,
        query: NodeApiRoutesQuery,
        routes: tuple[NodeServiceApiDependencyRouteDescriptor, ...],
    ) -> None:
        self.service_api_dependency_routes_by_query[query] = routes

    def record_hosted_service_runtimes(
        self,
        statuses: tuple[HostedServiceRuntimeStatus, ...],
    ) -> None:
        self.hosted_service_runtimes = statuses

    def record_hosted_runtimes(
        self,
        statuses: tuple[HostedRuntimeLifecycleStatus, ...],
    ) -> None:
        self.hosted_runtimes = statuses

    def record_boot_environment_descriptor(
        self,
        descriptor: BootEnvironmentDescriptor,
    ) -> None:
        self.boot_environment_descriptor = descriptor

    def record_environment_status(
        self,
        response: GetEnvironmentStatusResponse,
    ) -> None:
        self.environment_status_by_id[response.environment_id] = response

    def record_provisioned_environment(
        self,
        response: ProvisionEnvironmentResponse,
    ) -> None:
        if response.environment_id is not None:
            self.provisioned_environments_by_id[response.environment_id] = response


@dataclass(slots=True)
class NodeSdkClient:
    api_client: NodeGeneratedApiClient
    cache: NodeSdkCache | None = None

    async def discover_environment_configs(
        self,
        *,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> tuple[EnvironmentConfigDescriptor, ...]:
        response = await self.api_client.node.host.discover_environment_configs(
            DiscoverEnvironmentConfigsRequest(actor_id=actor_id, node_id=node_id)
        )
        _raise_if_failed(response, operation="discover_environment_configs")
        configs = tuple(response.configs)
        if self.cache is not None:
            self.cache.record_environment_configs(configs)
        return configs

    async def discover_service_api_dependency_routes(
        self,
        *,
        consumer_service_package_id: UUID | None = None,
        api_package_id: UUID | None = None,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> tuple[NodeServiceApiDependencyRouteDescriptor, ...]:
        query = NodeApiRoutesQuery(
            consumer_service_package_id=consumer_service_package_id,
            api_package_id=api_package_id,
        )
        response = (
            await self.api_client.node.host.discover_service_api_dependency_routes(
                DiscoverApiRoutesRequest(
                    actor_id=actor_id,
                    node_id=node_id,
                    consumer_service_package_id=consumer_service_package_id,
                    api_package_id=api_package_id,
                )
            )
        )
        _raise_if_failed(
            response,
            operation="discover_service_api_dependency_routes",
        )
        routes = tuple(response.routes)
        if self.cache is not None:
            self.cache.record_service_api_dependency_routes(
                query=query,
                routes=routes,
            )
        return routes

    async def describe_hosted_service_runtimes(
        self,
        *,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> tuple[HostedServiceRuntimeStatus, ...]:
        response = await self.api_client.node.host.describe_hosted_service_runtimes(
            DescribeHostedServiceRuntimesRequest(actor_id=actor_id, node_id=node_id)
        )
        _raise_if_failed(response, operation="describe_hosted_service_runtimes")
        statuses = tuple(response.hosted_service_runtimes)
        if self.cache is not None:
            self.cache.record_hosted_service_runtimes(statuses)
        return statuses

    async def describe_hosted_runtimes(
        self,
        *,
        runtime_kind: str | None = None,
        runtime_key: str | None = None,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> tuple[HostedRuntimeLifecycleStatus, ...]:
        response = await self.api_client.node.host.describe_hosted_runtimes(
            DescribeHostedRuntimesRequest(
                actor_id=actor_id,
                node_id=node_id,
                runtime_kind=runtime_kind,
                runtime_key=runtime_key,
            )
        )
        _raise_if_failed(response, operation="describe_hosted_runtimes")
        statuses = tuple(response.hosted_runtimes)
        if self.cache is not None:
            self.cache.record_hosted_runtimes(statuses)
        return statuses

    async def restart_hosted_runtime(
        self,
        *,
        runtime_key: str,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> RestartHostedRuntimeResponse:
        response = await self.api_client.node.host.restart_hosted_runtime(
            RestartHostedRuntimeRequest(
                actor_id=actor_id,
                node_id=node_id,
                runtime_key=runtime_key,
                reason=reason,
                evidence=evidence,
            )
        )
        _raise_if_failed(response, operation="restart_hosted_runtime")
        return response

    async def get_boot_environment_descriptor(
        self,
        *,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> BootEnvironmentDescriptor:
        response = await self.api_client.node.host.get_boot_environment_descriptor(
            GetBootEnvironmentDescriptorRequest(actor_id=actor_id, node_id=node_id)
        )
        _raise_if_failed(response, operation="get_boot_environment_descriptor")
        descriptor = response.descriptor
        if descriptor is None:
            raise NodeSdkError(
                "Node SDK get_boot_environment_descriptor returned no descriptor."
            )
        if self.cache is not None:
            self.cache.record_boot_environment_descriptor(descriptor)
        return descriptor

    async def provision_environment(
        self,
        *,
        environment_config_id: UUID | None = None,
        bundle_manifest_path: str | None = None,
        environment_title: str | None = None,
        environment_description: str | None = None,
        environment_port: int | None = None,
        database_url: str | None = None,
        persistence_backend: str | None = None,
        eager_ready: bool = True,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> ProvisionEnvironmentResponse:
        response = await self.api_client.node.host.provision_environment(
            ProvisionEnvironmentRequest(
                actor_id=actor_id,
                node_id=node_id,
                environment_config_id=environment_config_id,
                bundle_manifest_path=bundle_manifest_path,
                environment_title=environment_title,
                environment_description=environment_description,
                environment_port=environment_port,
                database_url=database_url,
                persistence_backend=persistence_backend,
                eager_ready=eager_ready,
            )
        )
        _raise_if_failed(response, operation="provision_environment")
        if self.cache is not None:
            self.cache.record_provisioned_environment(response)
        return response

    async def get_environment_status(
        self,
        *,
        environment_id: UUID,
        actor_id: UUID | None = None,
        node_id: UUID | None = None,
    ) -> GetEnvironmentStatusResponse:
        response = await self.api_client.node.host.get_environment_status(
            GetEnvironmentStatusRequest(
                actor_id=actor_id,
                node_id=node_id,
                environment_id=environment_id,
            )
        )
        _raise_if_failed(response, operation="get_environment_status")
        if self.cache is not None:
            self.cache.record_environment_status(response)
        return response


class AwareNodeSdk:
    def __init__(
        self,
        api_client: NodeGeneratedApiClient,
        *,
        cache: NodeSdkCache | None = None,
    ) -> None:
        self.api_client = api_client
        self.node = NodeSdkClient(api_client=api_client, cache=cache)
        self.package_run = NodePackageRunClient()


def _raise_if_failed(response: object, *, operation: str) -> None:
    error = getattr(response, "error", None)
    status = str(getattr(response, "status", "") or "").lower()
    if error is None and status not in {"failed", "error"}:
        return
    details = error or status or "unknown error"
    raise NodeSdkError(f"Node SDK {operation} failed: {details}")


__all__ = [
    "AwareNodeSdk",
    "NodeApiRoutesQuery",
    "NodeGeneratedApiClient",
    "NodeSdkCache",
    "NodeSdkClient",
    "NodeSdkError",
]
