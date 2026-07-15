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
    from aware_service_ontology_orm_models.service.service_contract_operation_permit_policy import (
        ServiceContractOperationPermitPolicy,
    )
    from aware_service_ontology_orm_models.service.service_contract_operation_price_policy import (
        ServiceContractOperationPricePolicy,
    )
    from aware_service_ontology_orm_models.service.service_contract_operation_quota_policy import (
        ServiceContractOperationQuotaPolicy,
    )
    from aware_service_ontology_orm_models.service.service_operation_config import ServiceOperationConfig


class ServiceContractConfigOperationGrant(ORMModel):
    # Relationships
    permit_policy: ServiceContractOperationPermitPolicy | None = Field(default=None, exclude=True)
    price_policy: ServiceContractOperationPricePolicy | None = Field(default=None, exclude=True)
    quota_policy: ServiceContractOperationQuotaPolicy | None = Field(default=None, exclude=True)
    service_operation_config: ServiceOperationConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_scope: str = Field(default="operation")
    description: str | None = Field(default=None)
    permit_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    price_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    quota_policy_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContractConfig.operation_grants")
    service_operation_config_id: UUID = Field(
        description="Foreign key for ServiceContractConfigOperationGrant.service_operation_config"
    )
