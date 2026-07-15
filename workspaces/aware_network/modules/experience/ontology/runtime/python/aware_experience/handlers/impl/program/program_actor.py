from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_actor import ProgramActor
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
from aware_identity_ontology.actor.actor import Actor
from aware_identity_ontology.actor.actor_role import ActorRole
from aware_identity_ontology.role.role import Role

# Environment Ontology
from aware_experience_ontology.stable_ids import (
    stable_program_actor_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_actor_role(
    program_actor: ProgramActor, actor_role_id: UUID, actor_config_role_config_id: UUID
) -> ProgramActorRole:
    """
    Bind one ActorRole that is eligible for this ProgramActor via ActorConfigRoleConfig.

    Contract:
    - Mutates only ProgramActor membership (`program_actor_roles`).
    - Program run attribution must resolve invoke actor context via ProgramActorRole.
    """

    # --- AWARE: LOGIC START add_actor_role
    program_actor_id = program_actor.id
    if program_actor_id is None:
        raise RuntimeError("ProgramActor.add_actor_role requires ProgramActor.id")

    session = current_handler_session()
    actor_role = session.imap_get(ActorRole, actor_role_id)
    actor_config_role_config = session.imap_get(ActorConfigRoleConfig, actor_config_role_config_id)

    program_config_actor_config = program_actor.program_config_actor_config
    if program_config_actor_config is None:
        program_config_actor_config = session.imap_get(
            ProgramConfigActorConfig,
            program_actor.program_config_actor_config_id,
        )
        if program_config_actor_config is not None:
            program_actor.program_config_actor_config = program_config_actor_config

    if actor_role is not None and actor_role.actor_id != program_actor.actor_id:
        raise RuntimeError(
            "ProgramActor.add_actor_role actor mismatch with ProgramActor.actor_id: "
            f"program_actor_id={program_actor_id} actor_role_id={actor_role_id}"
        )

    if (
        actor_config_role_config is not None
        and program_config_actor_config is not None
        and actor_config_role_config.actor_config_id != program_config_actor_config.actor_config_id
    ):
        raise RuntimeError(
            "ProgramActor.add_actor_role role config mismatch with ProgramConfigActorConfig.actor_config_id: "
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
                "ProgramActor.add_actor_role role mismatch with ActorConfigRoleConfig.role_config_id: "
                f"program_actor_id={program_actor_id} actor_role_id={actor_role_id} "
                f"actor_config_role_config_id={actor_config_role_config_id}"
            )

    assoc = await ProgramActorRole.build_via_program_actor(
        program_actor_id=program_actor_id,
        actor_role_id=actor_role_id,
        actor_config_role_config_id=actor_config_role_config_id,
    )
    if assoc.actor_role is None and actor_role is not None:
        assoc.actor_role = actor_role
    if assoc.actor_config_role_config is None and actor_config_role_config is not None:
        assoc.actor_config_role_config = actor_config_role_config

    if not any(existing.id == assoc.id for existing in program_actor.program_actor_roles):
        program_actor.program_actor_roles.append(assoc)
    return assoc
    # --- AWARE: LOGIC END add_actor_role


async def build_via_program(program_id: UUID, program_config_actor_config_id: UUID, actor_id: UUID) -> ProgramActor:
    """
    Create deterministic ProgramActor binding under Program.
    """

    # --- AWARE: LOGIC START build_via_program
    program_actor_id = stable_program_actor_id(
        program_id=program_id,
        program_config_actor_config_id=program_config_actor_config_id,
        actor_id=actor_id,
    )

    session = current_handler_session()
    program_config_actor_config = session.imap_get(ProgramConfigActorConfig, program_config_actor_config_id)
    actor = session.imap_get(Actor, actor_id)

    existing = session.imap_get(ProgramActor, program_actor_id)
    if existing is not None:
        if (
            existing.program_id != program_id
            or existing.program_config_actor_config_id != program_config_actor_config_id
            or existing.actor_id != actor_id
        ):
            raise RuntimeError(
                "ProgramActor.build_via_program payload mismatch for existing binding: "
                f"program_actor_id={program_actor_id}"
            )
        if existing.program_config_actor_config is None and program_config_actor_config is not None:
            existing.program_config_actor_config = program_config_actor_config
        if existing.actor is None and actor is not None:
            existing.actor = actor
        return existing

    return ProgramActor(
        id=program_actor_id,
        program_id=program_id,
        program_config_actor_config_id=program_config_actor_config_id,
        program_config_actor_config=program_config_actor_config,
        actor_id=actor_id,
        actor=actor,
    )
    # --- AWARE: LOGIC END build_via_program
