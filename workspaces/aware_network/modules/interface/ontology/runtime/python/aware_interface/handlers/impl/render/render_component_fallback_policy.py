from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneRenderNodeKind
from aware_interface_ontology.render.render_component_fallback_policy import RenderComponentFallbackPolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_render_component_contract(
    render_component_contract_id: UUID,
    policy_key: str,
    fallback_kind: str,
    fallback_component_ref: str | None = None,
    fallback_node_kind: PaneRenderNodeKind | None = None,
    description: str | None = None,
) -> RenderComponentFallbackPolicy:
    """
    Create one deterministic component fallback policy.

    Contract:
    - Fallback policy is declared by the component package, not improvised by a pane renderer.
    - `fallback_component_ref` supports a less capable component replacement.
    - `fallback_node_kind` supports lowering to primitive PaneRenderSpec nodes.
    """

    # --- AWARE: LOGIC START build_via_render_component_contract
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_render_component_contract
