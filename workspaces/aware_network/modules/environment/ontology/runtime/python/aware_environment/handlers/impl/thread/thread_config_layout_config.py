from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread_config_layout_config import ThreadConfigLayoutConfig
from aware_environment_ontology.thread.thread_config_layout_config_section import ThreadConfigLayoutConfigSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_thread_config_layout_config_id,
)

# --- AWARE: USER_IMPORTS END


async def add_section(
    thread_config_layout_config: ThreadConfigLayoutConfig,
    layout_config_section_config_id: UUID,
    object_projection_graph_id: UUID | None = None,
    key: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> ThreadConfigLayoutConfigSection:
    """
    Create a deterministic layout-section placement for this ThreadConfig layout.

    Contract:
    - Binds an Attention LayoutConfig section to an optional hosted projection graph.
    - Does not reference ProjectionExperienceSectionGraphBinding.
    """

    # --- AWARE: LOGIC START add_section
    if thread_config_layout_config.id is None:
        raise RuntimeError("ThreadConfigLayoutConfig.add_section requires ThreadConfigLayoutConfig.id")

    created = await ThreadConfigLayoutConfigSection.create_via_thread_config_layout_config(
        thread_config_layout_config_id=thread_config_layout_config.id,
        layout_config_section_config_id=layout_config_section_config_id,
        object_projection_graph_id=object_projection_graph_id,
        key=key,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
    )
    for existing in thread_config_layout_config.sections:
        if existing.id == created.id:
            return existing
    thread_config_layout_config.sections.append(created)
    return created
    # --- AWARE: LOGIC END add_section


async def create_via_thread_config(
    thread_config_id: UUID,
    layout_config_id: UUID,
    key: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> ThreadConfigLayoutConfig:
    """
    Create a deterministic ThreadConfigLayoutConfig association edge.

    Contract:
    - Identity is `(thread_config_id, layout_config_id)`.
    - Constructor is idempotent for repeated calls with the same pair.
    """

    # --- AWARE: LOGIC START create_via_thread_config
    thread_config_layout_config_id = stable_thread_config_layout_config_id(
        thread_config_id=thread_config_id,
        layout_config_id=layout_config_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(
        ThreadConfigLayoutConfig,
        thread_config_layout_config_id,
    )
    if existing is not None:
        if existing.thread_config_id != thread_config_id or existing.layout_config_id != layout_config_id:
            raise RuntimeError(
                "ThreadConfigLayoutConfig.create_via_thread_config mismatch "
                f"for existing thread_config_layout_config_id="
                f"{thread_config_layout_config_id}"
            )
        return existing

    return ThreadConfigLayoutConfig(
        id=thread_config_layout_config_id,
        thread_config_id=thread_config_id,
        layout_config_id=layout_config_id,
        key=key,
        position=position,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END create_via_thread_config
