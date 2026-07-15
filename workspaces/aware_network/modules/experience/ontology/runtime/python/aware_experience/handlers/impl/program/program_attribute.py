from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_attribute import ProgramAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(program_id: UUID, config_id: UUID, attribute_id: UUID) -> ProgramAttribute:
    """
    Create deterministic attribute association edge for one Program.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build
