from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderNodeKind,
)
from aware_interface_ontology.render.render_component_action_port import RenderComponentActionPort
from aware_interface_ontology.render.render_component_capability import RenderComponentCapability
from aware_interface_ontology.render.render_component_contract import RenderComponentContract
from aware_interface_ontology.render.render_component_fallback_policy import RenderComponentFallbackPolicy
from aware_interface_ontology.render.render_component_input_port import RenderComponentInputPort

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def add_input_port(
    render_component_contract: RenderComponentContract,
    port_key: str,
    value_kind: str,
    is_required: bool = True,
    description: str | None = None,
) -> RenderComponentInputPort:
    """
    Add one explicit state/data input port.
    """

    # --- AWARE: LOGIC START add_input_port
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_input_port


async def add_action_port(
    render_component_contract: RenderComponentContract,
    port_key: str,
    event: PaneActionEvent = PaneActionEvent.activate,
    is_required: bool = True,
    description: str | None = None,
) -> RenderComponentActionPort:
    """
    Add one explicit action output port.
    """

    # --- AWARE: LOGIC START add_action_port
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_action_port


async def require_capability(
    render_component_contract: RenderComponentContract,
    capability_kind: str,
    capability_key: str,
    is_required: bool = True,
    description: str | None = None,
) -> RenderComponentCapability:
    """
    Declare one renderer capability required or preferred by this component.
    """

    # --- AWARE: LOGIC START require_capability
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END require_capability


async def add_fallback_policy(
    render_component_contract: RenderComponentContract,
    policy_key: str,
    fallback_kind: str,
    fallback_component_ref: str | None = None,
    fallback_node_kind: PaneRenderNodeKind | None = None,
    description: str | None = None,
) -> RenderComponentFallbackPolicy:
    """
    Declare how renderers should degrade when this component cannot be mounted.
    """

    # --- AWARE: LOGIC START add_fallback_policy
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_fallback_policy


async def build_via_render_component_config(
    render_component_config_id: UUID,
    component_ref: str,
    contract_version: int = 1,
    display_name: str | None = None,
    description: str | None = None,
    surface_kind: str | None = None,
) -> RenderComponentContract:
    """
    Create one renderer-neutral component contract.

    Contract:
    - `component_ref` is the stable reference PaneRenderSpec will use when selecting a
      reusable render component.
    - Input ports receive explicitly bound pane/view state.
    - Action ports emit canonical pane/API actions through ActionBinding.
    - Capabilities and fallback policies let renderers degrade without guessing pane state.
    """

    # --- AWARE: LOGIC START build_via_render_component_config
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_render_component_config
