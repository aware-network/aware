from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_layout import ProgramLayout

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(program_id: UUID, key: str, config_id: UUID | None = None, is_active: bool = False) -> ProgramLayout:
    """
    Create a deterministic ProgramLayout under a Program.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build
