from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_topology_process_seed import EnvironmentTopologyProcessSeed
from aware_experience_ontology.environment.environment_topology_thread_seed import EnvironmentTopologyThreadSeed

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_topology_process_seed_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_thread_seed(
    environment_topology_process_seed: EnvironmentTopologyProcessSeed,
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
    Add one runtime Thread seed referencing a reusable Environment ThreadConfig.
    """

    # --- AWARE: LOGIC START add_thread_seed
    process_seed_id = environment_topology_process_seed.id
    if process_seed_id is None:
        raise RuntimeError("EnvironmentTopologyProcessSeed.add_thread_seed requires EnvironmentTopologyProcessSeed.id")
    normalized_thread_key = (thread_key or "").strip()
    if not normalized_thread_key:
        raise RuntimeError("EnvironmentTopologyProcessSeed.add_thread_seed requires non-empty thread_key")

    created = await EnvironmentTopologyThreadSeed.build_via_environment_topology_process_seed(
        environment_topology_process_seed_id=process_seed_id,
        thread_config_id=thread_config_id,
        thread_key=normalized_thread_key,
        key=(key or "").strip() or normalized_thread_key,
        title=title,
        description=description,
        position=position,
        is_main=is_main,
        narrative=narrative,
        intent=intent,
    )

    for existing in environment_topology_process_seed.thread_seeds:
        if existing.id == created.id:
            return existing
        if existing.thread_key.strip().casefold() == normalized_thread_key.casefold():
            raise RuntimeError(
                "EnvironmentTopologyProcessSeed.add_thread_seed detected duplicate thread_key "
                f"for process seed: thread_key={normalized_thread_key!r}"
            )
    if bool(created.is_main):
        for existing in environment_topology_process_seed.thread_seeds:
            if bool(existing.is_main):
                raise RuntimeError("EnvironmentTopologyProcessSeed.add_thread_seed allows a single main thread seed")
    environment_topology_process_seed.thread_seeds.append(created)
    return created
    # --- AWARE: LOGIC END add_thread_seed


async def build_via_environment_topology_seed(
    environment_topology_seed_id: UUID,
    process_config_id: UUID,
    process_key: str,
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentTopologyProcessSeed:
    """
    Construct one process seed.

    Contract:
    - `process_config_id` is reusable Environment ProcessConfig truth.
    - `process_key` is runtime instance identity.
    """

    # --- AWARE: LOGIC START build_via_environment_topology_seed
    normalized_process_key = (process_key or "").strip()
    if not normalized_process_key:
        raise RuntimeError(
            "EnvironmentTopologyProcessSeed.build_via_environment_topology_seed requires non-empty process_key"
        )
    seed_id = stable_environment_topology_process_seed_id(
        environment_topology_seed_id=environment_topology_seed_id,
        process_config_id=process_config_id,
        process_key=normalized_process_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentTopologyProcessSeed, seed_id)
    if existing is not None:
        if (
            existing.environment_topology_seed_id != environment_topology_seed_id
            or existing.process_config_id != process_config_id
            or existing.process_key != normalized_process_key
        ):
            raise RuntimeError(
                "EnvironmentTopologyProcessSeed.build_via_environment_topology_seed payload mismatch "
                f"for existing process seed: process_seed_id={seed_id}"
            )
        return existing

    return EnvironmentTopologyProcessSeed(
        id=seed_id,
        environment_topology_seed_id=environment_topology_seed_id,
        process_config_id=process_config_id,
        process_key=normalized_process_key,
        key=(key or "").strip() or normalized_process_key,
        title=title,
        description=description,
        position=position,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END build_via_environment_topology_seed
