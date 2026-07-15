from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.binding.code_section_binding_map import CodeSectionBindingMap

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_section_binding(
    code_section_binding_id: UUID,
    name: str,
    source_ref: str,
    target_ref: str,
    description: str | None = None,
    template_text: str | None = None,
) -> CodeSectionBindingMap:
    """
    Build a deterministic binding-map entry under a binding.
    """

    # --- AWARE: LOGIC START build_via_code_section_binding
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section_binding
