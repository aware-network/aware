from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import (
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.price.price import Price
    from aware_service_ontology_orm_models.service.service_operation_config_api_endpoint import (
        ServiceOperationConfigApiEndpoint,
    )
    from aware_service_ontology_orm_models.service.service_operation_config_api_view import (
        ServiceOperationConfigApiView,
    )
    from aware_service_ontology_orm_models.service.service_operation_config_role_requirement import (
        ServiceOperationConfigRoleRequirement,
    )


class ServiceOperationConfig(ORMModel):
    # Relationships
    api_endpoints: list[ServiceOperationConfigApiEndpoint] = Field(default_factory=list, exclude=True)
    api_views: list[ServiceOperationConfigApiView] = Field(default_factory=list, exclude=True)
    price: Price | None = Field(default=None, exclude=True)
    role_requirements: list[ServiceOperationConfigRoleRequirement] = Field(default_factory=list, exclude=True)

    # Attributes
    admission_mode: ServiceOperationAdmissionMode = Field(default=ServiceOperationAdmissionMode.contract_required)
    description: str | None = Field(default=None)
    fulfillment_kind: ServiceOperationFulfillmentKind = Field(default=ServiceOperationFulfillmentKind.coordination)
    name: str
    receipt_policy: ServiceOperationReceiptPolicy = Field(default=ServiceOperationReceiptPolicy.committed)
    settlement_policy: ServiceOperationSettlementPolicy = Field(default=ServiceOperationSettlementPolicy.none)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.service_operation_configs")
    price_id: UUID | None = Field(default=None, description="Foreign key for ServiceOperationConfig.price")
