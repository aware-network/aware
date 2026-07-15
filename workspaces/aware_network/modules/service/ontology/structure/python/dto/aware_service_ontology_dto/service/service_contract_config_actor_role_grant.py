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
    from aware_identity_ontology_dto.role.role_config import RoleConfig


class ServiceContractConfigActorRoleGrant(BaseModel):
    # Relationships
    role_config: RoleConfig | None = Field(default=None)

    # Attributes
    access_scope: str = Field(default="service")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    role_assignment_binding_required: bool = Field(default=True)
    scope_kind: str = Field(default="service")
    scope_ref: str = Field(default="default")
