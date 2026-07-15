from __future__ import annotations

from uuid import uuid4

import pytest

from aware_node_sdk import (
    NodeApiRoutesQuery,
    NodeSdkCache,
    NodeSdkClient,
    NodeSdkError,
)
from aware_node_service_dto.node.host import BootEnvironmentDescriptor
from aware_node_service_dto.node.host import DescribeHostedRuntimesResponse
from aware_node_service_dto.node.host import DiscoverApiRoutesResponse
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsResponse
from aware_node_service_dto.node.host import DescribeHostedServiceRuntimesResponse
from aware_node_service_dto.node.host import EnvironmentConfigDescriptor
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorResponse
from aware_node_service_dto.node.host import GetEnvironmentStatusResponse
from aware_node_service_dto.node.host import HostedRuntimeLifecycleStatus
from aware_node_service_dto.node.host import HostedServiceRuntimeStatus
from aware_node_service_dto.node.host import NodeServiceApiDependencyRouteDescriptor
from aware_node_service_dto.node.host import ProvisionEnvironmentResponse
from aware_node_service_dto.node.host import RestartHostedRuntimeResponse


class _HostApi:
    def __init__(
        self,
        *,
        config: EnvironmentConfigDescriptor,
        route: NodeServiceApiDependencyRouteDescriptor,
        hosted_runtime: HostedServiceRuntimeStatus,
        hosted_lifecycle_runtime: HostedRuntimeLifecycleStatus,
        boot: BootEnvironmentDescriptor,
        provision: ProvisionEnvironmentResponse,
        status: GetEnvironmentStatusResponse,
    ) -> None:
        self.config_requests = []
        self.route_requests = []
        self.hosted_runtime_requests = []
        self.hosted_lifecycle_runtime_requests = []
        self.restart_hosted_runtime_requests = []
        self.boot_requests = []
        self.provision_requests = []
        self.status_requests = []
        self._config = config
        self._route = route
        self._hosted_runtime = hosted_runtime
        self._hosted_lifecycle_runtime = hosted_lifecycle_runtime
        self._boot = boot
        self._provision = provision
        self._status = status

    async def discover_environment_configs(self, request):  # noqa: ANN001, ANN201
        self.config_requests.append(request)
        return DiscoverEnvironmentConfigsResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="succeeded",
            configs=[self._config],
        )

    async def discover_service_api_dependency_routes(
        self, request
    ):  # noqa: ANN001, ANN201
        self.route_requests.append(request)
        return DiscoverApiRoutesResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="succeeded",
            routes=[self._route],
        )

    async def describe_hosted_service_runtimes(self, request):  # noqa: ANN001, ANN201
        self.hosted_runtime_requests.append(request)
        return DescribeHostedServiceRuntimesResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="succeeded",
            hosted_service_runtimes=[self._hosted_runtime],
        )

    async def describe_hosted_runtimes(self, request):  # noqa: ANN001, ANN201
        self.hosted_lifecycle_runtime_requests.append(request)
        return DescribeHostedRuntimesResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="succeeded",
            hosted_runtimes=[self._hosted_lifecycle_runtime],
        )

    async def restart_hosted_runtime(self, request):  # noqa: ANN001, ANN201
        self.restart_hosted_runtime_requests.append(request)
        return RestartHostedRuntimeResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="failed",
            error="restart disabled",
            runtime_key=request.runtime_key,
            runtime_kind=self._hosted_lifecycle_runtime.runtime_kind,
            hosted_runtime=self._hosted_lifecycle_runtime,
            operation_receipt={"restart_enabled": False},
        )

    async def get_boot_environment_descriptor(self, request):  # noqa: ANN001, ANN201
        self.boot_requests.append(request)
        return GetBootEnvironmentDescriptorResponse(
            actor_id=request.actor_id,
            node_id=request.node_id,
            status="ready",
            descriptor=self._boot,
        )

    async def provision_environment(self, request):  # noqa: ANN001, ANN201
        self.provision_requests.append(request)
        return self._provision

    async def get_environment_status(self, request):  # noqa: ANN001, ANN201
        self.status_requests.append(request)
        return self._status


class _NodeApi:
    def __init__(self, host: _HostApi) -> None:
        self.host = host


class _ApiClient:
    def __init__(self, host: _HostApi) -> None:
        self.node = _NodeApi(host)


@pytest.mark.asyncio
async def test_node_sdk_routes_through_generated_api_and_records_cache() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    environment_config_id = uuid4()
    environment_id = uuid4()
    consumer_service_package_id = uuid4()
    api_package_id = uuid4()
    provider_service_package_id = uuid4()
    config = EnvironmentConfigDescriptor(
        environment_config_id=environment_config_id,
        title="Kernel",
        canonical_language="aware",
        bundle_manifest_path="/tmp/kernel.environment.json",
        ocg_hash="ocg",
        opg_hashes=["opg-a"],
    )
    route = NodeServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=consumer_service_package_id,
        consumer_service_package_name="aware-interface-service",
        provider_service_package_id=provider_service_package_id,
        provider_service_package_name="aware-environment-service",
        api_package_id=api_package_id,
        api_package_name="environment-service-api",
        route_kind="local_socket",
        host_id="environment-host",
        protocol_version="1",
        socket_path="/tmp/aware-environment.sock",
        request_timeout_s=30.0,
        service_names=["aware_environment"],
    )
    hosted_runtime = HostedServiceRuntimeStatus(
        host_id="aware_service_service",
        host_version="1.0.0",
        protocol_version="1",
        readiness_status="ready",
        is_ready=True,
        is_alive=True,
        supports_stream_events=True,
        summary="ready",
    )
    hosted_lifecycle_runtime = HostedRuntimeLifecycleStatus(
        runtime_key="interface:/tmp/interface.json",
        runtime_kind="interface",
        status="ready",
        is_ready=True,
        is_alive=True,
        socket_path="/tmp/interface.sock",
    )
    boot = BootEnvironmentDescriptor(
        kernel_environment_config_id=environment_config_id,
        boot_environment_id=environment_id,
        kernel_environment_config_title="Kernel",
        boot_environment_title="Boot Kernel",
        opg_hashes=["opg-a"],
    )
    provision = ProvisionEnvironmentResponse(
        actor_id=actor_id,
        node_id=node_id,
        status="ready",
        environment_id=environment_id,
        environment_config_id=environment_config_id,
        environment_title="Kernel Environment",
        environment_endpoint="http://127.0.0.1:8001",
    )
    status = GetEnvironmentStatusResponse(
        actor_id=actor_id,
        node_id=node_id,
        status="ready",
        environment_id=environment_id,
        environment_config_id=environment_config_id,
        environment_title="Kernel Environment",
        environment_endpoint="http://127.0.0.1:8001",
    )
    host = _HostApi(
        config=config,
        route=route,
        hosted_runtime=hosted_runtime,
        hosted_lifecycle_runtime=hosted_lifecycle_runtime,
        boot=boot,
        provision=provision,
        status=status,
    )
    cache = NodeSdkCache()
    sdk = NodeSdkClient(api_client=_ApiClient(host), cache=cache)

    configs = await sdk.discover_environment_configs(actor_id=actor_id, node_id=node_id)
    routes = await sdk.discover_service_api_dependency_routes(
        actor_id=actor_id,
        node_id=node_id,
        consumer_service_package_id=consumer_service_package_id,
        api_package_id=api_package_id,
    )
    hosted_runtimes = await sdk.describe_hosted_service_runtimes(
        actor_id=actor_id,
        node_id=node_id,
    )
    hosted_lifecycle_runtimes = await sdk.describe_hosted_runtimes(
        actor_id=actor_id,
        node_id=node_id,
        runtime_kind="interface",
    )
    boot_descriptor = await sdk.get_boot_environment_descriptor(
        actor_id=actor_id,
        node_id=node_id,
    )
    provision_response = await sdk.provision_environment(
        actor_id=actor_id,
        node_id=node_id,
        environment_config_id=environment_config_id,
        environment_title="Kernel Environment",
    )
    status_response = await sdk.get_environment_status(
        actor_id=actor_id,
        node_id=node_id,
        environment_id=environment_id,
    )

    assert configs == (config,)
    assert routes == (route,)
    assert hosted_runtimes == (hosted_runtime,)
    assert hosted_lifecycle_runtimes == (hosted_lifecycle_runtime,)
    assert boot_descriptor == boot
    assert provision_response.environment_id == environment_id
    assert status_response.environment_id == environment_id
    assert host.config_requests[0].node_id == node_id
    assert host.route_requests[0].consumer_service_package_id == (
        consumer_service_package_id
    )
    assert host.hosted_runtime_requests[0].node_id == node_id
    assert host.hosted_lifecycle_runtime_requests[0].runtime_kind == "interface"
    assert host.provision_requests[0].environment_title == "Kernel Environment"
    assert cache.environment_configs == (config,)
    assert cache.boot_environment_descriptor == boot
    assert cache.service_api_dependency_routes_by_query[
        NodeApiRoutesQuery(
            consumer_service_package_id=consumer_service_package_id,
            api_package_id=api_package_id,
        )
    ] == (route,)
    assert cache.hosted_service_runtimes == (hosted_runtime,)
    assert cache.hosted_runtimes == (hosted_lifecycle_runtime,)
    assert cache.provisioned_environments_by_id[environment_id] == provision
    assert cache.environment_status_by_id[environment_id] == status


@pytest.mark.asyncio
async def test_node_sdk_raises_on_failed_node_response() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    environment_id = uuid4()
    host = _HostApi(
        config=EnvironmentConfigDescriptor(
            environment_config_id=uuid4(),
            title="Kernel",
            canonical_language="aware",
            bundle_manifest_path="/tmp/kernel.environment.json",
        ),
        route=NodeServiceApiDependencyRouteDescriptor(
            consumer_service_package_id=uuid4(),
            consumer_service_package_name="consumer",
            provider_service_package_id=uuid4(),
            provider_service_package_name="provider",
            api_package_id=uuid4(),
            route_kind="local_socket",
            host_id="host",
            protocol_version="1",
            request_timeout_s=30.0,
        ),
        hosted_runtime=HostedServiceRuntimeStatus(
            host_id="aware_service_service",
            protocol_version="1",
            readiness_status="ready",
            is_ready=True,
            is_alive=True,
        ),
        hosted_lifecycle_runtime=HostedRuntimeLifecycleStatus(
            runtime_key="interface:/tmp/interface.json",
            runtime_kind="interface",
            status="ready",
            is_ready=True,
            is_alive=True,
        ),
        boot=BootEnvironmentDescriptor(
            kernel_environment_config_id=uuid4(),
            boot_environment_id=environment_id,
        ),
        provision=ProvisionEnvironmentResponse(
            actor_id=actor_id,
            node_id=node_id,
            status="failed",
            error="provision failed",
        ),
        status=GetEnvironmentStatusResponse(
            actor_id=actor_id,
            node_id=node_id,
            status="not_found",
            error="Environment is not registered on this node",
            environment_id=environment_id,
        ),
    )
    sdk = NodeSdkClient(api_client=_ApiClient(host))

    with pytest.raises(NodeSdkError, match="provision failed"):
        await sdk.provision_environment(
            actor_id=actor_id,
            node_id=node_id,
            environment_config_id=uuid4(),
        )

    with pytest.raises(NodeSdkError, match="not registered"):
        await sdk.get_environment_status(
            actor_id=actor_id,
            node_id=node_id,
            environment_id=environment_id,
        )


@pytest.mark.asyncio
async def test_node_sdk_restart_hosted_runtime_returns_failed_response() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    lifecycle_runtime = HostedRuntimeLifecycleStatus(
        runtime_key="interface:/tmp/interface.json",
        runtime_kind="interface",
        status="ready",
        is_ready=True,
        is_alive=True,
    )
    host = _HostApi(
        config=EnvironmentConfigDescriptor(
            environment_config_id=uuid4(),
            title="Kernel",
            canonical_language="aware",
            bundle_manifest_path="/tmp/kernel.environment.json",
        ),
        route=NodeServiceApiDependencyRouteDescriptor(
            consumer_service_package_id=uuid4(),
            consumer_service_package_name="consumer",
            provider_service_package_id=uuid4(),
            provider_service_package_name="provider",
            api_package_id=uuid4(),
            route_kind="local_socket",
            host_id="host",
            protocol_version="1",
            request_timeout_s=30.0,
        ),
        hosted_runtime=HostedServiceRuntimeStatus(
            host_id="aware_service_service",
            protocol_version="1",
            readiness_status="ready",
            is_ready=True,
            is_alive=True,
        ),
        hosted_lifecycle_runtime=lifecycle_runtime,
        boot=BootEnvironmentDescriptor(
            kernel_environment_config_id=uuid4(),
            boot_environment_id=uuid4(),
        ),
        provision=ProvisionEnvironmentResponse(status="ready"),
        status=GetEnvironmentStatusResponse(
            status="ready",
            environment_id=uuid4(),
        ),
    )
    sdk = NodeSdkClient(api_client=_ApiClient(host))

    with pytest.raises(NodeSdkError, match="restart disabled"):
        await sdk.restart_hosted_runtime(
            actor_id=actor_id,
            node_id=node_id,
            runtime_key=lifecycle_runtime.runtime_key,
            reason="stale",
            evidence={"source": "test"},
        )

    assert host.restart_hosted_runtime_requests[0].runtime_key == (
        lifecycle_runtime.runtime_key
    )
