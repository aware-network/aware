from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneActionEvent
from aware_interface_ontology.render.render_component_action_port import RenderComponentActionPort

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_render_component_contract(
    render_component_contract_id: UUID,
    port_key: str,
    event: PaneActionEvent = PaneActionEvent.activate,
    is_required: bool = True,
    description: str | None = None,
) -> RenderComponentActionPort:
    """
    Create one explicit component action port.

    Contract:
    - Ports describe user/agent events emitted by the component.
    - PaneRenderSpec ActionBinding maps the port to a canonical API capability endpoint.
    - Components do not call services directly.
    """

    # --- AWARE: LOGIC START build_via_render_component_contract
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_render_component_contract
