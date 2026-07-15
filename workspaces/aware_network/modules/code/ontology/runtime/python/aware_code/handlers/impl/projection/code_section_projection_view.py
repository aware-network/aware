from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.projection.code_section_projection_view import CodeSectionProjectionView

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_section_projection(
    code_section_projection_id: UUID, key: str, kind: str, is_default: bool = False, description: str | None = None
) -> CodeSectionProjectionView:
    """
    Build a deterministic projection-view entry under a projection.
    """

    # --- AWARE: LOGIC START build_via_code_section_projection
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section_projection
