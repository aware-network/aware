from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import (
    PaneRenderCapabilityKind,
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
)
from aware_interface_ontology.render.pane_render_node import PaneRenderNode
from aware_interface_ontology.render.pane_render_spec import PaneRenderSpec
from aware_interface_ontology.render.pane_renderer_capability_requirement import PaneRendererCapabilityRequirement

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import (
    stable_pane_render_spec_id,
    stable_pane_render_node_id,
    stable_pane_renderer_capability_requirement_id,
)

# --- AWARE: USER_IMPORTS END


async def create(
    pane_config_id: UUID,
    name: str,
    spec_version: str,
    root_node_key: str,
    view_ref: str | None = None,
    projection_view_key: str | None = None,
    state_model_id: UUID | None = None,
    description: str | None = None,
) -> PaneRenderSpec:
    """
    Create one deterministic renderer-neutral render spec for a pane/view binding.

    Contract:
    - Pane remains the canonical UI unit.
    - This spec starts after PaneConfig and never replaces
      Attention, FocusScope, ProjectionView, or PaneConfig truth.
    - Nodes and bindings are declarative data so renderers can interpret the same
      visual, semantic, and command contract without dynamic code loading.
    """

    # --- AWARE: LOGIC START create
    pane_render_spec_id = stable_pane_render_spec_id(
        pane_config_id=pane_config_id,
        name=name,
        spec_version=spec_version,
    )
    return PaneRenderSpec(
        id=pane_render_spec_id,
        pane_config_id=pane_config_id,
        name=name,
        spec_version=spec_version,
        root_node_key=root_node_key,
        view_ref=view_ref,
        projection_view_key=projection_view_key,
        state_model_id=state_model_id,
        description=description,
    )
    # --- AWARE: LOGIC END create


async def add_node(
    pane_render_spec: PaneRenderSpec,
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
    Add one ordered semantic render node to this spec.
    """

    # --- AWARE: LOGIC START add_node
    if pane_render_spec.id is None:
        raise RuntimeError("PaneRenderSpec.add_node requires PaneRenderSpec.id")
    node_id = stable_pane_render_node_id(
        pane_render_spec_id=pane_render_spec.id,
        node_key=node_key,
    )
    for existing in pane_render_spec.nodes:
        if existing.id == node_id or existing.node_key.casefold() == node_key.casefold():
            existing.id = node_id
            existing.pane_render_spec_id = pane_render_spec.id
            existing.node_key = node_key
            existing.node_kind = node_kind
            existing.semantic_role = semantic_role
            existing.parent_node_key = parent_node_key
            existing.slot_key = slot_key
            existing.order = order
            existing.label = label
            existing.text = text
            existing.placeholder = placeholder
            existing.component_ref = component_ref
            existing.component_contract_id = component_contract_id
            existing.fallback_node_kind = fallback_node_kind
            existing.fallback_text = fallback_text
            if getattr(existing, "state_bindings", None) is None:
                existing.state_bindings = []
            if getattr(existing, "action_bindings", None) is None:
                existing.action_bindings = []
            if getattr(existing, "style_tokens", None) is None:
                existing.style_tokens = []
            if not hasattr(existing, "component_contract"):
                existing.component_contract = None
            return existing

    created = PaneRenderNode.model_construct(
        id=node_id,
        pane_render_spec_id=pane_render_spec.id,
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
        state_bindings=[],
        action_bindings=[],
        style_tokens=[],
        component_contract=None,
    )
    pane_render_spec.nodes.append(created)
    return created
    # --- AWARE: LOGIC END add_node


async def require_renderer_capability(
    pane_render_spec: PaneRenderSpec,
    capability_kind: PaneRenderCapabilityKind,
    capability_key: str,
    is_required: bool = True,
) -> PaneRendererCapabilityRequirement:
    """
    Declare one renderer capability required or preferred by this render spec.
    """

    # --- AWARE: LOGIC START require_renderer_capability
    if pane_render_spec.id is None:
        raise RuntimeError("PaneRenderSpec.require_renderer_capability requires PaneRenderSpec.id")
    capability_kind_value = capability_kind.value if hasattr(capability_kind, "value") else str(capability_kind)
    requirement_id = stable_pane_renderer_capability_requirement_id(
        pane_render_spec_id=pane_render_spec.id,
        capability_kind=capability_kind_value,
        capability_key=capability_key,
    )
    for existing in pane_render_spec.renderer_requirements:
        existing_kind = (
            existing.capability_kind.value
            if hasattr(existing.capability_kind, "value")
            else str(existing.capability_kind)
        )
        if existing.id == requirement_id or (
            existing_kind.casefold() == capability_kind_value.casefold()
            and existing.capability_key.casefold() == capability_key.casefold()
        ):
            existing.id = requirement_id
            existing.pane_render_spec_id = pane_render_spec.id
            existing.capability_kind = capability_kind
            existing.capability_key = capability_key
            existing.is_required = bool(is_required)
            return existing

    created = PaneRendererCapabilityRequirement.model_construct(
        id=requirement_id,
        pane_render_spec_id=pane_render_spec.id,
        capability_kind=capability_kind,
        capability_key=capability_key,
        is_required=bool(is_required),
    )
    pane_render_spec.renderer_requirements.append(created)
    return created
    # --- AWARE: LOGIC END require_renderer_capability
