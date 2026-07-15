from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import (
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)
from aware_interface_ontology.render.pane_state_binding import PaneStateBinding

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import stable_pane_state_binding_id

# --- AWARE: USER_IMPORTS END


async def create_via_pane_render_node(
    pane_render_node_id: UUID,
    binding_key: str,
    target_property: PaneStateBindingTargetProperty,
    json_path: str,
    state_model_id: UUID | None = None,
    state_attribute_config_id: UUID | None = None,
    component_input_port_key: str | None = None,
    transform: PaneStateBindingTransform = PaneStateBindingTransform.raw,
    fallback_value: str | None = None,
) -> PaneStateBinding:
    """
    Create one relational binding from canonical Experience view state to a render property.

    Contract:
    - `state_model` points to ProjectionExperienceView.state_model when known.
    - `state_attribute_config` identifies the exact DTO attribute when available.
    - `json_path` is the materialized renderer path, not the source of semantic truth.
    - `target_property` is a bounded pane render target; `media_ref` carries
      StorageMediaRef pointers supplied by canonical view state.
    - `component_input_port_key` names the component input port this binding feeds;
      renderers must not infer unbound component inputs from pane state.
    - Transforms stay bounded and deterministic; complex behavior belongs in state providers.
    """

    # --- AWARE: LOGIC START create_via_pane_render_node
    return PaneStateBinding(
        id=stable_pane_state_binding_id(
            pane_render_node_id=pane_render_node_id,
            binding_key=binding_key,
        ),
        pane_render_node_id=pane_render_node_id,
        binding_key=binding_key,
        target_property=target_property,
        json_path=json_path,
        state_model_id=state_model_id,
        state_attribute_config_id=state_attribute_config_id,
        transform=transform,
        fallback_value=fallback_value,
    )
    # --- AWARE: LOGIC END create_via_pane_render_node
