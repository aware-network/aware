from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig
    from aware_identity_ontology.role.role_config import RoleConfig


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

    @classmethod
    async def build_via_projection_experience(
        cls,
        projection_experience_id: UUID,
        grant_key: str,
        actor_config_role_config_id: UUID,
        role_config_id: UUID,
        access_scope: str = "experience",
        participant_kind: str = "actor",
        class_instance_identity_required: bool = False,
        role_assignment_binding_required: bool = True,
        grant_policy_json: JsonObject | None = {},
        description: str | None = None,
    ) -> ExperienceContractActorRoleGrant:
        """
        Create one Experience-owned public actor-role grant.

        Contract:
        - Parent ProjectionExperience scope is propagated by constructor lowering.
        - Stable identity is `(projection_experience_id, grant_key)`.
        - The grant is not a global RoleConfig grant; it is RoleConfig eligibility
          through an Identity ActorConfigRoleConfig.
        - Runtime must reject mismatched actor-config/role-config pairs.
        """

        payload = {
            "projection_experience_id": projection_experience_id,
            "grant_key": grant_key,
            "actor_config_role_config_id": actor_config_role_config_id,
            "role_config_id": role_config_id,
            "access_scope": access_scope,
            "participant_kind": participant_kind,
            "class_instance_identity_required": class_instance_identity_required,
            "role_assignment_binding_required": role_assignment_binding_required,
            "grant_policy_json": grant_policy_json,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceContractActorRoleGrant):
            return value
        return ExperienceContractActorRoleGrant.validate_invocation_value(value)


class ExperienceContractActorRoleGrantBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.contract_actor_role_grants"
    )
    grant_key: str
    actor_config_role_config_id: UUID
    role_config_id: UUID
    access_scope: str = Field(default="experience")
    participant_kind: str = Field(default="actor")
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=True)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)


class ExperienceContractActorRoleGrantBuildViaProjectionExperienceOutput(BaseModel):
    value: ExperienceContractActorRoleGrant


FUNCTIONS = {
    "ExperienceContractActorRoleGrant": {
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create one Experience-owned public actor-role grant.\n\nContract:\n- Parent ProjectionExperience scope is propagated by constructor lowering.\n- Stable identity is `(projection_experience_id, grant_key)`.\n- The grant is not a global RoleConfig grant; it is RoleConfig eligibility\n  through an Identity ActorConfigRoleConfig.\n- Runtime must reject mismatched actor-config/role-config pairs.",
                "is_constructor": True,
            },
            "input": ExperienceContractActorRoleGrantBuildViaProjectionExperienceInput,
            "output": ExperienceContractActorRoleGrantBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ExperienceContractActorRoleGrant",
    "ExperienceContractActorRoleGrantBuildViaProjectionExperienceInput",
    "ExperienceContractActorRoleGrantBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
