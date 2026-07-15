from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.section.section_config import SectionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_section_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_layout_config_section_config(
    layout_config_section_config_id: UUID, key: str, title: str, description: str | None = None
) -> SectionConfig:
    """
    Build a deterministic SectionConfig by key.
    """

    # --- AWARE: LOGIC START build_via_layout_config_section_config
    section_config_id = stable_section_config_id(
        layout_config_section_config_id=layout_config_section_config_id,
        key=key,
    )
    session = current_handler_session()
    existing = session.imap_get(SectionConfig, section_config_id)
    if existing is not None:
        return existing
    return SectionConfig(
        id=section_config_id,
        layout_config_section_config_id=layout_config_section_config_id,
        key=key,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_layout_config_section_config
