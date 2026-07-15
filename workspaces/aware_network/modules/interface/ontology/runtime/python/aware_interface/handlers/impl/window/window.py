from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.window.window_enums import WindowActiveLayoutMode
from aware_interface_ontology.window.window import Window
from aware_interface_ontology.window.window_layout import WindowLayout

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface.stable_ids import stable_window_id, stable_window_layout_id

# --- AWARE: USER_IMPORTS END


async def build(window_id: UUID) -> Window:
    """
    Builds a new Window with a deterministic id.
    """

    # --- AWARE: LOGIC START build
    return Window(id=stable_window_id(window_id=window_id), window_id=window_id)
    # --- AWARE: LOGIC END build


async def add_layout(window: Window, layout_id: UUID) -> WindowLayout:
    """
    Attaches a Layout to this Window.
    """

    # --- AWARE: LOGIC START add_layout
    existing = next(
        (candidate for candidate in window.layouts if candidate.layout_id == layout_id),
        None,
    )
    if existing is not None:
        return existing

    attachment = WindowLayout.model_construct(
        id=stable_window_layout_id(
            window_id=window.id,
            layout_id=layout_id,
        ),
        window_id=window.id,
        layout_id=layout_id,
        layout=None,
        layout_sections=[],
    )
    window.layouts.append(attachment)
    return attachment
    # --- AWARE: LOGIC END add_layout


async def set_active_layout(
    window: Window, layout_id: UUID, mode: WindowActiveLayoutMode = WindowActiveLayoutMode.follow_thread_active
) -> None:
    """
    Sets the visible Attention Layout pointer for this Window without creating WindowLayout state.
    """

    # --- AWARE: LOGIC START set_active_layout
    window.active_layout_id = layout_id
    window.active_layout_mode = mode
    window.active_layout = None
    return None
    # --- AWARE: LOGIC END set_active_layout
