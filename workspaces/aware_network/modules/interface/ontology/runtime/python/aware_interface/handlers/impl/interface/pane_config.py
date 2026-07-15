from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.pane_config import PaneConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from uuid import UUID

from aware_interface_ontology.stable_ids import stable_pane_config_id

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    projection_experience_view_id: UUID,
    pane_kind: str,
    view_ref: str | None = None,
    description: str | None = None,
) -> PaneConfig:
    """
    Create one deterministic standalone pane-view adapter root.

    Contract:
    - PaneConfig is the Interface-owned render adapter for exactly one
      Experience projection view.
    - pane_kind is the stable cross-language implementation identity.
    - projection_experience_view is the stable pane-view identity key.
    - view_ref is authoring/debug metadata and must not become a second
      runtime identity rail.
    - A pane package must resolve its Experience view dependency without
      relying on a consuming InterfacePackage.
    - API/SDK invocation targets live on Experience projection-view invocation actions.
    - InterfaceConfig composes PaneConfig through `InterfaceConfigPaneConfig`; it does not
      permanently own pane identity.
    """

    # --- AWARE: LOGIC START build
    pane_config_id = stable_pane_config_id(
        name=name,
        projection_experience_view_id=projection_experience_view_id,
    )
    return PaneConfig(
        id=pane_config_id,
        projection_experience_view_id=projection_experience_view_id,
        projection_experience_view=None,
        name=name,
        pane_kind=pane_kind,
        view_ref=view_ref,
        description=description,
    )
    # --- AWARE: LOGIC END build
