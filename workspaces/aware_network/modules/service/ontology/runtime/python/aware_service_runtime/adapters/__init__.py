"""Compatibility adapters for service host/runtime boundaries."""

from aware_service_runtime.adapters.environment import (
    EnvironmentInvocationHandlerAdapter,
    EnvironmentServiceInvocation,
    EnvironmentServiceInvocationHandler,
    EnvironmentServiceResult,
    EnvironmentServiceTransport,
    build_environment_service_operation_request,
    build_environment_operation_context,
    build_service_operation_context,
    build_service_operation_invocation,
    build_service_operation_request,
    build_service_operation_result_from_response,
    coerce_environment_service_operation,
)

__all__ = [
    "EnvironmentInvocationHandlerAdapter",
    "EnvironmentServiceInvocation",
    "EnvironmentServiceInvocationHandler",
    "EnvironmentServiceResult",
    "EnvironmentServiceTransport",
    "build_environment_service_operation_request",
    "build_environment_operation_context",
    "build_service_operation_context",
    "build_service_operation_invocation",
    "build_service_operation_request",
    "build_service_operation_result_from_response",
    "coerce_environment_service_operation",
]
