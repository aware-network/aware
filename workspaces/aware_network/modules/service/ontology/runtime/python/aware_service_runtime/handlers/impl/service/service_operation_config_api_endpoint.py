from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_operation_config_api_endpoint import ServiceOperationConfigApiEndpoint
from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
    ServiceOperationConfigApiEndpointFunction,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_operation_config import ServiceOperationConfig
from aware_service_ontology.stable_ids import (
    stable_service_operation_config_api_endpoint_id,
)

# --- AWARE: USER_IMPORTS END


async def create_function(
    service_operation_config_api_endpoint: ServiceOperationConfigApiEndpoint,
    api_capability_endpoint_function_id: UUID,
    description: str | None = None,
) -> ServiceOperationConfigApiEndpointFunction:
    """
    Create one Service-owned bind to one API-owned endpoint function behind this endpoint facade.
    """

    # --- AWARE: LOGIC START create_function
    session = current_handler_session()

    api_capability_endpoint_function = session.imap_get(
        ApiCapabilityEndpointFunction,
        api_capability_endpoint_function_id,
    )
    if (
        api_capability_endpoint_function is not None
        and api_capability_endpoint_function.api_capability_endpoint_id
        != service_operation_config_api_endpoint.api_capability_endpoint_id
    ):
        raise RuntimeError(
            "ServiceOperationConfigApiEndpoint.create_function api_capability_endpoint_function does not belong "
            + "to parent ApiCapabilityEndpoint: "
            + f"service_operation_config_api_endpoint_id={service_operation_config_api_endpoint.id} "
            + f"api_capability_endpoint_function_id={api_capability_endpoint_function_id}"
        )

    created = await ServiceOperationConfigApiEndpointFunction.build_via_service_operation_config_api_endpoint(
        service_operation_config_api_endpoint_id=service_operation_config_api_endpoint.id,
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
        description=description,
    )
    for existing in service_operation_config_api_endpoint.endpoint_functions:
        if existing.id == created.id:
            return existing
    service_operation_config_api_endpoint.endpoint_functions.append(created)
    return created
    # --- AWARE: LOGIC END create_function


async def build_via_service_operation_config(
    service_operation_config_id: UUID,
    service_config_api_id: UUID,
    api_capability_endpoint_id: UUID,
    description: str | None = None,
) -> ServiceOperationConfigApiEndpoint:
    """
    Create one config-level binding from one public API endpoint facade to a ServiceOperationConfig.
    """

    # --- AWARE: LOGIC START build_via_service_operation_config
    service_operation_config_api_endpoint_id = stable_service_operation_config_api_endpoint_id(
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )
    session = current_handler_session()
    existing = session.imap_get(
        ServiceOperationConfigApiEndpoint,
        service_operation_config_api_endpoint_id,
    )
    if existing is not None:
        if (
            existing.service_operation_config_id != service_operation_config_id
            or existing.service_config_api_id != service_config_api_id
            or existing.api_capability_endpoint_id != api_capability_endpoint_id
        ):
            raise RuntimeError(
                "ServiceOperationConfigApiEndpoint.build_via_service_operation_config payload mismatch "
                + "for existing binding: service_operation_config_api_endpoint_id="
                + f"{service_operation_config_api_endpoint_id}"
            )
        return existing

    service_operation_config = session.imap_get(ServiceOperationConfig, service_operation_config_id)
    service_config_api = session.imap_get(ServiceConfigApi, service_config_api_id)
    if (
        service_operation_config is not None
        and service_config_api is not None
        and service_operation_config.service_config_id != service_config_api.service_config_id
    ):
        raise RuntimeError(
            "ServiceOperationConfigApiEndpoint.build_via_service_operation_config service_config_api "
            + "does not belong to parent ServiceConfig: "
            + f"service_operation_config_id={service_operation_config_id} "
            + f"service_config_api_id={service_config_api_id}"
        )

    api_capability_endpoint = session.imap_get(ApiCapabilityEndpoint, api_capability_endpoint_id)
    if service_config_api is not None and api_capability_endpoint is not None:
        api_capability = session.imap_get(ApiCapability, api_capability_endpoint.api_capability_id)
        if api_capability is not None and api_capability.api_id != service_config_api.api_id:
            raise RuntimeError(
                "ServiceOperationConfigApiEndpoint.build_via_service_operation_config "
                + "api_capability_endpoint does not belong to parent Api: "
                + f"service_config_api_id={service_config_api_id} "
                + f"api_capability_endpoint_id={api_capability_endpoint_id}"
            )

    return ServiceOperationConfigApiEndpoint(
        id=service_operation_config_api_endpoint_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_operation_config
