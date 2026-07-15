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
    from aware_identity_ontology_orm_models.role.role_config import RoleConfig


class ServiceContractConfigActorRoleGrant(ORMModel):
    # Relationships
    role_config: RoleConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_scope: str = Field(default="service")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    role_assignment_binding_required: bool = Field(default=True)
    scope_kind: str = Field(default="service")
    scope_ref: str = Field(default="default")

    # Foreign Keys
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContractConfig.actor_role_grants")
    role_config_id: UUID = Field(description="Foreign key for ServiceContractConfigActorRoleGrant.role_config")
