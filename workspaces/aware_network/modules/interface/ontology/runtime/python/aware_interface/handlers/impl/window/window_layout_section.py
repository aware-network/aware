from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.window.window_layout_section import WindowLayoutSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_window_layout(
    window_layout_id: UUID, layout_section_id: UUID, projection_experience_view_id: UUID
) -> WindowLayoutSection:
    """
    Builds a deterministic WindowLayoutSection attachment for (window_layout, layout_section).
    """

    # --- AWARE: LOGIC START build_via_window_layout
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_window_layout
