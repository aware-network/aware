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
    ServiceContractOperationPriceSource,
    ServiceOperationSettlementPolicy,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.price.price import Price
    from aware_economy_ontology_dto.price.pricing_policy import PricingPolicy


class ServiceContractOperationPricePolicy(BaseModel):
    # Relationships
    price: Price | None = Field(default=None)
    pricing_policy: PricingPolicy | None = Field(default=None)

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
