from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_graph import ProgramConfigGraph
from aware_experience_ontology.program.program_config_graph_program_config import ProgramConfigGraphProgramConfig
from aware_experience_ontology.program.program_config_graph_projection_experience_oigi import (
    ProgramConfigGraphProjectionExperienceOIGI,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience.stable_ids import (
    stable_program_config_graph_id,
    stable_program_config_graph_object_config_graph_id,
    stable_program_config_graph_program_config_id,
    stable_program_config_graph_projection_experience_oigi_id,
)

from aware_experience_ontology.program.program_config_graph_object_config_graph import (
    ProgramConfigGraphObjectConfigGraph,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    key: str,
    thread_config_id: UUID,
    object_config_graph_id: UUID,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> ProgramConfigGraph:
    """
    Create a deterministic ProgramConfigGraph bound to one Environment ThreadConfig and one
    ObjectConfigGraph.

    Contract:
    - Identity is derived from class key `key`.
    - Constructor is idempotent for the same key.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProgramConfigGraph.build requires non-empty key")
    graph_id = stable_program_config_graph_id(key=normalized_key)
    assoc_id = stable_program_config_graph_object_config_graph_id(
        program_config_graph_id=graph_id,
        object_config_graph_id=object_config_graph_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ProgramConfigGraph, graph_id)
    if existing is not None:
        for edge in existing.object_config_graphs:
            if edge.id == assoc_id:
                existing_key = (edge.key or "").strip() or None
                if edge.object_config_graph_id != object_config_graph_id or existing_key != normalized_key:
                    raise RuntimeError(
                        "ProgramConfigGraph.build object_config_graph association mismatch for existing graph: "
                        f"program_config_graph_id={graph_id} association_id={assoc_id}"
                    )
                return existing
        existing_edge = session.imap_get(ProgramConfigGraphObjectConfigGraph, assoc_id)
        if existing_edge is None:
            existing_edge = ProgramConfigGraphObjectConfigGraph(
                id=assoc_id,
                program_config_graph_id=graph_id,
                object_config_graph_id=object_config_graph_id,
                key=normalized_key,
            )
        existing.object_config_graphs.append(existing_edge)
        return existing

    object_config_graph_edge = ProgramConfigGraphObjectConfigGraph(
        id=assoc_id,
        program_config_graph_id=graph_id,
        object_config_graph_id=object_config_graph_id,
        key=normalized_key,
    )
    return ProgramConfigGraph(
        id=graph_id,
        key=normalized_key,
        title=title,
        description=description,
        narrative=narrative,
        intent=intent,
        object_config_graphs=[object_config_graph_edge],
    )
    # --- AWARE: LOGIC END build


async def add_program_config(
    program_config_graph: ProgramConfigGraph, program_config_id: UUID, key: str | None = None
) -> ProgramConfigGraphProgramConfig:
    """
    Link one existing ProgramConfig under this ProgramConfigGraph.

    Contract:
    - Association identity is deterministic from `(program_config_graph_id, program_config_id)`.
    - ProgramConfig creation is graph-agnostic and happens outside this edge API.
    """

    # --- AWARE: LOGIC START add_program_config
    graph_id = program_config_graph.id
    if graph_id is None:
        raise RuntimeError("ProgramConfigGraph.add_program_config requires id")

    assoc_id = stable_program_config_graph_program_config_id(
        program_config_graph_id=graph_id,
        program_config_id=program_config_id,
    )
    existing_assoc = await ProgramConfigGraphProgramConfig.build_via_program_config_graph(
        program_config_graph_id=graph_id,
        program_config_id=program_config_id,
        key=(key or "").strip() or None,
    )
    if existing_assoc.id != assoc_id:
        raise RuntimeError(
            "ProgramConfigGraph.add_program_config association identity mismatch: "
            f"expected={assoc_id} actual={existing_assoc.id}"
        )
    if not any(existing.id == existing_assoc.id for existing in program_config_graph.program_configs):
        program_config_graph.program_configs.append(existing_assoc)
    return existing_assoc
    # --- AWARE: LOGIC END add_program_config


async def add_projection_experience_oigi(
    program_config_graph: ProgramConfigGraph, projection_experience_oigi_id: UUID, key: str | None = None
) -> ProgramConfigGraphProjectionExperienceOIGI:
    """
    Link one ProjectionExperienceOIGI under this ProgramConfigGraph.
    """

    # --- AWARE: LOGIC START add_projection_experience_oigi
    graph_id = program_config_graph.id
    if graph_id is None:
        raise RuntimeError("ProgramConfigGraph.add_projection_experience_oigi requires id")

    normalized_key = (key or "").strip() or None
    assoc_id = stable_program_config_graph_projection_experience_oigi_id(
        program_config_graph_id=graph_id,
        projection_experience_oigi_id=projection_experience_oigi_id,
    )
    existing_assoc = await ProgramConfigGraphProjectionExperienceOIGI.build_via_program_config_graph(
        program_config_graph_id=graph_id,
        projection_experience_oigi_id=projection_experience_oigi_id,
        key=normalized_key,
    )
    if existing_assoc.id != assoc_id:
        raise RuntimeError(
            "ProgramConfigGraph.add_projection_experience_oigi association identity mismatch: "
            f"expected={assoc_id} actual={existing_assoc.id}"
        )
    if not any(existing.id == existing_assoc.id for existing in program_config_graph.projection_experience_oigis):
        program_config_graph.projection_experience_oigis.append(existing_assoc)
    return existing_assoc
    # --- AWARE: LOGIC END add_projection_experience_oigi
