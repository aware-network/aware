from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.render_component_input_port import RenderComponentInputPort

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_render_component_contract(
    render_component_contract_id: UUID,
    port_key: str,
    value_kind: str,
    is_required: bool = True,
    description: str | None = None,
) -> RenderComponentInputPort:
    """
    Create one explicit component input port.

    Contract:
    - Ports are component-local names, not view-state paths.
    - PaneRenderSpec StateBinding supplies the data bound into each port.
    - Renderers must not infer missing input values from underlying pane state.
    """

    # --- AWARE: LOGIC START build_via_render_component_contract
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_render_component_contract
