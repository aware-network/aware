from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import stable_pane_style_token_ref_id

# --- AWARE: USER_IMPORTS END


async def create_via_pane_render_node(
    pane_render_node_id: UUID, token_key: str, token_value: str | None = None
) -> PaneStyleTokenRef:
    """
    Attach renderer-adaptive style intent to a render node.

    Contract:
    - Tokens express semantic intent such as emphasis, density, status, or destructive.
    - Exact Flutter/CSS/Textual styling remains renderer policy, not ontology truth.
    """

    # --- AWARE: LOGIC START create_via_pane_render_node
    return PaneStyleTokenRef(
        id=stable_pane_style_token_ref_id(
            pane_render_node_id=pane_render_node_id,
            token_key=token_key,
        ),
        pane_render_node_id=pane_render_node_id,
        token_key=token_key,
        token_value=token_value,
    )
    # --- AWARE: LOGIC END create_via_pane_render_node
