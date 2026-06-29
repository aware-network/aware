from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection
from aware_code_ontology.projection.code_section_projection_edge import CodeSectionProjectionEdge
from aware_code_ontology.projection.code_section_projection_view import CodeSectionProjectionView

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_edge(
    code_section_projection: CodeSectionProjection, member: str, type_ref: str, target_projection_ref: str | None = None
) -> CodeSectionProjectionEdge:
    """
    Create a deterministic projection-edge entry under this projection.
    """

    # --- AWARE: LOGIC START create_edge
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_edge


async def create_view(
    code_section_projection: CodeSectionProjection,
    key: str,
    kind: str,
    is_default: bool = False,
    description: str | None = None,
) -> CodeSectionProjectionView:
    """
    Create a deterministic projection-view entry under this projection.
    """

    # --- AWARE: LOGIC START create_view
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_view


async def build_via_code_section(code_section_id: UUID) -> CodeSectionProjection:
    """
    Build the projection payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
