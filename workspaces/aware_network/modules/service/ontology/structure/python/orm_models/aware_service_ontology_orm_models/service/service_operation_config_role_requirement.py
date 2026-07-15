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


class ServiceOperationConfigRoleRequirement(ORMModel):
    # Relationships
    role_config: RoleConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_scope: str = Field(default="operation")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    role_assignment_binding_required: bool = Field(default=True)
    scope_kind: str = Field(default="operation")
    scope_ref: str = Field(default="default")

    # Foreign Keys
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.role_requirements")
    role_config_id: UUID = Field(description="Foreign key for ServiceOperationConfigRoleRequirement.role_config")
