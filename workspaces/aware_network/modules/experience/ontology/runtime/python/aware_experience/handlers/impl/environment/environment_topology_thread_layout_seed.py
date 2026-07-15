from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_topology_thread_layout_seed import (
    EnvironmentTopologyThreadLayoutSeed,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_topology_thread_layout_seed_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_environment_topology_thread_seed(
    environment_topology_thread_seed_id: UUID,
    layout_config_id: UUID,
    key: str | None = None,
    position: int | None = None,
    activate_on_seed: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentTopologyThreadLayoutSeed:
    """
    Construct one thread-layout seed.

    Contract:
    - `layout_config_id` must be allowed by the referenced ThreadConfig candidate set.
    - Attention still owns the LayoutConfig/SectionConfig topology.
    """

    # --- AWARE: LOGIC START build_via_environment_topology_thread_seed
    seed_id = stable_environment_topology_thread_layout_seed_id(
        environment_topology_thread_seed_id=environment_topology_thread_seed_id,
        layout_config_id=layout_config_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentTopologyThreadLayoutSeed, seed_id)
    if existing is not None:
        if (
            existing.environment_topology_thread_seed_id != environment_topology_thread_seed_id
            or existing.layout_config_id != layout_config_id
        ):
            raise RuntimeError(
                "EnvironmentTopologyThreadLayoutSeed.build_via_environment_topology_thread_seed "
                f"payload mismatch for existing layout seed: layout_seed_id={seed_id}"
            )
        return existing

    return EnvironmentTopologyThreadLayoutSeed(
        id=seed_id,
        environment_topology_thread_seed_id=environment_topology_thread_seed_id,
        layout_config_id=layout_config_id,
        key=(key or "").strip() or None,
        position=position,
        activate_on_seed=bool(activate_on_seed),
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END build_via_environment_topology_thread_seed
