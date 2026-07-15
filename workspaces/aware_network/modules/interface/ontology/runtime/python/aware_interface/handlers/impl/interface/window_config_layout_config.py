from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.window_config_layout_config import WindowConfigLayoutConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Attention Ontology
from aware_attention_ontology.layout.layout_config import LayoutConfig

# Interface Ontology
from aware_interface_ontology.stable_ids import stable_window_config_layout_config_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def set_attachment_config(
    window_config_layout_config: WindowConfigLayoutConfig, description: str | None = None, is_default: bool = False
) -> WindowConfigLayoutConfig:
    """
    Update the WindowConfig-scoped layout attachment on the join itself.
    """

    # --- AWARE: LOGIC START set_attachment_config
    if description is not None:
        window_config_layout_config.description = description
    window_config_layout_config.is_default = bool(is_default)
    return window_config_layout_config
    # --- AWARE: LOGIC END set_attachment_config


async def build_via_window_config(
    window_config_id: UUID, layout_config_id: UUID, description: str | None = None, is_default: bool = False
) -> WindowConfigLayoutConfig:
    """
    Create one deterministic WindowConfig↔LayoutConfig bridge.
    """

    # --- AWARE: LOGIC START build_via_window_config
    edge_id = stable_window_config_layout_config_id(
        window_config_id=window_config_id,
        layout_config_id=layout_config_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_layout_config = session.imap_get(LayoutConfig, layout_config_id) if session is not None else None
    if session is not None:
        existing = session.imap_get(WindowConfigLayoutConfig, edge_id)
        if existing is not None:
            if existing.layout_config_id not in (None, layout_config_id):
                raise RuntimeError(
                    "WindowConfigLayoutConfig existing layout_config_id mismatch: "
                    f"window_config_layout_config_id={edge_id}"
                )
            if description is not None and existing.description not in (None, description):
                raise RuntimeError(
                    "WindowConfigLayoutConfig existing description mismatch: "
                    f"window_config_layout_config_id={edge_id}"
                )
            if description is not None or existing.is_default != bool(is_default):
                return await existing.set_attachment_config(
                    description=description,
                    is_default=is_default,
                )
            return existing

    if resolved_layout_config is not None:
        return WindowConfigLayoutConfig.model_construct(
            id=edge_id,
            window_config_id=window_config_id,
            layout_config=resolved_layout_config,
            layout_config_id=layout_config_id,
            description=description,
            is_default=bool(is_default),
        )
    return WindowConfigLayoutConfig.model_construct(
        id=edge_id,
        window_config_id=window_config_id,
        layout_config_id=layout_config_id,
        description=description,
        is_default=bool(is_default),
    )
    # --- AWARE: LOGIC END build_via_window_config
