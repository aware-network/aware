from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.class_.code_section_class_base import CodeSectionClassBase

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_base(
    code_section_class: CodeSectionClass, base_ref: str, is_augment: bool = False
) -> CodeSectionClassBase:
    """
    Create a deterministic base entry under this class.
    """

    # --- AWARE: LOGIC START create_base
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_base


async def build_via_code_section(code_section_id: UUID) -> CodeSectionClass:
    """
    Build the class payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
