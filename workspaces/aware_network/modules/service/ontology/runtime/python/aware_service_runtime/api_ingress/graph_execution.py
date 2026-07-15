from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from aware_service_runtime.api_ingress.fulfillment import (
    ValidatedServiceApiFulfillmentBinding,
    ValidatedServiceApiFulfillmentContract,
)

if TYPE_CHECKING:
    from aware_api_runtime.service_protocol import (
        ApiServiceDispatchInstanceTargetPlan,
        ApiServiceDispatchPlan,
    )


class _MaterializedServiceOperationBindingProtocol(Protocol):
    @property
    def service_operation_id(self) -> UUID: ...

    @property
    def service_id(self) -> UUID: ...

    @property
    def service_operation_config_id(self) -> UUID: ...

    @property
    def api_endpoint_id(self) -> UUID | None: ...


@dataclass(frozen=True, slots=True)
class ServiceApiGraphExecutionBinding:
    service_operation_config_api_endpoint_function_id: UUID
    api_capability_endpoint_function_id: UUID
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    graph_function_runtime_target: str
    call_target_kind: str | None = None
    exact_output_field_name: str | None = None
    instance_target_plan: ApiServiceDispatchInstanceTargetPlan | None = None


@dataclass(frozen=True, slots=True)
class ServiceApiGraphExecutionPlan:
    service_operation_id: UUID
    service_id: UUID
    service_operation_config_id: UUID
    service_operation_config_api_endpoint_id: UUID
    api_call_id: UUID
    endpoint_ref: str
    request_object: object
    bindings: tuple[ServiceApiGraphExecutionBinding, ...]


def build_service_api_graph_execution_plan(
    *,
    dispatch_plan: ApiServiceDispatchPlan,
    materialized_operation_binding: _MaterializedServiceOperationBindingProtocol,
    validated_fulfillment: ValidatedServiceApiFulfillmentContract,
) -> ServiceApiGraphExecutionPlan:
    service_operation_config_api_endpoint_id = materialized_operation_binding.api_endpoint_id
    if service_operation_config_api_endpoint_id is None:
        raise RuntimeError(
            "Service graph fulfillment execution requires a materialized ServiceOperation "
            "bound to one ServiceOperationConfigApiEndpoint: "
            f"service_operation_id={materialized_operation_binding.service_operation_id}"
        )

    validated_by_api_function_id: dict[UUID, ValidatedServiceApiFulfillmentBinding] = {
        binding.api_capability_endpoint_function_id: binding
        for binding in validated_fulfillment.bindings
    }
    execution_bindings: list[ServiceApiGraphExecutionBinding] = []
    for fulfillment_binding in dispatch_plan.fulfillment_bindings:
        api_capability_endpoint_function_id = (
            fulfillment_binding.api_capability_endpoint_function_id
        )
        if api_capability_endpoint_function_id is None:
            raise RuntimeError(
                "Service graph fulfillment execution requires exact API-owned endpoint-function ids "
                "on the dispatch plan before building the execution plan: "
                f"endpoint_ref={dispatch_plan.endpoint_ref!r} "
                f"fulfillment_name={fulfillment_binding.name!r}"
            )
        validated_binding = validated_by_api_function_id.get(
            api_capability_endpoint_function_id
        )
        if validated_binding is None:
            raise RuntimeError(
                "Service graph fulfillment execution could not match the validated endpoint-function "
                "binding back onto the dispatch plan fulfillment metadata: "
                f"endpoint_ref={dispatch_plan.endpoint_ref!r} "
                f"api_capability_endpoint_function_id={api_capability_endpoint_function_id}"
            )
        execution_bindings.append(
            ServiceApiGraphExecutionBinding(
                service_operation_config_api_endpoint_function_id=(
                    validated_binding.service_operation_config_api_endpoint_function_id
                ),
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
                name=fulfillment_binding.name,
                graph_target=fulfillment_binding.graph_target,
                graph_capability_function_name=(
                    fulfillment_binding.graph_capability_function_name
                ),
                graph_function_python_ref=fulfillment_binding.graph_function_python_ref,
                graph_function_runtime_target=fulfillment_binding.graph_function_runtime_target,
                call_target_kind=fulfillment_binding.call_target_kind,
                exact_output_field_name=fulfillment_binding.exact_output_field_name,
                instance_target_plan=fulfillment_binding.instance_target_plan,
            )
        )

    return ServiceApiGraphExecutionPlan(
        service_operation_id=materialized_operation_binding.service_operation_id,
        service_id=materialized_operation_binding.service_id,
        service_operation_config_id=materialized_operation_binding.service_operation_config_id,
        service_operation_config_api_endpoint_id=service_operation_config_api_endpoint_id,
        api_call_id=dispatch_plan.envelope.api_call_id,
        endpoint_ref=dispatch_plan.endpoint_ref,
        request_object=dispatch_plan.request_object,
        bindings=tuple(execution_bindings),
    )


__all__ = [
    "ServiceApiGraphExecutionBinding",
    "ServiceApiGraphExecutionPlan",
    "build_service_api_graph_execution_plan",
]
