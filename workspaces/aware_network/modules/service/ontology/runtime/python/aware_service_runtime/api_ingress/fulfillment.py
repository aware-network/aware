from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_orm.session.session import Session
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
    ServiceOperationConfigApiEndpointFunction,
)

from aware_service_runtime.api_ingress.dispatch import (
    ResolvedServiceApiDispatch,
    ResolvedServiceApiDispatchCandidate,
    require_single_service_api_dispatch_candidate,
)


@dataclass(frozen=True, slots=True)
class ValidatedServiceApiFulfillmentBinding:
    service_operation_config_api_endpoint_function_id: UUID
    api_capability_endpoint_function_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ValidatedServiceApiFulfillmentContract:
    candidate: ResolvedServiceApiDispatchCandidate
    bindings: tuple[ValidatedServiceApiFulfillmentBinding, ...]


def validate_service_api_fulfillment_contract(
    *,
    session: Session,
    resolved_dispatch: ResolvedServiceApiDispatch,
) -> ValidatedServiceApiFulfillmentContract:
    candidate = require_single_service_api_dispatch_candidate(
        resolved_dispatch=resolved_dispatch,
    )
    endpoint_binding = session.imap_get(
        ServiceOperationConfigApiEndpoint,
        candidate.service_operation_config_api_endpoint_id,
    )
    if endpoint_binding is None:
        raise RuntimeError(
            "Service runtime could not re-materialize selected ServiceOperationConfigApiEndpoint "
            "for fulfillment validation: "
            f"service_operation_config_api_endpoint_id={candidate.service_operation_config_api_endpoint_id}"
        )

    allowed_bindings_by_api_function_id: dict[UUID, ServiceOperationConfigApiEndpointFunction] = {}
    for endpoint_function in endpoint_binding.endpoint_functions:
        if (
            isinstance(endpoint_function, ServiceOperationConfigApiEndpointFunction)
            and endpoint_function.api_capability_endpoint_function_id is not None
        ):
            allowed_bindings_by_api_function_id[
                endpoint_function.api_capability_endpoint_function_id
            ] = endpoint_function

    validated_bindings: list[ValidatedServiceApiFulfillmentBinding] = []
    for fulfillment_binding in resolved_dispatch.dispatch_plan.fulfillment_bindings:
        api_capability_endpoint_function_id = (
            fulfillment_binding.api_capability_endpoint_function_id
        )
        if api_capability_endpoint_function_id is None:
            raise RuntimeError(
                "Service runtime requires API-owned endpoint-function ids on the commit-backed "
                "dispatch plan before post-selection fulfillment validation: "
                f"endpoint_ref={resolved_dispatch.dispatch_plan.endpoint_ref!r} "
                f"fulfillment_name={fulfillment_binding.name!r}"
            )
        allowed_binding = allowed_bindings_by_api_function_id.get(
            api_capability_endpoint_function_id
        )
        if allowed_binding is None or allowed_binding.id is None:
            raise RuntimeError(
                "Service runtime selected a ServiceOperationConfigApiEndpoint that does not allow "
                "the API-owned fulfillment binding supplied by the dispatch plan: "
                f"endpoint_ref={resolved_dispatch.dispatch_plan.endpoint_ref!r} "
                + f"api_capability_endpoint_function_id={api_capability_endpoint_function_id} "
                + f"fulfillment_name={fulfillment_binding.name!r}"
            )
        validated_bindings.append(
            ValidatedServiceApiFulfillmentBinding(
                service_operation_config_api_endpoint_function_id=cast(
                    UUID, allowed_binding.id
                ),
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
                name=fulfillment_binding.name,
            )
        )

    return ValidatedServiceApiFulfillmentContract(
        candidate=candidate,
        bindings=tuple(validated_bindings),
    )


__all__ = [
    "ValidatedServiceApiFulfillmentBinding",
    "ValidatedServiceApiFulfillmentContract",
    "validate_service_api_fulfillment_contract",
]
