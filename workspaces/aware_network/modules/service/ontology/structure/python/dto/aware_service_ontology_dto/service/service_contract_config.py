from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import ServiceContractKind

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience import ProjectionExperience
    from aware_service_ontology_dto.service.service_contract_config_actor_role_grant import (
        ServiceContractConfigActorRoleGrant,
    )
    from aware_service_ontology_dto.service.service_contract_config_operation_grant import (
        ServiceContractConfigOperationGrant,
    )


class ServiceContractConfig(BaseModel):
    # Relationships
    actor_role_grants: list[ServiceContractConfigActorRoleGrant] = Field(default_factory=list)
    operation_grants: list[ServiceContractConfigOperationGrant] = Field(default_factory=list)
    projection_experience: ProjectionExperience | None = Field(default=None)

    # Attributes
    default_kind: ServiceContractKind = Field(default=ServiceContractKind.subscription)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    name: str
