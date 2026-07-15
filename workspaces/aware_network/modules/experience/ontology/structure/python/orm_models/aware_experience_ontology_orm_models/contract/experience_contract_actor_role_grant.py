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
    from aware_identity_ontology_orm_models.actor.actor_config_role_config import ActorConfigRoleConfig
    from aware_identity_ontology_orm_models.role.role_config import RoleConfig


class ExperienceContractActorRoleGrant(ORMModel):
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

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.contract_actor_role_grants"
    )
    actor_config_role_config_id: UUID | None = Field(
        default=None, description="Foreign key for ExperienceContractActorRoleGrant.actor_config_role_config"
    )
    role_config_id: UUID | None = Field(
        default=None, description="Foreign key for ExperienceContractActorRoleGrant.role_config"
    )
