from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.app_config import AppConfig
from aware_interface_ontology.interface.app_config_screen_config import AppConfigScreenConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(name: str, title: str | None = None, description: str | None = None) -> AppConfig:
    """
    Create one reusable app configuration.

    Contract:
    - AppConfig owns app-level screen selection intent.
    - Screen rows select Experience layout graph bindings.
    - AppConfig does not own Environment profile/session/process/thread truth.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build


async def attach_screen_config(
    app_config: AppConfig,
    screen_key: str,
    projection_experience_id: UUID,
    projection_experience_layout_graph_binding_id: UUID,
) -> AppConfigScreenConfig:
    """
    Attach one screen to this app config.

    Contract:
    - Parent AppConfig scope is injected by propagation.
    - The screen is a consumer entry point into Experience layout binding truth.
    - Runtime selection may activate Attention sessions later, but config does
      not mutate Attention or Environment state.
    """

    # --- AWARE: LOGIC START attach_screen_config
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_screen_config
