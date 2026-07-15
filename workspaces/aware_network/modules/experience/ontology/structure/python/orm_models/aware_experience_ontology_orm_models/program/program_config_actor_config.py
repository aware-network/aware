from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_config import ActorConfig


class ProgramConfigActorConfig(ORMModel):
    """
    ProgramConfig actor alias contract.
    Contract:
    - Binds one ProgramConfig alias to one Identity ActorConfig.
    - Alias identity is parent-path scoped under ProgramConfig.
    - Multiple aliases may reference the same ActorConfig.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None, exclude=True)

    # Attributes
    alias: str

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.actor_configs")
    actor_config_id: UUID = Field(description="Foreign key for ProgramConfigActorConfig.actor_config")
