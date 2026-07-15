from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_config_pane_config_section_config import (
    InterfaceConfigPaneConfigSectionConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import (
    stable_interface_config_pane_config_section_config_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_interface_config_pane_config(
    interface_config_pane_config_id: UUID, layout_config_section_config_id: UUID
) -> InterfaceConfigPaneConfigSectionConfig:
    """
    Create one deterministic Interface-scoped mount binding between this InterfaceConfigPaneConfig
    pane-view adapter and one layout section.
    """

    # --- AWARE: LOGIC START build_via_interface_config_pane_config
    binding_id = stable_interface_config_pane_config_section_config_id(
        interface_config_pane_config_id=interface_config_pane_config_id,
        layout_config_section_config_id=layout_config_section_config_id,
    )
    return InterfaceConfigPaneConfigSectionConfig(
        id=binding_id,
        interface_config_pane_config_id=interface_config_pane_config_id,
        layout_config_section_config_id=layout_config_section_config_id,
    )
    # --- AWARE: LOGIC END build_via_interface_config_pane_config
