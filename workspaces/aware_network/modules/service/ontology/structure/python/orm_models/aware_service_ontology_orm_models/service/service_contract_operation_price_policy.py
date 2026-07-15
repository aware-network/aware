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
    ServiceContractOperationPriceSource,
    ServiceOperationSettlementPolicy,
)

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.price.price import Price
    from aware_economy_ontology_orm_models.price.pricing_policy import PricingPolicy


class ServiceContractOperationPricePolicy(ORMModel):
    # Relationships
    price: Price | None = Field(default=None, exclude=True)
    pricing_policy: PricingPolicy | None = Field(default=None, exclude=True)

    # Attributes
    fail_closed: bool = Field(default=True)
    max_cost_required: bool = Field(default=False)
    price_ref: str | None = Field(default=None)
    price_source: ServiceContractOperationPriceSource = Field(
        default=ServiceContractOperationPriceSource.operation_default
    )
    pricing_policy_ref: str | None = Field(default=None)
    quote_ttl_s: int | None = Field(default=None)
    settlement_policy_override: ServiceOperationSettlementPolicy | None = Field(default=None)

    # Foreign Keys
    service_contract_config_operation_grant_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractConfigOperationGrant.price_policy"
    )
    price_id: UUID | None = Field(default=None, description="Foreign key for ServiceContractOperationPricePolicy.price")
    pricing_policy_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractOperationPricePolicy.pricing_policy"
    )
