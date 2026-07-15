from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.section.section_focus_scope import SectionFocusScope

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_section_focus_scope_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_section(
    section_id: UUID, focus_scope_id: UUID, title: str, description: str | None = None
) -> SectionFocusScope:
    """
    Builds a deterministic SectionFocusScope.
    """

    # --- AWARE: LOGIC START build_via_section
    section_focus_scope_id = stable_section_focus_scope_id(
        section_id=section_id,
        focus_scope_id=focus_scope_id,
    )
    session = current_handler_session()
    existing = session.imap_get(SectionFocusScope, section_focus_scope_id)
    if existing is not None:
        if existing.title != title:
            existing.title = title
        if existing.description != description:
            existing.description = description
        return existing

    return SectionFocusScope(
        id=section_focus_scope_id,
        section_id=section_id,
        focus_scope_id=focus_scope_id,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_section
