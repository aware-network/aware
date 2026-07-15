from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class ExperienceActorConfigRoleEligibility(BaseModel):
    """
    Canonical DTOs for Experience ActorConfig admission.
    Ownership:
    - Experience owns ActorConfig admission and role eligibility provenance.
    - Identity owns concrete RoleAssignmentBinding truth.
    - This DTO returns an Experience admission binding that carries Identity
    binding ids without making Experience DTOs depend on Identity DTOs.
    """

    # Attributes
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)


class ExperienceActorConfigRoleAdmissionBinding(BaseModel):
    # Attributes
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)
    actor_id: UUID
    role_id: UUID
    actor_role_id: UUID
    role_class_instance_id: UUID
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class ExperienceActorConfigAdmissionReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    reason: str | None = Field(default=None)
    experience_name: str
    actor_id: UUID | None = Field(default=None)
    actor_config_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    eligible_roles: list[ExperienceActorConfigRoleEligibility] = Field(default_factory=list)
    bindings: list[ExperienceActorConfigRoleAdmissionBinding] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)
