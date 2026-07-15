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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
    ServiceContractOperationPriceSource,
    ServiceContractOperationQuotaOverLimitBehavior,
    ServiceContractOperationQuotaUnit,
    ServiceContractOperationQuotaWindow,
    ServiceOperationSettlementPolicy,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_service_ontology.service.service_contract_operation_permit_policy import (
        ServiceContractOperationPermitPolicy,
    )
    from aware_service_ontology.service.service_contract_operation_price_policy import (
        ServiceContractOperationPricePolicy,
    )
    from aware_service_ontology.service.service_contract_operation_quota_policy import (
        ServiceContractOperationQuotaPolicy,
    )
    from aware_service_ontology.service.service_operation_config import ServiceOperationConfig


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

    async def configure_quota_policy(
        self,
        unit: ServiceContractOperationQuotaUnit = ServiceContractOperationQuotaUnit.operation,
        limit_amount: int | None = None,
        window: ServiceContractOperationQuotaWindow = ServiceContractOperationQuotaWindow.none,
        burst_limit: int | None = None,
        over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = ServiceContractOperationQuotaOverLimitBehavior.deny,
        fail_closed: bool = True,
    ) -> ServiceContractOperationQuotaPolicy:
        """
        Declares typed quota policy intent for this operation grant.

        Contract:
        - This controls allowance semantics only.
        - Runtime metering/billing may consume this policy, but Economy owns financial receipts.
        """

        payload = {
            "unit": unit,
            "limit_amount": limit_amount,
            "window": window,
            "burst_limit": burst_limit,
            "over_limit_behavior": over_limit_behavior,
            "fail_closed": fail_closed,
        }
        result = await invoke_instance(orm_model=self, function_name="configure_quota_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_operation_quota_policy import (
            ServiceContractOperationQuotaPolicy,
        )

        if isinstance(value, ServiceContractOperationQuotaPolicy):
            return value
        return ServiceContractOperationQuotaPolicy.validate_invocation_value(value)

    async def configure_permit_policy(
        self,
        requires_active_contract: bool = True,
        requires_smart_contract_permit: bool = False,
        requires_reservation_before_execute: bool = False,
        permit_scope: ServiceContractOperationPermitScope = ServiceContractOperationPermitScope.operation,
        idempotency_scope: ServiceContractOperationPermitIdempotencyScope = ServiceContractOperationPermitIdempotencyScope.request_hash,
        fail_closed: bool = True,
    ) -> ServiceContractOperationPermitPolicy:
        """
        Declares typed permit policy intent for this operation grant.

        Contract:
        - This controls pre-execution proof requirements.
        - Identity role evidence and Economy smart-contract receipts remain owned by their source domains.
        """

        payload = {
            "requires_active_contract": requires_active_contract,
            "requires_smart_contract_permit": requires_smart_contract_permit,
            "requires_reservation_before_execute": requires_reservation_before_execute,
            "permit_scope": permit_scope,
            "idempotency_scope": idempotency_scope,
            "fail_closed": fail_closed,
        }
        result = await invoke_instance(orm_model=self, function_name="configure_permit_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_operation_permit_policy import (
            ServiceContractOperationPermitPolicy,
        )

        if isinstance(value, ServiceContractOperationPermitPolicy):
            return value
        return ServiceContractOperationPermitPolicy.validate_invocation_value(value)

    async def configure_price_policy(
        self,
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
        Declares typed price selection policy intent for this operation grant.

        Contract:
        - This selects or overrides Economy price truth for the granted operation.
        - Quotes, reservations, escrow, and settlement remain Economy-owned receipts.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="configure_price_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_operation_price_policy import (
            ServiceContractOperationPricePolicy,
        )

        if isinstance(value, ServiceContractOperationPricePolicy):
            return value
        return ServiceContractOperationPricePolicy.validate_invocation_value(value)

    @classmethod
    async def build_via_service_contract_config(
        cls,
        service_contract_config_id: UUID,
        service_operation_config_id: UUID,
        access_scope: str = "operation",
        quota_policy_json: JsonObject | None = {},
        permit_policy_json: JsonObject | None = {},
        price_policy_json: JsonObject | None = {},
        description: str | None = None,
    ) -> ServiceContractConfigOperationGrant:
        """
        Creates one reusable operation grant under a ServiceContractConfig.

        Contract:
        - Parent ServiceContractConfig scope is propagated by constructor lowering.
        - Stable identity is one grant per ServiceOperationConfig under a ServiceContractConfig.
        - Quota, permit, and price policies are Service-side config snapshots; Economy owns execution
        receipts.
        - JSON policy attributes are compatibility mirrors; typed child policy objects are canonical.
        """

        payload = {
            "service_contract_config_id": service_contract_config_id,
            "service_operation_config_id": service_operation_config_id,
            "access_scope": access_scope,
            "quota_policy_json": quota_policy_json,
            "permit_policy_json": permit_policy_json,
            "price_policy_json": price_policy_json,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_contract_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractConfigOperationGrant):
            return value
        return ServiceContractConfigOperationGrant.validate_invocation_value(value)


class ServiceContractConfigOperationGrantConfigureQuotaPolicyInput(BaseModel):
    unit: ServiceContractOperationQuotaUnit = Field(default=ServiceContractOperationQuotaUnit.operation)
    limit_amount: int | None = Field(default=None)
    window: ServiceContractOperationQuotaWindow = Field(default=ServiceContractOperationQuotaWindow.none)
    burst_limit: int | None = Field(default=None)
    over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = Field(
        default=ServiceContractOperationQuotaOverLimitBehavior.deny
    )
    fail_closed: bool = Field(default=True)


class ServiceContractConfigOperationGrantConfigureQuotaPolicyOutput(BaseModel):
    value: ServiceContractOperationQuotaPolicy


class ServiceContractConfigOperationGrantConfigurePermitPolicyInput(BaseModel):
    requires_active_contract: bool = Field(default=True)
    requires_smart_contract_permit: bool = Field(default=False)
    requires_reservation_before_execute: bool = Field(default=False)
    permit_scope: ServiceContractOperationPermitScope = Field(default=ServiceContractOperationPermitScope.operation)
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = Field(
        default=ServiceContractOperationPermitIdempotencyScope.request_hash
    )
    fail_closed: bool = Field(default=True)


class ServiceContractConfigOperationGrantConfigurePermitPolicyOutput(BaseModel):
    value: ServiceContractOperationPermitPolicy


class ServiceContractConfigOperationGrantConfigurePricePolicyInput(BaseModel):
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


class ServiceContractConfigOperationGrantConfigurePricePolicyOutput(BaseModel):
    value: ServiceContractOperationPricePolicy


class ServiceContractConfigOperationGrantBuildViaServiceContractConfigInput(BaseModel):
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContractConfig.operation_grants")
    service_operation_config_id: UUID
    access_scope: str = Field(default="operation")
    quota_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    permit_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    price_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)


class ServiceContractConfigOperationGrantBuildViaServiceContractConfigOutput(BaseModel):
    value: ServiceContractConfigOperationGrant


FUNCTIONS = {
    "ServiceContractConfigOperationGrant": {
        "configure_quota_policy": {
            "canonical": {
                "name": "configure_quota_policy",
                "description": "Declares typed quota policy intent for this operation grant.\n\nContract:\n- This controls allowance semantics only.\n- Runtime metering/billing may consume this policy, but Economy owns financial receipts.",
                "is_constructor": False,
            },
            "input": ServiceContractConfigOperationGrantConfigureQuotaPolicyInput,
            "output": ServiceContractConfigOperationGrantConfigureQuotaPolicyOutput,
        },
        "configure_permit_policy": {
            "canonical": {
                "name": "configure_permit_policy",
                "description": "Declares typed permit policy intent for this operation grant.\n\nContract:\n- This controls pre-execution proof requirements.\n- Identity role evidence and Economy smart-contract receipts remain owned by their source domains.",
                "is_constructor": False,
            },
            "input": ServiceContractConfigOperationGrantConfigurePermitPolicyInput,
            "output": ServiceContractConfigOperationGrantConfigurePermitPolicyOutput,
        },
        "configure_price_policy": {
            "canonical": {
                "name": "configure_price_policy",
                "description": "Declares typed price selection policy intent for this operation grant.\n\nContract:\n- This selects or overrides Economy price truth for the granted operation.\n- Quotes, reservations, escrow, and settlement remain Economy-owned receipts.",
                "is_constructor": False,
            },
            "input": ServiceContractConfigOperationGrantConfigurePricePolicyInput,
            "output": ServiceContractConfigOperationGrantConfigurePricePolicyOutput,
        },
        "build_via_service_contract_config": {
            "canonical": {
                "name": "build_via_service_contract_config",
                "description": "Creates one reusable operation grant under a ServiceContractConfig.\n\nContract:\n- Parent ServiceContractConfig scope is propagated by constructor lowering.\n- Stable identity is one grant per ServiceOperationConfig under a ServiceContractConfig.\n- Quota, permit, and price policies are Service-side config snapshots; Economy owns execution receipts.\n- JSON policy attributes are compatibility mirrors; typed child policy objects are canonical.",
                "is_constructor": True,
            },
            "input": ServiceContractConfigOperationGrantBuildViaServiceContractConfigInput,
            "output": ServiceContractConfigOperationGrantBuildViaServiceContractConfigOutput,
        },
    },
}

__all__ = [
    "ServiceContractConfigOperationGrant",
    "ServiceContractConfigOperationGrantConfigureQuotaPolicyInput",
    "ServiceContractConfigOperationGrantConfigureQuotaPolicyOutput",
    "ServiceContractConfigOperationGrantConfigurePermitPolicyInput",
    "ServiceContractConfigOperationGrantConfigurePermitPolicyOutput",
    "ServiceContractConfigOperationGrantConfigurePricePolicyInput",
    "ServiceContractConfigOperationGrantConfigurePricePolicyOutput",
    "ServiceContractConfigOperationGrantBuildViaServiceContractConfigInput",
    "ServiceContractConfigOperationGrantBuildViaServiceContractConfigOutput",
    "FUNCTIONS",
]
