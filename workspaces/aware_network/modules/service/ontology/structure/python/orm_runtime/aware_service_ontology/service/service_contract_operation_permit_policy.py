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
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
)


class ServiceContractOperationPermitPolicy(ORMModel):
    # Attributes
    fail_closed: bool = Field(default=True)
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = Field(
        default=ServiceContractOperationPermitIdempotencyScope.request_hash
    )
    permit_scope: ServiceContractOperationPermitScope = Field(default=ServiceContractOperationPermitScope.operation)
    requires_active_contract: bool = Field(default=True)
    requires_reservation_before_execute: bool = Field(default=False)
    requires_smart_contract_permit: bool = Field(default=False)

    # Foreign Keys
    service_contract_config_operation_grant_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractConfigOperationGrant.permit_policy"
    )

    @classmethod
    async def build_via_service_contract_config_operation_grant(
        cls,
        service_contract_config_operation_grant_id: UUID,
        requires_active_contract: bool = True,
        requires_smart_contract_permit: bool = False,
        requires_reservation_before_execute: bool = False,
        permit_scope: ServiceContractOperationPermitScope = ServiceContractOperationPermitScope.operation,
        idempotency_scope: ServiceContractOperationPermitIdempotencyScope = ServiceContractOperationPermitIdempotencyScope.request_hash,
        fail_closed: bool = True,
    ) -> ServiceContractOperationPermitPolicy:
        """
        Creates the Service-owned permit policy intent for one operation grant.

        Contract:
        - Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.
        - Permit policy declares required execution proofs before an operation may run.
        - Identity still owns ActorRole evidence; Economy still owns smart-contract permits and
        reservations.
        """

        payload = {
            "service_contract_config_operation_grant_id": service_contract_config_operation_grant_id,
            "requires_active_contract": requires_active_contract,
            "requires_smart_contract_permit": requires_smart_contract_permit,
            "requires_reservation_before_execute": requires_reservation_before_execute,
            "permit_scope": permit_scope,
            "idempotency_scope": idempotency_scope,
            "fail_closed": fail_closed,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_contract_config_operation_grant", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractOperationPermitPolicy):
            return value
        return ServiceContractOperationPermitPolicy.validate_invocation_value(value)


class ServiceContractOperationPermitPolicyBuildViaServiceContractConfigOperationGrantInput(BaseModel):
    service_contract_config_operation_grant_id: UUID = Field(
        description="Foreign key for ServiceContractConfigOperationGrant.permit_policy"
    )
    requires_active_contract: bool = Field(default=True)
    requires_smart_contract_permit: bool = Field(default=False)
    requires_reservation_before_execute: bool = Field(default=False)
    permit_scope: ServiceContractOperationPermitScope = Field(default=ServiceContractOperationPermitScope.operation)
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = Field(
        default=ServiceContractOperationPermitIdempotencyScope.request_hash
    )
    fail_closed: bool = Field(default=True)


class ServiceContractOperationPermitPolicyBuildViaServiceContractConfigOperationGrantOutput(BaseModel):
    value: ServiceContractOperationPermitPolicy


FUNCTIONS = {
    "ServiceContractOperationPermitPolicy": {
        "build_via_service_contract_config_operation_grant": {
            "canonical": {
                "name": "build_via_service_contract_config_operation_grant",
                "description": "Creates the Service-owned permit policy intent for one operation grant.\n\nContract:\n- Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.\n- Permit policy declares required execution proofs before an operation may run.\n- Identity still owns ActorRole evidence; Economy still owns smart-contract permits and reservations.",
                "is_constructor": True,
            },
            "input": ServiceContractOperationPermitPolicyBuildViaServiceContractConfigOperationGrantInput,
            "output": ServiceContractOperationPermitPolicyBuildViaServiceContractConfigOperationGrantOutput,
        },
    },
}

__all__ = [
    "ServiceContractOperationPermitPolicy",
    "ServiceContractOperationPermitPolicyBuildViaServiceContractConfigOperationGrantInput",
    "ServiceContractOperationPermitPolicyBuildViaServiceContractConfigOperationGrantOutput",
    "FUNCTIONS",
]
