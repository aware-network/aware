from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_graph_object_config_graph import (
    ProgramConfigGraphObjectConfigGraph,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience.stable_ids import (
    stable_program_config_graph_object_config_graph_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config_graph(
    program_config_graph_id: UUID, object_config_graph_id: UUID, key: str | None = None
) -> ProgramConfigGraphObjectConfigGraph:
    """
    Create a deterministic ProgramConfigGraphObjectConfigGraph under this.

    Contract:
    - Identity is derived from `(program_config_graph_id, object_config_graph_id)`.
    - Constructor is idempotent for the same pair.
    """

    # --- AWARE: LOGIC START build_via_program_config_graph
    normalized_key = (key or "").strip() or None
    session = current_handler_session()
    assoc_id = stable_program_config_graph_object_config_graph_id(
        program_config_graph_id=program_config_graph_id,
        object_config_graph_id=object_config_graph_id,
    )
    existing = session.imap_get(ProgramConfigGraphObjectConfigGraph, assoc_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.program_config_graph_id != program_config_graph_id
            or existing.object_config_graph_id != object_config_graph_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProgramConfigGraphObjectConfigGraph.build_via_program_config_graph payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        return existing

    return ProgramConfigGraphObjectConfigGraph(
        id=assoc_id,
        program_config_graph_id=program_config_graph_id,
        object_config_graph_id=object_config_graph_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_program_config_graph
