from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import (
    EnvironmentReadinessClient,
    EnvironmentReadinessContext,
    EnvironmentReadinessError,
)
from aware_environment_service_dto.environment.environment import (
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    DescribeEnvironmentStatusRequest,
    DescribeEnvironmentStatusResponse,
    EnsureReadyRequest,
    EnsureReadyResponse,
    EnvironmentReadinessGraphReceipt,
    EnvironmentReadinessPersistenceReceipt,
    EnvironmentReadinessReceipt,
    EnvironmentReadinessRouteReceipt,
    GetLaneHeadRequest,
    GetLaneHeadResponse,
    GetObjectInstanceGraphCommitRequest,
    GetObjectInstanceGraphCommitResponse,
)


class _RecordingServiceRoutesClient:
    def __init__(self) -> None:
        self.requests: list[ConfigureServiceApiDependencyRoutesRequest] = []

    async def configure_service_api_dependency_routes(
        self,
        request: ConfigureServiceApiDependencyRoutesRequest,
    ) -> ConfigureServiceApiDependencyRoutesResponse:
        self.requests.append(request)
        return ConfigureServiceApiDependencyRoutesResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            route_count=len(request.routes),
            route_consumers_started=True,
        )


class _RecordingReadyClient:
    def __init__(self, *, status: str = "ready") -> None:
        self.status = status
        self.requests: list[EnsureReadyRequest] = []
        self.domain_commit_id = uuid4()
        self.oig_commit_id = uuid4()
        self.branch_id = uuid4()
        self.ocg_id = uuid4()
        self.oig_id = uuid4()
        self.root_object_id = uuid4()

    async def ensure_ready(self, request: EnsureReadyRequest) -> EnsureReadyResponse:
        self.requests.append(request)
        error = None if self.status == "ready" else "readiness unavailable"
        return EnsureReadyResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=self.branch_id,
            projection_hash="environment.projection",
            status=self.status,
            error=error,
            ocg_id=self.ocg_id,
            readiness_receipt=EnvironmentReadinessReceipt(
                status=self.status,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=self.branch_id,
                projection_hash="environment.projection",
                ocg_id=self.ocg_id,
                graph=EnvironmentReadinessGraphReceipt(
                    status="ready",
                    branch_id=self.branch_id,
                    projection_hash="environment.projection",
                    domain_commit_id=self.domain_commit_id,
                    object_instance_graph_commit_id=self.oig_commit_id,
                    object_instance_graph_id=self.oig_id,
                    root_object_id=self.root_object_id,
                    graph_hash_post="graph-post",
                ),
                persistence=EnvironmentReadinessPersistenceReceipt(
                    status="succeeded",
                    backend="postgres",
                    database_url_ref="env:DATABASE_URL",
                    migrated=True,
                    step_count=2,
                ),
                meta_route=EnvironmentReadinessRouteReceipt(
                    api_package_name="meta-service-api",
                    provider_service_package_name="aware-meta-service",
                    route_kind="local_service_host_ipc",
                    host_id="aware-meta-service-host",
                ),
            ),
        )


class _RecordingLaneHeadClient:
    def __init__(self) -> None:
        self.requests: list[GetLaneHeadRequest] = []
        self.commit_id = uuid4()
        self.oig_id = uuid4()
        self.root_object_id = uuid4()

    async def get_lane_head(
        self,
        request: GetLaneHeadRequest,
    ) -> GetLaneHeadResponse:
        self.requests.append(request)
        return GetLaneHeadResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            commit_id=self.commit_id,
            graph_hash_post="head-post",
            object_instance_graph_id=self.oig_id,
            root_object_id=self.root_object_id,
            head_version=1,
        )


class _RecordingCommitClient:
    def __init__(self) -> None:
        self.requests: list[GetObjectInstanceGraphCommitRequest] = []
        self.oig_commit_id = uuid4()

    async def get_object_instance_graph_commit(
        self,
        request: GetObjectInstanceGraphCommitRequest,
    ) -> GetObjectInstanceGraphCommitResponse:
        self.requests.append(request)
        return GetObjectInstanceGraphCommitResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            commit_id=request.commit_id,
            object_instance_graph_commit_id=self.oig_commit_id,
            commit=cast(
                Any,
                {
                    "id": str(request.commit_id),
                    "object_instance_graph_commit_id": str(self.oig_commit_id),
                },
            ),
        )


class _RecordingStatusClient:
    def __init__(self) -> None:
        self.requests: list[DescribeEnvironmentStatusRequest] = []

    async def describe_environment_status(
        self,
        request: DescribeEnvironmentStatusRequest,
    ) -> DescribeEnvironmentStatusResponse:
        self.requests.append(request)
        return DescribeEnvironmentStatusResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            status_version="environment.status.v1",
            blocks=[],
            refusals=[],
        )


class _RecordingEnvironmentApiClient:
    def __init__(self, *, ready_status: str = "ready") -> None:
        self.service_routes = _RecordingServiceRoutesClient()
        self.ready = _RecordingReadyClient(status=ready_status)
        self.lane_head = _RecordingLaneHeadClient()
        self.object_instance_graph_commit = _RecordingCommitClient()
        self.status = _RecordingStatusClient()


class _RecordingGeneratedApiClient:
    def __init__(self, *, ready_status: str = "ready") -> None:
        self.environment = _RecordingEnvironmentApiClient(
            ready_status=ready_status,
        )


def _context() -> EnvironmentReadinessContext:
    return EnvironmentReadinessContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_environment_readiness_client_configures_routes_and_ensures_ready() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentReadinessClient(api_client=api_client, context=context)

    route_receipt = await client.configure_service_api_dependency_routes(
        [
            {
                "api_package_name": "ontology-service-api",
                "route_kind": "remote_node_api_endpoint",
            }
        ]
    )
    ready_receipt = await client.ensure_ready()

    assert route_receipt.route_count == 1
    route_request = api_client.environment.service_routes.requests[0]
    assert route_request.actor_id == context.actor_id
    assert route_request.environment_id == context.environment_id
    assert route_request.routes[0]["api_package_name"] == "ontology-service-api"
    ready_request = api_client.environment.ready.requests[0]
    assert ready_request.environment_id == context.environment_id
    assert ready_receipt.status == "ready"
    assert ready_receipt.persistence_status == "succeeded"
    assert ready_receipt.persistence_backend == "postgres"
    assert ready_receipt.domain_commit_id == api_client.environment.ready.domain_commit_id
    assert (
        ready_receipt.object_instance_graph_commit_id
        == api_client.environment.ready.oig_commit_id
    )


@pytest.mark.asyncio
async def test_environment_readiness_client_reads_lane_head_and_commit() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentReadinessClient(api_client=api_client, context=context)
    ready_receipt = await client.ensure_ready()
    assert ready_receipt.branch_id is not None
    assert ready_receipt.projection_hash is not None
    read_client = EnvironmentReadinessClient(
        api_client=api_client,
        context=context.with_ready_receipt(ready_receipt),
    )

    lane = await read_client.get_lane_head()
    commit = await read_client.get_object_instance_graph_commit(lane.commit_id)
    status = await read_client.describe_environment_status(
        include_blocks=("runtime",),
        strict_commit_truth=True,
    )

    lane_request = api_client.environment.lane_head.requests[0]
    assert lane_request.branch_id == ready_receipt.branch_id
    assert lane_request.projection_hash == ready_receipt.projection_hash
    commit_request = api_client.environment.object_instance_graph_commit.requests[0]
    assert commit_request.commit_id == lane.commit_id
    assert commit.commit is not None
    assert commit.commit["id"] == str(lane.commit_id)
    status_request = api_client.environment.status.requests[0]
    assert status_request.include_blocks == ["runtime"]
    assert status_request.strict_commit_truth is True
    assert status.status_version == "environment.status.v1"


@pytest.mark.asyncio
async def test_environment_readiness_client_raises_on_failed_ready() -> None:
    api_client = _RecordingGeneratedApiClient(ready_status="failed")
    client = EnvironmentReadinessClient(api_client=api_client, context=_context())

    with pytest.raises(EnvironmentReadinessError, match="readiness unavailable"):
        await client.ensure_ready()


def test_environment_readiness_context_from_object_requires_environment_id() -> None:
    context = EnvironmentReadinessContext.from_object(
        type(
            "Context",
            (),
            {
                "environment_id": str(UUID("11111111-1111-1111-1111-111111111111")),
                "projection_hash": "environment.projection",
            },
        )()
    )

    assert context.environment_id == UUID("11111111-1111-1111-1111-111111111111")
    assert context.projection_hash == "environment.projection"

    with pytest.raises(ValueError, match="environment_id"):
        EnvironmentReadinessContext.from_object(object())
