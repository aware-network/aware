from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_config import ActorConfig


class EnvironmentProfileActorConfig(BaseModel):
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
