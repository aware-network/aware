from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)
from aware_interface_ontology.render.pane_action_binding import PaneActionBinding
from aware_interface_ontology.render.pane_render_node import PaneRenderNode
from aware_interface_ontology.render.pane_state_binding import PaneStateBinding
from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import (
    stable_pane_action_binding_id,
    stable_pane_render_node_id,
    stable_pane_state_binding_id,
    stable_pane_style_token_ref_id,
)

# --- AWARE: USER_IMPORTS END


async def bind_state(
    pane_render_node: PaneRenderNode,
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
    Bind one canonical view-state value to one render-node property.
    """

    # --- AWARE: LOGIC START bind_state
    if pane_render_node.id is None:
        raise RuntimeError("PaneRenderNode.bind_state requires PaneRenderNode.id")
    binding_id = stable_pane_state_binding_id(
        pane_render_node_id=pane_render_node.id,
        binding_key=binding_key,
    )
    for existing in pane_render_node.state_bindings:
        if existing.id == binding_id or existing.binding_key.casefold() == binding_key.casefold():
            existing.id = binding_id
            existing.pane_render_node_id = pane_render_node.id
            existing.binding_key = binding_key
            existing.target_property = target_property
            existing.json_path = json_path
            existing.state_model_id = state_model_id
            existing.state_attribute_config_id = state_attribute_config_id
            existing.component_input_port_key = component_input_port_key
            existing.transform = transform
            existing.fallback_value = fallback_value
            return existing

    created = PaneStateBinding.model_construct(
        id=binding_id,
        pane_render_node_id=pane_render_node.id,
        binding_key=binding_key,
        target_property=target_property,
        json_path=json_path,
        state_model_id=state_model_id,
        state_attribute_config_id=state_attribute_config_id,
        component_input_port_key=component_input_port_key,
        transform=transform,
        fallback_value=fallback_value,
    )
    pane_render_node.state_bindings.append(created)
    return created
    # --- AWARE: LOGIC END bind_state


async def bind_action(
    pane_render_node: PaneRenderNode,
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
    Bind a node event to one Experience view invocation action.
    """

    # --- AWARE: LOGIC START bind_action
    if pane_render_node.id is None:
        raise RuntimeError("PaneRenderNode.bind_action requires PaneRenderNode.id")
    binding_id = stable_pane_action_binding_id(
        pane_render_node_id=pane_render_node.id,
        binding_key=binding_key,
    )
    for existing in pane_render_node.action_bindings:
        if existing.id == binding_id or existing.binding_key.casefold() == binding_key.casefold():
            existing.id = binding_id
            existing.pane_render_node_id = pane_render_node.id
            existing.binding_key = binding_key
            existing.event = event
            existing.action_key = action_key
            existing.projection_experience_view_invocation_action_id = projection_experience_view_invocation_action_id
            existing.component_action_port_key = component_action_port_key
            existing.label = label
            existing.confirmation_policy = confirmation_policy
            existing.optimistic_policy = optimistic_policy
            existing.receipt_policy = receipt_policy
            if getattr(existing, "input_bindings", None) is None:
                existing.input_bindings = []
            return existing

    created = PaneActionBinding.model_construct(
        id=binding_id,
        pane_render_node_id=pane_render_node.id,
        binding_key=binding_key,
        event=event,
        action_key=action_key,
        projection_experience_view_invocation_action_id=projection_experience_view_invocation_action_id,
        component_action_port_key=component_action_port_key,
        label=label,
        confirmation_policy=confirmation_policy,
        optimistic_policy=optimistic_policy,
        receipt_policy=receipt_policy,
        input_bindings=[],
    )
    pane_render_node.action_bindings.append(created)
    return created
    # --- AWARE: LOGIC END bind_action


async def add_style_token(
    pane_render_node: PaneRenderNode, token_key: str, token_value: str | None = None
) -> PaneStyleTokenRef:
    """
    Attach one semantic style token to this node.
    """

    # --- AWARE: LOGIC START add_style_token
    if pane_render_node.id is None:
        raise RuntimeError("PaneRenderNode.add_style_token requires PaneRenderNode.id")
    token_id = stable_pane_style_token_ref_id(
        pane_render_node_id=pane_render_node.id,
        token_key=token_key,
    )
    for existing in pane_render_node.style_tokens:
        if existing.id == token_id or existing.token_key.casefold() == token_key.casefold():
            existing.id = token_id
            existing.pane_render_node_id = pane_render_node.id
            existing.token_key = token_key
            existing.token_value = token_value
            return existing

    created = PaneStyleTokenRef.model_construct(
        id=token_id,
        pane_render_node_id=pane_render_node.id,
        token_key=token_key,
        token_value=token_value,
    )
    pane_render_node.style_tokens.append(created)
    return created
    # --- AWARE: LOGIC END add_style_token


async def create_via_pane_render_spec(
    pane_render_spec_id: UUID,
    node_key: str,
    node_kind: PaneRenderNodeKind,
    semantic_role: PaneRenderSemanticRole | None = None,
    parent_node_key: str | None = None,
    slot_key: str | None = None,
    order: int = 0,
    label: str | None = None,
    text: str | None = None,
    placeholder: str | None = None,
    component_ref: str | None = None,
    component_contract_id: UUID | None = None,
    fallback_node_kind: PaneRenderNodeKind | None = None,
    fallback_text: str | None = None,
) -> PaneRenderNode:
    """
    Create one semantic render node inside its owning PaneRenderSpec.

    Contract:
    - `node_kind` is renderer-neutral intent, not a Flutter/HTML class.
    - `parent_node_key` keeps the materialized tree relational and commit-friendly.
    - Exact state and action truth is attached through bindings, not local scripts.
    - Component nodes use `component_ref` to select a RenderComponentContract.
      They still receive state/actions only through explicit bindings.
    """

    # --- AWARE: LOGIC START create_via_pane_render_spec
    node_id = stable_pane_render_node_id(
        pane_render_spec_id=pane_render_spec_id,
        node_key=node_key,
    )
    return PaneRenderNode(
        id=node_id,
        pane_render_spec_id=pane_render_spec_id,
        node_key=node_key,
        node_kind=node_kind,
        semantic_role=semantic_role,
        parent_node_key=parent_node_key,
        slot_key=slot_key,
        order=order,
        label=label,
        text=text,
        placeholder=placeholder,
        component_ref=component_ref,
        component_contract_id=component_contract_id,
        fallback_node_kind=fallback_node_kind,
        fallback_text=fallback_text,
    )
    # --- AWARE: LOGIC END create_via_pane_render_spec
