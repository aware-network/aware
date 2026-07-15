from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_config_api_projection import ServiceConfigApiProjection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_graph import ApiGraph
from aware_api_ontology.api.api_graph_projection import ApiGraphProjection
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import (
    stable_service_config_api_id,
    stable_service_config_api_projection_id,
)

# --- AWARE: USER_IMPORTS END


async def create_projection(
    service_config_api: ServiceConfigApi, api_graph_projection_id: UUID, description: str | None = None
) -> ServiceConfigApiProjection:
    """
    Creates one config-level API projection bridge under this ServiceConfigApi.
    """

    # --- AWARE: LOGIC START create_projection
    service_config_api_id = service_config_api.id
    if service_config_api_id is None:
        raise RuntimeError("ServiceConfigApi.create_projection requires ServiceConfigApi.id")

    session = current_handler_session()
    projection_id = stable_service_config_api_projection_id(
        service_config_api_id=service_config_api_id,
        api_graph_projection_id=api_graph_projection_id,
    )
    existing = session.imap_get(ServiceConfigApiProjection, projection_id)
    if existing is not None:
        if (
            existing.service_config_api_id != service_config_api_id
            or existing.api_graph_projection_id != api_graph_projection_id
        ):
            raise RuntimeError(
                "ServiceConfigApi.create_projection payload mismatch for existing projection bridge: "
                + f"service_config_api_projection_id={projection_id}"
            )
        if all(current.id != existing.id for current in service_config_api.api_projections):
            service_config_api.api_projections.append(existing)
        return existing

    api_graph_projection = session.imap_get(ApiGraphProjection, api_graph_projection_id)
    if api_graph_projection is not None:
        api_graph = session.imap_get(ApiGraph, api_graph_projection.api_graph_id)
        if api_graph is not None and api_graph.api_id != service_config_api.api_id:
            raise RuntimeError(
                "ServiceConfigApi.create_projection requires ApiGraphProjection to belong to the same Api bridge: "
                + f"service_config_api_id={service_config_api_id} "
                + f"api_graph_projection_id={api_graph_projection_id}"
            )

    created = await ServiceConfigApiProjection.build_via_service_config_api(
        service_config_api_id=service_config_api_id,
        api_graph_projection_id=api_graph_projection_id,
        description=description,
    )
    if all(current.id != created.id for current in service_config_api.api_projections):
        service_config_api.api_projections.append(created)
    return created
    # --- AWARE: LOGIC END create_projection


async def build_via_service_config(
    service_config_id: UUID, api_id: UUID, description: str | None = None
) -> ServiceConfigApi:
    """
    Create one config-level bridge between a ServiceConfig and one shared Api.
    """

    # --- AWARE: LOGIC START build_via_service_config
    service_config_api_id = stable_service_config_api_id(
        service_config_id=service_config_id,
        api_id=api_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ServiceConfigApi, service_config_api_id)
    if existing is not None:
        if existing.service_config_id != service_config_id or existing.api_id != api_id:
            raise RuntimeError(
                "ServiceConfigApi.build_via_service_config payload mismatch for existing bridge: "
                + f"service_config_api_id={service_config_api_id}"
            )
        return existing

    return ServiceConfigApi(
        id=service_config_api_id,
        service_config_id=service_config_id,
        api_id=api_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_config
