from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
    ServiceOperationConfigApiEndpointFunction,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_operation_config_api_endpoint import ServiceOperationConfigApiEndpoint
from aware_service_ontology.stable_ids import (
    stable_service_operation_config_api_endpoint_function_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_operation_config_api_endpoint(
    service_operation_config_api_endpoint_id: UUID,
    api_capability_endpoint_function_id: UUID,
    description: str | None = None,
) -> ServiceOperationConfigApiEndpointFunction:
    """
    Create one config-level binding from a ServiceOperationConfigApiEndpoint to one API-owned endpoint
    function.
    """

    # --- AWARE: LOGIC START build_via_service_operation_config_api_endpoint
    service_operation_config_api_endpoint_function_id = stable_service_operation_config_api_endpoint_function_id(
        service_operation_config_api_endpoint_id=service_operation_config_api_endpoint_id,
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
    )
    session = current_handler_session()
    existing = session.imap_get(
        ServiceOperationConfigApiEndpointFunction,
        service_operation_config_api_endpoint_function_id,
    )
    if existing is not None:
        if (
            existing.service_operation_config_api_endpoint_id != service_operation_config_api_endpoint_id
            or existing.api_capability_endpoint_function_id != api_capability_endpoint_function_id
        ):
            raise RuntimeError(
                "ServiceOperationConfigApiEndpointFunction.build_via_service_operation_config_api_endpoint "
                + "payload mismatch for existing binding: "
                + "service_operation_config_api_endpoint_function_id="
                + f"{service_operation_config_api_endpoint_function_id}"
            )
        return existing

    service_operation_config_api_endpoint = session.imap_get(
        ServiceOperationConfigApiEndpoint,
        service_operation_config_api_endpoint_id,
    )
    api_capability_endpoint_function = session.imap_get(
        ApiCapabilityEndpointFunction,
        api_capability_endpoint_function_id,
    )
    if (
        service_operation_config_api_endpoint is not None
        and api_capability_endpoint_function is not None
        and api_capability_endpoint_function.api_capability_endpoint_id
        != service_operation_config_api_endpoint.api_capability_endpoint_id
    ):
        raise RuntimeError(
            "ServiceOperationConfigApiEndpointFunction.build_via_service_operation_config_api_endpoint "
            + "api_capability_endpoint_function does not belong to parent ApiCapabilityEndpoint: "
            + f"service_operation_config_api_endpoint_id={service_operation_config_api_endpoint_id} "
            + f"api_capability_endpoint_function_id={api_capability_endpoint_function_id}"
        )

    return ServiceOperationConfigApiEndpointFunction(
        id=service_operation_config_api_endpoint_function_id,
        service_operation_config_api_endpoint_id=service_operation_config_api_endpoint_id,
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_operation_config_api_endpoint
