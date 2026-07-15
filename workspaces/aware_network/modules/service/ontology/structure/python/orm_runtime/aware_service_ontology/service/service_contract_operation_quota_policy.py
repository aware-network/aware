from __future__ import annotations

# Standard
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

    @classmethod
    async def build_via_service_contract_config_operation_grant(
        cls,
        service_contract_config_operation_grant_id: UUID,
        unit: ServiceContractOperationQuotaUnit = ServiceContractOperationQuotaUnit.operation,
        limit_amount: int | None = None,
        window: ServiceContractOperationQuotaWindow = ServiceContractOperationQuotaWindow.none,
        burst_limit: int | None = None,
        over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = ServiceContractOperationQuotaOverLimitBehavior.deny,
        fail_closed: bool = True,
    ) -> ServiceContractOperationQuotaPolicy:
        """
        Creates the Service-owned quota policy intent for one operation grant.

        Contract:
        - Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.
        - Quota policy declares usage allowance intent only.
        - Metering, billing, and financial settlement remain downstream runtime/Economy concerns.
        """

        payload = {
            "service_contract_config_operation_grant_id": service_contract_config_operation_grant_id,
            "unit": unit,
            "limit_amount": limit_amount,
            "window": window,
            "burst_limit": burst_limit,
            "over_limit_behavior": over_limit_behavior,
            "fail_closed": fail_closed,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_contract_config_operation_grant", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractOperationQuotaPolicy):
            return value
        return ServiceContractOperationQuotaPolicy.validate_invocation_value(value)


class ServiceContractOperationQuotaPolicyBuildViaServiceContractConfigOperationGrantInput(BaseModel):
    service_contract_config_operation_grant_id: UUID = Field(
        description="Foreign key for ServiceContractConfigOperationGrant.quota_policy"
    )
    unit: ServiceContractOperationQuotaUnit = Field(default=ServiceContractOperationQuotaUnit.operation)
    limit_amount: int | None = Field(default=None)
    window: ServiceContractOperationQuotaWindow = Field(default=ServiceContractOperationQuotaWindow.none)
    burst_limit: int | None = Field(default=None)
    over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = Field(
        default=ServiceContractOperationQuotaOverLimitBehavior.deny
    )
    fail_closed: bool = Field(default=True)


class ServiceContractOperationQuotaPolicyBuildViaServiceContractConfigOperationGrantOutput(BaseModel):
    value: ServiceContractOperationQuotaPolicy


FUNCTIONS = {
    "ServiceContractOperationQuotaPolicy": {
        "build_via_service_contract_config_operation_grant": {
            "canonical": {
                "name": "build_via_service_contract_config_operation_grant",
                "description": "Creates the Service-owned quota policy intent for one operation grant.\n\nContract:\n- Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.\n- Quota policy declares usage allowance intent only.\n- Metering, billing, and financial settlement remain downstream runtime/Economy concerns.",
                "is_constructor": True,
            },
            "input": ServiceContractOperationQuotaPolicyBuildViaServiceContractConfigOperationGrantInput,
            "output": ServiceContractOperationQuotaPolicyBuildViaServiceContractConfigOperationGrantOutput,
        },
    },
}

__all__ = [
    "ServiceContractOperationQuotaPolicy",
    "ServiceContractOperationQuotaPolicyBuildViaServiceContractConfigOperationGrantInput",
    "ServiceContractOperationQuotaPolicyBuildViaServiceContractConfigOperationGrantOutput",
    "FUNCTIONS",
]
