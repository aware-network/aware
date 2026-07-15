from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread_config_layout_config_section import ThreadConfigLayoutConfigSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_thread_config_layout_config_section_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_thread_config_layout_config(
    thread_config_layout_config_id: UUID,
    layout_config_section_config_id: UUID,
    object_projection_graph_id: UUID | None = None,
    key: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> ThreadConfigLayoutConfigSection:
    """
    Create a deterministic ThreadConfigLayoutConfigSection edge.

    Contract:
    - Identity is scoped under ThreadConfigLayoutConfig by layout section config.
    - Optional OPG ref must point at a hosted projection graph for the same thread config.
    - No Experience-owned graph binding appears in this Environment topology object.
    """

    # --- AWARE: LOGIC START create_via_thread_config_layout_config
    thread_config_layout_config_section_id = stable_thread_config_layout_config_section_id(
        thread_config_layout_config_id=thread_config_layout_config_id,
        layout_config_section_config_id=layout_config_section_config_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(
        ThreadConfigLayoutConfigSection,
        thread_config_layout_config_section_id,
    )
    if existing is not None:
        if (
            existing.thread_config_layout_config_id != thread_config_layout_config_id
            or existing.layout_config_section_config_id != layout_config_section_config_id
        ):
            raise RuntimeError(
                "ThreadConfigLayoutConfigSection."
                "create_via_thread_config_layout_config mismatch for existing "
                f"thread_config_layout_config_section_id="
                f"{thread_config_layout_config_section_id}"
            )
        return existing

    return ThreadConfigLayoutConfigSection(
        id=thread_config_layout_config_section_id,
        thread_config_layout_config_id=thread_config_layout_config_id,
        layout_config_section_config_id=layout_config_section_config_id,
        object_projection_graph_id=object_projection_graph_id,
        key=key,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END create_via_thread_config_layout_config
