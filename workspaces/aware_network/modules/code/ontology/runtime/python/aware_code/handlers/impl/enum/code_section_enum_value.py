from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_section(code_section_id: UUID, value: str, position: int = 0) -> CodeSectionEnumValue:
    """
    Build the enum-value payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
