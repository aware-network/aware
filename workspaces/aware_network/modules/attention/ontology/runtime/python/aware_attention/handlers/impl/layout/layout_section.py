from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.layout.layout_section import LayoutSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_layout_section_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def set_geometry(layout_section: LayoutSection, order: int, flex: float) -> LayoutSection:
    """
    Updates section order/flex geometry.
    """

    # --- AWARE: LOGIC START set_geometry
    changed = False
    if layout_section.order != order:
        layout_section.order = order
        changed = True
    if layout_section.flex != flex:
        layout_section.flex = flex
        changed = True
    if not changed:
        return layout_section
    return layout_section
    # --- AWARE: LOGIC END set_geometry


async def set_visibility(layout_section: LayoutSection, is_visible: bool) -> LayoutSection:
    """
    Updates whether this section is visible in the Layout.
    """

    # --- AWARE: LOGIC START set_visibility
    if layout_section.is_visible == is_visible:
        return layout_section
    layout_section.is_visible = is_visible
    return layout_section
    # --- AWARE: LOGIC END set_visibility


async def create_via_layout(
    layout_id: UUID, section_id: UUID, order: int = 0, flex: float = 1.0, is_visible: bool = True
) -> LayoutSection:
    """
    Creates a deterministic LayoutSection for a Layout and Section.
    """

    # --- AWARE: LOGIC START create_via_layout
    layout_section_id = stable_layout_section_id(
        layout_id=layout_id,
        section_id=section_id,
    )
    session = current_handler_session()
    existing = session.imap_get(LayoutSection, layout_section_id)
    if existing is not None:
        return existing
    return LayoutSection(
        id=layout_section_id,
        layout_id=layout_id,
        section_id=section_id,
        order=order,
        flex=flex,
        is_visible=is_visible,
    )
    # --- AWARE: LOGIC END create_via_layout
