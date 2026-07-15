from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_branch import ProgramBranch

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Environment Ontology
from aware_experience_ontology.stable_ids import stable_program_branch_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program(
    program_id: UUID,
    object_instance_graph_branch_id: UUID,
    key: str | None = None,
    view_key: str | None = None,
    is_active: bool = True,
) -> ProgramBranch:
    """
    Create a deterministic ProgramBranch association edge.

    Contract:
    - Identity is derived from `(program_id, object_instance_graph_branch_id)`.
    - Constructor is idempotent for repeated calls with the same pair.
    """

    # --- AWARE: LOGIC START build_via_program
    normalized_key = (key or "").strip() or None
    normalized_view_key = (view_key or "").strip() or None
    assoc_id = stable_program_branch_id(
        program_id=program_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ProgramBranch, assoc_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        existing_view_key = (existing.view_key or "").strip() or None
        if (
            existing.program_id != program_id
            or existing.object_instance_graph_branch_id != object_instance_graph_branch_id
            or existing_key != normalized_key
            or existing_view_key != normalized_view_key
            or existing.is_active != is_active
        ):
            raise RuntimeError(
                "ProgramBranch.build_via_program payload mismatch for existing association: "
                f"program_branch_id={assoc_id}"
            )
        return existing

    return ProgramBranch(
        id=assoc_id,
        program_id=program_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        key=normalized_key,
        view_key=normalized_view_key,
        is_active=is_active,
    )
    # --- AWARE: LOGIC END build_via_program
