from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneRenderCapabilityKind
from aware_interface_ontology.render.pane_renderer_capability_requirement import PaneRendererCapabilityRequirement

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import stable_pane_renderer_capability_requirement_id

# --- AWARE: USER_IMPORTS END


async def create_via_pane_render_spec(
    pane_render_spec_id: UUID, capability_kind: PaneRenderCapabilityKind, capability_key: str, is_required: bool = True
) -> PaneRendererCapabilityRequirement:
    """
    Declare one required or preferred renderer capability.

    Contract:
    - Renderers decide whether they can satisfy a PaneRenderSpec before attempting render.
    - Fallback remains a renderer/package policy until the spec grows explicit fallback nodes.
    """

    # --- AWARE: LOGIC START create_via_pane_render_spec
    capability_kind_value = capability_kind.value if hasattr(capability_kind, "value") else str(capability_kind)
    return PaneRendererCapabilityRequirement(
        id=stable_pane_renderer_capability_requirement_id(
            pane_render_spec_id=pane_render_spec_id,
            capability_kind=capability_kind_value,
            capability_key=capability_key,
        ),
        pane_render_spec_id=pane_render_spec_id,
        capability_kind=capability_kind,
        capability_key=capability_key,
        is_required=bool(is_required),
    )
    # --- AWARE: LOGIC END create_via_pane_render_spec
