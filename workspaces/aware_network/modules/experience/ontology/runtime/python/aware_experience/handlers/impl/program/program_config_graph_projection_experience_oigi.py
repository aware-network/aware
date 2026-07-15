from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_graph_projection_experience_oigi import (
    ProgramConfigGraphProjectionExperienceOIGI,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_program_config_graph_projection_experience_oigi_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config_graph(
    program_config_graph_id: UUID, projection_experience_oigi_id: UUID, key: str | None = None
) -> ProgramConfigGraphProjectionExperienceOIGI:
    """
    Create deterministic ProgramConfigGraphProjectionExperienceOIGI edge.
    """

    # --- AWARE: LOGIC START build_via_program_config_graph
    normalized_key = (key or "").strip() or None
    assoc_id = stable_program_config_graph_projection_experience_oigi_id(
        program_config_graph_id=program_config_graph_id,
        projection_experience_oigi_id=projection_experience_oigi_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramConfigGraphProjectionExperienceOIGI, assoc_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.program_config_graph_id != program_config_graph_id
            or existing.projection_experience_oigi_id != projection_experience_oigi_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProgramConfigGraphProjectionExperienceOIGI.build_via_program_config_graph payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        return existing

    return ProgramConfigGraphProjectionExperienceOIGI(
        id=assoc_id,
        program_config_graph_id=program_config_graph_id,
        projection_experience_oigi_id=projection_experience_oigi_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_program_config_graph
