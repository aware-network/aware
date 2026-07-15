from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import pytest

from aware_types import JsonObject
from aware_node.host_control_plane import (
    NodeHostBootEnvironmentReadResult,
    NodeHostControlPlaneService,
    NodeHostedEnvironmentState,
)
from aware_node_service_dto.node.host import BootEnvironmentDescriptor
from aware_node_service_dto.node.host import DiscoverApiRoutesRequest
from aware_node_service_dto.node.host import DiscoverApiRoutesResponse
from aware_node_service_dto.node.host import DescribeHostedRuntimesRequest
from aware_node_service_dto.node.host import DescribeHostedRuntimesResponse
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsRequest
from aware_node_service_dto.node.host import DiscoverEnvironmentConfigsResponse
from aware_node_service_dto.node.host import EnvironmentConfigDescriptor
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorRequest
from aware_node_service_dto.node.host import GetBootEnvironmentDescriptorResponse
from aware_node_service_dto.node.host import GetEnvironmentStatusRequest
from aware_node_service_dto.node.host import GetEnvironmentStatusResponse
from aware_node_service_dto.node.host import NodeServiceApiDependencyRouteDescriptor
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_node_service_dto.node.host import ProvisionEnvironmentResponse
from aware_node_service_dto.node.host import RestartHostedRuntimeRequest
from aware_node_service_dto.node.host import RestartHostedRuntimeResponse


@dataclass(slots=True)
class _FakePorts:
    configs: list[EnvironmentConfigDescriptor] = field(default_factory=list)
    service_api_dependency_routes: list[NodeServiceApiDependencyRouteDescriptor] = (
        field(default_factory=list)
    )
    hosted_runtime_lifecycle_statuses: list[dict[str, object]] = field(
        default_factory=list
    )
    boot_result: NodeHostBootEnvironmentReadResult = field(
        default_factory=lambda: NodeHostBootEnvironmentReadResult(
            response_status="not_found"
        )
    )
    provision_result: NodeHostedEnvironmentState | None = None
    status_result: NodeHostedEnvironmentState | None = None
    restart_result: dict[str, object] | None = None
    bootstrap_calls: int = 0
    provision_calls: list[ProvisionEnvironmentRequest] = field(default_factory=list)

    async def bootstrap_kernel_environment(self) -> None:
        self.bootstrap_calls += 1

    def discover_environment_config_descriptors(
        self,
    ) -> list[EnvironmentConfigDescriptor]:
        return list(self.configs)

    def discover_service_api_dependency_route_descriptors(
        self,
        *,
        consumer_service_package_id=None,
        api_package_id=None,
    ) -> list[NodeServiceApiDependencyRouteDescriptor]:
        routes = []
        for route in self.service_api_dependency_routes:
            if (
                consumer_service_package_id is not None
                and route.consumer_service_package_id != consumer_service_package_id
            ):
                continue
            if api_package_id is not None and route.api_package_id != api_package_id:
                continue
            routes.append(route)
        return routes

    def describe_hosted_service_runtime_statuses(self) -> list[dict[str, object]]:
        return []

    def describe_hosted_runtime_lifecycle_statuses(
        self,
        *,
        runtime_kind=None,
        runtime_key=None,
    ) -> list[dict[str, object]]:
        statuses = []
        for status in self.hosted_runtime_lifecycle_statuses:
            if runtime_kind is not None and status.get("runtime_kind") != runtime_kind:
                continue
            if runtime_key is not None and status.get("runtime_key") != runtime_key:
                continue
            statuses.append(status)
        return statuses

    async def restart_hosted_runtime(
        self,
        *,
        runtime_key,
        reason=None,
        evidence=None,
    ) -> dict[str, object]:
        if self.restart_result is not None:
            return self.restart_result
        matches = self.describe_hosted_runtime_lifecycle_statuses(
            runtime_key=runtime_key
        )
        return {
            "status": "failed",
            "error": "restart disabled in test",
            "runtime_kind": (
                matches[0].get("runtime_kind") if len(matches) == 1 else None
            ),
            "hosted_runtime": matches[0] if len(matches) == 1 else None,
            "operation_receipt": JsonObject(
                {
                    "runtime_key": runtime_key,
                    "reason": reason,
                    "evidence": dict(evidence or {}),
                    "match_count": len(matches),
                }
            ),
        }

    def read_boot_environment_descriptor(
        self, *, node_id
    ) -> NodeHostBootEnvironmentReadResult:
        return self.boot_result

    async def provision_environment(
        self,
        *,
        request: ProvisionEnvironmentRequest,
        node_id,
    ) -> NodeHostedEnvironmentState:
        self.provision_calls.append(request)
        assert self.provision_result is not None
        return self.provision_result

    def read_environment_status(self, *, environment_id):
        return self.status_result


@pytest.mark.asyncio
async def test_handle_discover_environment_configs_maps_descriptors() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    ports = _FakePorts(
        configs=[
            EnvironmentConfigDescriptor(
                environment_config_id=uuid4(),
                title="Kernel",
                canonical_language="aware",
                ocg_hash="ocg",
                opg_hashes=["opg-a"],
                outer_wrapper_kind="workspace",
                environment_handle="kernel",
                workspace_target_ref="kernel.default",
            )
        ]
    )
    service = NodeHostControlPlaneService(ports=ports)

    result = await service.handle_request(
        DiscoverEnvironmentConfigsRequest(actor_id=actor_id, node_id=node_id)
    )
    response = result.response
    assert isinstance(response, DiscoverEnvironmentConfigsResponse)

    assert result.request_status == "succeeded"
    assert result.request_error is None
    assert response.actor_id == actor_id
    assert response.node_id == node_id
    assert len(response.configs) == 1
    assert response.configs[0].title == "Kernel"


@pytest.mark.asyncio
async def test_handle_discover_service_api_dependency_routes_filters_descriptors() -> (
    None
):
    actor_id = uuid4()
    node_id = uuid4()
    consumer_id = uuid4()
    provider_id = uuid4()
    api_id = uuid4()
    ignored_api_id = uuid4()
    ports = _FakePorts(
        service_api_dependency_routes=[
            NodeServiceApiDependencyRouteDescriptor(
                consumer_service_package_id=consumer_id,
                consumer_service_package_name="aware-environment-service",
                provider_service_package_id=provider_id,
                provider_service_package_name="aware-meta-service",
                api_package_id=api_id,
                api_package_name="meta-service-api",
                route_kind="local_service_host_ipc",
                host_id="meta-host",
                host_version="1",
                protocol_version="service-host-ipc.v1",
                socket_path="/tmp/meta.sock",
                request_timeout_s=30.0,
                service_names=["aware_meta"],
                endpoint_refs_by_service=JsonObject(
                    {"aware_meta": ["meta.graph.resolve"]}
                ),
                stream_endpoint_refs_by_service=JsonObject(
                    {"aware_meta": ["meta.commit.subscribe"]}
                ),
            ),
            NodeServiceApiDependencyRouteDescriptor(
                consumer_service_package_id=consumer_id,
                consumer_service_package_name="aware-environment-service",
                provider_service_package_id=uuid4(),
                provider_service_package_name="ignored-service",
                api_package_id=ignored_api_id,
                api_package_name="ignored-api",
                route_kind="local_service_host_ipc",
                host_id="ignored-host",
                protocol_version="service-host-ipc.v1",
                socket_path="/tmp/ignored.sock",
                request_timeout_s=30.0,
            ),
        ]
    )
    service = NodeHostControlPlaneService(ports=ports)

    result = await service.handle_request(
        DiscoverApiRoutesRequest(
            actor_id=actor_id,
            node_id=node_id,
            consumer_service_package_id=consumer_id,
            api_package_id=api_id,
        )
    )
    response = result.response
    assert isinstance(response, DiscoverApiRoutesResponse)

    assert result.request_status == "succeeded"
    assert response.status == "succeeded"
    assert response.actor_id == actor_id
    assert response.node_id == node_id
    assert len(response.routes) == 1
    route = response.routes[0]
    assert route.provider_service_package_id == provider_id
    assert route.api_package_name == "meta-service-api"
    assert route.endpoint_refs_by_service == {"aware_meta": ["meta.graph.resolve"]}


@pytest.mark.asyncio
async def test_handle_describe_hosted_runtimes_filters_by_open_kind() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    ports = _FakePorts(
        hosted_runtime_lifecycle_statuses=[
            {
                "runtime_key": "service:/tmp/service.toml",
                "runtime_kind": "service",
                "status": "ready",
                "is_ready": True,
                "is_alive": True,
            },
            {
                "runtime_key": "interface:/tmp/interface.json",
                "runtime_kind": "interface",
                "status": "ready",
                "is_ready": True,
                "is_alive": True,
            },
        ]
    )
    service = NodeHostControlPlaneService(ports=ports)

    result = await service.handle_request(
        DescribeHostedRuntimesRequest(
            actor_id=actor_id,
            node_id=node_id,
            runtime_kind="interface",
        )
    )
    response = result.response
    assert isinstance(response, DescribeHostedRuntimesResponse)

    assert response.status == "succeeded"
    assert response.actor_id == actor_id
    assert response.node_id == node_id
    assert len(response.hosted_runtimes) == 1
    assert response.hosted_runtimes[0].runtime_kind == "interface"
    assert response.hosted_runtimes[0].runtime_key == "interface:/tmp/interface.json"


@pytest.mark.asyncio
async def test_handle_restart_hosted_runtime_returns_structured_failure() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    runtime_key = "interface:/tmp/interface.json"
    ports = _FakePorts(
        hosted_runtime_lifecycle_statuses=[
            {
                "runtime_key": runtime_key,
                "runtime_kind": "interface",
                "status": "ready",
                "is_ready": True,
                "is_alive": True,
            }
        ]
    )
    service = NodeHostControlPlaneService(ports=ports)

    result = await service.handle_request(
        RestartHostedRuntimeRequest(
            actor_id=actor_id,
            node_id=node_id,
            runtime_key=runtime_key,
            reason="stale host",
            evidence=JsonObject({"source": "test"}),
        )
    )
    response = result.response
    assert isinstance(response, RestartHostedRuntimeResponse)

    assert response.status == "failed"
    assert response.error == "restart disabled in test"
    assert response.runtime_key == runtime_key
    assert response.runtime_kind == "interface"
    assert response.hosted_runtime is not None
    assert response.hosted_runtime.runtime_kind == "interface"
    assert response.operation_receipt is not None
    assert response.operation_receipt["evidence"]["source"] == "test"


@pytest.mark.asyncio
async def test_handle_restart_hosted_runtime_maps_success() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    runtime_key = "interface:/tmp/interface.json"
    ports = _FakePorts(
        restart_result={
            "status": "succeeded",
            "error": None,
            "runtime_kind": "interface",
            "hosted_runtime": {
                "runtime_key": runtime_key,
                "runtime_kind": "interface",
                "status": "ready",
                "is_ready": True,
                "is_alive": True,
                "pid": 9922,
            },
            "operation_receipt": JsonObject(
                {
                    "operation": "restart_hosted_runtime",
                    "status": "succeeded",
                    "runtime_key": runtime_key,
                    "previous_pid": 9911,
                    "new_pid": 9922,
                }
            ),
        }
    )
    service = NodeHostControlPlaneService(ports=ports)

    result = await service.handle_request(
        RestartHostedRuntimeRequest(
            actor_id=actor_id,
            node_id=node_id,
            runtime_key=runtime_key,
            reason="stale host",
        )
    )
    response = result.response
    assert isinstance(response, RestartHostedRuntimeResponse)

    assert response.status == "succeeded"
    assert response.error is None
    assert response.runtime_key == runtime_key
    assert response.runtime_kind == "interface"
    assert response.hosted_runtime is not None
    assert response.hosted_runtime.pid == 9922
    assert response.operation_receipt is not None
    assert response.operation_receipt["new_pid"] == 9922


@pytest.mark.asyncio
async def test_handle_get_boot_environment_descriptor_bootstraps_and_preserves_request_status() -> (
    None
):
    actor_id = uuid4()
    node_id = uuid4()
    descriptor = BootEnvironmentDescriptor(
        kernel_environment_config_id=uuid4(),
        boot_environment_id=uuid4(),
        kernel_environment_config_title="Kernel",
        boot_environment_title="Boot Kernel",
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        opg_hashes=["opg-a"],
    )
    ports = _FakePorts(
        boot_result=NodeHostBootEnvironmentReadResult(
            response_status="failed",
            response_error="Environment boot failed",
            descriptor=descriptor,
            request_status="succeeded",
            request_error=None,
        )
    )
    service = NodeHostControlPlaneService(ports=ports)

    result = await service.handle_request(
        GetBootEnvironmentDescriptorRequest(actor_id=actor_id, node_id=node_id)
    )
    response = result.response
    assert isinstance(response, GetBootEnvironmentDescriptorResponse)

    assert ports.bootstrap_calls == 1
    assert result.request_status == "succeeded"
    assert response.actor_id == actor_id
    assert response.node_id == node_id
    assert response.status == "failed"
    assert response.error == "Environment boot failed"
    assert response.descriptor == descriptor


@pytest.mark.asyncio
async def test_handle_provision_environment_maps_runtime_state() -> None:
    actor_id = uuid4()
    node_id = uuid4()
    environment_id = uuid4()
    environment_config_id = uuid4()
    ports = _FakePorts(
        provision_result=NodeHostedEnvironmentState(
            environment_id=environment_id,
            status="ready",
            error=None,
            environment_config_id=environment_config_id,
            environment_config_title="Kernel",
            environment_title="Hosted Kernel",
            environment_endpoint="http://127.0.0.1:8123",
            runtime_artifact_refs_json='{"artifact_refs":[]}',
            service_api_provider_refs_json='{"provider_refs":[]}',
            ocg_hash="ocg",
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            opg_hashes=("opg-a", "opg-b"),
            outer_wrapper_kind="workspace",
            environment_handle="kernel",
            workspace_id="workspace-123",
            workspace_package_id="workspace-package-123",
            workspace_build_invocation_id="build-123",
            workspace_target_ref="environment:kernel",
            readiness_receipt=JsonObject(
                {
                    "status": "ready",
                    "environment_id": str(environment_id),
                    "graph": {"status": "ready"},
                }
            ),
            network_node_environment_receipt=JsonObject(
                {
                    "status": "succeeded",
                    "node_id": str(node_id),
                    "environment_id": str(environment_id),
                    "commit_id": str(uuid4()),
                }
            ),
        )
    )
    service = NodeHostControlPlaneService(ports=ports)
    request = ProvisionEnvironmentRequest(
        actor_id=actor_id,
        node_id=node_id,
        environment_config_id=environment_config_id,
        environment_title="Hosted Kernel",
    )

    result = await service.handle_request(request)
    response = result.response
    assert isinstance(response, ProvisionEnvironmentResponse)

    assert len(ports.provision_calls) == 1
    assert response.actor_id == actor_id
    assert response.node_id == node_id
    assert response.environment_id == environment_id
    assert response.environment_config_id == environment_config_id
    assert response.environment_endpoint == "http://127.0.0.1:8123"
    assert response.opg_hashes == ["opg-a", "opg-b"]
    assert response.provisioning_receipt is not None
    assert response.provisioning_receipt.status == "ready"
    assert response.provisioning_receipt.actor_id == actor_id
    assert response.provisioning_receipt.node_id == node_id
    assert response.provisioning_receipt.environment_id == environment_id
    assert response.provisioning_receipt.workspace_target_ref == "environment:kernel"
    assert response.provisioning_receipt.readiness_receipt is not None
    assert response.provisioning_receipt.readiness_receipt["graph"]["status"] == "ready"
    network_receipt = response.provisioning_receipt.network_node_environment_receipt
    assert network_receipt is not None
    assert network_receipt["status"] == "succeeded"
    assert network_receipt["node_id"] == str(node_id)


@pytest.mark.asyncio
async def test_handle_get_environment_status_returns_not_found_without_runtime_record() -> (
    None
):
    actor_id = uuid4()
    node_id = uuid4()
    environment_id = uuid4()
    service = NodeHostControlPlaneService(ports=_FakePorts())

    result = await service.handle_request(
        GetEnvironmentStatusRequest(
            actor_id=actor_id,
            node_id=node_id,
            environment_id=environment_id,
        )
    )
    response = result.response
    assert isinstance(response, GetEnvironmentStatusResponse)

    assert result.request_status == "succeeded"
    assert response.actor_id == actor_id
    assert response.node_id == node_id
    assert response.environment_id == environment_id
    assert response.status == "not_found"
    assert response.error == "Environment is not registered on this node"
