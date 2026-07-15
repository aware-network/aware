from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneActionEvent
from aware_interface_ontology.render.pane_action_binding import PaneActionBinding
from aware_interface_ontology.render.pane_input_binding import PaneInputBinding

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import (
    stable_pane_action_binding_id,
    stable_pane_input_binding_id,
)

# --- AWARE: USER_IMPORTS END


async def bind_input(
    pane_action_binding: PaneActionBinding,
    payload_path: str,
    source_node_key: str | None = None,
    source_json_path: str | None = None,
    literal_value: str | None = None,
) -> PaneInputBinding:
    """
    Map local control values or canonical state into an action payload field.
    """

    # --- AWARE: LOGIC START bind_input
    if pane_action_binding.id is None:
        raise RuntimeError("PaneActionBinding.bind_input requires PaneActionBinding.id")
    input_id = stable_pane_input_binding_id(
        pane_action_binding_id=pane_action_binding.id,
        payload_path=payload_path,
    )
    for existing in pane_action_binding.input_bindings:
        if existing.id == input_id or existing.payload_path.casefold() == payload_path.casefold():
            existing.id = input_id
            existing.pane_action_binding_id = pane_action_binding.id
            existing.payload_path = payload_path
            existing.source_node_key = source_node_key
            existing.source_json_path = source_json_path
            existing.literal_value = literal_value
            return existing

    created = PaneInputBinding.model_construct(
        id=input_id,
        pane_action_binding_id=pane_action_binding.id,
        payload_path=payload_path,
        source_node_key=source_node_key,
        source_json_path=source_json_path,
        literal_value=literal_value,
    )
    pane_action_binding.input_bindings.append(created)
    return created
    # --- AWARE: LOGIC END bind_input


async def create_via_pane_render_node(
    pane_render_node_id: UUID,
    binding_key: str,
    event: PaneActionEvent,
    action_key: str,
    projection_experience_view_invocation_action_id: UUID | None = None,
    component_action_port_key: str | None = None,
    label: str | None = None,
    confirmation_policy: str | None = None,
    optimistic_policy: str | None = None,
    receipt_policy: str | None = None,
) -> PaneActionBinding:
    """
    Create one declarative action affordance binding.

    Contract:
    - `action_key` is the renderer-facing key for one Experience view invocation action.
    - `projection_experience_view_invocation_action` is canonical dispatch truth.
    - `component_action_port_key` names the component-emitted action port when this
      binding is attached to a component node.
    - Renderers may display this as a button, command, menu item, shortcut, or agent command.
    """

    # --- AWARE: LOGIC START create_via_pane_render_node
    return PaneActionBinding(
        id=stable_pane_action_binding_id(
            pane_render_node_id=pane_render_node_id,
            binding_key=binding_key,
        ),
        pane_render_node_id=pane_render_node_id,
        binding_key=binding_key,
        event=event,
        action_key=action_key,
        projection_experience_view_invocation_action_id=projection_experience_view_invocation_action_id,
        component_action_port_key=component_action_port_key,
        label=label,
        confirmation_policy=confirmation_policy,
        optimistic_policy=optimistic_policy,
        receipt_policy=receipt_policy,
    )
    # --- AWARE: LOGIC END create_via_pane_render_node
