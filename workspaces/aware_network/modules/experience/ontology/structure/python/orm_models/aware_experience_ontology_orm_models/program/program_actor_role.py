from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_config_role_config import ActorConfigRoleConfig
    from aware_identity_ontology_orm_models.actor.actor_role import ActorRole


class ProgramActorRole(ORMModel):
    """
    Runtime role attribution edge under one ProgramActor.
    Contract:
    - Stores the role snapshot used by runtime invoke attribution.
    - Links role eligibility provenance through Identity ActorConfigRoleConfig.
    """

    # Relationships
    actor_role: ActorRole | None = Field(default=None, exclude=True)
    actor_config_role_config: ActorConfigRoleConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_actor_id: UUID = Field(description="Foreign key for ProgramActor.program_actor_roles")
    actor_role_id: UUID = Field(description="Foreign key for ProgramActorRole.actor_role")
    actor_config_role_config_id: UUID = Field(description="Foreign key for ProgramActorRole.actor_config_role_config")
