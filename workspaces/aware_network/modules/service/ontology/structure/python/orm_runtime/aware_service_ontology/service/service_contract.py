from __future__ import annotations

# Standard
from datetime import datetime
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
    ServiceContractKind,
    ServiceContractStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.smart_contract.smart_contract import SmartContract
    from aware_service_ontology.service.service_commercial_profile import ServiceCommercialProfile
    from aware_service_ontology.service.service_contract_config import ServiceContractConfig
    from aware_service_ontology.service.service_contract_economy_settlement import ServiceContractEconomySettlement


class ServiceContract(ORMModel):
    # Relationships
    commercial_profile: ServiceCommercialProfile | None = Field(default=None, exclude=True)
    consumer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    economy_settlement: ServiceContractEconomySettlement | None = Field(default=None, exclude=True)
    producer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    service_contract_config: ServiceContractConfig | None = Field(default=None, exclude=True)
    smart_contract: SmartContract | None = Field(default=None, exclude=True)

    # Attributes
    effective_from: datetime
    effective_until: datetime | None = Field(default=None)
    kind: ServiceContractKind
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    status: ServiceContractStatus = Field(default=ServiceContractStatus.pending)

    # Foreign Keys
    service_id: UUID = Field(description="Foreign key for Service.contracts")
    commercial_profile_id: UUID = Field(description="Foreign key for ServiceContract.commercial_profile")
    consumer_finance_entity_id: UUID = Field(description="Foreign key for ServiceContract.consumer_finance_entity")
    producer_finance_entity_id: UUID = Field(description="Foreign key for ServiceContract.producer_finance_entity")
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContract.service_contract_config")
    smart_contract_id: UUID = Field(description="Foreign key for ServiceContract.smart_contract")

    async def set_status(
        self,
        status: ServiceContractStatus,
        effective_until: datetime | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceContract:
        """Updates the lifecycle status for this ServiceContract receipt."""

        payload = {"status": status, "effective_until": effective_until, "metadata_json": metadata_json}
        result = await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContract):
            return value
        return ServiceContract.validate_invocation_value(value)

    async def configure_economy_settlement(
        self,
        permit_id: UUID,
        permit_nonce: int,
        payer_wallet_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_wallet_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
        deadline: datetime,
    ) -> ServiceContractEconomySettlement:
        """
        Binds typed Economy settlement coordinates to this concrete ServiceContract.

        Contract:
        - ServiceContract remains access/terms authority.
        - Economy owns capital mutation, spend-envelope cap checks, operation nonce allocation,
          reservation, escrow, and settlement receipts.
        - These coordinates replace the legacy metadata settlement payload for active settlement.
        """

        payload = {
            "permit_id": permit_id,
            "permit_nonce": permit_nonce,
            "payer_wallet_id": payer_wallet_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_wallet_id": receiver_wallet_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
            "deadline": deadline,
        }
        result = await invoke_instance(orm_model=self, function_name="configure_economy_settlement", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_economy_settlement import ServiceContractEconomySettlement

        if isinstance(value, ServiceContractEconomySettlement):
            return value
        return ServiceContractEconomySettlement.validate_invocation_value(value)

    @classmethod
    async def build_via_service(
        cls,
        service_id: UUID,
        service_contract_config_id: UUID,
        commercial_profile_id: UUID,
        producer_finance_entity_id: UUID,
        consumer_finance_entity_id: UUID,
        smart_contract_id: UUID,
        kind: ServiceContractKind,
        effective_from: datetime,
        status: ServiceContractStatus = ServiceContractStatus.pending,
        effective_until: datetime | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceContract:
        """
        Creates one Service-owned commercial agreement receipt under a concrete Service.

        Contract:
        - Stable identity is anchored by the parent Service containment rail plus ServiceContractConfig plus
        SmartContract.
        - `service_contract_config` points to reusable operation/role grant semantics.
        - `commercial_profile` is a typed reference rail for portal-backed provenance/navigation,
          not contract ownership or stable-id propagation.
        - Producer/consumer finance entities are settlement snapshots for this agreement.
        """

        payload = {
            "service_id": service_id,
            "service_contract_config_id": service_contract_config_id,
            "commercial_profile_id": commercial_profile_id,
            "producer_finance_entity_id": producer_finance_entity_id,
            "consumer_finance_entity_id": consumer_finance_entity_id,
            "smart_contract_id": smart_contract_id,
            "kind": kind,
            "effective_from": effective_from,
            "status": status,
            "effective_until": effective_until,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContract):
            return value
        return ServiceContract.validate_invocation_value(value)


class ServiceContractSetStatusInput(BaseModel):
    status: ServiceContractStatus
    effective_until: datetime | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceContractSetStatusOutput(BaseModel):
    value: ServiceContract


class ServiceContractConfigureEconomySettlementInput(BaseModel):
    permit_id: UUID
    permit_nonce: int
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    receiver_wallet_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    deadline: datetime


class ServiceContractConfigureEconomySettlementOutput(BaseModel):
    value: ServiceContractEconomySettlement


class ServiceContractBuildViaServiceInput(BaseModel):
    service_id: UUID = Field(description="Foreign key for Service.contracts")
    service_contract_config_id: UUID
    commercial_profile_id: UUID
    producer_finance_entity_id: UUID
    consumer_finance_entity_id: UUID
    smart_contract_id: UUID
    kind: ServiceContractKind
    effective_from: datetime
    status: ServiceContractStatus = Field(default=ServiceContractStatus.pending)
    effective_until: datetime | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceContractBuildViaServiceOutput(BaseModel):
    value: ServiceContract


FUNCTIONS = {
    "ServiceContract": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Updates the lifecycle status for this ServiceContract receipt.",
                "is_constructor": False,
            },
            "input": ServiceContractSetStatusInput,
            "output": ServiceContractSetStatusOutput,
        },
        "configure_economy_settlement": {
            "canonical": {
                "name": "configure_economy_settlement",
                "description": "Binds typed Economy settlement coordinates to this concrete ServiceContract.\n\nContract:\n- ServiceContract remains access/terms authority.\n- Economy owns capital mutation, spend-envelope cap checks, operation nonce allocation,\n  reservation, escrow, and settlement receipts.\n- These coordinates replace the legacy metadata settlement payload for active settlement.",
                "is_constructor": False,
            },
            "input": ServiceContractConfigureEconomySettlementInput,
            "output": ServiceContractConfigureEconomySettlementOutput,
        },
        "build_via_service": {
            "canonical": {
                "name": "build_via_service",
                "description": "Creates one Service-owned commercial agreement receipt under a concrete Service.\n\nContract:\n- Stable identity is anchored by the parent Service containment rail plus ServiceContractConfig plus SmartContract.\n- `service_contract_config` points to reusable operation/role grant semantics.\n- `commercial_profile` is a typed reference rail for portal-backed provenance/navigation,\n  not contract ownership or stable-id propagation.\n- Producer/consumer finance entities are settlement snapshots for this agreement.",
                "is_constructor": True,
            },
            "input": ServiceContractBuildViaServiceInput,
            "output": ServiceContractBuildViaServiceOutput,
        },
    },
}

__all__ = [
    "ServiceContract",
    "ServiceContractSetStatusInput",
    "ServiceContractSetStatusOutput",
    "ServiceContractConfigureEconomySettlementInput",
    "ServiceContractConfigureEconomySettlementOutput",
    "ServiceContractBuildViaServiceInput",
    "ServiceContractBuildViaServiceOutput",
    "FUNCTIONS",
]
