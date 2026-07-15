from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID

from aware_types import JsonArray
from aware_environment_service_dto.environment.environment import (
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    DescribeEnvironmentStatusRequest,
    DescribeEnvironmentStatusResponse,
    EnsureReadyRequest,
    EnsureReadyResponse,
    GetLaneHeadRequest,
    GetLaneHeadResponse,
    GetObjectInstanceGraphCommitRequest,
    GetObjectInstanceGraphCommitResponse,
)


class EnvironmentReadinessError(RuntimeError):
    """Raised when the Environment readiness SDK receives a failed response."""


class _EnvironmentReadyCapabilityClient(Protocol):
    async def ensure_ready(
        self,
        request: EnsureReadyRequest,
    ) -> EnsureReadyResponse: ...


class _EnvironmentLaneHeadCapabilityClient(Protocol):
    async def get_lane_head(
        self,
        request: GetLaneHeadRequest,
    ) -> GetLaneHeadResponse: ...


class _EnvironmentObjectInstanceGraphCommitCapabilityClient(Protocol):
    async def get_object_instance_graph_commit(
        self,
        request: GetObjectInstanceGraphCommitRequest,
    ) -> GetObjectInstanceGraphCommitResponse: ...


class _EnvironmentServiceRoutesCapabilityClient(Protocol):
    async def configure_service_api_dependency_routes(
        self,
        request: ConfigureServiceApiDependencyRoutesRequest,
    ) -> ConfigureServiceApiDependencyRoutesResponse: ...


class _EnvironmentStatusCapabilityClient(Protocol):
    async def describe_environment_status(
        self,
        request: DescribeEnvironmentStatusRequest,
    ) -> DescribeEnvironmentStatusResponse: ...


class _EnvironmentApiClient(Protocol):
    @property
    def ready(self) -> _EnvironmentReadyCapabilityClient: ...

    @property
    def lane_head(self) -> _EnvironmentLaneHeadCapabilityClient: ...

    @property
    def object_instance_graph_commit(
        self,
    ) -> _EnvironmentObjectInstanceGraphCommitCapabilityClient: ...

    @property
    def service_routes(self) -> _EnvironmentServiceRoutesCapabilityClient: ...

    @property
    def status(self) -> _EnvironmentStatusCapabilityClient: ...


class EnvironmentReadinessGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentReadinessContext:
    environment_id: UUID
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None

    @classmethod
    def from_object(cls, context: object) -> "EnvironmentReadinessContext":
        return cls(
            actor_id=_optional_uuid(getattr(context, "actor_id", None)),
            environment_id=_required_uuid(
                getattr(context, "environment_id", None),
                field_name="environment_id",
            ),
            process_id=_optional_uuid(getattr(context, "process_id", None)),
            thread_id=_optional_uuid(getattr(context, "thread_id", None)),
            branch_id=_optional_uuid(getattr(context, "branch_id", None)),
            projection_hash=_optional_text(getattr(context, "projection_hash", None)),
        )

    def with_ready_receipt(
        self,
        receipt: "EnvironmentReadyReceipt",
    ) -> "EnvironmentReadinessContext":
        return EnvironmentReadinessContext(
            actor_id=receipt.actor_id or self.actor_id,
            environment_id=receipt.environment_id,
            process_id=receipt.process_id or self.process_id,
            thread_id=receipt.thread_id or self.thread_id,
            branch_id=receipt.branch_id or self.branch_id,
            projection_hash=receipt.projection_hash or self.projection_hash,
        )


@dataclass(frozen=True, slots=True)
class EnvironmentRouteConfigurationReceipt:
    status: str
    error: str | None
    route_count: int
    route_consumers_started: bool
    raw_response: ConfigureServiceApiDependencyRoutesResponse


@dataclass(frozen=True, slots=True)
class EnvironmentReadyReceipt:
    status: str
    error: str | None
    actor_id: UUID | None
    environment_id: UUID
    process_id: UUID | None
    thread_id: UUID | None
    branch_id: UUID | None
    projection_hash: str | None
    ocg_id: UUID | None
    graph_status: str | None
    persistence_status: str | None
    persistence_backend: str | None
    meta_route_api_package_name: str | None
    domain_commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None
    object_instance_graph_id: UUID | None
    root_object_id: UUID | None
    graph_hash_post: str | None
    raw_response: EnsureReadyResponse


@dataclass(frozen=True, slots=True)
class EnvironmentLaneHeadReceipt:
    status: str
    error: str | None
    commit_id: UUID | None
    graph_hash_post: str | None
    object_instance_graph_id: UUID | None
    root_object_id: UUID | None
    head_version: int | None
    raw_response: GetLaneHeadResponse


@dataclass(frozen=True, slots=True)
class EnvironmentObjectInstanceGraphCommitReceipt:
    status: str
    error: str | None
    commit_id: UUID | None
    object_instance_graph_commit_id: UUID
    commit: Mapping[str, object] | None
    raw_response: GetObjectInstanceGraphCommitResponse


@dataclass(frozen=True, slots=True)
class EnvironmentStatusReceipt:
    status: str
    error: str | None
    status_version: str
    block_count: int
    refusal_count: int
    raw_response: DescribeEnvironmentStatusResponse


@dataclass(frozen=True, slots=True)
class EnvironmentReadinessClient:
    api_client: EnvironmentReadinessGeneratedApiClient
    context: EnvironmentReadinessContext

    async def configure_service_api_dependency_routes(
        self,
        routes: Sequence[Mapping[str, object]],
    ) -> EnvironmentRouteConfigurationReceipt:
        response = (
            await self.api_client.environment.service_routes.configure_service_api_dependency_routes(
                ConfigureServiceApiDependencyRoutesRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    process_id=self.context.process_id,
                    thread_id=self.context.thread_id,
                    branch_id=self.context.branch_id,
                    projection_hash=self.context.projection_hash,
                    routes=cast(JsonArray, [dict(route) for route in routes]),
                )
            )
        )
        receipt = EnvironmentRouteConfigurationReceipt(
            status=response.status,
            error=response.error,
            route_count=response.route_count,
            route_consumers_started=response.route_consumers_started,
            raw_response=response,
        )
        if _status(response.status) != "succeeded":
            raise EnvironmentReadinessError(
                "Environment route configuration failed: "
                f"{response.error or response.status}"
            )
        return receipt

    async def ensure_ready(self) -> EnvironmentReadyReceipt:
        response = await self.api_client.environment.ready.ensure_ready(
            EnsureReadyRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                process_id=self.context.process_id,
                thread_id=self.context.thread_id,
                branch_id=self.context.branch_id,
                projection_hash=self.context.projection_hash,
            )
        )
        receipt = _ready_receipt_from_response(response)
        if _status(response.status) != "ready":
            raise EnvironmentReadinessError(
                "Environment readiness failed: " f"{response.error or response.status}"
            )
        return receipt

    async def get_lane_head(
        self,
        *,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> EnvironmentLaneHeadReceipt:
        request_branch_id = branch_id or self.context.branch_id
        request_projection_hash = projection_hash or self.context.projection_hash
        response = await self.api_client.environment.lane_head.get_lane_head(
            GetLaneHeadRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                process_id=self.context.process_id,
                thread_id=self.context.thread_id,
                branch_id=request_branch_id,
                projection_hash=request_projection_hash,
            )
        )
        receipt = EnvironmentLaneHeadReceipt(
            status=response.status,
            error=response.error,
            commit_id=response.commit_id,
            graph_hash_post=response.graph_hash_post,
            object_instance_graph_id=response.object_instance_graph_id,
            root_object_id=response.root_object_id,
            head_version=response.head_version,
            raw_response=response,
        )
        if _status(response.status) != "succeeded":
            raise EnvironmentReadinessError(
                "Environment lane-head read failed: "
                f"{response.error or response.status}"
            )
        return receipt

    async def get_object_instance_graph_commit(
        self,
        commit_id: UUID,
    ) -> EnvironmentObjectInstanceGraphCommitReceipt:
        response = (
            await self.api_client.environment.object_instance_graph_commit.get_object_instance_graph_commit(
                GetObjectInstanceGraphCommitRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    process_id=self.context.process_id,
                    thread_id=self.context.thread_id,
                    branch_id=self.context.branch_id,
                    projection_hash=self.context.projection_hash,
                    commit_id=commit_id,
                )
            )
        )
        receipt = EnvironmentObjectInstanceGraphCommitReceipt(
            status=response.status,
            error=response.error,
            commit_id=response.commit_id,
            object_instance_graph_commit_id=response.object_instance_graph_commit_id,
            commit=dict(response.commit) if response.commit is not None else None,
            raw_response=response,
        )
        if _status(response.status) != "succeeded":
            raise EnvironmentReadinessError(
                "Environment OIG commit read failed: "
                f"{response.error or response.status}"
            )
        return receipt

    async def describe_environment_status(
        self,
        *,
        include_blocks: Sequence[str] = (),
        strict_commit_truth: bool = False,
    ) -> EnvironmentStatusReceipt:
        response = await self.api_client.environment.status.describe_environment_status(
            DescribeEnvironmentStatusRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                process_id=self.context.process_id,
                thread_id=self.context.thread_id,
                branch_id=self.context.branch_id,
                projection_hash=self.context.projection_hash,
                include_blocks=list(include_blocks),
                strict_commit_truth=strict_commit_truth,
            )
        )
        receipt = EnvironmentStatusReceipt(
            status=response.status,
            error=response.error,
            status_version=response.status_version,
            block_count=len(response.blocks),
            refusal_count=len(response.refusals),
            raw_response=response,
        )
        if _status(response.status) not in {"succeeded", "ready"}:
            raise EnvironmentReadinessError(
                "Environment status read failed: "
                f"{response.error or response.status}"
            )
        return receipt


def _ready_receipt_from_response(
    response: EnsureReadyResponse,
) -> EnvironmentReadyReceipt:
    readiness = response.readiness_receipt
    graph = readiness.graph if readiness is not None else None
    persistence = readiness.persistence if readiness is not None else None
    meta_route = readiness.meta_route if readiness is not None else None
    return EnvironmentReadyReceipt(
        status=response.status,
        error=response.error,
        actor_id=response.actor_id or (readiness.actor_id if readiness else None),
        environment_id=response.environment_id,
        process_id=response.process_id or (readiness.process_id if readiness else None),
        thread_id=response.thread_id or (readiness.thread_id if readiness else None),
        branch_id=(
            response.branch_id
            or (readiness.branch_id if readiness else None)
            or (graph.branch_id if graph is not None else None)
        ),
        projection_hash=(
            response.projection_hash
            or (readiness.projection_hash if readiness else None)
            or (graph.projection_hash if graph is not None else None)
        ),
        ocg_id=response.ocg_id or (readiness.ocg_id if readiness else None),
        graph_status=graph.status if graph is not None else None,
        persistence_status=persistence.status if persistence is not None else None,
        persistence_backend=persistence.backend if persistence is not None else None,
        meta_route_api_package_name=(
            meta_route.api_package_name if meta_route is not None else None
        ),
        domain_commit_id=graph.domain_commit_id if graph is not None else None,
        object_instance_graph_commit_id=(
            graph.object_instance_graph_commit_id if graph is not None else None
        ),
        object_instance_graph_id=(
            graph.object_instance_graph_id if graph is not None else None
        ),
        root_object_id=graph.root_object_id if graph is not None else None,
        graph_hash_post=graph.graph_hash_post if graph is not None else None,
        raw_response=response,
    )


def _status(value: str | None) -> str:
    return (value or "").strip().lower()


def _required_uuid(value: object, *, field_name: str) -> UUID:
    resolved = _optional_uuid(value)
    if resolved is None:
        raise ValueError(f"{field_name} is required.")
    return resolved


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = str(value).strip()
    return UUID(text) if text else None


def _optional_text(value: object) -> str | None:
    text = "" if value is None else str(value).strip()
    return text or None


__all__ = [
    "EnvironmentLaneHeadReceipt",
    "EnvironmentObjectInstanceGraphCommitReceipt",
    "EnvironmentReadinessClient",
    "EnvironmentReadinessContext",
    "EnvironmentReadinessError",
    "EnvironmentReadinessGeneratedApiClient",
    "EnvironmentReadyReceipt",
    "EnvironmentRouteConfigurationReceipt",
    "EnvironmentStatusReceipt",
]
