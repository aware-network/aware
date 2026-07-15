from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.section.section import Section
from aware_attention_ontology.section.section_focus_scope import SectionFocusScope

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_section_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(key: str, title: str, description: str | None = None) -> Section:
    """
    Builds a deterministic Section for a key.
    """

    # --- AWARE: LOGIC START build
    section_id = stable_section_id(key=key)
    session = current_handler_session()
    existing = session.imap_get(Section, section_id)
    if existing is not None:
        return existing
    return Section(
        id=section_id,
        key=key,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def add_focus_scope(
    section: Section, focus_scope_id: UUID, title: str, description: str | None = None
) -> SectionFocusScope:
    """
    Adds a FocusScope binding to this Section.
    """

    # --- AWARE: LOGIC START add_focus_scope
    for existing in section.focus_scopes:
        if existing.focus_scope_id == focus_scope_id:
            return existing

    section_focus_scope = await SectionFocusScope.build_via_section(
        section_id=section.id,
        focus_scope_id=focus_scope_id,
        title=title,
        description=description,
    )
    section.focus_scopes.append(section_focus_scope)
    return section_focus_scope
    # --- AWARE: LOGIC END add_focus_scope


async def set_active_focus_scope(section: Section, focus_scope_id: UUID) -> SectionFocusScope:
    """
    Set active_focus_scope to the given focus_scope_id.
    """

    # --- AWARE: LOGIC START set_active_focus_scope
    section_focus_scope: SectionFocusScope | None = next(
        (scope for scope in section.focus_scopes if scope.focus_scope_id == focus_scope_id),
        None,
    )
    if section_focus_scope is None:
        raise RuntimeError(
            "Section.set_active_focus_scope requires an existing focus scope binding. "
            "Call Section.add_focus_scope(...) first."
        )
    if section.active_focus_scope_id == section_focus_scope.id:
        return section_focus_scope

    section.active_focus_scope_id = section_focus_scope.id
    try:
        section.active_focus_scope = section_focus_scope
    except Exception:
        pass
    return section_focus_scope
    # --- AWARE: LOGIC END set_active_focus_scope
