from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role_config import RoleConfig


class RoleConfigInvocationActionConfig(ORMModel):
    """
    Experience action-entrypoint policy for admitted Identity roles.
    Contract:
    - Experience owns this policy because public consumers invoke Experience
    action configs, not ontology functions directly.
    - Identity owns `RoleConfig` and concrete `ActorRole` materialization.
    - Service/Ontology mutation policy remains the lower graph mutation gate.
    """

    # Relationships
    role_config: RoleConfig | None = Field(default=None)

    # Attributes
    policy_key: str = Field(default="invoke")
    requirement_kind: str = Field(default="admitted_actor_role")
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionConfig.role_policies"
    )
    role_config_id: UUID = Field(description="Foreign key for RoleConfigInvocationActionConfig.role_config")
