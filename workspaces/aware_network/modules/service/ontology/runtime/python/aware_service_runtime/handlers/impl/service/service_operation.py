from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceOperationStatus
from aware_service_ontology.service.service_operation import ServiceOperation

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_api_ontology.api.api_call import ApiCall
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.stable_ids import (
    stable_service_operation_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def set_status(
    service_operation: ServiceOperation, status: ServiceOperationStatus, result_info: str | None = None
) -> ServiceOperation:
    """
    Updates execution status for this ServiceOperation.
    """

    # --- AWARE: LOGIC START set_status
    service_operation.status = status
    service_operation.result_info = result_info
    return service_operation
    # --- AWARE: LOGIC END set_status


async def build_via_service(
    service_id: UUID,
    service_operation_config_id: UUID,
    operation_key: str,
    api_call_id: UUID | None = None,
    api_endpoint_id: UUID | None = None,
    status: ServiceOperationStatus = ServiceOperationStatus.queued,
    result_info: str | None = None,
    execution_context: JsonObject | None = None,
) -> ServiceOperation:
    """
    Creates one canonical service execution receipt under a concrete Service.
    """

    # --- AWARE: LOGIC START build_via_service
    normalized_operation_key = (operation_key or "").strip()
    if not normalized_operation_key:
        raise RuntimeError("ServiceOperation.build_via_service requires non-empty operation_key")

    service_operation_id = stable_service_operation_id(
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        operation_key=normalized_operation_key,
    )
    session = current_handler_session()
    existing = session.imap_get(ServiceOperation, service_operation_id)
    if existing is not None:
        if (
            existing.service_id != service_id
            or existing.service_operation_config_id != service_operation_config_id
            or existing.api_call_id != api_call_id
            or existing.api_endpoint_id != api_endpoint_id
            or (existing.operation_key or "").strip() != normalized_operation_key
        ):
            raise RuntimeError(
                "ServiceOperation.build_via_service payload mismatch for existing operation: "
                + f"service_operation_id={service_operation_id}"
            )
        return existing

    service = session.imap_get(Service, service_id)
    service_operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    if (
        service is not None
        and service_operation_config is not None
        and service_operation_config.service_config_id != service.service_config_id
    ):
        raise RuntimeError(
            "ServiceOperation.build_via_service service_operation_config does not belong "
            + "to the same ServiceConfig as the concrete Service: "
            + f"service_operation_config_id={service_operation_config_id}"
        )

    api_endpoint = None
    if api_call_id is not None:
        _ = session.imap_get(ApiCall, api_call_id)

    if api_endpoint_id is not None:
        api_endpoint = session.imap_get(
            ServiceOperationConfigApiEndpoint,
            api_endpoint_id,
        )
        if api_endpoint is not None and api_endpoint.service_operation_config_id != service_operation_config_id:
            raise RuntimeError(
                "ServiceOperation.build_via_service endpoint provenance does not match "
                + "service_operation_config: "
                + f"api_endpoint_id={api_endpoint_id}"
            )
        if service is not None and api_endpoint is not None:
            service_config_api = session.imap_get(ServiceConfigApi, api_endpoint.service_config_api_id)
            if service_config_api is not None and service_config_api.service_config_id != service.service_config_id:
                raise RuntimeError(
                    "ServiceOperation.build_via_service endpoint provenance does not belong "
                    + "to the same ServiceConfig as the concrete Service: "
                    + f"api_endpoint_id={api_endpoint_id}"
                )

    return ServiceOperation(
        id=service_operation_id,
        service_id=service_id,
        api_call_id=api_call_id,
        api_endpoint_id=api_endpoint_id,
        service_operation_config_id=service_operation_config_id,
        operation_key=normalized_operation_key,
        status=status,
        result_info=result_info,
        execution_context=cast(JsonObject, dict(execution_context or {})),
    )
    # --- AWARE: LOGIC END build_via_service
