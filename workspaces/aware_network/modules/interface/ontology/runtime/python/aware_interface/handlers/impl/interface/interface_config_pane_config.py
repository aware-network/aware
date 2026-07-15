from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_config_pane_config import InterfaceConfigPaneConfig
from aware_interface_ontology.interface.interface_config_pane_config_section_config import (
    InterfaceConfigPaneConfigSectionConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.interface.pane_config import PaneConfig
from aware_interface_ontology.stable_ids import (
    stable_interface_config_pane_config_id,
    stable_interface_config_pane_config_section_config_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_section_mount(
    interface_config_pane_config: InterfaceConfigPaneConfig, layout_config_section_config_id: UUID
) -> InterfaceConfigPaneConfigSectionConfig:
    """
    Attach one Interface-scoped section mount for one standalone PaneConfig pane-view adapter.
    """

    # --- AWARE: LOGIC START add_section_mount
    if interface_config_pane_config.id is None:
        raise RuntimeError("InterfaceConfigPaneConfig.add_section_mount requires " "InterfaceConfigPaneConfig.id")

    binding_id = stable_interface_config_pane_config_section_config_id(
        interface_config_pane_config_id=interface_config_pane_config.id,
        layout_config_section_config_id=layout_config_section_config_id,
    )
    for existing in interface_config_pane_config.section_mounts:
        if existing.id == binding_id or existing.layout_config_section_config_id == layout_config_section_config_id:
            return existing

    created = InterfaceConfigPaneConfigSectionConfig.model_construct(
        id=binding_id,
        interface_config_pane_config_id=interface_config_pane_config.id,
        layout_config_section_config=None,
        layout_config_section_config_id=layout_config_section_config_id,
    )
    interface_config_pane_config.section_mounts.append(created)
    return created
    # --- AWARE: LOGIC END add_section_mount


async def set_narrative_key(
    interface_config_pane_config: InterfaceConfigPaneConfig, narrative_key: str | None = None
) -> InterfaceConfigPaneConfig:
    """
    Update the Interface-scoped pane narrative key on the join itself.

    InterfaceConfig must call this public method instead of mutating an
    existing join directly, preserving runtime mutation-boundary ownership.
    """

    # --- AWARE: LOGIC START set_narrative_key
    interface_config_pane_config.narrative_key = narrative_key
    return interface_config_pane_config
    # --- AWARE: LOGIC END set_narrative_key


async def build_via_interface_config(
    interface_config_id: UUID, pane_config_id: UUID, narrative_key: str | None = None
) -> InterfaceConfigPaneConfig:
    """
    Create one deterministic InterfaceConfig↔PaneConfig composition join.

    Contract:
    - `PaneConfig` stays standalone semantic pane identity.
    - `InterfaceConfigPaneConfig` is the explicit composition rail for one interface package/config.
    - Interface-scoped mount policy belongs under this join, not under the standalone pane semantic
    rail.
    """

    # --- AWARE: LOGIC START build_via_interface_config
    interface_config_pane_config_id = stable_interface_config_pane_config_id(
        interface_config_id=interface_config_id,
        pane_config_id=pane_config_id,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_pane_config = session.imap_get(PaneConfig, pane_config_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(InterfaceConfigPaneConfig, interface_config_pane_config_id)
        if existing is not None:
            if narrative_key is not None and existing.narrative_key != narrative_key:
                return await existing.set_narrative_key(narrative_key=narrative_key)
            return existing

    return InterfaceConfigPaneConfig.model_construct(
        id=interface_config_pane_config_id,
        interface_config_id=interface_config_id,
        pane_config=resolved_pane_config,
        pane_config_id=pane_config_id,
        narrative_key=narrative_key,
    )
    # --- AWARE: LOGIC END build_via_interface_config
