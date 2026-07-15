from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.app_config_screen_config import AppConfigScreenConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_app_config(
    app_config_id: UUID,
    screen_key: str,
    projection_experience_id: UUID,
    projection_experience_layout_graph_binding_id: UUID,
) -> AppConfigScreenConfig:
    """
    Create one app screen config under an AppConfig.

    Contract:
    - `screen_key` is the app-owned entry token.
    - `projection_experience` is the Experience entry point.
    - `projection_experience_layout_graph_binding` is the Experience-owned
      layout-level binding for the screen.
    - The app does not target Environment internals or pane defaults.
    """

    # --- AWARE: LOGIC START build_via_app_config
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_app_config
