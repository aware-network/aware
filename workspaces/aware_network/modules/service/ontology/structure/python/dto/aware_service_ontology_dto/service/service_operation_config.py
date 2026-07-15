from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import (
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.price.price import Price
    from aware_service_ontology_dto.service.service_operation_config_api_endpoint import (
        ServiceOperationConfigApiEndpoint,
    )
    from aware_service_ontology_dto.service.service_operation_config_api_view import ServiceOperationConfigApiView
    from aware_service_ontology_dto.service.service_operation_config_role_requirement import (
        ServiceOperationConfigRoleRequirement,
    )


class ServiceOperationConfig(BaseModel):
    # Relationships
    api_endpoints: list[ServiceOperationConfigApiEndpoint] = Field(default_factory=list)
    api_views: list[ServiceOperationConfigApiView] = Field(default_factory=list)
    price: Price | None = Field(default=None)
    role_requirements: list[ServiceOperationConfigRoleRequirement] = Field(default_factory=list)

    # Attributes
    admission_mode: ServiceOperationAdmissionMode = Field(default=ServiceOperationAdmissionMode.contract_required)
    description: str | None = Field(default=None)
    fulfillment_kind: ServiceOperationFulfillmentKind = Field(default=ServiceOperationFulfillmentKind.coordination)
    name: str
    receipt_policy: ServiceOperationReceiptPolicy = Field(default=ServiceOperationReceiptPolicy.committed)
    settlement_policy: ServiceOperationSettlementPolicy = Field(default=ServiceOperationSettlementPolicy.none)
