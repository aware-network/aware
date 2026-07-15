from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_topology_process_seed import EnvironmentTopologyProcessSeed
from aware_experience_ontology.environment.environment_topology_seed import EnvironmentTopologySeed

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_topology_seed_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_process_seed(
    environment_topology_seed: EnvironmentTopologySeed,
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
    Add one runtime Process seed referencing a reusable Environment ProcessConfig.
    """

    # --- AWARE: LOGIC START add_process_seed
    topology_seed_id = environment_topology_seed.id
    if topology_seed_id is None:
        raise RuntimeError("EnvironmentTopologySeed.add_process_seed requires EnvironmentTopologySeed.id")
    normalized_process_key = (process_key or "").strip()
    if not normalized_process_key:
        raise RuntimeError("EnvironmentTopologySeed.add_process_seed requires non-empty process_key")

    created = await EnvironmentTopologyProcessSeed.build_via_environment_topology_seed(
        environment_topology_seed_id=topology_seed_id,
        process_config_id=process_config_id,
        process_key=normalized_process_key,
        key=(key or "").strip() or normalized_process_key,
        title=title,
        description=description,
        position=position,
        narrative=narrative,
        intent=intent,
    )

    for existing in environment_topology_seed.process_seeds:
        if existing.id == created.id:
            return existing
        if existing.process_key.strip().casefold() == normalized_process_key.casefold():
            raise RuntimeError(
                "EnvironmentTopologySeed.add_process_seed detected duplicate process_key "
                f"for topology seed: process_key={normalized_process_key!r}"
            )
    environment_topology_seed.process_seeds.append(created)
    return created
    # --- AWARE: LOGIC END add_process_seed


async def build_via_environment_experience(
    environment_experience_id: UUID,
    environment_experience_profile_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
) -> EnvironmentTopologySeed:
    """
    Construct one topology seed under an EnvironmentExperience.

    Contract:
    - Identity is scoped by EnvironmentExperience and seed key.
    - The referenced profile config supplies Experience config over Environment
      ProcessConfig/ThreadConfig contracts.
    - This seed supplies runtime process/thread/layout keys.
    """

    # --- AWARE: LOGIC START build_via_environment_experience
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentTopologySeed.build_via_environment_experience requires non-empty key")

    seed_id = stable_environment_topology_seed_id(
        environment_experience_id=environment_experience_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentTopologySeed, seed_id)
    if existing is not None:
        if (
            existing.environment_experience_id != environment_experience_id
            or existing.environment_experience_profile_config_id != environment_experience_profile_config_id
            or existing.key != normalized_key
        ):
            raise RuntimeError(
                "EnvironmentTopologySeed.build_via_environment_experience payload mismatch "
                f"for existing seed: topology_seed_id={seed_id}"
            )
        return existing

    return EnvironmentTopologySeed(
        id=seed_id,
        environment_experience_id=environment_experience_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        key=normalized_key,
        title=title,
        description=description,
        narrative=narrative,
    )
    # --- AWARE: LOGIC END build_via_environment_experience
