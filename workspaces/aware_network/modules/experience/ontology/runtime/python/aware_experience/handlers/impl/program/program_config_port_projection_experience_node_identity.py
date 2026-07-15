from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_program_config_port_projection_experience_node_identity_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config_port_projection_experience_node(
    program_config_port_projection_experience_node_id: UUID, projection_experience_node_identity_id: UUID, key: str
) -> ProgramConfigPortProjectionExperienceNodeIdentity:
    """
    Create deterministic ProgramConfigPortProjectionExperienceNodeIdentity edge.
    """

    # --- AWARE: LOGIC START build_via_program_config_port_projection_experience_node
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError(
            "ProgramConfigPortProjectionExperienceNodeIdentity.build_via_program_config_port " "requires non-empty key"
        )
    session = current_handler_session()
    port_projection_identity_id = stable_program_config_port_projection_experience_node_identity_id(
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        key=normalized_key,
    )
    existing = session.imap_get(
        ProgramConfigPortProjectionExperienceNodeIdentity,
        port_projection_identity_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_node_identity_id != projection_experience_node_identity_id
            or existing.key != normalized_key
        ):
            raise RuntimeError(
                "ProgramConfigPortProjectionExperienceNodeIdentity.build_via_program_config_port_projection_experience_node payload "
                "mismatch for existing edge: "
                f"program_config_port_projection_experience_node_identity_id={port_projection_identity_id}"
            )
        return existing

    return ProgramConfigPortProjectionExperienceNodeIdentity(
        id=port_projection_identity_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_program_config_port_projection_experience_node
