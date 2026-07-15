from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_config import ActorConfig


class EnvironmentProfileActorConfig(ORMModel):
    """
    EnvironmentProfileConfig actor eligibility policy.
    Contract:
    - Environment owns admission eligibility for shared OS entrance.
    - Identity owns ActorConfig, RoleConfig, Role, ActorRole, and concrete
    role assignment truth.
    - This edge never embeds actors and never grants access by itself.
    - Environment service admission resolves ActorConfig -> RoleConfig[] and
    delegates concrete role assignment to Identity.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None)

    # Attributes
    access_scope: str = Field(default="profile")
    description: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    policy_key: str = Field(default="admit")
    requirement_kind: str = Field(default="environment_actor_config")
    status: str = Field(default="active")

    # Foreign Keys
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.actor_configs")
    actor_config_id: UUID = Field(description="Foreign key for EnvironmentProfileActorConfig.actor_config")
