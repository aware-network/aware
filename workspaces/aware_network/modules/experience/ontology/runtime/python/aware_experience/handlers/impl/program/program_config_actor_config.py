from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_config_actor_config_id
from aware_identity_ontology.actor.actor_config import ActorConfig

from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config(
    program_config_id: UUID, actor_config_id: UUID, alias: str
) -> ProgramConfigActorConfig:
    """
    Create deterministic ProgramConfig actor alias association.
    """

    # --- AWARE: LOGIC START build_via_program_config
    normalized_alias = (alias or "").strip()
    if not normalized_alias:
        raise RuntimeError("ProgramConfigActorConfig.build_via_program_config requires non-empty alias")

    assoc_id = stable_program_config_actor_config_id(
        program_config_id=program_config_id,
        alias=normalized_alias,
    )
    session = current_handler_session()
    actor_config = session.imap_get(ActorConfig, actor_config_id)
    if actor_config is None:
        raise RuntimeError(
            "ProgramConfigActorConfig.build_via_program_config requires ActorConfig to exist. "
            + "Create it first via ActorConfig.create(...)."
        )

    existing = session.imap_get(ProgramConfigActorConfig, assoc_id)
    if existing is not None:
        existing_alias = (existing.alias or "").strip()
        if (
            existing.program_config_id != program_config_id
            or existing.actor_config_id != actor_config_id
            or existing_alias != normalized_alias
        ):
            raise RuntimeError(
                "ProgramConfigActorConfig.build_via_program_config payload mismatch for existing association: "
                + f"association_id={assoc_id}"
            )
        existing.actor_config = actor_config
        return existing

    return ProgramConfigActorConfig(
        id=assoc_id,
        program_config_id=program_config_id,
        actor_config_id=actor_config_id,
        actor_config=actor_config,
        alias=normalized_alias,
    )
    # --- AWARE: LOGIC END build_via_program_config
