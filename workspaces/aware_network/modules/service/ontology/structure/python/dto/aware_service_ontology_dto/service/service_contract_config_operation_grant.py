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
    from aware_service_ontology_dto.service.service_contract_operation_permit_policy import (
        ServiceContractOperationPermitPolicy,
    )
    from aware_service_ontology_dto.service.service_contract_operation_price_policy import (
        ServiceContractOperationPricePolicy,
    )
    from aware_service_ontology_dto.service.service_contract_operation_quota_policy import (
        ServiceContractOperationQuotaPolicy,
    )
    from aware_service_ontology_dto.service.service_operation_config import ServiceOperationConfig


class ServiceContractConfigOperationGrant(BaseModel):
    # Relationships
    permit_policy: ServiceContractOperationPermitPolicy | None = Field(default=None)
    price_policy: ServiceContractOperationPricePolicy | None = Field(default=None)
    quota_policy: ServiceContractOperationQuotaPolicy | None = Field(default=None)
    service_operation_config: ServiceOperationConfig | None = Field(default=None)

    # Attributes
    access_scope: str = Field(default="operation")
    description: str | None = Field(default=None)
    permit_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    price_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    quota_policy_json: JsonObject | None = Field(default_factory=JsonObject)
