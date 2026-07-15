from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_config import ActorConfig


class ProgramConfigActorConfig(BaseModel):
    """
    ProgramConfig actor alias contract.
    Contract:
    - Binds one ProgramConfig alias to one Identity ActorConfig.
    - Alias identity is parent-path scoped under ProgramConfig.
    - Multiple aliases may reference the same ActorConfig.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None)

    # Attributes
    alias: str
