from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_actor_role import ProgramActorRole
    from aware_experience_ontology_orm_models.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_identity_ontology_orm_models.actor.actor import Actor


class ProgramActor(ORMModel):
    """
    Runtime actor binding for one Program actor alias.
    Contract:
    - Binds one ProgramConfigActorConfig alias contract to one concrete Actor.
    - Identity is deterministic under Program for `(program_config_actor_config_id, actor_id)`.
    """

    # Relationships
    program_config_actor_config: ProgramConfigActorConfig | None = Field(default=None, exclude=True)
    actor: Actor | None = Field(default=None, exclude=True)
    program_actor_roles: list[ProgramActorRole] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.program_actors")
    program_config_actor_config_id: UUID = Field(description="Foreign key for ProgramActor.program_config_actor_config")
    actor_id: UUID = Field(description="Foreign key for ProgramActor.actor")
