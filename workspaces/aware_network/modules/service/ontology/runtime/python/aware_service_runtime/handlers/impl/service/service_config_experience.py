from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_config_experience import ServiceConfigExperience

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import stable_service_config_experience_id

# --- AWARE: USER_IMPORTS END


async def build_via_service_config(
    service_config_id: UUID, projection_experience_id: UUID, description: str | None = None
) -> ServiceConfigExperience:
    """
    Create one config-level bridge between a ServiceConfig and one shared ProjectionExperience.
    """

    # --- AWARE: LOGIC START build_via_service_config
    service_config_experience_id = stable_service_config_experience_id(
        service_config_id=service_config_id,
        projection_experience_id=projection_experience_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ServiceConfigExperience, service_config_experience_id)
    if existing is not None:
        if (
            existing.service_config_id != service_config_id
            or existing.projection_experience_id != projection_experience_id
        ):
            raise RuntimeError(
                "ServiceConfigExperience.build_via_service_config payload mismatch for existing bridge: "
                + f"service_config_experience_id={service_config_experience_id}"
            )
        return existing

    return ServiceConfigExperience(
        id=service_config_experience_id,
        service_config_id=service_config_id,
        projection_experience_id=projection_experience_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_config
