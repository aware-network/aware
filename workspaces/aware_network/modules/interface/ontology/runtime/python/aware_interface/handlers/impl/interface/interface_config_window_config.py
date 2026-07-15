from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_config_window_config import InterfaceConfigWindowConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Interface Ontology
from aware_interface_ontology.interface.window_config import WindowConfig
from aware_interface_ontology.stable_ids import stable_interface_config_window_config_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_interface_config(interface_config_id: UUID, window_config_id: UUID) -> InterfaceConfigWindowConfig:
    """
    Create one deterministic InterfaceConfig↔WindowConfig composition join.

    Contract:
    - `WindowConfig` stays standalone Interface-side window namespace identity.
    - `InterfaceConfigWindowConfig` is the explicit composition rail for one interface package/config.
    - Pane placement remains section-scoped through pane/view/section agreements, not through this join.
    """

    # --- AWARE: LOGIC START build_via_interface_config
    edge_id = stable_interface_config_window_config_id(
        interface_config_id=interface_config_id,
        window_config_id=window_config_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_window_config = session.imap_get(WindowConfig, window_config_id) if session is not None else None
    if session is not None:
        existing = session.imap_get(InterfaceConfigWindowConfig, edge_id)
        if existing is not None:
            if existing.window_config_id not in (None, window_config_id):
                raise RuntimeError(
                    "InterfaceConfigWindowConfig existing window_config_id mismatch: "
                    f"interface_config_window_config_id={edge_id}"
                )
            if existing.window_config is None and resolved_window_config is not None:
                existing.window_config = resolved_window_config
            if existing.window_config_id is None:
                existing.window_config_id = window_config_id
            return existing

    if resolved_window_config is not None:
        return InterfaceConfigWindowConfig.model_construct(
            id=edge_id,
            interface_config_id=interface_config_id,
            window_config=resolved_window_config,
            window_config_id=window_config_id,
        )
    return InterfaceConfigWindowConfig.model_construct(
        id=edge_id,
        interface_config_id=interface_config_id,
        window_config_id=window_config_id,
    )
    # --- AWARE: LOGIC END build_via_interface_config
