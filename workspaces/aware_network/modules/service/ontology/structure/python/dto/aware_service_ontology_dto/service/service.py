from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_service_ontology_dto.service.service_branch import ServiceBranch
    from aware_service_ontology_dto.service.service_commercial_profile import ServiceCommercialProfile
    from aware_service_ontology_dto.service.service_contract import ServiceContract
    from aware_service_ontology_dto.service.service_operation import ServiceOperation
    from aware_service_ontology_dto.service.service_plan import ServicePlan


class Service(BaseModel):
    # Relationships
    branches: list[ServiceBranch] = Field(default_factory=list)
    commercial_profile: ServiceCommercialProfile | None = Field(default=None)
    contracts: list[ServiceContract] = Field(default_factory=list)
    plans: list[ServicePlan] = Field(default_factory=list)
    service_operations: list[ServiceOperation] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
