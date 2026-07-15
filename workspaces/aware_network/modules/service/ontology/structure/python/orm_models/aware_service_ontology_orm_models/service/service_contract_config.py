from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import ServiceContractKind

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience import ProjectionExperience
    from aware_service_ontology_orm_models.service.service_contract_config_actor_role_grant import (
        ServiceContractConfigActorRoleGrant,
    )
    from aware_service_ontology_orm_models.service.service_contract_config_operation_grant import (
        ServiceContractConfigOperationGrant,
    )


class ServiceContractConfig(ORMModel):
    # Relationships
    actor_role_grants: list[ServiceContractConfigActorRoleGrant] = Field(default_factory=list, exclude=True)
    operation_grants: list[ServiceContractConfigOperationGrant] = Field(default_factory=list, exclude=True)
    projection_experience: ProjectionExperience | None = Field(default=None, exclude=True)

    # Attributes
    default_kind: ServiceContractKind = Field(default=ServiceContractKind.subscription)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    name: str

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.contract_configs")
    projection_experience_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractConfig.projection_experience"
    )
