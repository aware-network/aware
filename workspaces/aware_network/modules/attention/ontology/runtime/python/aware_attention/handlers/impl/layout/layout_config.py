from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Attention Ontology
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
    stable_section_config_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(key: str, title: str, description: str | None = None) -> LayoutConfig:
    """
    Build a deterministic LayoutConfig by key.
    """

    # --- AWARE: LOGIC START build
    layout_config_id = stable_layout_config_id(key=key)
    session = current_handler_session()
    existing = session.imap_get(LayoutConfig, layout_config_id)
    if existing is not None:
        return existing
    return LayoutConfig(
        id=layout_config_id,
        key=key,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def add_section_config(
    layout_config: LayoutConfig,
    section_key: str,
    title: str,
    description: str | None = None,
    order: int = 0,
    flex: float = 1.0,
    is_visible: bool = True,
) -> LayoutConfigSectionConfig:
    """
    Add a SectionConfig binding to this LayoutConfig.
    """

    # --- AWARE: LOGIC START add_section_config
    layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config.id,
        section_key=section_key,
    )
    section_config_id = stable_section_config_id(
        layout_config_section_config_id=layout_config_section_config_id,
        key=section_key,
    )

    for existing in layout_config.section_configs:
        existing_section_config = existing.section_config
        existing_section_config_id = existing_section_config.id if existing_section_config is not None else None
        if existing.id == layout_config_section_config_id or existing_section_config_id == section_config_id:
            return existing

    layout_config_section_config = await LayoutConfigSectionConfig.create_via_layout_config(
        layout_config_id=layout_config.id,
        section_key=section_key,
        title=title,
        description=description,
        order=order,
        flex=flex,
        is_visible=is_visible,
    )
    layout_config.section_configs.append(layout_config_section_config)
    return layout_config_section_config
    # --- AWARE: LOGIC END add_section_config
