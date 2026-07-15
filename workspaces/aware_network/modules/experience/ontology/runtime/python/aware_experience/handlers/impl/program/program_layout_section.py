from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_layout_section import ProgramLayoutSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(
    layout_id: UUID,
    key: str,
    order: int = 0,
    is_visible: bool = True,
    flex: float | None = None,
    is_active: bool = False,
    view_key: str | None = None,
    program_branch_id: UUID | None = None,
    port_section_id: UUID | None = None,
) -> ProgramLayoutSection:
    """
    Create a deterministic ProgramLayoutSection under a Program.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build
