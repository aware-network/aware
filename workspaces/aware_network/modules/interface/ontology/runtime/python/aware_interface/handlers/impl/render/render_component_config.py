from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Interface Ontology
from aware_interface_ontology.render.render_component_config import RenderComponentConfig
from aware_interface_ontology.render.render_component_contract import RenderComponentContract

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(name: str, description: str | None = None) -> RenderComponentConfig:
    """
    Create one reusable render component contract root.

    Contract:
    - This is the semantic root for a render component package.
    - Contracts describe renderer-neutral component ports and requirements.
    - State and actions still arrive through PaneRenderSpec bindings and canonical API rails.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build


async def add_contract(
    render_component_config: RenderComponentConfig,
    component_ref: str,
    contract_version: int = 1,
    display_name: str | None = None,
    description: str | None = None,
    surface_kind: str | None = None,
) -> RenderComponentContract:
    """
    Add one reusable render component contract exposed by this config.
    """

    # --- AWARE: LOGIC START add_contract
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_contract
