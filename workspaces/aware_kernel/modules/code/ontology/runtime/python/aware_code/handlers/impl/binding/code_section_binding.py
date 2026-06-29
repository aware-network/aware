from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.binding.code_section_binding import CodeSectionBinding
from aware_code_ontology.binding.code_section_binding_map import CodeSectionBindingMap

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_map(
    code_section_binding: CodeSectionBinding,
    name: str,
    source_ref: str,
    target_ref: str,
    description: str | None = None,
    template_text: str | None = None,
) -> CodeSectionBindingMap:
    """
    Create a deterministic binding-map entry under this binding.
    """

    # --- AWARE: LOGIC START create_map
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_map


async def build_via_code_section(code_section_id: UUID) -> CodeSectionBinding:
    """
    Build the binding payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
