from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractOperationPriceSource,
    ServiceOperationSettlementPolicy,
)

if TYPE_CHECKING:
    from aware_economy_ontology.price.price import Price
    from aware_economy_ontology.price.pricing_policy import PricingPolicy


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

    @classmethod
    async def build_via_service_contract_config_operation_grant(
        cls,
        service_contract_config_operation_grant_id: UUID,
        price_source: ServiceContractOperationPriceSource = ServiceContractOperationPriceSource.operation_default,
        price_id: UUID | None = None,
        price_ref: str | None = None,
        pricing_policy_id: UUID | None = None,
        pricing_policy_ref: str | None = None,
        settlement_policy_override: ServiceOperationSettlementPolicy | None = None,
        max_cost_required: bool = False,
        quote_ttl_s: int | None = None,
        fail_closed: bool = True,
    ) -> ServiceContractOperationPricePolicy:
        """
        Creates the Service-owned price selection policy intent for one operation grant.

        Contract:
        - Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.
        - Price policy selects Economy price truth; it does not compute quotes or settle funds.
        - Economy owns Price, PricingPolicy, PriceSchedule, RateSnapshot, reservation, escrow, and
        settlement receipts.
        """

        payload = {
            "service_contract_config_operation_grant_id": service_contract_config_operation_grant_id,
            "price_source": price_source,
            "price_id": price_id,
            "price_ref": price_ref,
            "pricing_policy_id": pricing_policy_id,
            "pricing_policy_ref": pricing_policy_ref,
            "settlement_policy_override": settlement_policy_override,
            "max_cost_required": max_cost_required,
            "quote_ttl_s": quote_ttl_s,
            "fail_closed": fail_closed,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_contract_config_operation_grant", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractOperationPricePolicy):
            return value
        return ServiceContractOperationPricePolicy.validate_invocation_value(value)


class ServiceContractOperationPricePolicyBuildViaServiceContractConfigOperationGrantInput(BaseModel):
    service_contract_config_operation_grant_id: UUID = Field(
        description="Foreign key for ServiceContractConfigOperationGrant.price_policy"
    )
    price_source: ServiceContractOperationPriceSource = Field(
        default=ServiceContractOperationPriceSource.operation_default
    )
    price_id: UUID | None = Field(default=None)
    price_ref: str | None = Field(default=None)
    pricing_policy_id: UUID | None = Field(default=None)
    pricing_policy_ref: str | None = Field(default=None)
    settlement_policy_override: ServiceOperationSettlementPolicy | None = Field(default=None)
    max_cost_required: bool = Field(default=False)
    quote_ttl_s: int | None = Field(default=None)
    fail_closed: bool = Field(default=True)


class ServiceContractOperationPricePolicyBuildViaServiceContractConfigOperationGrantOutput(BaseModel):
    value: ServiceContractOperationPricePolicy


FUNCTIONS = {
    "ServiceContractOperationPricePolicy": {
        "build_via_service_contract_config_operation_grant": {
            "canonical": {
                "name": "build_via_service_contract_config_operation_grant",
                "description": "Creates the Service-owned price selection policy intent for one operation grant.\n\nContract:\n- Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.\n- Price policy selects Economy price truth; it does not compute quotes or settle funds.\n- Economy owns Price, PricingPolicy, PriceSchedule, RateSnapshot, reservation, escrow, and settlement receipts.",
                "is_constructor": True,
            },
            "input": ServiceContractOperationPricePolicyBuildViaServiceContractConfigOperationGrantInput,
            "output": ServiceContractOperationPricePolicyBuildViaServiceContractConfigOperationGrantOutput,
        },
    },
}

__all__ = [
    "ServiceContractOperationPricePolicy",
    "ServiceContractOperationPricePolicyBuildViaServiceContractConfigOperationGrantInput",
    "ServiceContractOperationPricePolicyBuildViaServiceContractConfigOperationGrantOutput",
    "FUNCTIONS",
]
