from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_service_ontology_orm_models.service.service_branch import ServiceBranch
    from aware_service_ontology_orm_models.service.service_commercial_profile import ServiceCommercialProfile
    from aware_service_ontology_orm_models.service.service_contract import ServiceContract
    from aware_service_ontology_orm_models.service.service_operation import ServiceOperation
    from aware_service_ontology_orm_models.service.service_plan import ServicePlan


class Service(ORMModel):
    # Relationships
    branches: list[ServiceBranch] = Field(default_factory=list, exclude=True)
    commercial_profile: ServiceCommercialProfile | None = Field(default=None, exclude=True)
    contracts: list[ServiceContract] = Field(default_factory=list, exclude=True)
    plans: list[ServicePlan] = Field(default_factory=list, exclude=True)
    service_operations: list[ServiceOperation] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.services")
