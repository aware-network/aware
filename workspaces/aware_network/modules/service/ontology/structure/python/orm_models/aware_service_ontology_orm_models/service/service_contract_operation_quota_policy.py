from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import (
    ServiceContractOperationQuotaOverLimitBehavior,
    ServiceContractOperationQuotaUnit,
    ServiceContractOperationQuotaWindow,
)


class ServiceContractOperationQuotaPolicy(ORMModel):
    # Attributes
    burst_limit: int | None = Field(default=None)
    fail_closed: bool = Field(default=True)
    limit_amount: int | None = Field(default=None)
    over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = Field(
        default=ServiceContractOperationQuotaOverLimitBehavior.deny
    )
    unit: ServiceContractOperationQuotaUnit = Field(default=ServiceContractOperationQuotaUnit.operation)
    window: ServiceContractOperationQuotaWindow = Field(default=ServiceContractOperationQuotaWindow.none)

    # Foreign Keys
    service_contract_config_operation_grant_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractConfigOperationGrant.quota_policy"
    )
