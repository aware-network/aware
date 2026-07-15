from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from pydantic import BaseModel

from aware_service_runtime.api_ingress.gateway_execution import (
    build_gateway_service_api_execution_backend,
)
from aware_service_runtime.api_ingress.graph_execution import (
    ServiceApiGraphExecutionBinding,
    ServiceApiGraphExecutionPlan,
)
from aware_service_runtime.contracts import (
    ServiceGraphContextLike,
    ServiceGraphGateway,
    ServiceOperationContext,
)

LegacyServiceApiExecutionCallback = Callable[
    [ServiceApiGraphExecutionBinding, BaseModel],
    Awaitable[object | None],
]


class ServiceApiExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceApiExecutionBackendMode(str, Enum):
    auto = "auto"
    graph_gateway = "graph_gateway"
    legacy_callback = "legacy_callback"


@dataclass(frozen=True, slots=True)
class MissingServiceApiExecutionBackend(ServiceApiExecutionBackend):
    execution_plan: ServiceApiGraphExecutionPlan

    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None:
        _ = request
        _ = _resolve_execution_binding(
            execution_plan=self.execution_plan,
            fulfillment_name=fulfillment_name,
        )
        raise RuntimeError(
            "Service execution context was invoked without a configured ServiceGraphGateway backend: "
            f"endpoint_ref={self.execution_plan.endpoint_ref!r} fulfillment_name={fulfillment_name!r}"
        )


@dataclass(frozen=True, slots=True)
class LegacyCallbackServiceApiExecutionBackend(ServiceApiExecutionBackend):
    execution_plan: ServiceApiGraphExecutionPlan
    execution_callback: LegacyServiceApiExecutionCallback

    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None:
        binding = _resolve_execution_binding(
            execution_plan=self.execution_plan,
            fulfillment_name=fulfillment_name,
        )
        return await self.execution_callback(binding, request)


def build_service_api_execution_backend(
    *,
    execution_plan: ServiceApiGraphExecutionPlan,
    backend_mode: ServiceApiExecutionBackendMode = ServiceApiExecutionBackendMode.auto,
    graph_context: ServiceGraphContextLike | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    operation_context: ServiceOperationContext | None = None,
    execution_callback: LegacyServiceApiExecutionCallback | None = None,
) -> ServiceApiExecutionBackend:
    if backend_mode == ServiceApiExecutionBackendMode.graph_gateway:
        if graph_context is None or graph_gateway is None or operation_context is None:
            raise RuntimeError(
                "Service execution backend selection requires graph_context, graph_gateway, "
                "and operation_context for graph_gateway mode."
            )
        return build_gateway_service_api_execution_backend(
            execution_plan=execution_plan,
            graph_context=graph_context,
            graph_gateway=graph_gateway,
            operation_context=operation_context,
        )
    if backend_mode == ServiceApiExecutionBackendMode.legacy_callback:
        if execution_callback is None:
            raise RuntimeError(
                "Service execution backend selection requires execution_callback for "
                "legacy_callback mode."
            )
        return LegacyCallbackServiceApiExecutionBackend(
            execution_plan=execution_plan,
            execution_callback=execution_callback,
        )
    if (
        graph_context is not None
        and graph_gateway is not None
        and operation_context is not None
    ):
        return build_gateway_service_api_execution_backend(
            execution_plan=execution_plan,
            graph_context=graph_context,
            graph_gateway=graph_gateway,
            operation_context=operation_context,
        )
    if graph_gateway is not None and operation_context is not None:
        raise RuntimeError(
            "Service execution backend selection received a graph_gateway route "
            "without package-owned graph_context."
        )
    if execution_callback is not None:
        return LegacyCallbackServiceApiExecutionBackend(
            execution_plan=execution_plan,
            execution_callback=execution_callback,
        )
    return MissingServiceApiExecutionBackend(execution_plan=execution_plan)


def _resolve_execution_binding(
    *,
    execution_plan: ServiceApiGraphExecutionPlan,
    fulfillment_name: str,
) -> ServiceApiGraphExecutionBinding:
    matches = [
        binding
        for binding in execution_plan.bindings
        if binding.name == fulfillment_name
    ]
    if not matches:
        raise RuntimeError(
            "Service execution context could not resolve fulfillment binding from the committed execution plan: "
            f"endpoint_ref={execution_plan.endpoint_ref!r} fulfillment_name={fulfillment_name!r}"
        )
    if len(matches) != 1:
        raise RuntimeError(
            "Service execution context resolved multiple fulfillment bindings for one fulfillment name: "
            f"endpoint_ref={execution_plan.endpoint_ref!r} fulfillment_name={fulfillment_name!r}"
        )
    return matches[0]


__all__ = [
    "LegacyCallbackServiceApiExecutionBackend",
    "LegacyServiceApiExecutionCallback",
    "MissingServiceApiExecutionBackend",
    "ServiceApiExecutionBackend",
    "ServiceApiExecutionBackendMode",
    "build_service_api_execution_backend",
]
