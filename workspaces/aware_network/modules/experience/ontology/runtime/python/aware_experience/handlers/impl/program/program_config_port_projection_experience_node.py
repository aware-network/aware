from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_program_config_port_projection_experience_node_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_identity(
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode,
    projection_experience_node_identity_id: UUID,
    key: str,
) -> ProgramConfigPortProjectionExperienceNodeIdentity:
    """
    Attach one optional ProjectionExperienceNodeIdentity under this port node edge.
    """

    # --- AWARE: LOGIC START create_identity
    node_id = program_config_port_projection_experience_node.id
    if node_id is None:
        raise RuntimeError("ProgramConfigPortProjectionExperienceNode.create_identity requires id")
    created = await ProgramConfigPortProjectionExperienceNodeIdentity.build_via_program_config_port_projection_experience_node(
        program_config_port_projection_experience_node_id=node_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        key=key,
    )
    existing = program_config_port_projection_experience_node.projection_node_identity
    if existing is not None:
        if existing.id == created.id:
            return existing
        raise RuntimeError(
            "ProgramConfigPortProjectionExperienceNode.create_identity requires a single identity edge; "
            f"existing={existing.id} requested={created.id}"
        )
    program_config_port_projection_experience_node.projection_node_identity = created
    return created
    # --- AWARE: LOGIC END create_identity


async def build_via_program_config_port(
    program_config_port_id: UUID, projection_experience_node_id: UUID, key: str
) -> ProgramConfigPortProjectionExperienceNode:
    """
    Create deterministic ProgramConfigPortProjectionExperienceNode edge.
    """

    # --- AWARE: LOGIC START build_via_program_config_port
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError(
            "ProgramConfigPortProjectionExperienceNode.build_via_program_config_port " "requires non-empty key"
        )
    assoc_id = stable_program_config_port_projection_experience_node_id(
        program_config_port_id=program_config_port_id,
        projection_experience_node_id=projection_experience_node_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramConfigPortProjectionExperienceNode, assoc_id)
    if existing is not None:
        if (
            existing.program_config_port_id != program_config_port_id
            or existing.projection_experience_node_id != projection_experience_node_id
            or (existing.key or "").strip() != normalized_key
        ):
            raise RuntimeError(
                "ProgramConfigPortProjectionExperienceNode.build_via_program_config_port payload "
                "mismatch for existing edge: "
                f"program_config_port_projection_experience_node_id={assoc_id}"
            )
        return existing
    return ProgramConfigPortProjectionExperienceNode(
        id=assoc_id,
        program_config_port_id=program_config_port_id,
        projection_experience_node_id=projection_experience_node_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_program_config_port
