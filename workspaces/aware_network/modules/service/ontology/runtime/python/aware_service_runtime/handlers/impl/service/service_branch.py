from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_branch import ServiceBranch

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import stable_service_branch_id

# --- AWARE: USER_IMPORTS END


async def build_via_service(
    service_id: UUID,
    service_config_api_projection_id: UUID,
    object_instance_graph_branch_id: UUID,
    description: str | None = None,
) -> ServiceBranch:
    """
    Create one concrete service-instance branch binding for one subscribed API projection lane.
    """

    # --- AWARE: LOGIC START build_via_service
    branch_id = stable_service_branch_id(
        service_id=service_id,
        service_config_api_projection_id=service_config_api_projection_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ServiceBranch, branch_id)
    if existing is not None:
        if (
            existing.service_id != service_id
            or existing.service_config_api_projection_id != service_config_api_projection_id
            or existing.object_instance_graph_branch_id != object_instance_graph_branch_id
        ):
            raise RuntimeError(
                "ServiceBranch.build_via_service payload mismatch for existing branch binding: "
                + f"service_branch_id={branch_id}"
            )
        return existing

    return ServiceBranch(
        id=branch_id,
        service_id=service_id,
        service_config_api_projection_id=service_config_api_projection_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service
