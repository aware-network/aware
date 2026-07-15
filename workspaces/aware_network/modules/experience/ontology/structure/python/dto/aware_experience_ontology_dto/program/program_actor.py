from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_actor_role import ProgramActorRole
    from aware_experience_ontology_dto.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_identity_ontology_dto.actor.actor import Actor


class ProgramActor(BaseModel):
    """
    Runtime actor binding for one Program actor alias.
    Contract:
    - Binds one ProgramConfigActorConfig alias contract to one concrete Actor.
    - Identity is deterministic under Program for `(program_config_actor_config_id, actor_id)`.
    """

    # Relationships
    program_config_actor_config: ProgramConfigActorConfig | None = Field(default=None)
    actor: Actor | None = Field(default=None)
    program_actor_roles: list[ProgramActorRole] = Field(default_factory=list)
