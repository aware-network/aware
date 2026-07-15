from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import (
    ServiceContractOperationQuotaOverLimitBehavior,
    ServiceContractOperationQuotaUnit,
    ServiceContractOperationQuotaWindow,
)


class ServiceContractOperationQuotaPolicy(BaseModel):
    # Attributes
    burst_limit: int | None = Field(default=None)
    fail_closed: bool = Field(default=True)
    limit_amount: int | None = Field(default=None)
    over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = Field(
        default=ServiceContractOperationQuotaOverLimitBehavior.deny
    )
    unit: ServiceContractOperationQuotaUnit = Field(default=ServiceContractOperationQuotaUnit.operation)
    window: ServiceContractOperationQuotaWindow = Field(default=ServiceContractOperationQuotaWindow.none)
