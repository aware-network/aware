from __future__ import annotations

from collections.abc import Mapping
from typing import cast
from uuid import UUID

from aware_environment_service_dto.environment.environment import EnvironmentOperationContext
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperation,
)
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperationRequest,
)

from aware_service_runtime.contracts import (
    ServiceOperationHandler,
    ServiceOperationContext,
    ServiceOperationInvocation,
    ServiceOperationInvocationHandler,
    ServiceOperationRequest,
    ServiceOperationResponse,
    ServiceOperationResult,
    ServiceOperationTransport,
)


EnvironmentServiceInvocation = ServiceOperationInvocation
EnvironmentServiceInvocationHandler = ServiceOperationInvocationHandler
EnvironmentServiceResult = ServiceOperationResult
EnvironmentServiceTransport = ServiceOperationTransport

__all__ = [
    "EnvironmentInvocationHandlerAdapter",
    "EnvironmentServiceInvocation",
    "EnvironmentServiceInvocationHandler",
    "EnvironmentServiceResult",
    "EnvironmentServiceTransport",
    "build_environment_operation_context",
    "build_environment_service_operation_request",
    "build_service_operation_context",
    "build_service_operation_invocation",
    "build_service_operation_request",
    "build_service_operation_result_from_response",
    "coerce_environment_service_operation",
]


def build_environment_operation_context(
    *,
    env_req: EnvironmentServiceOperationRequest,
) -> EnvironmentOperationContext:
    return EnvironmentOperationContext(
        actor_id=env_req.actor_id,
        environment_id=env_req.environment_id,
        process_id=env_req.process_id,
        thread_id=env_req.thread_id,
        branch_id=env_req.branch_id,
        projection_hash=env_req.projection_hash,
    )


def build_service_operation_context(
    *,
    env_req: EnvironmentServiceOperationRequest,
) -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=env_req.actor_id,
        branch_id=_require_uuid(env_req.branch_id, field_name="branch_id"),
        projection_hash=_require_projection_hash(env_req.projection_hash),
    )


def build_service_operation_request(
    *,
    env_req: EnvironmentServiceOperationRequest,
    stream_target_id: UUID | None = None,
    stream_correlation_id: UUID | None = None,
    network_request_id: UUID | None = None,
) -> ServiceOperationRequest:
    return ServiceOperationRequest(
        context=build_service_operation_context(env_req=env_req),
        service=env_req.service_operation.service,
        operation=env_req.service_operation.model_dump(mode="json"),
        stream_target_id=stream_target_id,
        stream_correlation_id=stream_correlation_id,
        network_request_id=network_request_id,
    )


def build_service_operation_invocation(
    *,
    env_req: EnvironmentServiceOperationRequest,
    stream_target_id: UUID | None = None,
    stream_correlation_id: UUID | None = None,
    network_request_id: UUID | None = None,
) -> ServiceOperationInvocation:
    return ServiceOperationInvocation(
        env_req=env_req,
        stream_target_id=stream_target_id,
        stream_correlation_id=stream_correlation_id,
        network_request_id=network_request_id,
    )


def build_environment_service_operation_request(
    *,
    request: ServiceOperationRequest,
    environment_context: EnvironmentOperationContext | None = None,
) -> EnvironmentServiceOperationRequest:
    if environment_context is None:
        raise RuntimeError(
            "Cannot derive EnvironmentServiceOperationRequest from native "
            "ServiceOperationRequest alone. Environment orchestration context "
            "must be passed explicitly by the Environment-owned caller."
        )
    service_operation = coerce_environment_service_operation(
        payload=request.operation,
    )
    if service_operation is None:
        raise TypeError(
            "Service request operation is not an EnvironmentServiceOperation. "
            "Use the environment adapter only with Environment-compatible requests."
        )
    return EnvironmentServiceOperationRequest(
        operation="service_operation",
        actor_id=environment_context.actor_id or request.context.actor_id,
        environment_id=environment_context.environment_id,
        process_id=environment_context.process_id,
        thread_id=environment_context.thread_id,
        branch_id=environment_context.branch_id or request.context.branch_id,
        projection_hash=(
            environment_context.projection_hash or request.context.projection_hash
        ),
        service_operation=service_operation,
    )


def coerce_environment_service_operation(
    *,
    payload: object | None,
) -> EnvironmentServiceOperation | None:
    if payload is None:
        return None
    if isinstance(payload, EnvironmentServiceOperation):
        return payload
    if isinstance(payload, Mapping):
        data = dict(payload)
        if set(data).issubset({"service", "operation"}):
            return EnvironmentServiceOperation.model_validate(data)
        return EnvironmentServiceOperation.parse(data)
    raise TypeError(
        "Service response payload is not an EnvironmentServiceOperation. "
        "Use an environment adapter only with Environment-compatible responses."
    )


def build_service_operation_result_from_response(
    *,
    response: ServiceOperationResponse,
) -> ServiceOperationResult:
    response_service_operation = coerce_environment_service_operation(
        payload=response.response_payload,
    )
    return ServiceOperationResult(
        status=response.status,
        error=response.error,
        response_payload=response.response_payload,
        response_service_operation=response_service_operation,
        stream_lifecycle=response.stream_lifecycle,
    )


class EnvironmentInvocationHandlerAdapter(ServiceOperationHandler):
    """Adapt legacy Environment-hosted service plugins into native request handlers."""

    def __init__(
        self,
        *,
        plugin: ServiceOperationInvocationHandler,
    ) -> None:
        self._plugin = plugin
        self.service = plugin.service

    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse:
        environment_context = _current_environment_context()
        invocation = build_service_operation_invocation(
            env_req=build_environment_service_operation_request(
                request=request,
                environment_context=environment_context,
            ),
            stream_target_id=request.stream_target_id,
            stream_correlation_id=request.stream_correlation_id,
            network_request_id=request.network_request_id,
        )
        return await self._plugin.handle_request(invocation=invocation)

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        environment_context = _current_environment_context()
        invocation = build_service_operation_invocation(
            env_req=build_environment_service_operation_request(
                request=request,
                environment_context=environment_context,
            ),
            stream_target_id=request.stream_target_id,
            stream_correlation_id=request.stream_correlation_id,
            network_request_id=request.network_request_id,
        )
        await self._plugin.handle_notification(invocation=invocation)


def _current_environment_context() -> EnvironmentOperationContext | None:
    from aware_service_runtime.api_ingress.host_context import (
        current_service_api_host_context,
    )

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return host_context.environment_context


def _require_uuid(value: UUID | None, *, field_name: str) -> UUID:
    if value is None:
        raise TypeError(f"Environment service request is missing {field_name}.")
    return cast(UUID, value)


def _require_projection_hash(value: str | None) -> str:
    if value is None:
        raise TypeError("Environment service request is missing projection_hash.")
    return value
