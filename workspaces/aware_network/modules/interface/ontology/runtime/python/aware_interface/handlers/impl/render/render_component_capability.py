from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.render_component_capability import RenderComponentCapability

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_render_component_contract(
    render_component_contract_id: UUID,
    capability_kind: str,
    capability_key: str,
    is_required: bool = True,
    description: str | None = None,
) -> RenderComponentCapability:
    """
    Create one renderer capability requirement or preference.

    Contract:
    - Capability kind/key are renderer-neutral labels.
    - Required capabilities must be satisfied or fall back according to policy.
    - Preferred capabilities may enhance native rendering without changing pane semantics.
    """

    # --- AWARE: LOGIC START build_via_render_component_contract
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_render_component_contract
