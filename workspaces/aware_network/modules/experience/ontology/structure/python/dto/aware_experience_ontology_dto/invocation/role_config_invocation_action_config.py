from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.role.role_config import RoleConfig


class RoleConfigInvocationActionConfig(BaseModel):
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
