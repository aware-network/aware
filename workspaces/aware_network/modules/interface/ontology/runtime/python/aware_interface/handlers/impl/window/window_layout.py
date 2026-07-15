from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.window.window_layout import WindowLayout
from aware_interface_ontology.window.window_layout_section import WindowLayoutSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Interface
from aware_interface.stable_ids import stable_window_layout_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_layout_section(
    window_layout: WindowLayout, layout_section_id: UUID, projection_experience_view_id: UUID
) -> WindowLayoutSection:
    """
    Attach one section binding under this WindowLayout.
    """

    # --- AWARE: LOGIC START add_layout_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_layout_section


async def build_via_window(window_id: UUID, layout_id: UUID) -> WindowLayout:
    """
    Builds a deterministic WindowLayout attachment for (window, layout).
    """

    # --- AWARE: LOGIC START build_via_window
    window_layout_id = stable_window_layout_id(
        window_id=window_id,
        layout_id=layout_id,
    )
    session = current_handler_session()
    existing = session.imap_get(WindowLayout, window_layout_id)
    if existing is not None:
        return existing

    return WindowLayout(
        id=window_layout_id,
        window_id=window_id,
        layout_id=layout_id,
    )
    # --- AWARE: LOGIC END build_via_window
