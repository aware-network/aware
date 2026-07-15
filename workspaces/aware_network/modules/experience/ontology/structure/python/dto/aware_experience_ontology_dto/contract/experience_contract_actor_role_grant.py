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
    from aware_identity_ontology_dto.actor.actor_config_role_config import ActorConfigRoleConfig
    from aware_identity_ontology_dto.role.role_config import RoleConfig


class ExperienceContractActorRoleGrant(BaseModel):
    """
    Experience-owned contract-visible actor-role grant.
    Contract:
    - Experience owns public actor participation eligibility for an Experience.
    - Identity owns ActorConfig, RoleConfig, and concrete ActorRole assignment truth.
    - Provider contracts may later reference this grant, but providers do not
    invent Experience actor-role grants.
    """

    # Relationships
    actor_config_role_config: ActorConfigRoleConfig
    role_config: RoleConfig

    # Attributes
    access_scope: str = Field(default="experience")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    grant_key: str
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    participant_kind: str = Field(default="actor")
    role_assignment_binding_required: bool = Field(default=True)
