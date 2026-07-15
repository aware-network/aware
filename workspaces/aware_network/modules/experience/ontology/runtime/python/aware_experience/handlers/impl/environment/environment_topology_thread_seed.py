from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_topology_thread_layout_seed import (
    EnvironmentTopologyThreadLayoutSeed,
)
from aware_experience_ontology.environment.environment_topology_thread_seed import EnvironmentTopologyThreadSeed

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_topology_thread_seed_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_layout_seed(
    environment_topology_thread_seed: EnvironmentTopologyThreadSeed,
    layout_config_id: UUID,
    key: str | None = None,
    position: int | None = None,
    activate_on_seed: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentTopologyThreadLayoutSeed:
    """
    Add one layout activation seed referencing a ThreadConfig layout candidate.
    """

    # --- AWARE: LOGIC START add_layout_seed
    thread_seed_id = environment_topology_thread_seed.id
    if thread_seed_id is None:
        raise RuntimeError("EnvironmentTopologyThreadSeed.add_layout_seed requires EnvironmentTopologyThreadSeed.id")

    created = await EnvironmentTopologyThreadLayoutSeed.build_via_environment_topology_thread_seed(
        environment_topology_thread_seed_id=thread_seed_id,
        layout_config_id=layout_config_id,
        key=key,
        position=position,
        activate_on_seed=activate_on_seed,
        narrative=narrative,
        intent=intent,
    )

    for existing in environment_topology_thread_seed.layout_seeds:
        if existing.id == created.id:
            return existing
        if existing.layout_config_id == layout_config_id:
            raise RuntimeError(
                "EnvironmentTopologyThreadSeed.add_layout_seed detected duplicate layout_config_id "
                f"for thread seed: layout_config_id={layout_config_id}"
            )
    if bool(created.activate_on_seed):
        for existing in environment_topology_thread_seed.layout_seeds:
            if bool(existing.activate_on_seed):
                raise RuntimeError("EnvironmentTopologyThreadSeed.add_layout_seed allows a single active layout seed")
    environment_topology_thread_seed.layout_seeds.append(created)
    return created
    # --- AWARE: LOGIC END add_layout_seed


async def build_via_environment_topology_process_seed(
    environment_topology_process_seed_id: UUID,
    thread_config_id: UUID,
    thread_key: str,
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    is_main: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentTopologyThreadSeed:
    """
    Construct one thread seed.

    Contract:
    - `thread_config_id` is reusable Environment ThreadConfig truth.
    - `thread_key` is runtime instance identity.
    """

    # --- AWARE: LOGIC START build_via_environment_topology_process_seed
    normalized_thread_key = (thread_key or "").strip()
    if not normalized_thread_key:
        raise RuntimeError(
            "EnvironmentTopologyThreadSeed.build_via_environment_topology_process_seed requires non-empty thread_key"
        )
    seed_id = stable_environment_topology_thread_seed_id(
        environment_topology_process_seed_id=environment_topology_process_seed_id,
        thread_config_id=thread_config_id,
        thread_key=normalized_thread_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentTopologyThreadSeed, seed_id)
    if existing is not None:
        if (
            existing.environment_topology_process_seed_id != environment_topology_process_seed_id
            or existing.thread_config_id != thread_config_id
            or existing.thread_key != normalized_thread_key
        ):
            raise RuntimeError(
                "EnvironmentTopologyThreadSeed.build_via_environment_topology_process_seed payload mismatch "
                f"for existing thread seed: thread_seed_id={seed_id}"
            )
        return existing

    return EnvironmentTopologyThreadSeed(
        id=seed_id,
        environment_topology_process_seed_id=environment_topology_process_seed_id,
        thread_config_id=thread_config_id,
        thread_key=normalized_thread_key,
        key=(key or "").strip() or normalized_thread_key,
        title=title,
        description=description,
        position=position,
        is_main=bool(is_main),
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END build_via_environment_topology_process_seed
