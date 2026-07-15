from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.window_config import WindowConfig
from aware_interface_ontology.interface.window_config_layout_config import WindowConfigLayoutConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Interface Ontology
from aware_interface_ontology.stable_ids import (
    stable_window_config_id,
    stable_window_config_layout_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(key: str, description: str | None = None) -> WindowConfig:
    """
    Create one deterministic Interface-side window configuration.

    Contract:
    - `WindowConfig` is the authored/config namespace that names one interface window.
    - It composes attention-owned layouts through explicit joins.
    - It does not own pane semantics.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("WindowConfig.build requires non-empty key")

    window_config_id = stable_window_config_id(key=normalized_key)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(WindowConfig, window_config_id)
        if existing is not None:
            if (existing.key or "").strip() != normalized_key:
                raise RuntimeError(
                    "WindowConfig.build payload mismatch for existing window config: "
                    f"window_config_id={window_config_id}"
                )
            return existing

    return WindowConfig.model_construct(
        id=window_config_id,
        key=normalized_key,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def attach_layout_config(
    window_config: WindowConfig, layout_config_id: UUID, description: str | None = None, is_default: bool = False
) -> WindowConfigLayoutConfig:
    """
    Attach one attention-owned LayoutConfig to this Interface-side window configuration.
    """

    # --- AWARE: LOGIC START attach_layout_config
    if window_config.id is None:
        raise RuntimeError("WindowConfig.attach_layout_config requires WindowConfig.id")

    window_config_layout_config_id = stable_window_config_layout_config_id(
        window_config_id=window_config.id,
        layout_config_id=layout_config_id,
    )

    for existing in window_config.layout_configs:
        if existing.id == window_config_layout_config_id or existing.layout_config_id == layout_config_id:
            if existing.is_default != bool(is_default) or (
                description is not None and existing.description != description
            ):
                return await existing.set_attachment_config(
                    description=description,
                    is_default=is_default,
                )
            return existing

    created = WindowConfigLayoutConfig.model_construct(
        id=window_config_layout_config_id,
        window_config_id=window_config.id,
        layout_config=None,
        layout_config_id=layout_config_id,
        description=description,
        is_default=is_default,
    )
    window_config.layout_configs.append(created)
    return created
    # --- AWARE: LOGIC END attach_layout_config
