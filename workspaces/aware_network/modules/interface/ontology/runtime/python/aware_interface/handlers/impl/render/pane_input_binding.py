from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_input_binding import PaneInputBinding

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import stable_pane_input_binding_id

# --- AWARE: USER_IMPORTS END


async def create_via_pane_action_binding(
    pane_action_binding_id: UUID,
    payload_path: str,
    source_node_key: str | None = None,
    source_json_path: str | None = None,
    literal_value: str | None = None,
) -> PaneInputBinding:
    """
    Create one deterministic action payload binding.

    Contract:
    - Renderer-local input values are payload inputs only, never canonical state.
    - Canonical state values can be copied through `source_json_path`.
    - Constants can be supplied through `literal_value` for simple action payloads.
    """

    # --- AWARE: LOGIC START create_via_pane_action_binding
    return PaneInputBinding(
        id=stable_pane_input_binding_id(
            pane_action_binding_id=pane_action_binding_id,
            payload_path=payload_path,
        ),
        pane_action_binding_id=pane_action_binding_id,
        payload_path=payload_path,
        source_node_key=source_node_key,
        source_json_path=source_json_path,
        literal_value=literal_value,
    )
    # --- AWARE: LOGIC END create_via_pane_action_binding
