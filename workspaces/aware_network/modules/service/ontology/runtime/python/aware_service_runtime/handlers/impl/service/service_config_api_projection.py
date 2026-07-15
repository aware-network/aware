from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_config_api_projection import ServiceConfigApiProjection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import stable_service_config_api_projection_id

# --- AWARE: USER_IMPORTS END


async def build_via_service_config_api(
    service_config_api_id: UUID, api_graph_projection_id: UUID, description: str | None = None
) -> ServiceConfigApiProjection:
    """
    Create one config-level bridge from a ServiceConfigApi to one API-owned graph projection.
    """

    # --- AWARE: LOGIC START build_via_service_config_api
    projection_id = stable_service_config_api_projection_id(
        service_config_api_id=service_config_api_id,
        api_graph_projection_id=api_graph_projection_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ServiceConfigApiProjection, projection_id)
    if existing is not None:
        if (
            existing.service_config_api_id != service_config_api_id
            or existing.api_graph_projection_id != api_graph_projection_id
        ):
            raise RuntimeError(
                "ServiceConfigApiProjection.build_via_service_config_api payload mismatch for existing bridge: "
                + f"service_config_api_projection_id={projection_id}"
            )
        return existing

    return ServiceConfigApiProjection(
        id=projection_id,
        service_config_api_id=service_config_api_id,
        api_graph_projection_id=api_graph_projection_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_config_api
