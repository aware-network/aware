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


class ServiceOperationConfigRoleRequirement(BaseModel):
    # Relationships
    role_config: RoleConfig | None = Field(default=None)

    # Attributes
    access_scope: str = Field(default="operation")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    role_assignment_binding_required: bool = Field(default=True)
    scope_kind: str = Field(default="operation")
    scope_ref: str = Field(default="default")
