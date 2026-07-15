from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_actor_role import ProgramActorRole

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_identity_ontology.actor.actor_config_role_config import (
    ActorConfigRoleConfig,
)
from aware_experience_ontology.program.program_config_actor_config import (
    ProgramConfigActorConfig,
)

# Identity Ontology
from aware_identity_ontology.actor.actor_role import ActorRole
from aware_identity_ontology.role.role import Role

# Environment Ontology
from aware_experience_ontology.program.program_actor import ProgramActor
from aware_experience_ontology.stable_ids import (
    stable_program_actor_role_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_actor(
    program_actor_id: UUID, actor_role_id: UUID, actor_config_role_config_id: UUID
) -> ProgramActorRole:
    """
    Create deterministic ProgramActorRole under ProgramActor.
    """

    # --- AWARE: LOGIC START build_via_program_actor
    program_actor_role_id = stable_program_actor_role_id(
        program_actor_id=program_actor_id,
        actor_role_id=actor_role_id,
        actor_config_role_config_id=actor_config_role_config_id,
    )

    session = current_handler_session()
    program_actor = session.imap_get(ProgramActor, program_actor_id)
    actor_role = session.imap_get(ActorRole, actor_role_id)
    actor_config_role_config = session.imap_get(ActorConfigRoleConfig, actor_config_role_config_id)

    if program_actor is not None and actor_role is not None and actor_role.actor_id != program_actor.actor_id:
        raise RuntimeError(
            "ProgramActorRole.build_via_program_actor actor mismatch with ProgramActor.actor_id: "
            f"program_actor_id={program_actor_id} actor_role_id={actor_role_id}"
        )

    if program_actor is not None and actor_config_role_config is not None:
        program_config_actor_config = program_actor.program_config_actor_config
        if program_config_actor_config is None:
            program_config_actor_config = session.imap_get(
                ProgramConfigActorConfig,
                program_actor.program_config_actor_config_id,
            )
            if program_config_actor_config is not None:
                program_actor.program_config_actor_config = program_config_actor_config
        if (
            program_config_actor_config is not None
            and actor_config_role_config.actor_config_id != program_config_actor_config.actor_config_id
        ):
            raise RuntimeError(
                "ProgramActorRole.build_via_program_actor actor config mismatch with ProgramConfigActorConfig: "
                f"program_actor_id={program_actor_id} actor_config_role_config_id={actor_config_role_config_id}"
            )

    role = None
    if actor_role is not None:
        role = actor_role.role
        if role is None:
            role = session.imap_get(Role, actor_role.role_id)
            if role is not None:
                actor_role.role = role
    if role is not None and actor_config_role_config is not None:
        if role.role_config_id != actor_config_role_config.role_config_id:
            raise RuntimeError(
                "ProgramActorRole.build_via_program_actor role mismatch with ActorConfigRoleConfig.role_config_id: "
                f"program_actor_id={program_actor_id} actor_role_id={actor_role_id} "
                f"actor_config_role_config_id={actor_config_role_config_id}"
            )

    existing = session.imap_get(ProgramActorRole, program_actor_role_id)
    if existing is not None:
        if (
            existing.program_actor_id != program_actor_id
            or existing.actor_role_id != actor_role_id
            or existing.actor_config_role_config_id != actor_config_role_config_id
        ):
            raise RuntimeError(
                "ProgramActorRole.build_via_program_actor payload mismatch for existing binding: "
                f"program_actor_role_id={program_actor_role_id}"
            )
        if existing.actor_role is None and actor_role is not None:
            existing.actor_role = actor_role
        if existing.actor_config_role_config is None and actor_config_role_config is not None:
            existing.actor_config_role_config = actor_config_role_config
        return existing

    return ProgramActorRole(
        id=program_actor_role_id,
        program_actor_id=program_actor_id,
        actor_role_id=actor_role_id,
        actor_role=actor_role,
        actor_config_role_config_id=actor_config_role_config_id,
        actor_config_role_config=actor_config_role_config,
    )
    # --- AWARE: LOGIC END build_via_program_actor
