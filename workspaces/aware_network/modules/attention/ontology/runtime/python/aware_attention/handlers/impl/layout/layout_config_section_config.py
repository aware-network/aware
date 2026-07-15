from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.section.section_config import SectionConfig
from aware_attention_ontology.stable_ids import (
    stable_layout_config_section_config_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def set_geometry(
    layout_config_section_config: LayoutConfigSectionConfig, order: int, flex: float
) -> LayoutConfigSectionConfig:
    """
    Update section config order/flex geometry.
    """

    # --- AWARE: LOGIC START set_geometry
    changed = False
    if layout_config_section_config.order != order:
        layout_config_section_config.order = order
        changed = True
    if layout_config_section_config.flex != flex:
        layout_config_section_config.flex = flex
        changed = True
    if not changed:
        return layout_config_section_config
    return layout_config_section_config
    # --- AWARE: LOGIC END set_geometry


async def set_visibility(
    layout_config_section_config: LayoutConfigSectionConfig, is_visible: bool
) -> LayoutConfigSectionConfig:
    """
    Update whether this section config is visible in the LayoutConfig.
    """

    # --- AWARE: LOGIC START set_visibility
    if layout_config_section_config.is_visible == is_visible:
        return layout_config_section_config
    layout_config_section_config.is_visible = is_visible
    return layout_config_section_config
    # --- AWARE: LOGIC END set_visibility


async def create_via_layout_config(
    layout_config_id: UUID,
    section_key: str,
    title: str,
    description: str | None = None,
    order: int = 0,
    flex: float = 1.0,
    is_visible: bool = True,
) -> LayoutConfigSectionConfig:
    """
    Build a deterministic LayoutConfigSectionConfig for a LayoutConfig and SectionConfig.
    """

    # --- AWARE: LOGIC START create_via_layout_config
    layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key=section_key,
    )
    session = current_handler_session()
    existing = session.imap_get(LayoutConfigSectionConfig, layout_config_section_config_id)
    if existing is not None:
        return existing
    section_config = await SectionConfig.build_via_layout_config_section_config(
        layout_config_section_config_id=layout_config_section_config_id,
        key=section_key,
        title=title,
        description=description,
    )
    return LayoutConfigSectionConfig(
        id=layout_config_section_config_id,
        layout_config_id=layout_config_id,
        section_config=section_config,
        section_key=section_key,
        order=order,
        flex=flex,
        is_visible=is_visible,
    )
    # --- AWARE: LOGIC END create_via_layout_config
