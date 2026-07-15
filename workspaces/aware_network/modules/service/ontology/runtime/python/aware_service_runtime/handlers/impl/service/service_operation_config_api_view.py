from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_operation_config_api_view import ServiceOperationConfigApiView

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_view import ApiView
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.stable_ids import (
    stable_service_operation_config_api_view_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_operation_config(
    service_operation_config_id: UUID, service_config_api_id: UUID, api_view_id: UUID, description: str | None = None
) -> ServiceOperationConfigApiView:
    """
    Creates one ServiceOperationConfig-owned fulfillment binding for an API view.

    Contract:
    - Parent ServiceOperationConfig scope is propagated by constructor lowering.
    - `api_view` is the API-owned readable state contract this Service operation fulfills.
    - The owning ServiceOperationConfig is the fulfillment provider; no nested view-provider rail
    exists.
    """

    # --- AWARE: LOGIC START build_via_service_operation_config
    binding_id = stable_service_operation_config_api_view_id(
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_view_id=api_view_id,
    )
    session = current_handler_session()

    existing = session.imap_get(ServiceOperationConfigApiView, binding_id)
    if existing is not None:
        if (
            existing.service_operation_config_id != service_operation_config_id
            or existing.service_config_api_id != service_config_api_id
            or existing.api_view_id != api_view_id
        ):
            raise RuntimeError(
                "ServiceOperationConfigApiView payload mismatch for existing binding: " + f"binding_id={binding_id}"
            )
        existing.description = description
        return existing

    service_operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    service_config_api = session.imap_get(ServiceConfigApi, service_config_api_id)
    if (
        service_operation_config is not None
        and service_config_api is not None
        and service_operation_config.service_config_id != service_config_api.service_config_id
    ):
        raise RuntimeError(
            "ServiceOperationConfigApiView.build_via_service_operation_config service_config_api "
            + "does not belong to parent ServiceConfig: "
            + f"service_operation_config_id={service_operation_config_id} "
            + f"service_config_api_id={service_config_api_id}"
        )

    api_view = session.imap_get(ApiView, api_view_id)
    if service_config_api is not None and api_view is not None and api_view.api_id != service_config_api.api_id:
        raise RuntimeError(
            "ServiceOperationConfigApiView.build_via_service_operation_config api_view "
            + "does not belong to ServiceConfigApi Api: "
            + f"service_config_api_id={service_config_api_id} "
            + f"api_view_id={api_view_id}"
        )

    return ServiceOperationConfigApiView(
        id=binding_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_view_id=api_view_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_operation_config
