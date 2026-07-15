from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.layout.layout import Layout
from aware_attention_ontology.layout.layout_section import LayoutSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_layout_id
from aware_attention_ontology.section.section import Section
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(key: str, title: str, description: str | None = None) -> Layout:
    """
    Create a deterministic Layout by key.
    """

    # --- AWARE: LOGIC START build
    layout_id = stable_layout_id(key=key)
    session = current_handler_session()
    existing = session.imap_get(Layout, layout_id)
    if existing is not None:
        return existing
    return Layout(
        id=layout_id,
        key=key,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def add_section(layout: Layout, section_id: UUID, title: str, description: str | None = None) -> LayoutSection:
    """
    Adds a Section to this Layout.
    """

    # --- AWARE: LOGIC START add_section
    for existing in layout.sections:
        if existing.section_id == section_id:
            return existing

    session = current_handler_session()
    section = session.imap_get(Section, section_id)
    if section is None:
        section = Section(
            id=section_id,
            key=str(section_id),
            title=title,
            description=description,
        )

    layout_section = await LayoutSection.create_via_layout(
        layout_id=layout.id,
        section_id=section_id,
        order=0,
        flex=1.0,
        is_visible=True,
    )
    try:
        layout_section.section = section
    except Exception:
        pass
    layout.sections.append(layout_section)
    return layout_section
    # --- AWARE: LOGIC END add_section
